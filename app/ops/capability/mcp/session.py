"""P2b-T2 · `McpSession`：握手（降级链 + 钉版断言 + expected_server 校验 + ping 门）与调用面。

握手链（委派书 §5-④ · 偏差 D2 调和）
-----------------------------------
config 层钉版语义不变（`mcp_config.py` 仅接受 2025-06-18 = **首选版本**）；session 层
实现单回退链 `SUPPORTED_PROTOCOL_VERSIONS`：initialize 失败或 server 应答的
`protocolVersion` 不在支持集时按链降级重试；链耗尽 → `McpHandshakeError` 断连。

双超时分层（委派书 §5-②）：配置值 → transport 默认 → 调用时 `clamp(floor=1000ms,
cap=120000ms)`；默认 connect_timeout=10s / call_timeout=30s 钉死（mcp_config.py
_DEFAULT_* 同值）。

调用面：`call_tool` 经 `circuit.guard` 熔断（key 按 server · 委派书 §5-④ /
终稿 §5.4）；读工具超时/传输失败**重试 1 次**，写工具禁重试（§5.4）。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from app.ops.capability import circuit
from app.ops.capability.mcp.errors import (
    McpError,
    McpHandshakeError,
    McpIdentityMismatchError,
    McpTimeoutError,
    McpTransportError,
)
from app.ops.capability.mcp.jsonrpc import JsonRpcRemoteError
from app.ops.capability.mcp.transport import McpTransport
from app.ops.capability.mcp_config import McpServerConfig
from app.ops.capability.types import WRITE_SIDE_EFFECTS
from app.ops.tracing import trace_span

logger = logging.getLogger(__name__)

#: 握手降级链（首选 = config.protocol_version 钉版 2025-06-18；应答版本须 ∈ 本集否则断连）
SUPPORTED_PROTOCOL_VERSIONS: tuple[str, ...] = ("2025-06-18", "2025-03-26", "2024-11-05")

#: 双超时 clamp 边界（委派书 §5-② 表照抄：floor 1000ms / cap 120000ms）
TIMEOUT_FLOOR_S = 1.0
TIMEOUT_CAP_S = 120.0

#: 默认超时钉死（与 mcp_config.py _DEFAULT_CONNECT_TIMEOUT_S/_DEFAULT_CALL_TIMEOUT_S 同值）
DEFAULT_CONNECT_TIMEOUT_S = 10.0
DEFAULT_CALL_TIMEOUT_S = 30.0

CLIENT_INFO: dict[str, str] = {"name": "ops-desk-api", "version": "p2b-t2"}


def clamp_timeout_s(
    value: float | int | None,
    *,
    default: float,
    floor: float = TIMEOUT_FLOOR_S,
    cap: float = TIMEOUT_CAP_S,
) -> float:
    """双超时分层收口：None → default；其余 clamp 到 [floor, cap]。"""
    if value is None:
        value = default
    v = float(value)
    if v != v or v <= 0:  # NaN / 非正 → default（config 层已拒非正，此处双保险）
        v = float(default)
    return min(max(v, floor), cap)


@dataclass(frozen=True)
class _McpCircuitSpec:
    """circuit.guard 的轻量 spec：breaker key 按 server（`mcp.{server_key}`）。

    `side_effect` 承接调用语义：写态在熔断非 closed 时不参与半开探测
    （circuit.check · 写探测限制）。
    """

    capability_id: str
    side_effect: str


class McpSession:
    """一条已建立 MCP 会话（单 server）。由 `connect` 类方法产出，勿直接构造。"""

    def __init__(
        self,
        *,
        key: str,
        config: McpServerConfig,
        transport: McpTransport,
        negotiated_version: str,
        server_info: dict[str, Any],
        tools: tuple[dict[str, Any], ...],
    ) -> None:
        self.key = key
        self.config = config
        self.transport = transport
        self.negotiated_version = negotiated_version
        self.server_info = server_info
        #: 启动期 tools/list 原始结果（翻译/exclude/overrides 是 T3 地盘，此处原样缓存）
        self.tools = tools

    # ---- 生命周期 ----

    @classmethod
    async def connect(cls, config: McpServerConfig, transport: McpTransport) -> McpSession:
        """建连 + 握手 + expected_server 校验 + ping 门 + tools/list。

        任一步失败：关闭 transport 清理半成品（含取消），异常上抛给 manager 隔离。
        """
        await transport.start()
        try:
            negotiated, server_info = await cls._handshake(config, transport)
            await cls._ping_gate(config, transport)
            tools = await cls._list_tools(config, transport)
        except BaseException:
            await cls._safe_close(transport)
            raise
        return cls(
            key=config.key,
            config=config,
            transport=transport,
            negotiated_version=negotiated,
            server_info=server_info,
            tools=tools,
        )

    async def aclose(self) -> None:
        await self.transport.aclose()

    # ---- 调用面 ----

    async def call_tool(
        self,
        name: str,
        arguments: dict[str, Any] | None = None,
        *,
        side_effect: str | None = None,
    ) -> Any:
        """tools/call：双超时 clamp + 熔断按 server + 读重试 1 次/写禁重试（§5.4）。

        `side_effect` 缺省取 config.default_side_effect，再缺省按 `read`
        （宁可多探一次，不误拦写 · 与 circuit 写探测默认否对齐）。
        """
        timeout = clamp_timeout_s(
            self.config.call_timeout_s, default=DEFAULT_CALL_TIMEOUT_S
        )
        se = side_effect or self.config.default_side_effect or "read"
        spec = _McpCircuitSpec(capability_id=f"mcp.{self.key}", side_effect=se)
        is_write = se in WRITE_SIDE_EFFECTS
        attempts = 1 if is_write else 2  # 读重试 1 次（共 2 试）· 写禁重试
        last_exc: BaseException | None = None
        for _ in range(attempts):
            try:
                with circuit.guard(spec):
                    return await self.transport.request(
                        "tools/call",
                        {"name": name, "arguments": arguments or {}},
                        timeout_s=timeout,
                    )
            except (McpTransportError, McpTimeoutError) as exc:
                # 环境类（含超时）才允许读重试；JsonRpcRemoteError（业务）与
                # CircuitOpen 不重试，直接上抛
                last_exc = exc
                continue
        assert last_exc is not None
        raise last_exc

    async def list_tools(self) -> tuple[dict[str, Any], ...]:
        """启动期缓存的 tools/list 原样返回（禁热加载：不重拉 · list_changed 不响应）。"""
        return self.tools

    # ---- 握手内部 ----

    @classmethod
    async def _handshake(
        cls, config: McpServerConfig, transport: McpTransport
    ) -> tuple[str, dict[str, Any]]:
        connect_timeout = clamp_timeout_s(
            config.connect_timeout_s, default=DEFAULT_CONNECT_TIMEOUT_S
        )
        # 首选 = config 钉版；其后接回退链其余版本
        chain = (
            config.protocol_version,
            *(v for v in SUPPORTED_PROTOCOL_VERSIONS if v != config.protocol_version),
        )
        last_exc: BaseException | None = None
        for version in chain:
            try:
                result = await transport.request(
                    "initialize",
                    {
                        "protocolVersion": version,
                        "capabilities": {},
                        "clientInfo": dict(CLIENT_INFO),
                    },
                    timeout_s=connect_timeout,
                )
            except (McpError, JsonRpcRemoteError) as exc:
                logger.warning(
                    "mcp initialize 版本 %s 失败（server=%s）：%s", version, config.key, exc
                )
                last_exc = exc
                continue
            result = result or {}
            offered = result.get("protocolVersion")
            if offered in SUPPORTED_PROTOCOL_VERSIONS:
                # 握手成功：发 initialized 通知后进 expected_server 校验
                await transport.notify("notifications/initialized")
                server_info = result.get("serverInfo") or {}
                cls._assert_expected_server(config, server_info)
                return str(offered), server_info
            logger.warning(
                "mcp server=%s 应答 protocolVersion=%r 不在支持集，降级重试",
                config.key,
                offered,
            )
            last_exc = McpHandshakeError(
                f"server 应答 protocolVersion={offered!r} 不在支持集 {SUPPORTED_PROTOCOL_VERSIONS}"
            )
        raise McpHandshakeError(
            f"initialize 握手失败：版本链 {chain} 全部失败（server={config.key}）"
        ) from last_exc

    @staticmethod
    def _assert_expected_server(
        config: McpServerConfig, server_info: dict[str, Any]
    ) -> None:
        expected = config.expected_server
        if expected is None:
            return
        # 委派书口径：serverInfo.name 精确相等（version 字段不入校验 · 留 T3/后续面）
        actual = server_info.get("name")
        if actual != expected.name:
            with trace_span(
                "mcp.connect",
                tags=["mcp", "connect"],
                server=config.key,
                reason="identity_mismatch",
                expected=expected.name,
                actual=actual,
            ):
                pass
            logger.warning(
                "mcp server=%s identity mismatch：expected=%r actual=%r，拒连",
                config.key,
                expected.name,
                actual,
            )
            raise McpIdentityMismatchError(
                f"identity_mismatch: expected serverInfo.name={expected.name!r}, "
                f"actual={actual!r}（server={config.key}）"
            )

    @classmethod
    async def _ping_gate(cls, config: McpServerConfig, transport: McpTransport) -> None:
        """ping 门：握手成功后首 ping 验证活性；不过则断连（委派书「ping 门」）。"""
        timeout = clamp_timeout_s(
            config.connect_timeout_s, default=DEFAULT_CONNECT_TIMEOUT_S
        )
        try:
            await transport.request("ping", timeout_s=timeout)
        except Exception as exc:
            raise McpHandshakeError(f"ping 门未过（server={config.key}）") from exc

    @classmethod
    async def _list_tools(
        cls, config: McpServerConfig, transport: McpTransport
    ) -> tuple[dict[str, Any], ...]:
        timeout = clamp_timeout_s(config.call_timeout_s, default=DEFAULT_CALL_TIMEOUT_S)
        result = await transport.request("tools/list", timeout_s=timeout)
        tools = (result or {}).get("tools") or []
        return tuple(t for t in tools if isinstance(t, dict))

    @staticmethod
    async def _safe_close(transport: McpTransport) -> None:
        try:
            await transport.aclose()
        except Exception:  # noqa: BLE001 - 清理失败不掩盖握手根因
            logger.warning("mcp transport 清理失败", exc_info=True)


__all__ = [
    "CLIENT_INFO",
    "DEFAULT_CALL_TIMEOUT_S",
    "DEFAULT_CONNECT_TIMEOUT_S",
    "SUPPORTED_PROTOCOL_VERSIONS",
    "TIMEOUT_CAP_S",
    "TIMEOUT_FLOOR_S",
    "McpSession",
    "clamp_timeout_s",
]
