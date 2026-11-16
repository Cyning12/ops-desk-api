"""P2b-T2 · MCP 薄 transport：``McpTransport`` Protocol（async 形态）+ stdio/http 两实现。

帧纪律
------
- **stdio**：`asyncio.create_subprocess_exec` 拉起子进程，stdin/stdout 走**换行分隔
  JSON-RPC**（一行一帧）。env **白名单过滤**：不整体继承 `os.environ`，仅
  `MINIMAL_ENV_KEYS` 最小集 + `env_allowlist` 显式键（11 终稿 §5.3）。
  `cwd` 缺省 None = 继承 API 仓 CWD（§5.3）。
- **http**：StreamableHTTP 最小子集——POST `application/json`，Accept 同时声明
  `text/event-stream`；应答为 json 直取，为 SSE 则逐 `data:` 帧解析取消息。

server→client 消息纪律（两传输共用 `_ResponseMux`）
---------------------------------------------------
- `ping` 请求 → 立即回 `{}` result；
- **其余请求 1s 内回 JSON-RPC 错误 -32601 防挂起**（委派书 §5-⑤ · 立即发送，远低于 1s）；
- 通知（无 id）安全忽略——含 `notifications/tools/list_changed` 不响应不动作
  （委派书 §5-⑥ · 与禁热加载同构）。

超时纪律：`request(..., timeout_s=...)` 由 `asyncio.wait_for` 统一收口
（HTTP client 自身 timeout=None，避免双层超时互相踩）。
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import os
from collections.abc import Awaitable, Callable
from typing import Any, Protocol

import httpx

from app.ops.capability.errors import CAUSE_HTTP_STATUS
from app.ops.capability.mcp.errors import (
    McpProtocolError,
    McpTimeoutError,
    McpTransportError,
)
from app.ops.capability.mcp.jsonrpc import (
    METHOD_NOT_FOUND,
    JsonRpcRemoteError,
    is_notification,
    is_request,
    make_error,
    make_request,
    make_result,
    next_id,
)

logger = logging.getLogger(__name__)

#: stdio 子进程 env 最小集（不继承 os.environ · §5.3；env_allowlist 显式键在此之上叠加）
MINIMAL_ENV_KEYS: tuple[str, ...] = (
    "PATH",
    "HOME",
    "LANG",
    "LC_ALL",
    "LC_CTYPE",
    "TZ",
    "TMPDIR",
    "TEMP",
    "TMP",
    "SystemRoot",
    "WINDIR",
)


def filtered_env(
    environ: dict[str, str] | os._Environ[str], allowlist: tuple[str, ...] | list[str]
) -> dict[str, str]:
    """白名单过滤：最小集 + allowlist 显式键；**其余环境变量一律不传给子进程**。"""
    env: dict[str, str] = {}
    for key in (*MINIMAL_ENV_KEYS, *allowlist):
        if key in environ:
            env[key] = str(environ[key])
    return env


class McpTransport(Protocol):
    """MCP transport async 协议面（session 只见 JSON-RPC 语义，不见帧格式）。"""

    async def start(self) -> None:
        """拉起底层通道（stdio 起子进程 / http 建 client）。幂等。"""
        ...

    async def request(
        self, method: str, params: dict[str, Any] | None = None, *, timeout_s: float
    ) -> Any:
        """发 JSON-RPC 请求并等应答 result；超时抛 McpTimeoutError，
        远端 error 应答抛 JsonRpcRemoteError，传输失败抛 McpTransportError。"""
        ...

    async def notify(self, method: str, params: dict[str, Any] | None = None) -> None:
        """发 JSON-RPC 通知（无应答）。"""
        ...

    async def aclose(self) -> None:
        """关闭通道并回收资源。幂等。"""
        ...


class _ResponseMux:
    """response / server→client 请求 / 通知 三态分发 + pending 请求表（两传输共用）。

    ``send`` 由具体 transport 提供：stdio=写 stdin 行；http=POST 并解析应答体
    （应答消息经 `handle_message` 回流本 mux）。
    """

    def __init__(self, send: Callable[[dict[str, Any]], Awaitable[None]]) -> None:
        self._send = send
        self._pending: dict[Any, asyncio.Future[Any]] = {}
        self._bg: set[asyncio.Task[None]] = set()

    # ---- 入向分发 ----

    def handle_message(self, msg: Any) -> None:
        if not isinstance(msg, dict):
            return
        if is_request(msg):
            self._answer_server_request(msg)
            return
        if is_notification(msg):
            # 安全忽略（含 notifications/tools/list_changed · 不响应不动作）
            return
        # response
        fut = self._pending.pop(msg.get("id"), None)
        if fut is None or fut.done():
            return  # 未知/迟到应答：忽略
        error = msg.get("error")
        if error is not None:
            fut.set_exception(
                JsonRpcRemoteError(
                    int(error.get("code", 0)),
                    str(error.get("message", "")),
                    error.get("data"),
                )
            )
        else:
            fut.set_result(msg.get("result"))

    def _answer_server_request(self, msg: dict[str, Any]) -> None:
        """server→client 请求：ping 回 {}，其余立即回 -32601（1s 内防挂起 · §5-⑤）。"""
        method = str(msg.get("method", ""))
        if method == "ping":
            reply = make_result(msg["id"], {})
        else:
            reply = make_error(
                msg["id"], METHOD_NOT_FOUND, f"server→client 方法不支持: {method}"
            )
        task = asyncio.ensure_future(self._send_quiet(reply))
        self._bg.add(task)
        task.add_done_callback(self._bg.discard)

    async def _send_quiet(self, payload: dict[str, Any]) -> None:
        try:
            await self._send(payload)
        except Exception:  # noqa: BLE001 - 回执失败仅记日志，绝不反噬主链路
            logger.warning("mcp server→client 应答发送失败", exc_info=True)

    # ---- 出向请求 ----

    async def call(
        self, method: str, params: dict[str, Any] | None, timeout_s: float
    ) -> Any:
        req_id = next_id()
        loop = asyncio.get_running_loop()
        fut: asyncio.Future[Any] = loop.create_future()
        self._pending[req_id] = fut
        try:
            return await asyncio.wait_for(
                self._roundtrip(req_id, method, params, fut), timeout=timeout_s
            )
        except TimeoutError:
            raise McpTimeoutError(f"mcp 请求 {method} 超时（{timeout_s:.1f}s）") from None
        finally:
            self._pending.pop(req_id, None)

    async def _roundtrip(
        self,
        req_id: Any,
        method: str,
        params: dict[str, Any] | None,
        fut: asyncio.Future[Any],
    ) -> Any:
        await self._send(make_request(req_id, method, params))
        return await fut

    def fail_all(self, exc: BaseException) -> None:
        """通道级故障：所有在途请求同因失败（子进程退出 / 非 JSON 帧）。"""
        pending = list(self._pending.values())
        self._pending.clear()
        for fut in pending:
            if not fut.done():
                fut.set_exception(exc)


class StdioTransport:
    """stdio transport：子进程 + 换行 JSON-RPC 行帧 + env 白名单过滤。"""

    def __init__(
        self,
        *,
        command: str,
        args: tuple[str, ...] | list[str] = (),
        cwd: str | None = None,
        env_allowlist: tuple[str, ...] | list[str] = (),
    ) -> None:
        if not command:
            raise ValueError("stdio transport 需要 command")
        self._argv = (command, *args)
        self._cwd = cwd  # None = 继承 API 仓 CWD（§5.3 缺省）
        self._env = filtered_env(os.environ, env_allowlist)
        self._proc: asyncio.subprocess.Process | None = None
        self._reader_task: asyncio.Task[None] | None = None
        self._stderr_task: asyncio.Task[None] | None = None
        self._mux = _ResponseMux(self._write_payload)
        self._closed = False

    async def start(self) -> None:
        if self._proc is not None:
            return
        try:
            self._proc = await asyncio.create_subprocess_exec(
                *self._argv,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self._cwd,
                env=self._env,
            )
        except (FileNotFoundError, PermissionError, OSError) as exc:
            raise McpTransportError(
                f"stdio 子进程拉起失败: {self._argv[0]}: {exc}"
            ) from exc
        self._reader_task = asyncio.create_task(self._read_loop(), name="mcp-stdio-reader")
        self._stderr_task = asyncio.create_task(
            self._drain_stderr(), name="mcp-stdio-stderr"
        )

    async def request(
        self, method: str, params: dict[str, Any] | None = None, *, timeout_s: float
    ) -> Any:
        self._require_started()
        return await self._mux.call(method, params, timeout_s)

    async def notify(self, method: str, params: dict[str, Any] | None = None) -> None:
        self._require_started()
        from app.ops.capability.mcp.jsonrpc import make_notification

        await self._write_payload(make_notification(method, params))

    async def aclose(self) -> None:
        if self._closed:
            return
        self._closed = True
        for task in (self._reader_task, self._stderr_task):
            if task is not None:
                task.cancel()
        proc = self._proc
        if proc is None:
            return
        if proc.stdin is not None:
            with contextlib.suppress(BrokenPipeError, RuntimeError):
                proc.stdin.close()
        if proc.returncode is None:
            # §5.1：terminate → 5s 宽限 → kill
            with contextlib.suppress(ProcessLookupError):
                proc.terminate()
            try:
                await asyncio.wait_for(proc.wait(), timeout=5.0)
            except TimeoutError:
                with contextlib.suppress(ProcessLookupError):
                    proc.kill()
                await proc.wait()
        self._mux.fail_all(McpTransportError("stdio transport 已关闭"))
        for task in (self._reader_task, self._stderr_task):
            if task is not None:
                with contextlib.suppress(asyncio.CancelledError):
                    await task

    # ---- 内部 ----

    def _require_started(self) -> None:
        if self._proc is None or self._closed:
            raise McpTransportError("stdio transport 未启动或已关闭")

    async def _write_payload(self, payload: dict[str, Any]) -> None:
        proc = self._proc
        if proc is None or proc.stdin is None or proc.returncode is not None:
            raise McpTransportError("stdio 子进程不可写（未启动或已退出）")
        try:
            proc.stdin.write(json.dumps(payload, ensure_ascii=False).encode("utf-8") + b"\n")
            await proc.stdin.drain()
        except (BrokenPipeError, ConnectionResetError) as exc:
            raise McpTransportError(f"stdio 写帧失败: {exc}") from exc

    async def _read_loop(self) -> None:
        proc = self._proc
        assert proc is not None and proc.stdout is not None
        while True:
            try:
                line = await proc.stdout.readline()
            except (ValueError, RuntimeError) as exc:
                self._mux.fail_all(McpTransportError(f"stdio 读帧失败: {exc}"))
                return
            if not line:  # EOF：子进程退出
                self._mux.fail_all(
                    McpTransportError(f"stdio 子进程退出（exit={proc.returncode}）")
                )
                return
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                # 换行 JSON-RPC 帧纪律：一行必须是一帧合法 JSON；违例视为通道级故障
                self._mux.fail_all(McpProtocolError("stdio 帧非 JSON（对端违反行帧纪律）"))
                return
            self._mux.handle_message(msg)

    async def _drain_stderr(self) -> None:
        proc = self._proc
        assert proc is not None and proc.stderr is not None
        while True:
            line = await proc.stderr.readline()
            if not line:
                return
            logger.debug("mcp stdio stderr: %s", line.decode("utf-8", "replace").rstrip())


class HttpTransport:
    """StreamableHTTP 最小子集 transport：POST application/json（Accept 兼声明 SSE）。"""

    def __init__(self, *, url: str) -> None:
        if not url:
            raise ValueError("http transport 需要 url")
        self._url = url
        self._client: httpx.AsyncClient | None = None
        self._mux = _ResponseMux(self._post_payload)
        self._closed = False

    async def start(self) -> None:
        if self._client is None:
            # timeout=None：超时由 mux.call 的 wait_for 统一收口，避免双层超时互踩
            self._client = httpx.AsyncClient(timeout=None)

    async def request(
        self, method: str, params: dict[str, Any] | None = None, *, timeout_s: float
    ) -> Any:
        self._require_started()
        return await self._mux.call(method, params, timeout_s)

    async def notify(self, method: str, params: dict[str, Any] | None = None) -> None:
        self._require_started()
        from app.ops.capability.mcp.jsonrpc import make_notification

        await self._post_payload(make_notification(method, params))

    async def aclose(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._mux.fail_all(McpTransportError("http transport 已关闭"))
        if self._client is not None:
            await self._client.aclose()

    # ---- 内部 ----

    def _require_started(self) -> None:
        if self._client is None or self._closed:
            raise McpTransportError("http transport 未启动或已关闭")

    async def _post_payload(self, payload: dict[str, Any]) -> None:
        client = self._client
        assert client is not None
        try:
            resp = await client.post(
                self._url,
                json=payload,
                headers={"Accept": "application/json, text/event-stream"},
            )
        except httpx.TimeoutException as exc:
            raise McpTimeoutError(f"mcp http 请求超时: {exc}") from exc
        except httpx.HTTPError as exc:
            raise McpTransportError(f"mcp http 连接失败: {exc}") from exc
        if resp.status_code == 202 or not resp.content:
            return  # 通知/无应答体面
        if resp.status_code != 200:
            raise McpTransportError(
                f"mcp http 应答状态 {resp.status_code}",
                cause=CAUSE_HTTP_STATUS,
                http_status=resp.status_code,
            )
        content_type = resp.headers.get("content-type", "")
        if content_type.startswith("text/event-stream"):
            self._handle_sse(resp.text)
            return
        try:
            msg = json.loads(resp.text)
        except json.JSONDecodeError as exc:
            raise McpProtocolError("mcp http 应答非 JSON") from exc
        self._mux.handle_message(msg)

    def _handle_sse(self, body: str) -> None:
        """解析 SSE 帧：逐 event 收集 data: 行，拼出完整 JSON 消息回流 mux。"""
        data_lines: list[str] = []
        for raw_line in body.splitlines() + [""]:  # 末尾补空行收尾最后一帧
            line = raw_line.rstrip("\r")
            if line.startswith("data:"):
                data_lines.append(line[5:].lstrip())
                continue
            if line == "" and data_lines:
                payload = "\n".join(data_lines)
                data_lines = []
                try:
                    msg = json.loads(payload)
                except json.JSONDecodeError:
                    logger.warning("mcp http SSE 帧非 JSON，跳过")
                    continue
                self._mux.handle_message(msg)


__all__ = [
    "MINIMAL_ENV_KEYS",
    "HttpTransport",
    "McpTransport",
    "StdioTransport",
    "filtered_env",
]
