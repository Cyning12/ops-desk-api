"""P0' T5 · ops_goals 仅 DDL 约束真值（issue #23 裁定 A2）。

仅落表零功能：默认值/NOT NULL 约束/索引存在性——本地真 PG 实证（承 T4 体例）。
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from tests.conftest import DB_AVAILABLE

_DB_REQUIRED = pytest.mark.skipif(not DB_AVAILABLE, reason="需要本地 PG（opsdesk_test）真跑 ops_goals 约束")


@_DB_REQUIRED
@pytest.mark.asyncio
async def test_ops_goals_defaults_and_roundtrip(seeded_maintainer) -> None:
    """建行默认值：status='active' · tenant_id='' · created_at/updated_at 自动；读出回环一致。"""
    from app.db.models import OpsGoal
    from app.db.session import AsyncSessionLocal

    goal_id = str(uuid.uuid4())
    thread_id = f"th-g-{uuid.uuid4().hex[:8]}"
    async with AsyncSessionLocal() as db:
        db.add(OpsGoal(goal_id=goal_id, thread_id=thread_id, objective="把支付告警排查到底"))
        await db.commit()
    async with AsyncSessionLocal() as db:
        row = await db.get(OpsGoal, goal_id)
        assert row is not None
        assert row.status == "active"
        assert row.tenant_id == ""  # 承 notes/runs 先例默认 ''
        assert row.objective == "把支付告警排查到底"
        assert row.created_at is not None
        assert row.updated_at is not None
    async with AsyncSessionLocal() as db:
        row = await db.get(OpsGoal, goal_id)
        await db.delete(row)
        await db.commit()


@_DB_REQUIRED
@pytest.mark.asyncio
async def test_ops_goals_tenant_id_not_null(seeded_maintainer) -> None:
    """tenant freeze F1-F6：tenant_id 必填——DB 级 NOT NULL 约束生效。

    注：ORM 显式 None 会触发 Python 侧 default=''（已知 quirk），故用裸 SQL
    直插 NULL 触达 DB 约束（承「迁移通过、tenant_id 必填约束生效」验收原文）。
    """
    from sqlalchemy import text

    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        with pytest.raises(IntegrityError):
            await db.execute(
                text(
                    "INSERT INTO ops_goals (goal_id, tenant_id, thread_id, objective)"
                    " VALUES (gen_random_uuid(), NULL, 'th', 'x')"
                )
            )
            await db.commit()


@_DB_REQUIRED
@pytest.mark.asyncio
async def test_ops_goals_objective_not_null(seeded_maintainer) -> None:
    """objective 必填（A2 列清单）。"""
    from app.db.models import OpsGoal
    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        db.add(OpsGoal(goal_id=str(uuid.uuid4()), thread_id="th", objective=None))  # type: ignore[arg-type]
        with pytest.raises(IntegrityError):
            await db.commit()
