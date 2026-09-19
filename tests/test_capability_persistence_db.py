"""W6 · DB 版防重存储与回执 sink（真 PostgreSQL · opsdesk_test）。

契约测试——重点不是 CRUD 能不能跑，而是：

1. **跨实例防重**：DB 版必须让"两个进程各自拿同一 key"只有一个能执行
   （进程内版做不到，这正是它存在的理由）
2. **租约判定走数据库时钟**：多实例各机器时钟有偏差，用本地时钟判租约必然出错
3. **租户隔离**：同 key 不同租户互不影响
4. 异步接口：DB 版**只提供异步**，同步调用要明确报错而不是悄悄阻塞事件循环

⚠️ 本文件全部用 ``async def``（``asyncio_mode=auto``）。**不要用 ``asyncio.run``**——
既有 conftest 的 ``_reset_engine`` 是按"每个测试一个 loop"管理的，
自建 loop 会与连接池绑定冲突（表现为 ``coroutine was never awaited``）。
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import text

from app.ops.capability import (
    DbIdempotencyStore,
    DbReceiptSink,
    GenericHttpAdapter,
    InMemoryReceiptSink,
    NullIdempotencyStore,
    ainvoke,
    configure_persistence_from_env,
    get_idempotency_store,
    get_receipt_sink,
    register,
    reset_idempotency_store,
    reset_receipt_sink,
    set_idempotency_store,
    set_receipt_sink,
    unregister,
)
from app.ops.capability.adapters import FakeHttpTransport, StaticCredentialVault
from app.ops.capability.receipts import Receipt
from app.ops.capability.types import CapabilitySpec
from app.db.session import AsyncSessionLocal
from tests.conftest import DB_AVAILABLE

pytestmark = pytest.mark.skipif(
    not DB_AVAILABLE, reason="需要 PostgreSQL（conftest 会准备 opsdesk_test）"
)

_TENANT = "w6-test-tenant"
_OTHER_TENANT = "w6-test-tenant-2"


async def _clear_test_rows() -> None:
    async with AsyncSessionLocal() as session:
        async with session.begin():
            for table in ("ops_capability_idempotency", "ops_capability_receipts"):
                await session.execute(
                    text(f"DELETE FROM {table} WHERE tenant_id LIKE 'w6-test-%'")
                )


@pytest.fixture(autouse=True)
async def _clean():
    reset_idempotency_store()
    reset_receipt_sink()
    await _clear_test_rows()
    yield
    reset_idempotency_store()
    reset_receipt_sink()
    await _clear_test_rows()


def _key() -> str:
    return f"k-{uuid.uuid4().hex[:12]}"


# ---------------- 防重状态机 ----------------


async def test_db_claim_first_then_in_flight_then_duplicate():
    store = DbIdempotencyStore(lease_seconds=120)
    key = _key()

    first = await store.aclaim(key, capability_id="c", tenant_id=_TENANT)
    second = await store.aclaim(key, capability_id="c", tenant_id=_TENANT)
    await store.acomplete(key, receipt_id="R-1", tenant_id=_TENANT)
    third = await store.aclaim(key, capability_id="c", tenant_id=_TENANT)

    assert first.acquired is True and first.attempts == 1
    assert second.acquired is False and second.in_flight is True and second.attempts == 2
    assert third.acquired is False and third.duplicate is True
    assert third.receipt_id == "R-1"


async def test_db_two_stores_share_state_across_instances():
    """★ 这是 DB 版存在的全部理由：两个「进程」（两个 store 实例）共享同一份防重状态。"""
    key = _key()
    proc_a = DbIdempotencyStore(lease_seconds=120)
    proc_b = DbIdempotencyStore(lease_seconds=120)

    a = await proc_a.aclaim(key, capability_id="c", tenant_id=_TENANT)
    b = await proc_b.aclaim(key, capability_id="c", tenant_id=_TENANT)

    assert a.acquired is True
    assert b.acquired is False and b.in_flight is True  # 另一个进程拿不到执行权


async def test_db_expired_lease_allows_takeover():
    store = DbIdempotencyStore(lease_seconds=0.01)
    key = _key()
    await store.aclaim(key, capability_id="c", tenant_id=_TENANT)
    await asyncio_sleep(0.15)
    taken = await store.aclaim(key, capability_id="c", tenant_id=_TENANT)

    assert taken.acquired is True
    assert taken.took_over_stale_lease is True
    assert taken.attempts == 2


async def test_db_release_allows_retry():
    store = DbIdempotencyStore(lease_seconds=120)
    key = _key()
    first = await store.aclaim(key, capability_id="c", tenant_id=_TENANT)
    await store.arelease(key, tenant_id=_TENANT)
    after = await store.aclaim(key, capability_id="c", tenant_id=_TENANT)

    assert first.acquired is True
    assert after.acquired is True  # 释放后可以重新执行


async def test_db_tenant_isolation():
    """同 key 不同租户互不影响——唯一约束是 (tenant_id, idempotency_key)。"""
    store = DbIdempotencyStore(lease_seconds=120)
    key = _key()
    a = await store.aclaim(key, capability_id="c", tenant_id=_TENANT)
    b = await store.aclaim(key, capability_id="c", tenant_id=_OTHER_TENANT)

    assert a.acquired is True and b.acquired is True  # 两个租户各自执行


async def test_db_concurrent_claims_only_one_wins():
    """并发 claim 靠数据库唯一约束保证只有一个赢（应用层没有锁）。"""
    store = DbIdempotencyStore(lease_seconds=120)
    key = _key()
    import asyncio

    claims = await asyncio.gather(
        *[store.aclaim(key, capability_id="c", tenant_id=_TENANT) for _ in range(6)],
        return_exceptions=True,
    )
    ok = [c for c in claims if hasattr(c, "acquired")]
    assert len(ok) == 6, [c for c in claims if not hasattr(c, "acquired")]
    assert sum(1 for c in ok if c.acquired) == 1


def test_db_sync_claim_is_not_exposed():
    """DB 版只有异步接口——同步路径不该悄悄可用（那会阻塞事件循环）。"""
    assert not hasattr(DbIdempotencyStore(lease_seconds=1), "claim")


# ---------------- 回执落库 ----------------


def _receipt(**over) -> Receipt:
    base = dict(
        receipt_id=uuid.uuid4().hex[:16],
        capability_id="oa.ticket.create",
        side_effect="write",
        ok=True,
        created_at="2026-09-19T12:00:00+00:00",
        tenant_id=_TENANT,
        user_id="u-1",
        idempotency_key="k-receipt",
        captured={"$.data.ticketId": "T-9"},
    )
    base.update(over)
    return Receipt(**base)


async def test_db_receipt_sink_persists_and_is_queryable():
    receipt = _receipt()
    await DbReceiptSink().arecord(receipt)

    async with AsyncSessionLocal() as session:
        rows = await session.execute(
            text(
                "SELECT receipt_id, capability_id, side_effect, ok, "
                "user_id, idempotency_key, captured "
                "FROM ops_capability_receipts WHERE receipt_id = :rid"
            ),
            {"rid": receipt.receipt_id},
        )
        row = rows.first()

    assert row is not None
    assert row[0] == receipt.receipt_id
    assert row[1] == "oa.ticket.create"
    assert row[2] == "write"
    assert row[3] is True
    assert row[4] == "u-1"
    assert row[5] == "k-receipt"
    # jsonb 往返后仍是结构化对象（收据要能被查询，不是一坨文本）
    assert row[6] == {"$.data.ticketId": "T-9"}


def test_db_receipt_sink_rejects_sync_call():
    with pytest.raises(RuntimeError, match="只提供异步落库"):
        DbReceiptSink().record(_receipt())


# ---------------- 端到端（经 gateway 异步路径） ----------------


def _write_spec(**over) -> CapabilitySpec:
    http = {
        "method": "POST",
        "base_url": "OA_BASE",
        "path": "/api/v1/ticket/create",
        "auth": "oa_gateway_token",
        "body_map": {"subject": "{{subject}}"},
        "idempotency_key": "t:{{subject}}",
        "timeout_ms": 2000,
        "success_when": {"path": "$.code", "in": [0]},
        "error_map": {"1001": "args_schema_invalid"},
    }
    http.update(over.pop("http", {}))
    base = dict(
        capability_id="oa.ticket.create",
        kind="http",
        description="建单",
        args_schema={"type": "object", "properties": {"subject": {"type": "string"}}},
        tags=("oa",),
        side_effect="write",
        hitl_required=True,
        when_to_use="单测",
        receipt_capture=("$.data.ticketId",),
        http=http,
    )
    base.update(over)
    return CapabilitySpec(**base)


def _register_write(spec: CapabilitySpec, tx: FakeHttpTransport) -> None:
    register(
        spec,
        GenericHttpAdapter(
            spec,
            transport=tx,
            vault=StaticCredentialVault({"oa_gateway_token": "s3cret"}),
        ),
    )


async def test_async_path_persists_receipt_and_completes_key(
    monkeypatch: pytest.MonkeyPatch,
):
    """异步路径必须真正落到 DB：键被标 done、回执带 write_confirmed、键↔回执对得上。"""
    monkeypatch.setenv("OA_BASE", "http://oa.test.local")
    store = DbIdempotencyStore(lease_seconds=120)
    set_idempotency_store(store)
    set_receipt_sink(DbReceiptSink())

    spec = _write_spec()
    tx = FakeHttpTransport(payload={"code": 0, "data": {"ticketId": "T-77"}})
    _register_write(spec, tx)
    ctx = {"tenant_id": _TENANT, "user_id": "u-1", "_host_policy": {"allow_write": True}}

    first = await ainvoke("oa.ticket.create", {"subject": "打印机故障"}, ctx=ctx)
    second = await ainvoke("oa.ticket.create", {"subject": "打印机故障"}, ctx=ctx)
    rows = await store.asnapshot(tenant_id=_TENANT)
    unregister("oa.ticket.create")

    assert first.ok is True
    assert second.ok is True and second.meta.get("duplicated") is True
    # ★ 第二次没真发请求
    assert len(tx.calls) == 1
    # ★ 键被标 done，且与第一次的回执 id 对上
    assert len(rows) == 1
    assert rows[0]["status"] == "done"
    assert rows[0]["receipt_id"] == first.meta["receipt_id"]


async def test_db_receipt_row_is_written_by_async_gateway(
    monkeypatch: pytest.MonkeyPatch,
):
    """回执真的进库了（不是只回填了 meta）。"""
    monkeypatch.setenv("OA_BASE", "http://oa.test.local")
    set_idempotency_store(DbIdempotencyStore(lease_seconds=120))
    set_receipt_sink(DbReceiptSink())

    spec = _write_spec(http={"idempotency_key": "t:db-{{subject}}"})
    _register_write(spec, FakeHttpTransport(payload={"code": 0, "data": {"ticketId": "T-DB"}}))
    ctx = {"tenant_id": _TENANT, "user_id": "u-2", "_host_policy": {"allow_write": True}}

    result = await ainvoke("oa.ticket.create", {"subject": "db"}, ctx=ctx)
    unregister("oa.ticket.create")
    assert result.ok is True

    async with AsyncSessionLocal() as session:
        rows = await session.execute(
            text(
                "SELECT count(*) FROM ops_capability_receipts "
                "WHERE tenant_id = :t AND capability_id = 'oa.ticket.create'"
            ),
            {"t": _TENANT},
        )
        count = int(rows.scalar() or 0)
    assert count == 1


# ---------------- 装配 ----------------


def test_configure_persistence_defaults_to_null(monkeypatch: pytest.MonkeyPatch):
    """未配置 = 显式不防重（并告警）——**装配是部署动作，不是代码默认值**。"""
    monkeypatch.delenv("OPS_CAPABILITY_PERSISTENCE", raising=False)
    assert configure_persistence_from_env() == "null"
    assert isinstance(get_idempotency_store(), NullIdempotencyStore)


def test_configure_persistence_memory_mode(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("OPS_CAPABILITY_PERSISTENCE", "memory")
    assert configure_persistence_from_env() == "memory"
    assert get_idempotency_store().__class__.__name__ == "InMemoryIdempotencyStore"
    assert isinstance(get_receipt_sink(), InMemoryReceiptSink)


def test_configure_persistence_db_mode(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("OPS_CAPABILITY_PERSISTENCE", "db")
    assert configure_persistence_from_env() == "db"
    assert isinstance(get_idempotency_store(), DbIdempotencyStore)
    assert isinstance(get_receipt_sink(), DbReceiptSink)


def test_configure_persistence_rejects_unknown_mode(monkeypatch: pytest.MonkeyPatch):
    """写错了要变成「不防重 + 显式报错」，不能悄悄退回某个实现。"""
    monkeypatch.setenv("OPS_CAPABILITY_PERSISTENCE", "redis")
    assert configure_persistence_from_env() == "null"
    assert isinstance(get_idempotency_store(), NullIdempotencyStore)


async def asyncio_sleep(seconds: float) -> None:
    import asyncio

    await asyncio.sleep(seconds)
