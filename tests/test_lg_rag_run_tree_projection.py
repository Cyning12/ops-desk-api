"""P4-T6 · 委派 claim（19-p4-contracts §7.3/§7.4）+ runs 投影加性（§11.4）。

- claim_child_run：归属从父行取值（§8.2）· 撞 uq 重入取回零重复建行 ·
  并发双建仅一胜（承 tests/test_capability_persistence_db.py:139 体例）·
  深度断言（父 depth != 0 / 父缺失 → 拒建 + logger.exception）；
- REST 投影加性：GET /threads/{tid}/runs 列表项新增 parent_run_id/depth ——
  普通 run 默认 null/0 · 子 run 取回父 id/1（§11.4 · 加性变更豁免零 diff §11.5）。
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime

import pytest
from httpx import AsyncClient
from sqlalchemy import delete, func, select

from app.db.models import OpsLgRagRun, OpsLgRagThread, OpsUser
from app.db.session import AsyncSessionLocal
from tests.conftest import DB_AVAILABLE

_DB_REQUIRED = pytest.mark.skipif(
    not DB_AVAILABLE, reason="需要本地 PG（opsdesk_test）真跑 claim/投影"
)

MAINTAINER_ID = "00000000-0000-0000-0000-000000000001"
_RUNS = "/api/ops/lg-rag/threads/{tid}/runs"
_BASE_TS = datetime(2026, 11, 18, 8, 0, 0)


async def _count_children(parent_run_id: str) -> int:
    async with AsyncSessionLocal() as db:
        return await db.scalar(
            select(func.count())
            .select_from(OpsLgRagRun)
            .where(OpsLgRagRun.parent_run_id == parent_run_id)
        )


async def _cleanup_prefix(prefix: str) -> None:
    async with AsyncSessionLocal() as db:
        await db.execute(delete(OpsLgRagRun).where(OpsLgRagRun.run_id.like(f"{prefix}%")))
        await db.execute(
            delete(OpsLgRagThread).where(OpsLgRagThread.id.like(f"{prefix}%"))
        )
        await db.commit()


@_DB_REQUIRED
@pytest.mark.asyncio
async def test_claim_child_run_inherit_and_reentrant_reuse(seeded_maintainer) -> None:
    """§8.2 归属继承 + §7.3 撞 uq 取回复用（零重复建行 · 防 replan/resume 重放）。"""
    from app.ops.lg_rag.run_store import claim_child_run, create_run

    user_id = str(seeded_maintainer["user"].id)
    prefix = f"p4t6-{uuid.uuid4().hex[:8]}"
    parent_id, child_id, child2_id = f"{prefix}-p", f"{prefix}-c1", f"{prefix}-c2"
    thread_id = f"{prefix}-th"
    try:
        assert (
            await create_run(
                run_id=parent_id,
                thread_id=thread_id,
                user_id=user_id,
                tenant_id="tenant-p4t6",
            )
            is True
        )
        rid, created = await claim_child_run(
            parent_run_id=parent_id, subtask_id="st-1", child_run_id=child_id
        )
        assert (rid, created) == (child_id, True)
        async with AsyncSessionLocal() as db:
            row = await db.get(OpsLgRagRun, child_id)
            assert row is not None
            assert row.parent_run_id == parent_id
            assert row.subtask_id == "st-1"
            assert row.depth == 1
            assert row.status == "running"
            # §8.2：归属全从父行取值（不从请求上下文取）
            assert row.tenant_id == "tenant-p4t6"
            assert str(row.user_id) == user_id
            assert row.thread_id == thread_id
        # 撞 uq 重入：取回同一 child run_id · created=False · 行数仍 1
        rid2, created2 = await claim_child_run(
            parent_run_id=parent_id, subtask_id="st-1", child_run_id=child2_id
        )
        assert (rid2, created2) == (child_id, False)
        assert await _count_children(parent_id) == 1
    finally:
        await _cleanup_prefix(prefix)


@_DB_REQUIRED
@pytest.mark.asyncio
async def test_claim_concurrent_only_one_wins(seeded_maintainer) -> None:
    """并发双 INSERT 正确（19 §7.3 R9/N6）：败者阻塞至胜者提交后 SELECT 取回。"""
    from app.ops.lg_rag.run_store import claim_child_run, create_run

    user_id = str(seeded_maintainer["user"].id)
    prefix = f"p4t6-{uuid.uuid4().hex[:8]}"
    parent_id = f"{prefix}-p"
    try:
        assert (
            await create_run(
                run_id=parent_id,
                thread_id=f"{prefix}-th",
                user_id=user_id,
                tenant_id="t",
            )
            is True
        )
        results = await asyncio.gather(
            *[
                claim_child_run(
                    parent_run_id=parent_id,
                    subtask_id="st-c",
                    child_run_id=f"{prefix}-c{i}",
                )
                for i in range(6)
            ]
        )
        assert sum(1 for _, created in results if created) == 1
        assert len({rid for rid, _ in results}) == 1  # 全部取回同一 child run_id
        assert await _count_children(parent_id) == 1
    finally:
        await _cleanup_prefix(prefix)


@_DB_REQUIRED
@pytest.mark.asyncio
async def test_claim_depth_assert_and_missing_parent(
    seeded_maintainer, caplog: pytest.LogCaptureFixture
) -> None:
    """§7.3 深度断言：父 depth != 0 / 父缺失 → 拒建（None）+ logger.exception。"""
    from app.ops.lg_rag.run_store import claim_child_run, create_run

    user_id = str(seeded_maintainer["user"].id)
    prefix = f"p4t6-{uuid.uuid4().hex[:8]}"
    parent_id, child_id = f"{prefix}-p", f"{prefix}-c1"
    try:
        await create_run(
            run_id=parent_id,
            thread_id=f"{prefix}-th",
            user_id=user_id,
            tenant_id="t",
        )
        rid, created = await claim_child_run(
            parent_run_id=parent_id, subtask_id="st-1", child_run_id=child_id
        )
        assert (rid, created) == (child_id, True)

        with caplog.at_level(logging.ERROR, logger="app.ops.lg_rag.run_store"):
            # 深度硬上限 1：以 depth=1 的子 run 为父 → 拒建
            assert (
                await claim_child_run(
                    parent_run_id=child_id,
                    subtask_id="st-x",
                    child_run_id=f"{prefix}-c9",
                )
                is None
            )
            # 父缺失 → 拒建
            assert (
                await claim_child_run(
                    parent_run_id=f"{prefix}-nope",
                    subtask_id="st-y",
                    child_run_id=f"{prefix}-c8",
                )
                is None
            )
        messages = [r.getMessage() for r in caplog.records]
        assert any("depth" in m and "拒建" in m for m in messages)
        assert any("父 run 不存在" in m for m in messages)
        # 拒建零建行
        assert await _count_children(child_id) == 0
    finally:
        await _cleanup_prefix(prefix)


# ---------------------------------------------------------------------------
# §11.4 REST 投影加性
# ---------------------------------------------------------------------------


@pytest.fixture
async def run_tree_seed():
    """造 thread + 根 run + 子 run（承 test_lg_rag_runs_readonly_api seed 体例）。"""
    if not DB_AVAILABLE:
        pytest.skip("PostgreSQL not available")
    prefix = f"p4t6p-{uuid.uuid4().hex[:8]}"
    created_user = False
    async with AsyncSessionLocal() as db:
        if await db.get(OpsUser, MAINTAINER_ID) is None:
            db.add(OpsUser(id=MAINTAINER_ID, username=f"{prefix}-mt", role="maintainer"))
            created_user = True
        await db.commit()
    tid = f"{prefix}-th"
    parent_id, child_id = f"{prefix}-p", f"{prefix}-c1"
    async with AsyncSessionLocal() as db:
        db.add(OpsLgRagThread(id=tid, user_id=MAINTAINER_ID))
        db.add(
            OpsLgRagRun(
                run_id=parent_id,
                tenant_id="tenant-p4t6",
                user_id=MAINTAINER_ID,
                thread_id=tid,
                status="running",
                created_at=_BASE_TS,
            )
        )
        db.add(
            OpsLgRagRun(
                run_id=child_id,
                tenant_id="tenant-p4t6",
                user_id=MAINTAINER_ID,
                thread_id=tid,
                status="running",
                created_at=_BASE_TS,
                parent_run_id=parent_id,
                subtask_id="st-1",
                depth=1,
            )
        )
        await db.commit()
    yield prefix, tid, parent_id, child_id
    async with AsyncSessionLocal() as db:
        await db.execute(delete(OpsLgRagRun).where(OpsLgRagRun.run_id.like(f"{prefix}%")))
        await db.execute(
            delete(OpsLgRagThread).where(OpsLgRagThread.id.like(f"{prefix}%"))
        )
        if created_user:
            await db.execute(delete(OpsUser).where(OpsUser.id == MAINTAINER_ID))
        await db.commit()


@_DB_REQUIRED
async def test_runs_list_projection_run_tree_fields(
    client: AsyncClient, override_auth_maintainer: None, run_tree_seed: tuple
) -> None:
    """§11.4：列表项含 parent_run_id/depth · 根 run 默认 null/0 · 子 run 父 id/1。"""
    _, tid, parent_id, child_id = run_tree_seed
    resp = await client.get(_RUNS.format(tid=tid))
    assert resp.status_code == 200, resp.text
    runs = {r["run_id"]: r for r in resp.json()["data"]["runs"]}
    assert set(runs) == {parent_id, child_id}
    # 加性字段在投影面出现
    for row in runs.values():
        assert "parent_run_id" in row and "depth" in row
    # 根 run 默认（既有行零 diff 语义：null/0）
    assert runs[parent_id]["parent_run_id"] is None
    assert runs[parent_id]["depth"] == 0
    # 子 run 投影
    assert runs[child_id]["parent_run_id"] == parent_id
    assert runs[child_id]["depth"] == 1
