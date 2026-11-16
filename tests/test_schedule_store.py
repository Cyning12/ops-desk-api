"""P3-T2 · schedule store 单测（issue #23 · 契约 15 §1）。

纯函数面（无 DB）：compute_next_fire_at 三种 kind · humanized_display 文案 ·
sanitize_instruction 单行化 · 词表。
DB 面（真 PG）：create 创建语义 · 双上限 · R6 thread 归属 · patch 状态机与重算。
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.ops.schedule.store import (
    ERR_INTERVAL_MIN,
    ERR_KIND,
    ERR_THREAD_OWNER,
    ERR_USER_LIMIT,
    MAX_ACTIVE_PER_USER,
    MIN_INTERVAL_SECONDS,
    ScheduleValidationError,
    compute_next_fire_at,
    humanized_display,
    sanitize_instruction,
)
from tests.conftest import DB_AVAILABLE

_DB_REQUIRED = pytest.mark.skipif(
    not DB_AVAILABLE, reason="需要本地 PG（opsdesk_test）真跑 schedule store"
)

_NOW = datetime(2026, 11, 16, 12, 0, 0, tzinfo=UTC)


class TestComputeNextFireAt:
    def test_once_at_future(self):
        run_at = _NOW + timedelta(hours=2)
        assert compute_next_fire_at(
            schedule_kind="once_at", run_at=run_at, now=_NOW
        ) == run_at

    def test_once_at_past_rejected(self):
        with pytest.raises(ScheduleValidationError, match="run_at 必须是未来时刻"):
            compute_next_fire_at(
                schedule_kind="once_at", run_at=_NOW - timedelta(hours=1), now=_NOW
            )

    def test_once_at_naive_interpreted_utc(self):
        """naive datetime 按 UTC 解释（timestamptz 语义）。"""
        naive = (_NOW + timedelta(hours=1)).replace(tzinfo=None)
        got = compute_next_fire_at(schedule_kind="once_at", run_at=naive, now=_NOW)
        assert got.tzinfo is not None

    def test_interval_now_plus_delta(self):
        got = compute_next_fire_at(
            schedule_kind="interval", interval_seconds=600, now=_NOW
        )
        assert got == _NOW + timedelta(seconds=600)

    def test_interval_below_min_422(self):
        with pytest.raises(ScheduleValidationError) as exc:
            compute_next_fire_at(
                schedule_kind="interval", interval_seconds=MIN_INTERVAL_SECONDS - 1, now=_NOW
            )
        assert str(exc.value) == ERR_INTERVAL_MIN

    def test_unknown_kind_422(self):
        with pytest.raises(ScheduleValidationError) as exc:
            compute_next_fire_at(schedule_kind="cron", now=_NOW)
        assert str(exc.value) == ERR_KIND

    def test_daily_at_same_day_when_future(self):
        # Asia/Shanghai 20:00 = UTC 12:00（此刻）；21:00 仍在今天
        got = compute_next_fire_at(
            schedule_kind="daily_at", time_of_day="21:00", now=_NOW
        )
        assert got == datetime(2026, 11, 16, 13, 0, tzinfo=UTC)

    def test_daily_at_next_day_when_passed(self):
        """严格晚于 now：当今天该时刻已过（含恰等）→ 次日（15 §1.2）。"""
        got = compute_next_fire_at(
            schedule_kind="daily_at", time_of_day="19:00", now=_NOW
        )
        assert got == datetime(2026, 11, 17, 11, 0, tzinfo=UTC)
        edge = compute_next_fire_at(
            schedule_kind="daily_at", time_of_day="20:00", now=_NOW
        )
        assert edge == datetime(2026, 11, 17, 12, 0, tzinfo=UTC)

    def test_daily_at_bad_format_422(self):
        with pytest.raises(ScheduleValidationError, match="time_of_day"):
            compute_next_fire_at(schedule_kind="daily_at", time_of_day="25:00", now=_NOW)

    def test_daily_at_bad_timezone_422(self):
        with pytest.raises(ScheduleValidationError, match="timezone"):
            compute_next_fire_at(
                schedule_kind="daily_at", time_of_day="09:00",
                tz_name="Mars/Olympus", now=_NOW,
            )


class TestHumanizedDisplay:
    def test_once_at(self):
        run_at = datetime(2026, 12, 1, 1, 30, tzinfo=UTC)  # 北京 09:30
        got = humanized_display(schedule_kind="once_at", run_at=run_at)
        assert got == "将于 2026-12-01 09:30（北京时间）执行一次"

    def test_interval_minutes(self):
        assert humanized_display(schedule_kind="interval", interval_seconds=900) == "每 15 分钟"

    def test_interval_hours(self):
        assert humanized_display(schedule_kind="interval", interval_seconds=7200) == "每 2 小时"

    def test_daily_at(self):
        assert (
            humanized_display(schedule_kind="daily_at", time_of_day="09:00")
            == "每天 09:00（北京时间）"
        )

    def test_timezone_fallback_raw_name(self):
        got = humanized_display(
            schedule_kind="daily_at", time_of_day="09:00", tz_name="America/New_York"
        )
        assert got == "每天 09:00（America/New_York）"


class TestSanitizeInstruction:
    def test_control_chars_and_ws_folded(self):
        assert sanitize_instruction("提醒\n站会\t开始  了") == "提醒 站会 开始 了"

    def test_non_string(self):
        assert sanitize_instruction(None) == ""  # type: ignore[arg-type]


@_DB_REQUIRED
class TestStoreDb:
    async def _mk_user(self):
        """建真用户（ops_schedules.user_id FK ops_users）。"""
        from app.db.models import OpsUser
        from app.db.session import AsyncSessionLocal

        async with AsyncSessionLocal() as db:
            user = OpsUser(username=f"sch-{uuid.uuid4().hex[:8]}", role="viewer")
            db.add(user)
            await db.commit()
            await db.refresh(user)
            return user

    async def test_create_semantics(self):
        """创建：status=active · fire_count=0 · next_fire_at 即算 · 响应全字段（15 §1.3/§1.2）。"""
        from app.ops.schedule.store import create_schedule

        user = await self._mk_user()
        run_at = datetime.now(UTC) + timedelta(hours=3)
        got = await create_schedule(
            tenant_id="ops-desk-pilot",
            user_id=user.id,
            thread_id=f"th-{uuid.uuid4().hex[:8]}",
            name="一次性提醒",
            instruction="  提醒\n喝水  ",
            schedule_kind="once_at",
            run_at=run_at,
        )
        assert got["status"] == "active"
        assert got["fire_count"] == 0
        assert got["next_fire_at"] is not None
        assert got["instruction"] == "提醒 喝水"
        assert got["catchup_policy"] == "fire_once"
        assert got["humanized_display"].startswith("将于 ")
        for key in (
            "schedule_id", "tenant_id", "user_id", "thread_id", "name", "instruction",
            "schedule_kind", "run_at", "interval_seconds", "time_of_day", "timezone",
            "next_fire_at", "catchup_policy", "status", "fire_count", "max_fires",
            "last_fired_at", "created_at", "updated_at", "humanized_display",
        ):
            assert key in got, f"响应缺字段 {key}（15 §1.2 全字段）"

    async def test_thread_owner_mismatch_422(self):
        """R6：thread 存在且非当前用户所有 → 422 逐字文案零写（15 §1.7-2）。"""
        from app.db.models import OpsLgRagThread
        from app.db.session import AsyncSessionLocal
        from app.ops.schedule.store import create_schedule

        owner = await self._mk_user()
        other = await self._mk_user()
        thread_id = f"th-{uuid.uuid4().hex[:8]}"
        async with AsyncSessionLocal() as db:
            db.add(OpsLgRagThread(id=thread_id, user_id=owner.id))
            await db.commit()
        with pytest.raises(ScheduleValidationError) as exc:
            await create_schedule(
                tenant_id="ops-desk-pilot",
                user_id=other.id,
                thread_id=thread_id,
                name="x",
                instruction="y",
                schedule_kind="interval",
                interval_seconds=600,
            )
        assert str(exc.value) == ERR_THREAD_OWNER

    async def test_thread_not_exists_allowed(self):
        """R6：thread 不存在允许创建（15 §1.7-2）。"""
        from app.ops.schedule.store import create_schedule

        user = await self._mk_user()
        got = await create_schedule(
            tenant_id="ops-desk-pilot",
            user_id=user.id,
            thread_id=f"th-not-exists-{uuid.uuid4().hex[:8]}",
            name="x",
            instruction="y",
            schedule_kind="interval",
            interval_seconds=600,
        )
        assert got["schedule_id"]

    async def test_per_user_active_limit(self):
        """配额：per-user active 达 20 → 422 逐字文案（15 §1.8 · R4）。"""
        from app.ops.schedule.store import create_schedule

        user = await self._mk_user()
        thread_id = f"th-{uuid.uuid4().hex[:8]}"
        for i in range(MAX_ACTIVE_PER_USER):
            await create_schedule(
                tenant_id="ops-desk-pilot",
                user_id=user.id,
                thread_id=thread_id,
                name=f"n{i}",
                instruction="y",
                schedule_kind="interval",
                interval_seconds=600,
            )
        with pytest.raises(ScheduleValidationError) as exc:
            await create_schedule(
                tenant_id="ops-desk-pilot",
                user_id=user.id,
                thread_id=thread_id,
                name="overflow",
                instruction="y",
                schedule_kind="interval",
                interval_seconds=600,
            )
        assert str(exc.value) == ERR_USER_LIMIT

    async def test_patch_state_machine_and_cancelled_terminal(self):
        """状态机（15 §1.6）：active→paused→active；→cancelled 后再 PATCH → 422 逐字。"""
        from app.ops.schedule.store import (
            ERR_CANCELLED,
            create_schedule,
            patch_schedule,
        )

        user = await self._mk_user()
        got = await create_schedule(
            tenant_id="ops-desk-pilot",
            user_id=user.id,
            thread_id=f"th-{uuid.uuid4().hex[:8]}",
            name="n",
            instruction="y",
            schedule_kind="interval",
            interval_seconds=600,
        )
        sid = got["schedule_id"]
        p = await patch_schedule(
            schedule_id=sid, tenant_id="ops-desk-pilot", user_id=user.id, status="paused"
        )
        assert p["status"] == "paused"
        a = await patch_schedule(
            schedule_id=sid, tenant_id="ops-desk-pilot", user_id=user.id, status="active"
        )
        assert a["status"] == "active"
        c = await patch_schedule(
            schedule_id=sid, tenant_id="ops-desk-pilot", user_id=user.id, status="cancelled"
        )
        assert c["status"] == "cancelled"
        with pytest.raises(ScheduleValidationError) as exc:
            await patch_schedule(
                schedule_id=sid, tenant_id="ops-desk-pilot", user_id=user.id, status="active"
            )
        assert str(exc.value) == ERR_CANCELLED

    async def test_patch_reschedule_recomputes_next_fire(self):
        """改排期 → 重算 next_fire_at（15 §1.6 · N5）。"""
        from app.ops.schedule.store import create_schedule, patch_schedule

        user = await self._mk_user()
        got = await create_schedule(
            tenant_id="ops-desk-pilot",
            user_id=user.id,
            thread_id=f"th-{uuid.uuid4().hex[:8]}",
            name="n",
            instruction="y",
            schedule_kind="interval",
            interval_seconds=600,
        )
        sid = got["schedule_id"]
        old_next = datetime.fromisoformat(got["next_fire_at"])
        patched = await patch_schedule(
            schedule_id=sid,
            tenant_id="ops-desk-pilot",
            user_id=user.id,
            interval_seconds=3600,
        )
        new_next = datetime.fromisoformat(patched["next_fire_at"])
        assert patched["interval_seconds"] == 3600
        assert new_next > old_next
        assert new_next > datetime.now(UTC)

    async def test_cross_tenant_and_cross_user_invisible(self):
        """隔离：跨 tenant / 跨 user → list 不见 · get/patch 404（15 §1.7-1）。"""
        from app.ops.schedule.store import (
            ScheduleNotFoundError,
            create_schedule,
            get_schedule_with_fires,
            list_schedules,
            patch_schedule,
        )

        user_a = await self._mk_user()
        user_b = await self._mk_user()
        got = await create_schedule(
            tenant_id="ops-desk-pilot",
            user_id=user_a.id,
            thread_id=f"th-{uuid.uuid4().hex[:8]}",
            name="n",
            instruction="y",
            schedule_kind="interval",
            interval_seconds=600,
        )
        sid = got["schedule_id"]
        # 跨 user
        assert await list_schedules(
            tenant_id="ops-desk-pilot", user_id=user_b.id, thread_id=got["thread_id"]
        ) == []
        with pytest.raises(ScheduleNotFoundError):
            await get_schedule_with_fires(
                schedule_id=sid, tenant_id="ops-desk-pilot", user_id=user_b.id
            )
        with pytest.raises(ScheduleNotFoundError):
            await patch_schedule(
                schedule_id=sid, tenant_id="ops-desk-pilot", user_id=user_b.id, status="paused"
            )
        # 跨 tenant
        assert await list_schedules(
            tenant_id="ops-desk-pilot-b", user_id=user_a.id
        ) == []
        with pytest.raises(ScheduleNotFoundError):
            await get_schedule_with_fires(
                schedule_id=sid, tenant_id="ops-desk-pilot-b", user_id=user_a.id
            )
