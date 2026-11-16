"""P2b-T2 · MCP transport 层单测：jsonrpc 编解码 + _ResponseMux 协议纪律 + env 白名单。

协议纪律锚（委派书 m00002 · 登记偏差 D1：终稿无对应节号，以委派书为准）
--------------------------------------------------------------------------
(a) server→client 的 ping 请求须回 {} result；
(b) server→client 的**非 tools/*** 其余请求须 1s 内回 JSON-RPC 错误 -32601 防挂起；
(c) 通知（无 id，含 tools/list_changed）安全忽略、不回帧、不动作；
(f) env 白名单：不继承 os.environ，仅 PATH 等最小集 + env_allowlist 显式键。
"""

from __future__ import annotations

import asyncio

import pytest

from app.ops.capability.mcp import jsonrpc
from app.ops.capability.mcp.errors import McpProtocolError, McpTimeoutError
from app.ops.capability.mcp.jsonrpc import JsonRpcRemoteError
from app.ops.capability.mcp.transport import _ResponseMux, filtered_env

# ---------------------------------------------------------------- jsonrpc 编解码


def test_make_request_shape_and_id_sequence() -> None:
    req1 = jsonrpc.make_request(jsonrpc.next_id(), "initialize", {"a": 1})
    req2 = jsonrpc.make_request(jsonrpc.next_id(), "ping")
    assert req1 == {"jsonrpc": "2.0", "id": req1["id"], "method": "initialize", "params": {"a": 1}}
    assert isinstance(req1["id"], int)
    assert req2["id"] != req1["id"]
    assert "params" not in req2


def test_make_notification_has_no_id() -> None:
    msg = jsonrpc.make_notification("notifications/initialized")
    assert msg["jsonrpc"] == "2.0"
    assert msg["method"] == "notifications/initialized"
    assert "id" not in msg


def test_make_result_and_error_shape() -> None:
    assert jsonrpc.make_result(7, {"ok": True}) == {
        "jsonrpc": "2.0",
        "id": 7,
        "result": {"ok": True},
    }
    err = jsonrpc.make_error(7, jsonrpc.METHOD_NOT_FOUND, "nf", data={"m": "x"})
    assert err["id"] == 7
    assert err["error"]["code"] == -32601
    assert err["error"]["data"] == {"m": "x"}


def test_message_kind_discrimination() -> None:
    assert jsonrpc.is_request({"method": "ping", "id": 1})
    assert jsonrpc.is_notification({"method": "notifications/x"})
    assert jsonrpc.is_response({"id": 1, "result": {}})
    assert jsonrpc.is_response({"id": 1, "error": {"code": -32601, "message": "nf"}})
    assert not jsonrpc.is_request({"method": "notifications/x"})
    assert not jsonrpc.is_notification({"method": "ping", "id": 1})
    assert not jsonrpc.is_response({"method": "ping", "id": 1})


def test_jsonrpc_remote_error_attrs() -> None:
    exc = JsonRpcRemoteError(code=-32601, message="not found", data={"x": 1})
    assert exc.code == -32601
    assert "not found" in str(exc)
    assert exc.data == {"x": 1}


# ---------------------------------------------------------------- _ResponseMux 纪律


def _collector() -> tuple[list[dict], object]:
    sent: list[dict] = []

    async def send(msg) -> None:
        sent.append(msg)

    return sent, send


async def test_mux_replies_to_server_ping_with_empty_result() -> None:
    sent, send = _collector()
    mux = _ResponseMux(send)
    mux.handle_message({"jsonrpc": "2.0", "id": 99, "method": "ping"})
    await asyncio.sleep(0)  # 应答经后台 task 异步发出
    assert sent == [{"jsonrpc": "2.0", "id": 99, "result": {}}]


async def test_mux_replies_method_not_found_to_other_server_requests() -> None:
    sent, send = _collector()
    mux = _ResponseMux(send)
    for method in ("roots/list", "sampling/createMessage", "tools/list", "elicitation/create"):
        mux.handle_message({"jsonrpc": "2.0", "id": 1, "method": method})
    await asyncio.sleep(0)
    assert len(sent) == 4
    for msg, method in zip(
        sent, ("roots/list", "sampling/createMessage", "tools/list", "elicitation/create"), strict=True
    ):
        assert msg["error"]["code"] == jsonrpc.METHOD_NOT_FOUND
        assert method in msg["error"]["message"]


async def test_mux_ignores_notifications_including_list_changed() -> None:
    sent, send = _collector()
    mux = _ResponseMux(send)
    mux.handle_message({"jsonrpc": "2.0", "method": "notifications/initialized"})
    mux.handle_message({"jsonrpc": "2.0", "method": "notifications/tools/list_changed"})
    mux.handle_message({"jsonrpc": "2.0", "method": "notifications/progress", "params": {}})
    await asyncio.sleep(0)
    assert sent == []


def test_mux_ignores_unknown_id_response_and_non_dict() -> None:
    sent, send = _collector()
    mux = _ResponseMux(send)
    mux.handle_message({"jsonrpc": "2.0", "id": 12345, "result": {"late": True}})
    mux.handle_message(["not", "a", "dict"])
    assert sent == []


async def _wait_sent(sent: list[dict], count: int) -> None:
    for _ in range(20):
        await asyncio.sleep(0)
        if len(sent) >= count:
            return
    raise AssertionError(f"sent 未达 {count}: {sent}")


async def test_mux_call_routes_result_and_raises_remote_error() -> None:
    sent, send = _collector()
    mux = _ResponseMux(send)

    # result 路由
    task1 = asyncio.create_task(mux.call("tools/list", {"x": 1}, timeout_s=1.0))
    await _wait_sent(sent, 1)
    req = sent[-1]
    assert req["method"] == "tools/list"
    mux.handle_message({"jsonrpc": "2.0", "id": req["id"], "result": {"tools": []}})
    assert await task1 == {"tools": []}

    # error → JsonRpcRemoteError（业务类，不计熔断）
    task2 = asyncio.create_task(mux.call("tools/call", None, timeout_s=1.0))
    await _wait_sent(sent, 2)
    req2 = sent[-1]
    mux.handle_message(
        {"jsonrpc": "2.0", "id": req2["id"], "error": {"code": -32602, "message": "bad args"}}
    )
    with pytest.raises(JsonRpcRemoteError) as ei:
        await task2
    assert ei.value.code == -32602


async def test_mux_call_timeout_raises_mcp_timeout_error() -> None:
    sent, send = _collector()
    mux = _ResponseMux(send)
    with pytest.raises(McpTimeoutError):
        await mux.call("ping", None, timeout_s=0.01)
    assert not mux._pending  # 超时后 pending 已清理


async def test_mux_fail_all_fails_pending_calls() -> None:
    sent, send = _collector()
    mux = _ResponseMux(send)
    task = asyncio.create_task(mux.call("ping", None, timeout_s=10.0))
    await _wait_sent(sent, 1)
    mux.fail_all(McpProtocolError("broken pipe"))
    with pytest.raises(McpProtocolError, match="broken pipe"):
        await task


# ---------------------------------------------------------------- env 白名单


def test_filtered_env_keeps_only_minimal_set_and_allowlist(monkeypatch) -> None:
    environ = {
        "PATH": "/usr/bin",
        "HOME": "/home/x",
        "OPS_DATABASE_URL": "postgresql://secret",  # 机密：绝不传子进程
        "AWS_SECRET_ACCESS_KEY": "secret",
        "MCP_STUB_PROTOCOL_VERSION": "2024-11-05",
        "LANG": "en_US.UTF-8",
        "CUSTOM_UNLISTED": "nope",
    }
    child = filtered_env(environ, ("MCP_STUB_PROTOCOL_VERSION",))
    assert child["PATH"] == "/usr/bin"
    assert child["HOME"] == "/home/x"
    assert child["MCP_STUB_PROTOCOL_VERSION"] == "2024-11-05"
    # 机密与非白名单键一律不传（不继承 os.environ 全体 · §5.3）
    assert "OPS_DATABASE_URL" not in child
    assert "AWS_SECRET_ACCESS_KEY" not in child
    assert "CUSTOM_UNLISTED" not in child
    # LANG 属 PATH 等最小集（MINIMAL_ENV_KEYS）→ 允许
    assert child["LANG"] == "en_US.UTF-8"


def test_filtered_env_drops_allowlist_keys_absent_in_environ() -> None:
    child = filtered_env({"PATH": "/bin"}, ("NOT_SET_KEY",))
    assert child == {"PATH": "/bin"}
