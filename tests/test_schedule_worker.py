"""P3-T3 · Schedule worker 触发执行器（issue #23 · 设计 14 §1.1-§1.8 · 契约 15 §4/§7.1）。

- env 闸（R8）：默认 off · on · 非法回退 off + warning；tick 默认 30 非法/越界回退。
- DB 抢占（真 PG）：SKIP LOCKED 并发双扫不重领 · 幂等键撞行不重火 · batch 上限。
- 状态机全流转：claimed→fired（run_id 写回才算）/ failed（R6 外来 thread ·
  R11 悬空 user+schedule 自动 paused · run 创建失败）/ skipped（max_fires · 执行时
  schedule 已 paused）。
- 补跑 fire_once：过期 interval 单 tick 只补一次并推进严格未来。
- 启动补链（R10）：claimed 孤儿（run_id IS NULL 且超龄）按台账重放。
- 预算归因（R4）：start_run_worker 显式收 creator user_id/tenant_id ·
  ops_lg_rag_runs.user_id == creator（归因链锚定 · ops_llm_usage 无 user_id 列）。
- 闸 off 默认零行为：TestClient 零 diff（lifespan 不建 task）。
- fix-434（issue #434 第一项 · 15 §1.2「fire 时不存在则 worker 自建」）：
  fire 同事务 thread upsert——无 turns schedule 点火后 ops_lg_rag_threads
  补最小行 · 既有行二火不动 · 端到端 runs 卡片端点 200 含 run_id（不再 404）。
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import create_async_engine

from app.db.models import (
    OpsLgRagRun,
    OpsLgRagThread,
    OpsSchedule,
    OpsScheduleFire,
    OpsUser,
)
from app.db.session import AsyncSessionLocal
from app.ops.schedule import worker
from tests.conftest import DB_AVAILABLE

_DB_REQUIRED = pytest.mark.skipif(
    not DB_AVAILABLE, reason="需要本地 PG（opsdesk_test）真跑 schedule worker"
)

_NOW = datetime(2026, 11, 16, 12, 0, 0, tzinfo=UTC)


async def _purge_async() -> None:
    """清场：opsdesk_test 为共享库（T2 波残留行）· worker 断言依赖全局计数。

    独立 engine（用后即 dispose）避免与 pytest-asyncio 测试 loop 的连接池串线；
    插真行+删行纪律（铁律：禁 DROP 式容错）。
    """

    from app.config import settings

    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
            await conn.execute(delete(OpsScheduleFire))
            await conn.execute(delete(OpsSchedule))
    finally:
        await eng.dispose()


@pytest.fixture(autouse=True)
def _purge_schedule_tables():
    if DB_AVAILABLE:
        asyncio.run(_purge_async())
        # asyncio.run() 会把当前 loop 置 None（_set_called=True）；
        # 本仓 pytest-asyncio 旧版在 runtest 时 asyncio.get_event_loop() 取当前 loop，
        # 须补一个全新 loop 供其驱动 async 测试。
        asyncio.set_event_loop(asyncio.new_event_loop())
    yield


# ---------- helpers ----------


async def _mk_user() -> OpsUser:
    async with AsyncSessionLocal() as db:
        user = OpsUser(username=f"sch-w-{uuid.uuid4().hex[:8]}", role="viewer")
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user


async def _mk_schedule(
    user: OpsUser,
    *,
    schedule_kind: str = "interval",
    next_fire_at: datetime | None = None,
    status: str = "active",
    fire_count: int = 0,
    max_fires: int | None = None,
    interval_seconds: int | None = 600,
    run_at: datetime | None = None,
    time_of_day: str | None = None,
    thread_id: str | None = None,
    name: str = "巡检",
) -> OpsSchedule:
    async with AsyncSessionLocal() as db:
        row = OpsSchedule(
            tenant_id="ops-desk-pilot",
            user_id=user.id,
            thread_id=thread_id or f"th-{uuid.uuid4().hex[:8]}",
            name=name,
            instruction="巡检同步状态",
            schedule_kind=schedule_kind,
            run_at=run_at,
            interval_seconds=interval_seconds,
            time_of_day=time_of_day,
            timezone="Asia/Shanghai",
            next_fire_at=next_fire_at or (_NOW - timedelta(minutes=5)),
            catchup_policy="fire_once",
            status=status,
            fire_count=fire_count,
            max_fires=max_fires,
        )
        db.add(row)
        await db.commit()
        await db.refresh(row)
        return row


async def _fires_of(schedule_id) -> list[OpsScheduleFire]:
    async with AsyncSessionLocal() as db:
        return list(
            (
                await db.execute(
                    select(OpsScheduleFire).where(OpsScheduleFire.schedule_id == schedule_id)
                )
            )
            .scalars()
            .all()
        )


async def _schedule_of(schedule_id) -> OpsSchedule:
    async with AsyncSessionLocal() as db:
        row = await db.get(OpsSchedule, schedule_id)
        assert row is not None
        return row


async def _noop(**kwargs):
    return {}


class _WorkerSpy:
    """start_run_worker 探针：记录 kwargs，返回假 bus。"""

    def __init__(self) -> None:
        self.calls: list[dict] = []

    def __call__(self, **kwargs):
        self.calls.append(kwargs)
        return object()


@pytest.fixture
def worker_spy(monkeypatch):
    from app.ops.lg_rag import run_worker as _run_worker

    spy = _WorkerSpy()
    monkeypatch.setattr(_run_worker, "start_run_worker", spy)
    return spy


# ---------- env 闸（R8 · 纯函数面无 DB） ----------


class TestGateEnv:
    def test_default_off(self, monkeypatch):
        monkeypatch.delenv(worker.ENV_SCHEDULE_ENABLED, raising=False)
        assert worker.schedule_worker_enabled() == worker.MODE_OFF

    def test_on_case_insensitive(self, monkeypatch):
        monkeypatch.setenv(worker.ENV_SCHEDULE_ENABLED, " ON ")
        assert worker.schedule_worker_enabled() == worker.MODE_ON

    def test_invalid_falls_back_off_with_warning(self, monkeypatch, caplog):
        monkeypatch.setenv(worker.ENV_SCHEDULE_ENABLED, "enabled")
        with caplog.at_level(logging.WARNING, logger="app.ops.schedule.worker"):
            assert worker.schedule_worker_enabled() == worker.MODE_OFF
        assert "按 off 处理" in caplog.text

    def test_tick_default(self, monkeypatch):
        monkeypatch.delenv(worker.ENV_TICK_SECONDS, raising=False)
        assert worker.tick_seconds() == 30

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [("abc", 30), ("0", 30), ("-5", 30), ("3601", 30), ("5", 5), ("60", 60)],
    )
    def test_tick_parse(self, monkeypatch, raw, expected):
        monkeypatch.setenv(worker.ENV_TICK_SECONDS, raw)
        assert worker.tick_seconds() == expected


# ---------- DB 抢占（14 §1.4 · 真 PG） ----------


@_DB_REQUIRED
class TestClaim:
    async def test_due_interval_claimed_and_advanced(self):
        user = await _mk_user()
        sch = await _mk_schedule(user)
        planned = sch.next_fire_at
        claimed = await worker.claim_due_schedules(now=_NOW)
        assert len(claimed) == 1
        fires = await _fires_of(sch.schedule_id)
        assert len(fires) == 1
        assert fires[0].status == "claimed"
        assert fires[0].planned_fire_at == planned
        after = await _schedule_of(sch.schedule_id)
        assert after.fire_count == 1
        assert after.last_fired_at is not None
        assert after.next_fire_at == _NOW + timedelta(seconds=600)
        assert after.next_fire_at > _NOW

    async def test_future_and_paused_not_claimed(self):
        user = await _mk_user()
        future = await _mk_schedule(user, next_fire_at=_NOW + timedelta(hours=1))
        paused = await _mk_schedule(user, status="paused")
        cancelled = await _mk_schedule(user, status="cancelled")
        claimed = await worker.claim_due_schedules(now=_NOW)
        assert claimed == []
        for sch in (future, paused, cancelled):
            assert await _fires_of(sch.schedule_id) == []

    async def test_once_at_claimed_once_no_advance(self):
        """once_at 幂等键 + NOT EXISTS 双保险：重复 tick 不重火（15 §1.2 max_fires=1 语义）。"""
        user = await _mk_user()
        sch = await _mk_schedule(
            user,
            schedule_kind="once_at",
            interval_seconds=None,
            run_at=_NOW - timedelta(minutes=5),
        )
        planned = sch.next_fire_at
        first = await worker.claim_due_schedules(now=_NOW)
        assert len(first) == 1
        second = await worker.claim_due_schedules(now=_NOW + timedelta(minutes=10))
        assert second == []
        fires = await _fires_of(sch.schedule_id)
        assert len(fires) == 1
        after = await _schedule_of(sch.schedule_id)
        assert after.next_fire_at == planned  # once_at 不推进（无下一时刻可算）
        assert after.fire_count == 1

    async def test_idempotency_key_collision_skips(self):
        """幂等键撞行（他方已占该计划时刻）→ 不重火 · 不炸事务。"""
        user = await _mk_user()
        sch = await _mk_schedule(user)
        async with AsyncSessionLocal() as db:
            db.add(
                OpsScheduleFire(
                    schedule_id=sch.schedule_id,
                    tenant_id=sch.tenant_id,
                    planned_fire_at=sch.next_fire_at,
                    status="fired",
                )
            )
            await db.commit()
        claimed = await worker.claim_due_schedules(now=_NOW)
        assert claimed == []  # NOT EXISTS 谓词先过滤
        assert len(await _fires_of(sch.schedule_id)) == 1
        assert (await _schedule_of(sch.schedule_id)).fire_count == 0

    async def test_concurrent_scanners_no_double_claim(self):
        """并发双扫不重领（SKIP LOCKED 行锁=租约 · 14 §1.4）。"""
        user = await _mk_user()
        sch = await _mk_schedule(user)
        first, second = await asyncio.gather(
            worker.claim_due_schedules(now=_NOW),
            worker.claim_due_schedules(now=_NOW),
        )
        assert len(first) + len(second) == 1
        fires = await _fires_of(sch.schedule_id)
        assert len(fires) == 1
        assert (await _schedule_of(sch.schedule_id)).fire_count == 1

    async def test_max_fires_reached_marks_skipped(self):
        """max_fires 达限（PATCH 调低所致）→ fire 立即 skipped · 不增 fire_count ·
        interval 仍推进 next_fire_at（提高 max_fires 即自然恢复 · 15 §4.1 状态机字面）。"""
        user = await _mk_user()
        sch = await _mk_schedule(user, fire_count=1, max_fires=1)
        claimed = await worker.claim_due_schedules(now=_NOW)
        assert len(claimed) == 1
        fires = await _fires_of(sch.schedule_id)
        assert [f.status for f in fires] == ["skipped"]
        after = await _schedule_of(sch.schedule_id)
        assert after.fire_count == 1  # 不增
        assert after.next_fire_at == _NOW + timedelta(seconds=600)

    async def test_batch_limit(self):
        user = await _mk_user()
        schs = [await _mk_schedule(user) for _ in range(3)]
        claimed = await worker.claim_due_schedules(now=_NOW, batch_limit=2)
        assert len(claimed) == 2
        total = 0
        for sch in schs:
            total += len(await _fires_of(sch.schedule_id))
        assert total == 2


# ---------- 触发语义 + 状态机（15 §4 · 真 PG） ----------


@_DB_REQUIRED
class TestFireExecution:
    async def test_full_tick_fired_with_attribution(self, worker_spy, caplog):
        """happy path：fire fired · run_id 写回 · 审计三元组 · R4 预算归因链锚定 creator。"""
        user = await _mk_user()
        sch = await _mk_schedule(user, name="夜间巡检")
        with caplog.at_level(logging.INFO, logger="app.ops.schedule.worker"):
            stats = await worker.run_schedule_tick(now=_NOW)
        assert stats == {"claimed": 1, "fired": 1, "failed": 0, "skipped": 0}
        fires = await _fires_of(sch.schedule_id)
        assert len(fires) == 1
        fire = fires[0]
        assert fire.status == "fired"
        assert fire.run_id is not None
        assert fire.fired_at is not None
        # 触发语义：query 带 [定时任务 · {name}] 前缀（仅展示 · 15 §4.4）
        assert len(worker_spy.calls) == 1
        call = worker_spy.calls[0]
        assert call["query"] == "[定时任务 · 夜间巡检] 巡检同步状态"
        assert call["mode"] == "supervisor"
        assert call["thread_id"] == sch.thread_id
        assert call["run_id"] == fire.run_id
        # R4 预算归因：creator 身份显式传（请求上下文外创建）
        assert call["user_id"] == str(user.id)
        assert call["tenant_id"] == sch.tenant_id
        # 归因链锚定：ops_lg_rag_runs.user_id == creator（usage.run_id → runs.user_id）
        async with AsyncSessionLocal() as db:
            run = await db.get(OpsLgRagRun, fire.run_id)
        assert run is not None
        assert str(run.user_id) == str(user.id)
        assert run.tenant_id == sch.tenant_id
        # 审计日志三元组（schedule_id / fire_id / run_id · 15 §4.4）
        assert "schedule fired" in caplog.text
        assert str(sch.schedule_id) in caplog.text
        assert str(fire.id) in caplog.text
        assert fire.run_id in caplog.text

    async def test_foreign_thread_failed(self, worker_spy, caplog):
        """R6：fire 前复核 thread 归属——外来 thread → failed 不投递。"""
        user = await _mk_user()
        other = await _mk_user()
        thread_id = f"th-{uuid.uuid4().hex[:8]}"
        async with AsyncSessionLocal() as db:
            db.add(OpsLgRagThread(id=thread_id, user_id=other.id))
            await db.commit()
        sch = await _mk_schedule(user, thread_id=thread_id)
        with caplog.at_level(logging.WARNING, logger="app.ops.schedule.worker"):
            stats = await worker.run_schedule_tick(now=_NOW)
        assert stats["failed"] == 1 and stats["fired"] == 0
        fires = await _fires_of(sch.schedule_id)
        assert fires[0].status == "failed"
        assert fires[0].run_id is None
        assert worker_spy.calls == []
        assert "foreign thread" in caplog.text
        # schedule 不暂停（仅 user 悬空才 paused · R11）
        assert (await _schedule_of(sch.schedule_id)).status == "active"

    async def test_dangling_user_failed_and_schedule_paused(
        self, monkeypatch, worker_spy, caplog
    ):
        """R11：创建者悬空 → failed + schedule 自动 paused（14 §1.2 注）。

        注：ops_schedules.user_id FK ON DELETE CASCADE——真删 user 会连带删
        schedule，DB 层无法自然留出悬空行；R11 为防御性复核（如 FK 约束被绕过
        的手工修数场景），测试以 patch AsyncSession.get 模拟 OpsUser 读空。
        """
        from sqlalchemy.ext.asyncio import AsyncSession as _SASession

        orig_get = _SASession.get

        async def _fake_get(self, entity, ident, **kwargs):
            if entity is OpsUser:
                return None
            return await orig_get(self, entity, ident, **kwargs)

        monkeypatch.setattr(_SASession, "get", _fake_get)
        user = await _mk_user()
        sch = await _mk_schedule(user)
        with caplog.at_level(logging.WARNING, logger="app.ops.schedule.worker"):
            stats = await worker.run_schedule_tick(now=_NOW)
        assert stats["failed"] == 1
        fires = await _fires_of(sch.schedule_id)
        assert fires[0].status == "failed"
        assert worker_spy.calls == []
        assert "dangling user" in caplog.text
        assert (await _schedule_of(sch.schedule_id)).status == "paused"

    async def test_create_run_failure_marks_failed(self, monkeypatch, worker_spy, caplog):
        """run 创建失败 → failed + logger.exception 留痕（14 §11 · 不重打）。"""
        from app.ops.lg_rag import run_store as _run_store

        async def _boom(**kwargs):
            raise RuntimeError("db down")

        monkeypatch.setattr(_run_store, "create_run", _boom)
        user = await _mk_user()
        sch = await _mk_schedule(user)
        with caplog.at_level(logging.ERROR, logger="app.ops.schedule.worker"):
            stats = await worker.run_schedule_tick(now=_NOW)
        assert stats["failed"] == 1
        fires = await _fires_of(sch.schedule_id)
        assert fires[0].status == "failed"
        assert fires[0].run_id is None  # 失败回滚不留半成品写回（重读 DB 视角）
        assert worker_spy.calls == []
        assert "schedule fire failed" in caplog.text

    async def test_paused_between_claim_and_execute_skipped(self, worker_spy):
        """claimed 后·执行前 schedule 被 paused → 执行置 skipped（15 §4.1）。"""
        user = await _mk_user()
        sch = await _mk_schedule(user)
        claimed = await worker.claim_due_schedules(now=_NOW)
        assert len(claimed) == 1
        async with AsyncSessionLocal() as db:
            row = await db.get(OpsSchedule, sch.schedule_id)
            row.status = "paused"
            await db.commit()
        outcome = await worker._execute_fire(fire_id=claimed[0], source="tick")
        assert outcome == "skipped"
        fires = await _fires_of(sch.schedule_id)
        assert fires[0].status == "skipped"
        assert worker_spy.calls == []


# ---------- 补跑 fire_once + 启动补链（14 §1.5 · R10） ----------


@_DB_REQUIRED
class TestCatchupAndRelink:
    async def test_fire_once_single_catchup(self, worker_spy):
        """停机跨 N 个 interval 只补一次：过期 30 分钟（3 个 interval）单 tick 只火一次，
        next_fire_at 推进到严格未来（14 §1.5 fire_once）。"""
        user = await _mk_user()
        sch = await _mk_schedule(user, next_fire_at=_NOW - timedelta(minutes=30))
        stats = await worker.run_schedule_tick(now=_NOW)
        assert stats["fired"] == 1
        assert len(worker_spy.calls) == 1
        after = await _schedule_of(sch.schedule_id)
        assert after.next_fire_at > _NOW
        assert after.fire_count == 1
        # 下一轮（同 now）不再入选
        stats2 = await worker.run_schedule_tick(now=_NOW)
        assert stats2["claimed"] == 0

    async def test_relink_stale_claimed_fires(self, worker_spy):
        """启动补链：claimed 孤儿（run_id IS NULL 且超龄）按台账重放（15 §4.3 只信台账）。"""
        user = await _mk_user()
        sch = await _mk_schedule(user)
        stale = OpsScheduleFire(
            schedule_id=sch.schedule_id,
            tenant_id=sch.tenant_id,
            planned_fire_at=sch.next_fire_at,
            status="claimed",
        )
        async with AsyncSessionLocal() as db:
            db.add(stale)
            await db.commit()
            await db.refresh(stale)
            # created_at 拨老（列默认 now · 测试直拨）
            stale.created_at = _NOW - timedelta(seconds=worker.CLAIM_STALE_SECONDS + 60)
            await db.commit()
        stats = await worker.relink_stale_claimed_fires(now=_NOW)
        assert stats["relinked"] == 1
        assert stats["fired"] == 1
        fires = await _fires_of(sch.schedule_id)
        assert len(fires) == 1
        assert fires[0].id == stale.id
        assert fires[0].status == "fired"
        assert fires[0].run_id is not None
        assert len(worker_spy.calls) == 1
        assert worker_spy.calls[0]["user_id"] == str(user.id)

    async def test_relink_ignores_fresh_claimed(self, worker_spy):
        """未超龄的 claimed 行不补链（执行可能在飞）。"""
        user = await _mk_user()
        sch = await _mk_schedule(user)
        async with AsyncSessionLocal() as db:
            db.add(
                OpsScheduleFire(
                    schedule_id=sch.schedule_id,
                    tenant_id=sch.tenant_id,
                    planned_fire_at=sch.next_fire_at,
                    status="claimed",
                )
            )
            await db.commit()
        stats = await worker.relink_stale_claimed_fires(now=_NOW)
        assert stats["relinked"] == 0
        assert worker_spy.calls == []

    async def test_relink_paused_schedule_marks_skipped(self, worker_spy):
        """补链时 schedule 已 paused → 台账行置 skipped 不重放。"""
        user = await _mk_user()
        sch = await _mk_schedule(user, status="paused")
        async with AsyncSessionLocal() as db:
            fire = OpsScheduleFire(
                schedule_id=sch.schedule_id,
                tenant_id=sch.tenant_id,
                planned_fire_at=sch.next_fire_at,
                status="claimed",
            )
            db.add(fire)
            await db.commit()
            await db.refresh(fire)
            fire.created_at = _NOW - timedelta(seconds=worker.CLAIM_STALE_SECONDS + 60)
            await db.commit()
        stats = await worker.relink_stale_claimed_fires(now=_NOW)
        assert stats["relinked"] == 1
        assert stats["skipped"] == 1
        fires = await _fires_of(sch.schedule_id)
        assert fires[0].status == "skipped"
        assert worker_spy.calls == []


# ---------- lifespan 挂接 + 闸 off 零 diff（R8 · TestClient） ----------


@_DB_REQUIRED
class TestLifespanGate:
    def test_gate_off_zero_diff(self, monkeypatch):
        """off（默认）：lifespan 不创建 worker task · REST 面零 diff（14 §1.7 进验收）。"""
        from fastapi.testclient import TestClient

        from app.main import app as fastapi_app

        monkeypatch.delenv(worker.ENV_SCHEDULE_ENABLED, raising=False)
        worker._WORKER_TASK = None
        with TestClient(fastapi_app) as tc:
            assert worker._WORKER_TASK is None
            resp = tc.get("/api/ops/schedules")
            assert resp.status_code == 401  # 未登录 401 · REST 面不被闸（15 §7.1）
        assert worker._WORKER_TASK is None

    def test_gate_invalid_zero_diff(self, monkeypatch, caplog):
        """非法值回退 off + warning · 零创建（R8 fail-closed）。"""
        from fastapi.testclient import TestClient

        from app.main import app as fastapi_app

        monkeypatch.setenv(worker.ENV_SCHEDULE_ENABLED, "yes")
        worker._WORKER_TASK = None
        with (
            caplog.at_level(logging.WARNING, logger="app.ops.schedule.worker"),
            TestClient(fastapi_app),
        ):
            assert worker._WORKER_TASK is None
        assert "按 off 处理" in caplog.text

    def test_gate_on_creates_and_stops_task(self, monkeypatch):
        """on：lifespan 创建 task（启动补链+首轮 tick 真跑 DB）· shutdown cancel 收尾。"""
        from fastapi.testclient import TestClient

        from app.main import app as fastapi_app

        monkeypatch.setenv(worker.ENV_SCHEDULE_ENABLED, "on")
        monkeypatch.setenv(worker.ENV_TICK_SECONDS, "3600")
        worker._WORKER_TASK = None
        with TestClient(fastapi_app):
            task = worker._WORKER_TASK
            assert task is not None
            assert not task.done()
        assert worker._WORKER_TASK is None
        assert task.done()


class TestFivePieceSet:
    """五件套本体（承 auto_resume:273-309 · 无 DB 纯事件循环面）。"""

    async def test_start_idempotent_and_stop(self, monkeypatch):
        monkeypatch.setattr(worker, "relink_stale_claimed_fires", _noop)
        monkeypatch.setattr(worker, "run_schedule_tick", _noop)
        worker._WORKER_TASK = None
        t1 = worker.start_schedule_worker()
        t2 = worker.start_schedule_worker()
        assert t1 is t2  # 模块级句柄幂等复用
        await asyncio.sleep(0.05)
        await worker.stop_schedule_worker()
        assert worker._WORKER_TASK is None
        assert t1.done()

    async def test_loop_survives_tick_exception(self, monkeypatch):
        """tick 内 DB 异常 → logger.exception + 下周期重试（不炸 · 14 §11）。"""
        calls = {"n": 0}

        async def _flaky(**kwargs):
            calls["n"] += 1
            if calls["n"] == 1:
                raise RuntimeError("db glitch")
            return {}

        monkeypatch.setattr(worker, "relink_stale_claimed_fires", _noop)
        monkeypatch.setattr(worker, "run_schedule_tick", _flaky)
        monkeypatch.setenv(worker.ENV_TICK_SECONDS, "1")
        worker._WORKER_TASK = None
        task = worker.start_schedule_worker()
        await asyncio.sleep(1.3)
        await worker.stop_schedule_worker()
        assert calls["n"] >= 2  # 失败后下周期重试
        assert task.done()


# ---------- fix-434 · fire 同事务 thread upsert（issue #434 第一项 · 15 §1.2） ----------


@_DB_REQUIRED
class TestThreadUpsert:
    async def test_missing_thread_row_created_on_fire(self, worker_spy):
        """无 turns 的 schedule fire → ops_lg_rag_threads 补最小行（id/user_id=creator）。"""
        user = await _mk_user()
        sch = await _mk_schedule(user)
        stats = await worker.run_schedule_tick(now=_NOW)
        assert stats["fired"] == 1
        async with AsyncSessionLocal() as db:
            thread = await db.get(OpsLgRagThread, sch.thread_id)
        assert thread is not None
        assert str(thread.user_id) == str(user.id)

    async def test_existing_thread_row_untouched_on_refire(self, worker_spy):
        """既有行（属 creator）二火后 created_at/user_id 不变（upsert 已存在不动）。"""
        user = await _mk_user()
        thread_id = f"th-{uuid.uuid4().hex[:8]}"
        async with AsyncSessionLocal() as db:
            db.add(OpsLgRagThread(id=thread_id, user_id=user.id))
            await db.commit()
        await _mk_schedule(user, thread_id=thread_id, max_fires=2)
        async with AsyncSessionLocal() as db:
            before = await db.get(OpsLgRagThread, thread_id)
            assert before is not None
            created_at_before = before.created_at
        stats1 = await worker.run_schedule_tick(now=_NOW)
        assert stats1["fired"] == 1
        stats2 = await worker.run_schedule_tick(now=_NOW + timedelta(seconds=600))
        assert stats2["fired"] == 1
        async with AsyncSessionLocal() as db:
            after = await db.get(OpsLgRagThread, thread_id)
        assert after.created_at == created_at_before
        assert str(after.user_id) == str(user.id)

    async def test_runs_card_endpoint_200_after_fire(
        self, client, override_auth_maintainer, worker_spy
    ):
        """端到端可见性（承 test_lg_rag_runs_readonly_api.py 先例形态）：
        fire 后 creator 会话 GET runs 卡片端点 → 200 且含该 run_id（不再 404）。"""
        maintainer_id = "00000000-0000-0000-0000-000000000001"
        async with AsyncSessionLocal() as db:
            user = await db.get(OpsUser, maintainer_id)
            if user is None:
                user = OpsUser(
                    id=maintainer_id,
                    username=f"fix434-{uuid.uuid4().hex[:8]}",
                    role="maintainer",
                )
                db.add(user)
                await db.commit()
                await db.refresh(user)
        sch = await _mk_schedule(user)
        stats = await worker.run_schedule_tick(now=_NOW)
        assert stats["fired"] == 1
        fires = await _fires_of(sch.schedule_id)
        run_id = fires[0].run_id
        assert run_id is not None
        resp = await client.get(f"/api/ops/lg-rag/threads/{sch.thread_id}/runs")
        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        ids = [r["run_id"] for r in body["data"]["runs"]]
        assert run_id in ids
