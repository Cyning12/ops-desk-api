"""P3-T2 · ops_schedules / ops_schedule_fires 仅 DDL 约束真值（issue #23 · 契约 15 §4）。

默认值 / NOT NULL / 唯一幂等键 / 索引存在性——本地真 PG 实证（承 test_ops_goals_ddl 体例）。
"""

from __future__ import annotations

import uuid
from datetime import UTC

import pytest
from sqlalchemy.exc import IntegrityError

from tests.conftest import DB_AVAILABLE

_DB_REQUIRED = pytest.mark.skipif(
    not DB_AVAILABLE, reason="需要本地 PG（opsdesk_test）真跑 ops_schedules 约束"
)


def _mk_schedule_row(**over):
    from app.db.models import OpsSchedule

    kwargs = {
        "tenant_id": "ops-desk-pilot",
        "thread_id": f"th-{uuid.uuid4().hex[:8]}",
        "name": "每天提醒",
        "instruction": "提醒我站会",
        "schedule_kind": "interval",
        "interval_seconds": 600,
        "next_fire_at": __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ),
    }
    kwargs.update(over)
    return OpsSchedule(**kwargs)


@_DB_REQUIRED
@pytest.mark.asyncio
async def test_ops_schedules_defaults_and_roundtrip(seeded_maintainer) -> None:
    """建行默认值：status='active' · fire_count=0 · catchup_policy='fire_once' ·
    timezone='Asia/Shanghai' · created_at/updated_at 自动；读出回环一致。"""
    from app.db.models import OpsSchedule
    from app.db.session import AsyncSessionLocal

    user = seeded_maintainer["user"]
    async with AsyncSessionLocal() as db:
        row = _mk_schedule_row(user_id=user.id)
        db.add(row)
        await db.commit()
        sid = row.schedule_id
    async with AsyncSessionLocal() as db:
        got = await db.get(OpsSchedule, sid)
        assert got is not None
        assert got.status == "active"
        assert got.fire_count == 0
        assert got.catchup_policy == "fire_once"
        assert got.timezone == "Asia/Shanghai"
        assert got.tenant_id == "ops-desk-pilot"
        assert got.created_at is not None
        assert got.updated_at is not None
        assert got.created_at.tzinfo is not None  # timestamptz aware
        await db.delete(got)
        await db.commit()


@_DB_REQUIRED
@pytest.mark.asyncio
async def test_ops_schedules_tenant_id_not_null(seeded_maintainer) -> None:
    """tenant freeze F1-F6：tenant_id 必填——裸 SQL 直插 NULL 触达 DB 级 NOT NULL。"""
    from sqlalchemy import text

    from app.db.session import AsyncSessionLocal

    user = seeded_maintainer["user"]
    async with AsyncSessionLocal() as db:
        with pytest.raises(IntegrityError):
            await db.execute(
                text(
                    "INSERT INTO ops_schedules (tenant_id, user_id, thread_id, name, instruction,"
                    " schedule_kind, next_fire_at)"
                    " VALUES (NULL, :uid, 'th', 'n', 'i', 'interval', now())"
                ),
                {"uid": str(user.id)},
            )
            await db.commit()


@_DB_REQUIRED
@pytest.mark.asyncio
async def test_ops_schedule_fires_uq_planned_idempotent(seeded_maintainer) -> None:
    """uq(schedule_id, planned_fire_at) 幂等键（15 §4.1）：同键二次 INSERT → IntegrityError。

    该约束是 T3 worker ON CONFLICT DO NOTHING 的落点（15 §4.2 写入纪律）。
    """
    from datetime import datetime

    from sqlalchemy import text

    from app.db.models import OpsSchedule
    from app.db.session import AsyncSessionLocal

    user = seeded_maintainer["user"]
    planned = datetime(2026, 12, 1, 9, 0, tzinfo=UTC)
    async with AsyncSessionLocal() as db:
        row = _mk_schedule_row(user_id=user.id)
        db.add(row)
        await db.commit()
        sid = row.schedule_id
        await db.execute(
            text(
                "INSERT INTO ops_schedule_fires"
                " (id, schedule_id, tenant_id, planned_fire_at, status)"
                " VALUES (gen_random_uuid(), :sid, :tid, :planned, 'claimed')"
            ),
            {"sid": str(sid), "tid": "ops-desk-pilot", "planned": planned},
        )
        await db.commit()
        with pytest.raises(IntegrityError):
            await db.execute(
                text(
                    "INSERT INTO ops_schedule_fires"
                    " (id, schedule_id, tenant_id, planned_fire_at, status)"
                    " VALUES (gen_random_uuid(), :sid, :tid, :planned, 'claimed')"
                ),
                {"sid": str(sid), "tid": "ops-desk-pilot", "planned": planned},
            )
            await db.commit()
        await db.rollback()
        got = await db.get(OpsSchedule, sid)
        await db.delete(got)
        await db.commit()


@_DB_REQUIRED
@pytest.mark.asyncio
async def test_ops_schedules_indexes_exist(seeded_maintainer) -> None:
    """索引存在性：idx_ops_schedules_next_fire(status,next_fire_at) ·
    idx_ops_schedule_fires_run_id(run_id · 15 §3.1 归因反查防 N+1)。"""
    from sqlalchemy import text

    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        rows = (
            await db.execute(
                text(
                    "SELECT indexname FROM pg_indexes"
                    " WHERE tablename IN ('ops_schedules', 'ops_schedule_fires')"
                )
            )
        ).all()
    names = {r[0] for r in rows}
    assert "idx_ops_schedules_next_fire" in names
    assert "idx_ops_schedule_fires_run_id" in names
