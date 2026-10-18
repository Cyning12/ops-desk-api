"""W5 · 幂等防重（含租约）与异步路径。

两个主张在这里被钉死：
1. **同一个幂等键不会在本层发出两次请求**（不是"回放结果"，是"不重复执行"）。
2. **失败不是完成**——只有确知下游无副作用时才释放幂等键，其余交给租约。
   超时不代表没成功，释放会让重试建出第二张单。
"""

from __future__ import annotations

import asyncio
import threading
import time
from typing import Any

import pytest

from app.ops.capability import (
    InMemoryIdempotencyStore,
    InMemoryReceiptSink,
    NullIdempotencyStore,
    get_idempotency_store,
    invoke,
    reset_idempotency_store,
    set_idempotency_store,
    set_receipt_sink,
)
from app.ops.capability.adapters import (
    FakeHttpTransport,
    GenericHttpAdapter,
    HttpCapabilityError,
    HttpResponse,
    StaticCredentialVault,
)
from app.ops.capability.defaults import ensure_default_capabilities
from app.ops.capability.gateway import get_registry, register, unregister
from app.ops.capability.types import CapabilitySpec

_SECRET = "s3cret"
_ARGS = {
    "type": "object",
    "properties": {"subject": {"type": "string"}},
}
_HTTP_WRITE = {
    "method": "POST",
    "base_url": "OA_BASE",
    "path": "/api/v1/ticket/create",
    "auth": "oa_gateway_token",
    "body_map": {"subject": "{{subject}}"},
    "idempotency_key": "t:{{subject}}",
    "timeout_ms": 2000,
    "success_when": {"path": "$.code", "in": [0]},
    "error_map": {"1001": "args_schema_invalid", "2003": "permission_denied"},
}


@pytest.fixture(autouse=True)
def _clean(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("OA_BASE", "http://oa.test.local")
    reset_idempotency_store()
    yield
    get_registry().clear()
    reset_idempotency_store()
    ensure_default_capabilities()


def _write_spec(**over) -> CapabilitySpec:
    http = dict(_HTTP_WRITE)
    http.update(over.pop("http", {}))
    base = {
        "capability_id": "oa.ticket.create",
        "kind": "http",
        "description": "建单",
        "args_schema": dict(_ARGS),
        "side_effect": "write",
        "hitl_required": True,
        "when_to_use": "单测",
        "receipt_capture": ("$.data.ticketId",),
        "http": http,
    }
    base.update(over)
    return CapabilitySpec(**base)


def _adapter(spec: CapabilitySpec, store: Any, tx: Any = None) -> GenericHttpAdapter:
    return GenericHttpAdapter(
        spec,
        transport=tx or FakeHttpTransport(payload={"code": 0, "data": {"ticketId": "T-1"}}),
        vault=StaticCredentialVault({"oa_gateway_token": _SECRET}),
        store=store,
    )


# ---------------- 存储状态机 ----------------


def test_first_claim_acquires():
    store = InMemoryIdempotencyStore()
    claim = store.claim("k1", capability_id="c", tenant_id="t")
    assert claim.acquired is True
    assert claim.attempts == 1
    assert claim.duplicate is False


def test_second_claim_while_in_flight_is_blocked():
    store = InMemoryIdempotencyStore()
    store.claim("k1")
    second = store.claim("k1")
    assert second.acquired is False
    assert second.in_flight is True
    assert second.attempts == 2


def test_claim_after_complete_is_duplicate_with_receipt():
    store = InMemoryIdempotencyStore()
    store.claim("k1")
    store.complete("k1", receipt_id="R-9")
    again = store.claim("k1")
    assert again.acquired is False
    assert again.duplicate is True
    assert again.receipt_id == "R-9"


def test_expired_lease_allows_takeover():
    """**没有租约，进程崩一次就会把该键永久卡死**——这条是租约存在的全部理由。"""
    store = InMemoryIdempotencyStore(lease_seconds=0.05)
    store.claim("k1")
    assert store.claim("k1").in_flight is True
    time.sleep(0.08)
    taken = store.claim("k1")
    assert taken.acquired is True
    assert taken.took_over_stale_lease is True
    assert taken.attempts == 3  # 1 首次 + 1 被拒 + 1 接管


def test_release_allows_immediate_retry():
    store = InMemoryIdempotencyStore()
    store.claim("k1")
    store.release("k1")
    assert store.claim("k1").acquired is True


def test_concurrent_claims_only_one_wins():
    store = InMemoryIdempotencyStore()
    acquired: list[bool] = []
    lock = threading.Lock()
    barrier = threading.Barrier(8)

    def worker() -> None:
        barrier.wait()
        claim = store.claim("k1")
        with lock:
            acquired.append(claim.acquired)

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert acquired.count(True) == 1


def test_null_store_always_acquires_and_warns(caplog):
    store = NullIdempotencyStore()
    assert store.claim("k1", capability_id="c").acquired is True
    assert "幂等防重未启用" in caplog.text


def test_default_store_is_null_and_visible():
    assert isinstance(get_idempotency_store(), NullIdempotencyStore)


# ---------------- adapter 侧 ----------------


def test_second_write_does_not_reach_transport():
    store = InMemoryIdempotencyStore()
    spec = _write_spec()
    tx = FakeHttpTransport(payload={"code": 0, "data": {"ticketId": "T-1"}})
    adapter = _adapter(spec, store, tx)

    first = adapter.invoke({"subject": "打印机故障"})
    assert first["result"]["data"]["ticketId"] == "T-1"
    assert len(tx.calls) == 1

    second = adapter.invoke({"subject": "打印机故障"})
    assert second["duplicated"] is True
    # ★ 关键：第二次**没有**再发请求
    assert len(tx.calls) == 1


def test_in_flight_raises_duplicate_id():
    store = InMemoryIdempotencyStore()
    spec = _write_spec()
    tx = FakeHttpTransport(payload={"code": 0, "data": {"ticketId": "T-1"}})
    adapter = _adapter(spec, store, tx)

    store.claim(adapter._prepare({"subject": "x"}, None).idempotency_key)
    with pytest.raises(HttpCapabilityError) as ei:
        adapter.invoke({"subject": "x"})
    assert ei.value.code == "duplicate_id"
    assert tx.calls == []


def test_rejected_by_downstream_releases_key():
    """下游明确拒绝 = 无副作用 → 允许重试（否则一次参数错误要等整个租约）。"""
    store = InMemoryIdempotencyStore()
    spec = _write_spec()
    tx = FakeHttpTransport(payload={"code": 1001})
    adapter = _adapter(spec, store, tx)

    with pytest.raises(HttpCapabilityError) as ei:
        adapter.invoke({"subject": "x"})
    assert ei.value.code == "args_schema_invalid"
    assert len(store) == 0  # 已释放


def test_timeout_keeps_key_in_flight_fail_closed():
    """★ 超时不代表没成功。保持 in_flight，交给租约——**宁可拒，也不冒重复执行的风险**。"""
    store = InMemoryIdempotencyStore()
    spec = _write_spec()
    tx = FakeHttpTransport(exc=TimeoutError("timeout"))
    adapter = _adapter(spec, store, tx)

    with pytest.raises(HttpCapabilityError) as ei:
        adapter.invoke({"subject": "x"})
    assert ei.value.code == "upstream_error"
    assert len(store) == 1
    snap = next(iter(store.snapshot().values()))
    assert snap["status"] == "in_flight"


def test_unknown_upstream_code_keeps_key_in_flight():
    store = InMemoryIdempotencyStore()
    spec = _write_spec()
    tx = FakeHttpTransport(payload={"code": 9999})
    adapter = _adapter(spec, store, tx)
    with pytest.raises(HttpCapabilityError):
        adapter.invoke({"subject": "x"})
    assert len(store) == 1


def test_read_capability_has_no_idempotency_key():
    store = InMemoryIdempotencyStore()
    spec = _write_spec(side_effect="read", http={"idempotency_key": None})
    tx = FakeHttpTransport(payload={"code": 0, "data": {}})
    adapter = _adapter(spec, store, tx)
    adapter.invoke({"subject": "x"})
    adapter.invoke({"subject": "x"})
    assert len(tx.calls) == 2  # 只读本来就不该防重
    assert len(store) == 0


# ---------------- 异步路径（不阻塞事件循环） ----------------


class _SlowTransport:
    """每次请求睡 0.3s；用来证明并发调用没有被串行化。"""

    def __init__(self, delay: float = 0.3) -> None:
        self.delay = delay
        self.calls = 0

    def request(self, **kwargs: Any) -> HttpResponse:
        self.calls += 1
        time.sleep(self.delay)
        return HttpResponse(status=200, payload={"code": 0, "data": {}})


def test_ainvoke_does_not_block_the_event_loop():
    """阻塞传输必须被挪出事件循环——否则一次慢下游会把整个服务按住。"""
    spec = _write_spec(side_effect="read", http={"idempotency_key": None})
    tx = _SlowTransport(0.3)
    adapter = _adapter(spec, InMemoryIdempotencyStore(), tx)

    async def run() -> float:
        started = time.perf_counter()
        await asyncio.gather(*[adapter.ainvoke({"subject": f"s{i}"}) for i in range(3)])
        return time.perf_counter() - started

    elapsed = asyncio.run(run())
    assert tx.calls == 3
    # 串行会 ≥0.9s；并发应接近 0.3s
    assert elapsed < 0.7, f"疑似阻塞事件循环：{elapsed:.2f}s"


def test_async_write_dedup_also_works():
    store = InMemoryIdempotencyStore()
    spec = _write_spec()
    tx = FakeHttpTransport(payload={"code": 0, "data": {"ticketId": "T-1"}})
    adapter = _adapter(spec, store, tx)

    async def run() -> tuple[dict, dict]:
        first = await adapter.ainvoke({"subject": "x"})
        second = await adapter.ainvoke({"subject": "x"})
        return first, second

    first, second = asyncio.run(run())
    assert first["result"]["data"]["ticketId"] == "T-1"
    assert second["duplicated"] is True
    assert len(tx.calls) == 1


# ---------------- 经 gateway：键 ↔ 回执 对上 ----------------


def test_gateway_completes_key_with_receipt_id():
    store = InMemoryIdempotencyStore()
    set_idempotency_store(store)
    sink = InMemoryReceiptSink()
    set_receipt_sink(sink)
    spec = _write_spec()
    register(spec, _adapter(spec, store))
    ctx = {"tenant_id": "t1", "_host_policy": {"allow_write": True}}

    r1 = invoke("oa.ticket.create", {"subject": "打印机故障"}, ctx=ctx)
    assert r1.ok is True
    snap = store.snapshot()
    assert len(snap) == 1
    assert snap[next(iter(snap))]["status"] == "done"
    # 键与回执对上：complete 用的是真实回执 id
    assert snap[next(iter(snap))]["receipt_id"] == r1.meta["receipt_id"]

    r2 = invoke("oa.ticket.create", {"subject": "打印机故障"}, ctx=ctx)
    assert r2.ok is True
    assert r2.meta.get("duplicated") is True
    # 命中幂等键没有执行 → 不产生第二条回执
    assert len(sink) == 1
    unregister("oa.ticket.create")
