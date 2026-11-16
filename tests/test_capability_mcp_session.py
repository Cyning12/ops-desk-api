"""P2b-T2 · McpSession 单测（FakeTransport）：握手降级/超时/identity/重试/clamp。

协议覆盖锚（委派书 m00002 · 登记偏差 D1：节号以委派书内联细节为准）
-------------------------------------------------------------------
- 握手：一次试 config.protocol_version（=2025-06-18 钉版首选），失败按
  SUPPORTED_PROTOCOL_VERSIONS 降级重试；server 应答版本须在支持集否则继续降级；
  链穷尽 → McpHandshakeError 断连（D2 调和：终稿 §11 钉版唯一 vs 委派书回退表）。
- initialize timeout = clamp(connect_timeout)（默认 10s · floor 1s · cap 120s）。
- expected_server：serverInfo.name 精确相等，不匹配 → McpIdentityMismatchError + 断连。
- ping 门：握手后 ping，失败拒连。
- call_tool：clamp floor/cap · 读（side_effect=read）重试 1 次 · 写禁重试（§5.4）。
"""

from __future__ import annotations

import pytest

from app.ops.capability.mcp import jsonrpc
from app.ops.capability.mcp.errors import (
    McpHandshakeError,
    McpIdentityMismatchError,
    McpTimeoutError,
    McpTransportError,
)
from app.ops.capability.mcp.jsonrpc import JsonRpcRemoteError
from app.ops.capability.mcp.session import (
    SUPPORTED_PROTOCOL_VERSIONS,
    McpSession,
    clamp_timeout_s,
)
from app.ops.capability.mcp_config import McpExpectedServer, McpServerConfig


class FakeTransport:
    """内存 transport：按 method 分派 handler，记录全部调用。"""

    def __init__(self, handlers: dict | None = None) -> None:
        self.handlers = dict(handlers or {})
        self.started = False
        self.closed = False
        self.calls: list[tuple[str, object, float | None]] = []
        self.notified: list[str] = []

    async def start(self) -> None:
        self.started = True

    async def request(self, method, params=None, *, timeout_s=None):
        self.calls.append((method, params, timeout_s))
        handler = self.handlers.get(method)
        if handler is None:
            return {}
        value = handler(params) if callable(handler) else handler
        if isinstance(value, BaseException):
            raise value
        return value

    async def notify(self, method, params=None) -> None:
        self.notified.append(method)

    async def aclose(self) -> None:
        self.closed = True


def _config(**overrides) -> McpServerConfig:
    base = {"key": "s1", "transport": "stdio", "command": "stub"}
    base.update(overrides)
    return McpServerConfig(**base)


def _initialize_result(version: str = "2025-06-18", name: str = "srv") -> dict:
    return {
        "protocolVersion": version,
        "capabilities": {},
        "serverInfo": {"name": name, "version": "1.0"},
    }


def _ok_handlers(**overrides) -> dict:
    handlers = {
        "initialize": _initialize_result(),
        "ping": {},
        "tools/list": {"tools": [{"name": "echo"}]},
    }
    handlers.update(overrides)
    return handlers


# ---------------------------------------------------------------- 握手


async def test_connect_happy_path_handshake_ping_gate_and_tools() -> None:
    transport = FakeTransport(_ok_handlers())
    session = await McpSession.connect(_config(), transport)
    assert transport.started
    assert session.negotiated_version == "2025-06-18"
    assert session.server_info == {"name": "srv", "version": "1.0"}
    assert [t["name"] for t in session.tools] == ["echo"]
    assert "notifications/initialized" in transport.notified
    # tools 缓存：list_tools 不重拉（§5-⑥ 同构 · 禁热加载）
    again = await session.list_tools()
    assert again == session.tools
    assert [c[0] for c in transport.calls].count("tools/list") == 1


async def test_handshake_fallback_on_method_not_found() -> None:
    offered: list[str] = []

    def initialize(params) -> dict:
        offered.append(params["protocolVersion"])
        if params["protocolVersion"] == "2025-06-18":
            raise JsonRpcRemoteError(code=-32601, message="unsupported version")
        return _initialize_result(version=params["protocolVersion"])

    transport = FakeTransport(_ok_handlers(initialize=initialize))
    session = await McpSession.connect(_config(), transport)
    assert offered == ["2025-06-18", "2025-03-26"]
    assert session.negotiated_version == "2025-03-26"


async def test_handshake_fallback_when_server_answers_unsupported_version() -> None:
    def initialize(params) -> dict:
        if params["protocolVersion"] == "2025-06-18":
            return _initialize_result(version="2099-01-01")  # 不在支持集
        return _initialize_result(version=params["protocolVersion"])

    transport = FakeTransport(_ok_handlers(initialize=initialize))
    session = await McpSession.connect(_config(), transport)
    assert session.negotiated_version == "2025-03-26"


async def test_handshake_chain_exhausted_raises_and_closes() -> None:
    def initialize(params) -> dict:
        return _initialize_result(version="2099-01-01")  # 永远不支持

    transport = FakeTransport(_ok_handlers(initialize=initialize))
    with pytest.raises(McpHandshakeError, match="全部失败"):
        await McpSession.connect(_config(), transport)
    assert transport.closed  # 断连清理


async def test_handshake_initialize_timeout_raises_and_closes() -> None:
    transport = FakeTransport(
        _ok_handlers(initialize=McpTimeoutError("initialize 超时（10.0s）"))
    )
    with pytest.raises(McpHandshakeError, match="握手失败"):
        await McpSession.connect(_config(), transport)
    assert transport.closed


async def test_initialize_timeout_value_is_clamped_connect_timeout() -> None:
    transport = FakeTransport(_ok_handlers())
    await McpSession.connect(_config(connect_timeout_s=0.001), transport)
    init_call = next(c for c in transport.calls if c[0] == "initialize")
    assert init_call[2] == 1.0  # floor 1000ms
    await McpSession.connect(_config(connect_timeout_s=9999.0), FakeTransport(_ok_handlers()))


async def test_ping_gate_failure_rejects_connection() -> None:
    transport = FakeTransport(_ok_handlers(ping=McpTimeoutError("ping 超时")))
    with pytest.raises(McpHandshakeError, match="ping 门未过"):
        await McpSession.connect(_config(), transport)
    assert transport.closed


# ---------------------------------------------------------------- expected_server


async def test_expected_server_match_passes() -> None:
    transport = FakeTransport(_ok_handlers())
    session = await McpSession.connect(
        _config(expected_server=McpExpectedServer(name="srv")), transport
    )
    assert session.server_info["name"] == "srv"


async def test_expected_server_mismatch_rejects_and_closes() -> None:
    transport = FakeTransport(_ok_handlers())
    with pytest.raises(McpIdentityMismatchError, match="identity_mismatch"):
        await McpSession.connect(
            _config(expected_server=McpExpectedServer(name="other")), transport
        )
    assert transport.closed


# ---------------------------------------------------------------- call_tool


async def _connected_session(handlers=None, **cfg) -> tuple[McpSession, FakeTransport]:
    merged = _ok_handlers(**(handlers or {}))
    transport = FakeTransport(merged)
    session = await McpSession.connect(_config(**cfg), transport)
    return session, transport


async def test_call_tool_passthrough_result_and_default_arguments() -> None:
    def call(params) -> dict:
        assert params["name"] == "echo"
        assert params["arguments"] == {"text": "hi"}
        return {"content": [{"type": "text", "text": "hi"}], "isError": False}

    session, _ = await _connected_session({"tools/call": call})
    result = await session.call_tool("echo", {"text": "hi"}, side_effect="read")
    assert result["isError"] is False


async def test_call_tool_timeout_clamped_to_cap() -> None:
    session, transport = await _connected_session(call_timeout_s=9999.0)
    await session.call_tool("echo", side_effect="read")
    call = next(c for c in transport.calls if c[0] == "tools/call")
    assert call[2] == 120.0  # 上限 120000ms


async def test_call_tool_default_arguments_empty_dict() -> None:
    seen: list[dict] = []

    def call(params) -> dict:
        seen.append(params)
        return {"ok": True}

    session, _ = await _connected_session({"tools/call": call})
    await session.call_tool("echo", side_effect="read")
    assert seen[0]["arguments"] == {}


async def test_read_call_retries_once_on_transport_failure() -> None:
    attempts = {"n": 0}

    def call(params) -> dict:
        attempts["n"] += 1
        if attempts["n"] == 1:
            raise McpTransportError("transient")
        return {"ok": True}

    session, _ = await _connected_session({"tools/call": call})
    result = await session.call_tool("echo", side_effect="read")
    assert result == {"ok": True}
    assert attempts["n"] == 2  # 读重试 1 次（§5.4）


async def test_write_call_never_retries() -> None:
    attempts = {"n": 0}

    def call(params) -> dict:
        attempts["n"] += 1
        raise McpTransportError("transient")

    session, _ = await _connected_session({"tools/call": call})
    with pytest.raises(McpTransportError):
        await session.call_tool("echo", side_effect="write")
    assert attempts["n"] == 1  # 写禁重试（§5.4）


async def test_remote_error_is_business_class_no_retry() -> None:
    attempts = {"n": 0}

    def call(params) -> dict:
        attempts["n"] += 1
        raise JsonRpcRemoteError(code=-32602, message="bad params")

    session, _ = await _connected_session({"tools/call": call})
    with pytest.raises(JsonRpcRemoteError):
        await session.call_tool("echo", side_effect="read")
    assert attempts["n"] == 1  # 业务类异常不重试（也不计熔断 · 无 cause 属性）


# ---------------------------------------------------------------- clamp 单测


def test_clamp_timeout_defaults_floor_cap_and_nan() -> None:
    assert clamp_timeout_s(None, default=10.0) == 10.0
    assert clamp_timeout_s(float("nan"), default=10.0) == 10.0
    assert clamp_timeout_s(-5.0, default=30.0) == 30.0
    assert clamp_timeout_s(0.0001, default=10.0) == 1.0  # floor 1000ms
    assert clamp_timeout_s(99999.0, default=10.0) == 120.0  # cap 120000ms
    assert clamp_timeout_s(45.0, default=10.0) == 45.0


def test_supported_version_chain_head_is_pinned() -> None:
    assert SUPPORTED_PROTOCOL_VERSIONS[0] == "2025-06-18"
    assert jsonrpc  # 模块已载入（静默 unused 检查）
