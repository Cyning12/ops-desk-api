"""P0' T4 · run 一等实体（ops_lg_rag_runs · issue #23 裁定 A1）。

- 纯函数真值表：status_for_event（done payload 逐字落列 · error · hitl.resumed）。
- 收口集成：persist_run_event 挂钩 best-effort 状态流转（DB 真跑）。
- 补行/主扫：backfill_missing_run_rows · list_stale_running_runs（orphan 两段式）。
"""

from __future__ import annotations

import uuid
from datetime import timedelta

import pytest

from app.db.models import now_utc
from tests.conftest import DB_AVAILABLE

_DB_REQUIRED = pytest.mark.skipif(not DB_AVAILABLE, reason="需要本地 PG（opsdesk_test）真跑 run 实体表")


def test_status_for_event_truth_table() -> None:
    """纯函数：done{status:X}→X 逐字；error→error；hitl.resumed→running；其余不变。"""
    from app.ops.lg_rag.run_store import status_for_event

    assert status_for_event("done", {"status": "done"}) == "done"
    assert status_for_event("done", {"status": "waiting_approval"}) == "waiting_approval"
    assert status_for_event("done", {"status": "disconnected"}) == "disconnected"
    assert status_for_event("done", {"status": "resumed"}) == "resumed"
    assert status_for_event("done", {}) == "done"  # 缺 status 兜底
    assert status_for_event("done", None) == "done"
    assert status_for_event("error", {"stage": "x"}) == "error"
    assert status_for_event("hitl.resumed", {}) == "running"
    for et in ("token", "thought", "node.progress", "hitl.waiting", "run.start", "answer"):
        assert status_for_event(et, {"status": "done"}) is None


@_DB_REQUIRED
@pytest.mark.asyncio
async def test_persist_chokepoint_drives_run_status(seeded_maintainer) -> None:
    """建行 → persist 收口挂钩：waiting_approval →(hitl.resumed)→ running →(done{resumed})→ resumed 终态。"""

    from app.db.models import OpsLgRagRun
    from app.db.session import AsyncSessionLocal
    from app.ops.lg_rag import event_store
    from app.ops.lg_rag.run_store import create_run

    user_id = str(seeded_maintainer["user"].id)
    run_id = f"t4rs-{uuid.uuid4().hex[:10]}"
    thread_id = f"th-t4-{uuid.uuid4().hex[:8]}"

    created = await create_run(
        run_id=run_id, thread_id=thread_id, user_id=user_id, tenant_id="tenant-a"
    )
    assert created is True
    # 幂等：单飞复用/重复建行 → False 不报错
    assert (
        await create_run(run_id=run_id, thread_id=thread_id, user_id=user_id, tenant_id="t")
        is False
    )
    # user_id 缺失 → 静默跳过
    assert await create_run(run_id="x", thread_id="t", user_id=None, tenant_id=None) is False

    async with AsyncSessionLocal() as db:
        row = await db.get(OpsLgRagRun, run_id)
        assert row is not None
        assert row.status == "running"
        assert row.tenant_id == "tenant-a"
        assert row.finished_at is None

    async def _persist(seq: int, event_type: str, payload: dict) -> None:
        await event_store.persist_run_event(
            run_id=run_id,
            seq=seq,
            user_id=user_id,
            thread_id=thread_id,
            ts_ms=seq,
            agent_role="system",
            event_type=event_type,
            payload=payload,
        )

    await _persist(1, "run.start", {"run_id": run_id})  # 不变
    async with AsyncSessionLocal() as db:
        assert (await db.get(OpsLgRagRun, run_id)).status == "running"

    await _persist(2, "done", {"status": "waiting_approval"})  # 挂起（非终态词表外 → 保留 finished_at 为空）
    async with AsyncSessionLocal() as db:
        row = await db.get(OpsLgRagRun, run_id)
        assert row.status == "waiting_approval"
        assert row.finished_at is None  # 非终态：resume 还要续跑

    await _persist(3, "hitl.resumed", {})  # 回升 running 清 finished_at
    async with AsyncSessionLocal() as db:
        row = await db.get(OpsLgRagRun, run_id)
        assert row.status == "running"
        assert row.finished_at is None

    await _persist(4, "done", {"status": "resumed"})  # 沉降终态
    async with AsyncSessionLocal() as db:
        row = await db.get(OpsLgRagRun, run_id)
        assert row.status == "resumed"
        assert row.finished_at is not None


@_DB_REQUIRED
@pytest.mark.asyncio
async def test_persist_error_and_unknown_run_noop(seeded_maintainer) -> None:
    """error → 终态 error + finished_at；无 run 行的状态更新静默跳过（补行兜）。"""
    from app.db.models import OpsLgRagRun
    from app.db.session import AsyncSessionLocal
    from app.ops.lg_rag import event_store
    from app.ops.lg_rag.run_store import create_run

    user_id = str(seeded_maintainer["user"].id)
    run_id = f"t4err-{uuid.uuid4().hex[:10]}"
    await create_run(run_id=run_id, thread_id="th", user_id=user_id, tenant_id=None)
    await event_store.persist_run_event(
        run_id=run_id,
        seq=1,
        user_id=user_id,
        thread_id="th",
        ts_ms=1,
        agent_role="system",
        event_type="error",
        payload={"stage": "boom"},
    )
    async with AsyncSessionLocal() as db:
        row = await db.get(OpsLgRagRun, run_id)
        assert row.status == "error"
        assert row.finished_at is not None
        assert row.tenant_id == ""  # tenant 不可知 → 承 notes 先例 ''

    ghost = f"t4ghost-{uuid.uuid4().hex[:10]}"
    await event_store.persist_run_event(
        run_id=ghost,
        seq=1,
        user_id=user_id,
        thread_id="th",
        ts_ms=1,
        agent_role="system",
        event_type="done",
        payload={"status": "done"},
    )
    async with AsyncSessionLocal() as db:
        assert await db.get(OpsLgRagRun, ghost) is None  # 不建行、不报错


@_DB_REQUIRED
@pytest.mark.asyncio
async def test_backfill_missing_run_rows(seeded_maintainer) -> None:
    """events 有帧但 runs 无行 → backfill 补行（tenant '' · created_at=首帧时间）。"""
    from app.db.models import OpsLgRagRun
    from app.db.session import AsyncSessionLocal
    from app.ops.lg_rag import event_store
    from app.ops.lg_rag.run_store import backfill_missing_run_rows

    user_id = str(seeded_maintainer["user"].id)
    run_id = f"t4bf-{uuid.uuid4().hex[:10]}"
    thread_id = f"th-bf-{uuid.uuid4().hex[:8]}"
    await event_store.persist_run_event(
        run_id=run_id,
        seq=1,
        user_id=user_id,
        thread_id=thread_id,
        ts_ms=1,
        agent_role="system",
        event_type="run.start",
        payload={},
    )
    async with AsyncSessionLocal() as db:
        assert await db.get(OpsLgRagRun, run_id) is None

    n = await backfill_missing_run_rows(limit=200)
    assert n >= 1
    async with AsyncSessionLocal() as db:
        row = await db.get(OpsLgRagRun, run_id)
        assert row is not None
        assert row.status == "running"
        assert row.tenant_id == ""
        assert row.thread_id == thread_id


@_DB_REQUIRED
@pytest.mark.asyncio
async def test_list_stale_running_runs_filters(seeded_maintainer) -> None:
    """主扫：仅 status='running'；stale>0 时末帧新鲜者排除；终态行排除。"""
    from sqlalchemy import update

    from app.db.models import OpsLgRagRun
    from app.db.session import AsyncSessionLocal
    from app.ops.lg_rag.run_store import create_run, list_stale_running_runs

    user_id = str(seeded_maintainer["user"].id)
    stale_run = f"t4st-{uuid.uuid4().hex[:10]}"
    fresh_run = f"t4fr-{uuid.uuid4().hex[:10]}"
    done_run = f"t4dn-{uuid.uuid4().hex[:10]}"
    for rid in (stale_run, fresh_run, done_run):
        await create_run(run_id=rid, thread_id="th", user_id=user_id, tenant_id=None)
    async with AsyncSessionLocal() as db:
        # stale_run：建行时间回拨 1 小时（无事件 → last_activity=created_at）
        await db.execute(
            update(OpsLgRagRun)
            .where(OpsLgRagRun.run_id == stale_run)
            .values(created_at=now_utc() - timedelta(hours=1))
        )
        # done_run：终态
        await db.execute(
            update(OpsLgRagRun)
            .where(OpsLgRagRun.run_id == done_run)
            .values(status="done", finished_at=now_utc())
        )
        await db.commit()

    ids = {
        r["run_id"]
        for r in await list_stale_running_runs(stale_after_seconds=60, limit=500)
    }
    assert stale_run in ids  # 老 run 无新帧 → 陈旧
    assert fresh_run not in ids  # 建行即新鲜 → 排除
    assert done_run not in ids  # 终态 → 排除

    ids0 = {
        r["run_id"]
        for r in await list_stale_running_runs(stale_after_seconds=0, limit=500)
    }
    assert fresh_run in ids0  # stale=0 无时间过滤（承旧 list_open_runs 语义）
    assert done_run not in ids0
