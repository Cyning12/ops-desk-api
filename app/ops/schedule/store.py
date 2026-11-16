"""Schedule 读写唯一收口（P3-T2 · issue #23 · 契约真源 15 §1/§4 · 设计真源 14 R1-R23）。

状态机规则式（15 §1.6 矩阵），**LLM 不自判 status**：

- 创建 → active（fire_count=0 · next_fire_at 按 kind 即算 · 15 §1.3）；
- active↔paused 人工互转；active/paused→cancelled 人工；**cancelled 终态
  不可逆**（已 cancelled 再 PATCH → 422 逐字文案 · 15 §1.8）；
- 任一排期字段变更 → 重算 next_fire_at（重算守卫 N5：重算值须 > now）。

纪律分层（承 goals/store.py:11-16 先例）：读路径（list/get）best-effort
吞错 + 日志，返回 []/None 绝不反噬；写路径（create/patch）**显式抛错不吞**
（ScheduleNotFoundError → 404 · ScheduleValidationError → 422 逐字文案）。

排期算术用 stdlib zoneinfo（否 croniter 新依赖 · R3 裁定）；daily_at 取
时区内**严格晚于 now** 的下一个 time_of_day 本地时刻（v1 不随 DST 校准 ·
15 §1.2 钉明）。worker 点火循环不在本波（T3）。
"""

from __future__ import annotations

import logging
import re
import uuid as _uuid
from datetime import UTC, datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import func, select

from app.db.models import OpsLgRagThread, OpsSchedule, OpsScheduleFire
from app.db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)

# 词表（15 §1.2/§4.1 · 14 §1）
SCHEDULE_KINDS: frozenset[str] = frozenset({"once_at", "interval", "daily_at"})
SCHEDULE_STATUSES: frozenset[str] = frozenset({"active", "paused", "cancelled"})
FIRE_STATUSES: frozenset[str] = frozenset({"claimed", "fired", "skipped", "failed"})
CATCHUP_POLICIES: frozenset[str] = frozenset({"fire_once"})
DEFAULT_TIMEZONE = "Asia/Shanghai"

# 配额与下限（15 §1.8 · R4）
MAX_ACTIVE_PER_USER = 20
MAX_PER_TENANT = 200
MIN_INTERVAL_SECONDS = 300

# 合法流转矩阵（15 §1.6）：active↔paused 人工双向；→cancelled 人工；cancelled 终态
_ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    "active": frozenset({"paused", "cancelled"}),
    "paused": frozenset({"active", "cancelled"}),
    "cancelled": frozenset(),
}

# 422 文案词表（15 §1.8 · detail 字段逐字使用 · 前端不做二次包装）
ERR_USER_LIMIT = "本会话定时任务已达上限（20 个），请先暂停或取消不用的任务"
ERR_TENANT_LIMIT = "本租户定时任务已达上限（200 个），请联系管理员暂停或取消不用的任务"
ERR_INTERVAL_MIN = "定时任务间隔不能小于 300 秒（5 分钟）"
ERR_KIND = "非法的 schedule_kind（允许值：once_at / interval / daily_at）"
ERR_STATUS = "非法的 status（允许值：active / paused / cancelled）"
ERR_THREAD_OWNER = "该对话不属于当前用户，无法创建定时任务"
ERR_CANCELLED = "已取消的定时任务不可修改"

# instruction 单行化（15 §1.2 · 承 goals sanitize_objective 先例 · 不截断：instruction 是执行体）
_CONTROL_CHARS_RE = re.compile(r"[\x00-\x1f\x7f]+")
_WS_RE = re.compile(r"\s+")
_TIME_OF_DAY_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")

# 时区中文名映射（15 §1.8 · v1 仅收 Asia/Shanghai，其余回退原名）
_TIMEZONE_ZH_NAMES: dict[str, str] = {"Asia/Shanghai": "北京时间"}

#: humanized_display 时间格式（15 §1.8 「YYYY-MM-DD HH:mm」）
_HUMAN_DT_FMT = "%Y-%m-%d %H:%M"


class ScheduleNotFoundError(Exception):
    """schedule 不存在 / 跨 tenant / 跨 user 不可见（REST 映射 404 · 不泄露存在性）。"""


class ScheduleValidationError(Exception):
    """词表外 / 校验失败 / 终态再改（REST 映射 422 · detail 逐字文案）。"""


def sanitize_instruction(text: str) -> str:
    """instruction 单行化：控制符→空格、折叠空白（15 §1.2 · 承 goals 先例）。"""
    if not isinstance(text, str):
        return ""
    single = _CONTROL_CHARS_RE.sub(" ", text)
    return _WS_RE.sub(" ", single).strip()


def _now() -> datetime:
    return datetime.now(UTC)


def _ensure_aware(dt: datetime) -> datetime:
    """naive datetime 按 UTC 解释（timestamptz 语义 · asyncpg 要求 aware）。"""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


def _validate_timezone(tz_name: str) -> ZoneInfo:
    try:
        return ZoneInfo(tz_name)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise ScheduleValidationError(f"非法的 timezone（IANA 时区名）：{tz_name}") from exc


def compute_next_fire_at(
    *,
    schedule_kind: str,
    run_at: datetime | None = None,
    interval_seconds: int | None = None,
    time_of_day: str | None = None,
    tz_name: str = DEFAULT_TIMEZONE,
    now: datetime | None = None,
) -> datetime:
    """按 kind 计算 next_fire_at（15 §1.3 创建语义 · N5 重算共用同一入口）。

    - once_at → run_at（须未来时刻）；
    - interval → now + interval_seconds（≥300 · 15 §1.8）；
    - daily_at → tz_name 时区内严格晚于 now 的下一个 time_of_day（HH:MM 24h）。
    """
    now = now or _now()
    if schedule_kind not in SCHEDULE_KINDS:
        raise ScheduleValidationError(ERR_KIND)
    if schedule_kind == "once_at":
        if run_at is None:
            raise ScheduleValidationError("once_at 任务必须提供 run_at")
        run_at = _ensure_aware(run_at)
        if run_at <= now:
            raise ScheduleValidationError("run_at 必须是未来时刻")
        return run_at
    if schedule_kind == "interval":
        if interval_seconds is None:
            raise ScheduleValidationError("interval 任务必须提供 interval_seconds")
        if interval_seconds < MIN_INTERVAL_SECONDS:
            raise ScheduleValidationError(ERR_INTERVAL_MIN)
        return now + timedelta(seconds=interval_seconds)
    # daily_at
    if not time_of_day or not _TIME_OF_DAY_RE.match(time_of_day):
        raise ScheduleValidationError("非法的 time_of_day（格式：HH:MM · 24 小时制）")
    tz = _validate_timezone(tz_name)
    hh, mm = int(time_of_day[:2]), int(time_of_day[3:5])
    local_now = now.astimezone(tz)
    candidate = datetime.combine(local_now.date(), time(hh, mm), tzinfo=tz)
    if candidate <= local_now:
        candidate = datetime.combine(local_now.date() + timedelta(days=1), time(hh, mm), tzinfo=tz)
    return candidate.astimezone(UTC)


def humanized_display(
    *,
    schedule_kind: str,
    run_at: datetime | None = None,
    interval_seconds: int | None = None,
    time_of_day: str | None = None,
    tz_name: str = DEFAULT_TIMEZONE,
) -> str:
    """人类化频率文案（15 §1.8 · R20 · 卡片/列表展示用）。"""
    zh_tz = _TIMEZONE_ZH_NAMES.get(tz_name, tz_name)
    if schedule_kind == "once_at" and run_at is not None:
        try:
            local = _ensure_aware(run_at).astimezone(ZoneInfo(tz_name))
        except (ZoneInfoNotFoundError, ValueError):
            local = _ensure_aware(run_at)
        return f"将于 {local.strftime(_HUMAN_DT_FMT)}（{zh_tz}）执行一次"
    if schedule_kind == "interval" and interval_seconds is not None:
        minutes = interval_seconds // 60
        if interval_seconds >= 3600 and interval_seconds % 3600 == 0:
            return f"每 {interval_seconds // 3600} 小时"
        return f"每 {minutes} 分钟"
    if schedule_kind == "daily_at" and time_of_day:
        return f"每天 {time_of_day}（{zh_tz}）"
    return ""


def _to_dict(row: OpsSchedule) -> dict[str, Any]:
    """schedule 响应对象（15 §1.2 全字段 + humanized_display）。"""
    return {
        "schedule_id": str(row.schedule_id),
        "tenant_id": row.tenant_id,
        "user_id": str(row.user_id),
        "thread_id": row.thread_id,
        "name": row.name,
        "instruction": row.instruction,
        "schedule_kind": row.schedule_kind,
        "run_at": row.run_at.isoformat() if row.run_at else None,
        "interval_seconds": row.interval_seconds,
        "time_of_day": row.time_of_day,
        "timezone": row.timezone,
        "next_fire_at": row.next_fire_at.isoformat() if row.next_fire_at else None,
        "catchup_policy": row.catchup_policy,
        "status": row.status,
        "fire_count": row.fire_count,
        "max_fires": row.max_fires,
        "last_fired_at": row.last_fired_at.isoformat() if row.last_fired_at else None,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        "humanized_display": humanized_display(
            schedule_kind=row.schedule_kind,
            run_at=row.run_at,
            interval_seconds=row.interval_seconds,
            time_of_day=row.time_of_day,
            tz_name=row.timezone,
        ),
    }


def _fire_to_dict(row: OpsScheduleFire) -> dict[str, Any]:
    """fires 投影（15 §1.5 recent_fires 字段集）。"""
    return {
        "id": str(row.id),
        "planned_fire_at": row.planned_fire_at.isoformat() if row.planned_fire_at else None,
        "run_id": row.run_id,
        "status": row.status,
        "fired_at": row.fired_at.isoformat() if row.fired_at else None,
    }


async def _assert_thread_owned(db: Any, *, thread_id: str, user_id: Any) -> None:
    """R6（15 §1.7-2）：thread 存在须归属当前用户否则 422 零写；不存在允许。"""
    thread = await db.get(OpsLgRagThread, thread_id)
    if thread is not None and str(thread.user_id) != str(user_id):
        raise ScheduleValidationError(ERR_THREAD_OWNER)


async def _assert_quota(db: Any, *, tenant_id: str, user_id: str) -> None:
    """双上限（15 §1.8 · R4）：per-user active ≤20 · per-tenant 全量 ≤200。"""
    user_active = await db.scalar(
        select(func.count())
        .select_from(OpsSchedule)
        .where(
            OpsSchedule.tenant_id == tenant_id,
            OpsSchedule.user_id == user_id,
            OpsSchedule.status == "active",
        )
    )
    if (user_active or 0) >= MAX_ACTIVE_PER_USER:
        raise ScheduleValidationError(ERR_USER_LIMIT)
    tenant_total = await db.scalar(
        select(func.count()).select_from(OpsSchedule).where(OpsSchedule.tenant_id == tenant_id)
    )
    if (tenant_total or 0) >= MAX_PER_TENANT:
        raise ScheduleValidationError(ERR_TENANT_LIMIT)


def _validate_kind_fields(
    *,
    schedule_kind: str,
    run_at: datetime | None,
    interval_seconds: int | None,
    time_of_day: str | None,
    tz_name: str,
    now: datetime | None = None,
) -> datetime:
    """按 kind 校验字段齐备性并算 next_fire_at（创建/PATCH 共用）。"""
    next_fire_at = compute_next_fire_at(
        schedule_kind=schedule_kind,
        run_at=run_at,
        interval_seconds=interval_seconds,
        time_of_day=time_of_day,
        tz_name=tz_name,
        now=now,
    )
    if schedule_kind == "daily_at":
        _validate_timezone(tz_name)
    return next_fire_at


async def create_schedule(
    *,
    tenant_id: str,
    user_id: Any,
    thread_id: str,
    name: str,
    instruction: str,
    schedule_kind: str,
    run_at: datetime | None = None,
    interval_seconds: int | None = None,
    time_of_day: str | None = None,
    tz_name: str = DEFAULT_TIMEZONE,
    max_fires: int | None = None,
) -> dict[str, Any]:
    """创建定时任务（REST POST 唯一写入口）。**显式抛错不吞**：

    - 词表外 kind / interval<300 / run_at 非未来 / time_of_day 非法 → 422（零写）
    - 双上限超限 → 422 逐字文案（零写）
    - thread 存在且非当前用户所有 → 422 逐字文案（零写 · R6）
    """
    if schedule_kind not in SCHEDULE_KINDS:
        raise ScheduleValidationError(ERR_KIND)
    if max_fires is not None and max_fires < 1:
        raise ScheduleValidationError("max_fires 必须 ≥ 1")
    name = (name or "").strip()
    if not name or len(name) > 120:
        raise ScheduleValidationError("name 长度须在 1..120 之间")
    instruction = sanitize_instruction(instruction)
    if not instruction:
        raise ScheduleValidationError("instruction 不能为空")
    if run_at is not None:
        run_at = _ensure_aware(run_at)
    next_fire_at = _validate_kind_fields(
        schedule_kind=schedule_kind,
        run_at=run_at,
        interval_seconds=interval_seconds,
        time_of_day=time_of_day,
        tz_name=tz_name,
    )
    async with AsyncSessionLocal() as db:
        await _assert_thread_owned(db, thread_id=thread_id, user_id=user_id)
        await _assert_quota(db, tenant_id=tenant_id, user_id=user_id)
        row = OpsSchedule(
            tenant_id=tenant_id,
            user_id=user_id,
            thread_id=thread_id,
            name=name,
            instruction=instruction,
            schedule_kind=schedule_kind,
            run_at=run_at if schedule_kind == "once_at" else None,
            interval_seconds=interval_seconds if schedule_kind == "interval" else None,
            time_of_day=time_of_day if schedule_kind == "daily_at" else None,
            timezone=tz_name,
            next_fire_at=next_fire_at,
            catchup_policy="fire_once",
            status="active",
            fire_count=0,
            max_fires=max_fires,
        )
        db.add(row)
        await db.commit()
        await db.refresh(row)
        return _to_dict(row)


async def list_schedules(
    *,
    tenant_id: str,
    user_id: Any,
    thread_id: str | None = None,
    status: str | None = None,
) -> list[dict[str, Any]]:
    """当前用户 schedule 列表（15 §1.4：谓词 tenant+user · v1 不分页）。best-effort → []。"""
    if status is not None and status not in SCHEDULE_STATUSES:
        raise ScheduleValidationError(ERR_STATUS)
    try:
        async with AsyncSessionLocal() as db:
            stmt = select(OpsSchedule).where(
                OpsSchedule.tenant_id == tenant_id,
                OpsSchedule.user_id == user_id,
            )
            if thread_id:
                stmt = stmt.where(OpsSchedule.thread_id == thread_id)
            if status:
                stmt = stmt.where(OpsSchedule.status == status)
            stmt = stmt.order_by(OpsSchedule.created_at.asc())
            rows = (await db.execute(stmt)).scalars().all()
            return [_to_dict(r) for r in rows]
    except ScheduleValidationError:
        raise
    except Exception:
        logger.exception("schedule list failed tenant_id=%s user_id=%s", tenant_id, user_id)
        return []


async def get_schedule_with_fires(
    *, schedule_id: str, tenant_id: str, user_id: Any
) -> dict[str, Any]:
    """单条详情 + recent_fires（15 §1.5 · 最近 10 条 planned_fire_at 倒序）。

    跨 tenant / 跨 user / 不存在 → ScheduleNotFoundError（404 不泄露存在性）。
    """
    try:
        sid = _uuid.UUID(schedule_id)
    except (ValueError, AttributeError, TypeError) as exc:
        raise ScheduleNotFoundError(schedule_id) from exc
    async with AsyncSessionLocal() as db:
        row = await db.get(OpsSchedule, sid)
        if row is None or row.tenant_id != tenant_id or str(row.user_id) != str(user_id):
            raise ScheduleNotFoundError(schedule_id)
        fires = (
            (
                await db.execute(
                    select(OpsScheduleFire)
                    .where(OpsScheduleFire.schedule_id == row.schedule_id)
                    .order_by(OpsScheduleFire.planned_fire_at.desc())
                    .limit(10)
                )
            )
            .scalars()
            .all()
        )
        return {
            "schedule": _to_dict(row),
            "recent_fires": [_fire_to_dict(f) for f in fires],
        }


# PATCH 可改排期字段（任一变更 → 重算 next_fire_at · 15 §1.6 · N5）
_SCHEDULE_FIELDS: frozenset[str] = frozenset(
    {"run_at", "interval_seconds", "time_of_day", "timezone"}
)


async def patch_schedule(
    *,
    schedule_id: str,
    tenant_id: str,
    user_id: Any,
    status: str | None = None,
    name: str | None = None,
    instruction: str | None = None,
    run_at: datetime | None = None,
    interval_seconds: int | None = None,
    time_of_day: str | None = None,
    tz_name: str | None = None,
    max_fires: int | None = None,
    clear_max_fires: bool = False,
) -> dict[str, Any]:
    """状态机 + 改排期（15 §1.6 · REST PATCH 唯一写入口）。**显式抛错不吞**：

    - 不存在 / 跨 tenant / 跨 user → ScheduleNotFoundError（404）
    - 已 cancelled 再 PATCH → 422 逐字文案（终态不可逆）
    - 词表外 status / 非法流转 → 422
    - 排期字段变更 → 重算 next_fire_at（N5 守卫：重算值须 > now）
    """
    try:
        sid = _uuid.UUID(schedule_id)
    except (ValueError, AttributeError, TypeError) as exc:
        raise ScheduleNotFoundError(schedule_id) from exc
    if status is not None and status not in SCHEDULE_STATUSES:
        raise ScheduleValidationError(ERR_STATUS)
    if max_fires is not None and max_fires < 1:
        raise ScheduleValidationError("max_fires 必须 ≥ 1")
    async with AsyncSessionLocal() as db:
        row = await db.get(OpsSchedule, sid)
        if row is None or row.tenant_id != tenant_id or str(row.user_id) != str(user_id):
            raise ScheduleNotFoundError(schedule_id)
        if row.status == "cancelled":
            raise ScheduleValidationError(ERR_CANCELLED)

        if status is not None and status != row.status:
            allowed = _ALLOWED_TRANSITIONS.get(row.status, frozenset())
            if status not in allowed:
                raise ScheduleValidationError(f"非法的状态流转：{row.status} → {status}")
            row.status = status

        if name is not None:
            name = name.strip()
            if not name or len(name) > 120:
                raise ScheduleValidationError("name 长度须在 1..120 之间")
            row.name = name
        if instruction is not None:
            instruction = sanitize_instruction(instruction)
            if not instruction:
                raise ScheduleValidationError("instruction 不能为空")
            row.instruction = instruction
        if clear_max_fires:
            row.max_fires = None
        elif max_fires is not None:
            row.max_fires = max_fires

        schedule_dirty = (
            run_at is not None
            or interval_seconds is not None
            or time_of_day is not None
            or tz_name is not None
        )
        if schedule_dirty:
            new_run_at = run_at if run_at is not None else row.run_at
            if new_run_at is not None:
                new_run_at = _ensure_aware(new_run_at)
            new_interval = interval_seconds if interval_seconds is not None else row.interval_seconds
            new_tod = time_of_day if time_of_day is not None else row.time_of_day
            new_tz = tz_name if tz_name is not None else row.timezone
            next_fire_at = _validate_kind_fields(
                schedule_kind=row.schedule_kind,
                run_at=new_run_at,
                interval_seconds=new_interval,
                time_of_day=new_tod,
                tz_name=new_tz,
            )
            # N5 重算守卫：重算值须 > now（compute 对 once_at/daily_at 已保证未来，
            # interval=now+Δ 恒未来；此处兜底防御显式钉死）
            if next_fire_at <= _now():
                raise ScheduleValidationError("重算后的 next_fire_at 必须是未来时刻")
            if row.schedule_kind == "once_at":
                row.run_at = new_run_at
            elif row.schedule_kind == "interval":
                row.interval_seconds = new_interval
            else:
                row.time_of_day = new_tod
            row.timezone = new_tz
            row.next_fire_at = next_fire_at

        await db.commit()
        await db.refresh(row)
        return _to_dict(row)
