"""真 MCP client adapter（Capability Gateway · ROADMAP U3）。

可注入 transport/session；统一仍走 gateway ``invoke → CapabilityResult``。
默认**不**注册（``OPS_CAPABILITY_MCP_ENABLED`` 关）；CI 用 ``FakeTransport`` 零外网。
**不**引入 MCP 官方重 SDK；HTTP JSON-RPC 仅为可选薄 transport。
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
import uuid
from typing import Any, Protocol, runtime_checkable

# 稳定 id（env 开启时注册；单测可覆盖）
MCP_CLIENT_CAPABILITY_ID = "mcp_client"


class McpClientError(Exception):
    """MCP 协议 / transport 失败（gateway 捕获 → ``ok=False``）。"""


@runtime_checkable
class McpTransport(Protocol):
    """可注入的 MCP tools/call 传输面（stdio / HTTP / Fake 均可）。"""

    def call_tool(self, name: str, arguments: Any) -> Any:
        """执行 ``tools/call``；失败应 raise（勿吞异常）。"""
        ...


class FakeTransport:
    """单测用假传输：零 socket / 零外网。

    - 默认返回 ``result``
    - ``error`` 非空 → raise ``McpClientError``
    - ``exc`` 非空 → 原样 raise
    """

    def __init__(
        self,
        *,
        result: Any = None,
        error: str | None = None,
        exc: BaseException | None = None,
    ) -> None:
        self._result: Any = (
            {"content": [{"type": "text", "text": "ok"}]} if result is None else result
        )
        self._error = error
        self._exc = exc
        self.calls: list[tuple[str, Any]] = []

    def call_tool(self, name: str, arguments: Any) -> Any:
        self.calls.append((name, arguments))
        if self._exc is not None:
            raise self._exc
        if self._error is not None:
            raise McpClientError(self._error)
        return self._result


class HttpJsonRpcTransport:
    """可选薄 HTTP JSON-RPC transport（``tools/call``）。

    仅在显式构造 / env 开启且配置了 endpoint 时使用；默认 CI 路径不实例化。
    """

    def __init__(self, endpoint: str, *, timeout_s: float = 30.0) -> None:
        self._endpoint = (endpoint or "").strip()
        if not self._endpoint:
            raise ValueError("MCP HTTP endpoint 不能为空")
        self._timeout_s = timeout_s

    def call_tool(self, name: str, arguments: Any) -> Any:
        payload = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments if arguments is not None else {}},
        }
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self._endpoint,
            data=body,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self._timeout_s) as resp:
                raw = resp.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:200]
            raise McpClientError(f"MCP HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise McpClientError(f"MCP 网络错误: {exc.reason!r}") from exc
        except TimeoutError as exc:
            raise McpClientError("MCP 请求超时") from exc

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise McpClientError(f"MCP 响应非 JSON: {raw[:120]!r}") from exc

        if not isinstance(data, dict):
            raise McpClientError("MCP 响应形状非法")
        if "error" in data and data["error"] is not None:
            err = data["error"]
            msg = err.get("message", repr(err)) if isinstance(err, dict) else repr(err)
            raise McpClientError(f"MCP JSON-RPC error: {msg}")
        result = data.get("result")
        if isinstance(result, dict) and result.get("isError"):
            raise McpClientError(f"MCP tools/call isError: {result!r}"[:200])
        return result


class McpClientAdapter:
    """真 MCP client；``kind=mcp``，契约与 Mock 相同：``invoke(args) → Any``。

    ``args`` 形状（推荐）::

        {"name": "tool_name", "arguments": {...}}

    若构造时传入 ``default_tool``，也可直接传 arguments（dict / 任意）。
    """

    kind = "mcp"

    def __init__(
        self,
        transport: McpTransport,
        *,
        default_tool: str | None = None,
    ) -> None:
        self._transport = transport
        self._default_tool = (default_tool or "").strip() or None

    def invoke(self, args: Any, *, ctx: dict[str, Any] | None = None) -> Any:
        del ctx
        name, arguments = self._resolve_call(args)
        result = self._transport.call_tool(name, arguments)
        if isinstance(result, dict) and result.get("isError"):
            raise McpClientError(f"MCP tools/call isError: {result!r}"[:200])
        return {
            "protocol": "mcp",
            "kind": self.kind,
            "tool": name,
            "result": result,
        }

    def _resolve_call(self, args: Any) -> tuple[str, Any]:
        if isinstance(args, dict) and "name" in args:
            name = str(args.get("name") or "").strip()
            if not name:
                raise McpClientError("MCP tools/call 缺少 name")
            return name, args.get("arguments", {})
        if self._default_tool:
            return self._default_tool, args if args is not None else {}
        raise McpClientError(
            "MCP tools/call 需 args={'name':..., 'arguments':...} 或构造时指定 default_tool"
        )


def register_mcp_client_if_enabled(
    *,
    enabled: bool | None = None,
    transport: McpTransport | None = None,
    capability_id: str = MCP_CLIENT_CAPABILITY_ID,
    default_tool: str | None = None,
    description: str = "真 MCP client（env 开启；默认 CI 不注册）",
) -> str | None:
    """按 env / 显式参数注册真 client；未启用或缺少 transport/endpoint → 不注册。

    返回新注册的 capability_id；跳过时返回 None。
    """
    from app.config import settings
    from app.ops.capability.gateway import get_registry, register
    from app.ops.capability.types import CapabilitySpec

    flag = settings.ops_capability_mcp_enabled if enabled is None else enabled
    if not flag:
        return None

    registry = get_registry()
    if registry.get(capability_id) is not None:
        return None

    tool = (default_tool or settings.ops_capability_mcp_default_tool or "").strip() or None
    tx = transport
    if tx is None:
        endpoint = (settings.ops_capability_mcp_endpoint or "").strip()
        if not endpoint:
            return None
        tx = HttpJsonRpcTransport(endpoint)

    register(
        CapabilitySpec(
            capability_id=capability_id,
            kind="mcp",
            description=description,
            tags=("mcp", "client", "u3"),
            risk_level="medium",
            enabled=True,
        ),
        McpClientAdapter(tx, default_tool=tool),
    )
    return capability_id
