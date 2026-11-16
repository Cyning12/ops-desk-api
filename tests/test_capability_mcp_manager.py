"""P2b-T2 · McpSessionManager 单测：隔离/并发去重/迟关闭/取消感知/逆序关闭+unregister 钩子。

生命周期锚（11 终稿 §5.1 + 委派书 §4-E 三条 · m00002）
-----------------------------------------------------
- 单 server 失败 warn 跳过，不影响其余（§4-B 隔离）；
- start() 幂等 + 同 key 单 flight（并发去重）；
- aclose() 取消在途建连（取消感知：子任务自清半成品 transport 后重抛）；
- aclose 后才建完的连接立即 close 不入池（迟关闭）；
- aclose 逆序关闭 + unregister_hook 回调（R5c 接口面 · T3 挂点 · 本单 hook 缺省 no-op）。
"""

from __future__ import annotations

import asyncio

from app.ops.capability.mcp.manager import McpSessionManager
from app.ops.capability.mcp_config import McpServerConfig


class FakeTransport:
    def __init__(self, handlers: dict | None = None, *, start_gate: asyncio.Event | None = None) -> None:
        self.handlers = dict(handlers or {})
        self.started = False
        self.closed = False
        self.calls: list[tuple[str, object, object]] = []
        self._start_gate = start_gate

    async def start(self) -> None:
        if self._start_gate is not None:
            await self._start_gate.wait()
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
        pass

    async def aclose(self) -> None:
        self.closed = True


def _initialize_result() -> dict:
    return {
        "protocolVersion": "2025-06-18",
        "capabilities": {},
        "serverInfo": {"name": "srv", "version": "1.0"},
    }


def _ok_transport(**overrides) -> FakeTransport:
    handlers = {"initialize": _initialize_result(), "ping": {}, "tools/list": {"tools": []}}
    handlers.update(overrides)
    return FakeTransport(handlers)


def _configs(*keys: str) -> tuple[McpServerConfig, ...]:
    return tuple(McpServerConfig(key=k, transport="stdio", command="stub") for k in keys)


def _factory_map(mapping: dict[str, FakeTransport]):
    def factory(config: McpServerConfig) -> FakeTransport:
        return mapping[config.key]

    return factory


# ---------------------------------------------------------------- 建连与隔离


async def test_start_connects_all_and_sessions_queryable() -> None:
    mapping = {"a": _ok_transport(), "b": _ok_transport()}
    manager = McpSessionManager(_configs("a", "b"), transport_factory=_factory_map(mapping))
    await manager.start()
    assert manager.connected_keys() == ("a", "b")
    assert manager.get_session("a") is not None
    assert manager.get_session("missing") is None
    await manager.aclose()


async def test_single_server_failure_isolated(caplog) -> None:
    from app.ops.capability.mcp.errors import McpTransportError

    mapping = {
        "bad": _ok_transport(initialize=McpTransportError("boom")),
        "good": _ok_transport(),
    }
    manager = McpSessionManager(_configs("bad", "good"), transport_factory=_factory_map(mapping))
    with caplog.at_level("WARNING"):
        await manager.start()  # 不抛
    assert manager.connected_keys() == ("good",)
    assert any("bad" in r.message and "建连失败" in r.message for r in caplog.records)
    await manager.aclose()


async def test_start_is_idempotent() -> None:
    mapping = {"a": _ok_transport()}
    calls = {"n": 0}

    def factory(config):
        calls["n"] += 1
        return mapping[config.key]

    manager = McpSessionManager(_configs("a"), transport_factory=factory)
    await manager.start()
    await manager.start()
    assert calls["n"] == 1
    await manager.aclose()


async def test_concurrent_connect_same_key_single_flight() -> None:
    gate = asyncio.Event()
    mapping = {"a": _ok_transport()}
    mapping["a"]._start_gate = gate
    manager = McpSessionManager(_configs("a"), transport_factory=_factory_map(mapping))
    t1 = asyncio.create_task(manager._connect_one(_configs("a")[0]))
    t2 = asyncio.create_task(manager._connect_one(_configs("a")[0]))
    await asyncio.sleep(0)
    gate.set()
    await asyncio.gather(t1, t2)
    assert manager.connected_keys() == ("a",)
    await manager.aclose()


# ---------------------------------------------------------------- 关闭语义


async def test_aclose_reverse_order_and_unregister_hook() -> None:
    close_order: list[str] = []
    mapping = {}
    for key in ("a", "b", "c"):
        transport = _ok_transport()
        original_aclose = transport.aclose

        async def wrapped(key=key, transport=transport, original=original_aclose):
            close_order.append(key)
            await original()

        transport.aclose = wrapped
        mapping[key] = transport
    hook_calls: list[str] = []
    manager = McpSessionManager(
        _configs("a", "b", "c"),
        transport_factory=_factory_map(mapping),
        unregister_hook=hook_calls.append,
    )
    await manager.start()
    await manager.aclose()
    assert close_order == ["c", "b", "a"]  # 逆序（§5.1）
    assert hook_calls == ["c", "b", "a"]  # R5c 接口面：每 server 回调一次
    assert manager.connected_keys() == ()
    # 幂等
    await manager.aclose()
    assert hook_calls == ["c", "b", "a"]


async def test_aclose_cancels_inflight_connect_and_cleans_transport() -> None:
    gate = asyncio.Event()  # 永不 set → start 卡住
    transport = _ok_transport()
    transport._start_gate = gate
    manager = McpSessionManager(_configs("a"), transport_factory=lambda c: transport)
    start_task = asyncio.create_task(manager.start())
    for _ in range(50):  # 等 _connect_one 注册 inflight（否则 aclose 无从取消）
        await asyncio.sleep(0)
        if manager._inflight:
            break
    assert manager._inflight
    await manager.aclose()  # 取消感知：取消在途建连
    assert transport.closed  # 半成品 transport 已清理
    await asyncio.gather(start_task, return_exceptions=True)
    assert manager.connected_keys() == ()


async def test_late_finished_connect_closes_immediately_not_pooled() -> None:
    gate = asyncio.Event()
    transport = _ok_transport()
    transport._start_gate = gate
    manager = McpSessionManager(_configs("a"), transport_factory=lambda c: transport)
    task = asyncio.create_task(manager._connect_one(_configs("a")[0]))
    await asyncio.sleep(0)
    manager._closed = True  # 模拟 aclose 已置位（迟关闭窗口）
    gate.set()
    await task
    assert transport.closed  # 建完即 close
    assert manager.connected_keys() == ()  # 不入池


async def test_session_close_failure_does_not_block_others(caplog) -> None:
    mapping = {"a": _ok_transport(), "b": _ok_transport()}

    async def broken_aclose():
        raise RuntimeError("close boom")

    mapping["a"].aclose = broken_aclose
    manager = McpSessionManager(_configs("a", "b"), transport_factory=_factory_map(mapping))
    await manager.start()
    with caplog.at_level("WARNING"):
        await manager.aclose()
    assert mapping["b"].closed
    assert any("关闭失败" in r.message for r in caplog.records)


async def test_unregister_hook_failure_only_warns(caplog) -> None:
    mapping = {"a": _ok_transport()}

    def bad_hook(key: str) -> None:
        raise RuntimeError("hook boom")

    manager = McpSessionManager(
        _configs("a"), transport_factory=_factory_map(mapping), unregister_hook=bad_hook
    )
    await manager.start()
    with caplog.at_level("WARNING"):
        await manager.aclose()  # 不抛
    assert any("unregister_hook 失败" in r.message for r in caplog.records)
