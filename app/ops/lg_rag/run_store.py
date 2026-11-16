"""lg-rag run 一等实体读写（P0' T4 · issue #23 裁定 A1）。

`ops_lg_rag_runs` 是 run 生命周期的权威状态面：`persist_run_event` 收口按事件
推导状态（done payload 的 status 逐字落列）；`start_run_worker` 起始建行。
**所有写面 best-effort**——调用方吞错，绝不反噬事件插入；缺行/失败由 orphan
两段式扫描兜住。
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import and_, func, or_, select, text
from sqlalchemy.exc import ProgrammingError

from app.db.models import OpsLgRagRun, OpsLgRagRunEvent, now_utc
from app.db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)

# 终态集合：终帧（done/error）落列后置 finished_at；hitl.resumed 回升 running。
TERMINAL_STATUSES: frozenset[str] = frozenset({"done", "resumed", "disconnected", "error"})


def status_for_event(event_type: str, payload: dict[str, Any] | None) -> str | None:
    """由事件推导 run 目标状态；None = 不变。

    - done{status:X} → X（逐字落列；缺 status 兜底 "done"）
    - error → "error"
    - hitl.resumed → "running"（清 finished_at）
    - 其余（token/thought/node.progress/hitl.waiting 等）→ 不变
    """
    if event_type == "done":
        s = (payload or {}).get("status")
        return s if isinstance(s, str) and s else "done"
    if event_type == "error":
        return "error"
    if event_type == "hitl.resumed":
        return "running"
    return None


def _as_utc_naive(dt: datetime) -> datetime:
    """混时区归一（migrate 后 timestamptz → aware；create_all 面 naive → UTC）。"""
    if dt.tzinfo is not None:
        return dt.astimezone(UTC).replace(tzinfo=None)
    return dt


async def create_run(
    *, run_id: str, thread_id: str, user_id: str | None, tenant_id: str | None
) -> bool:
    """建行（幂等）：已存在（单飞复用/补行后）→ False；user_id 缺失 → False。

    best-effort：调用方自行 try/except；本函数只在显式不可建行时静默返回 False。
    """
    if not run_id or not user_id:
        return False
    async with AsyncSessionLocal() as db:
        existing = await db.get(OpsLgRagRun, run_id)
        if existing is not None:
            return False
        db.add(
            OpsLgRagRun(
                run_id=run_id,
                tenant_id=tenant_id or "",
                user_id=user_id,
                thread_id=thread_id or "",
                status="running",
            )
        )
        await db.commit()
    return True


async def apply_run_event_status(
    *, run_id: str, event_type: str, payload: dict[str, Any] | None
) -> None:
    """persist 收口挂钩：按事件推进 run 状态；无 run 行（前 T4 / 建行失败）静默跳过。"""
    target = status_for_event(event_type, payload)
    if target is None:
        return
    async with AsyncSessionLocal() as db:
        row = await db.get(OpsLgRagRun, run_id)
        if row is None:
            return  # 无前 T4 行 —— orphan 补行子路径兜住
        row.status = target
        row.finished_at = now_utc() if target in TERMINAL_STATUSES else None
        await db.commit()


async def list_stale_running_runs(
    *, stale_after_seconds: int, limit: int = 50
) -> list[dict[str, Any]]:
    """runs 表主扫：status='running' 候选 + created_at 预筛 + per-run 末帧精确 stale。

    返回 [{run_id, user_id, thread_id, max_seq, last_activity_at}]。时间语义与旧
    `event_store.list_open_runs` 一致（stale<=0 → 无时间过滤）。
    """
    cutoff = (
        now_utc() - timedelta(seconds=stale_after_seconds)
        if stale_after_seconds > 0
        else None
    )
    async with AsyncSessionLocal() as db:
        stmt = (
            select(OpsLgRagRun)
            .where(OpsLgRagRun.status == "running")
            .order_by(OpsLgRagRun.created_at.asc())
            .limit(limit)
        )
        if cutoff is not None:
            stmt = stmt.where(OpsLgRagRun.created_at < cutoff)
        candidates = (await db.execute(stmt)).scalars().all()
        if not candidates:
            return []
        ids = [r.run_id for r in candidates]
        agg = (
            select(
                OpsLgRagRunEvent.run_id,
                func.max(OpsLgRagRunEvent.seq),
                func.max(OpsLgRagRunEvent.created_at),
            )
            .where(OpsLgRagRunEvent.run_id.in_(ids))
            .group_by(OpsLgRagRunEvent.run_id)
        )
        stats = {
            row[0]: (int(row[1]), row[2])
            for row in (await db.execute(agg)).all()
        }
    out: list[dict[str, Any]] = []
    for r in candidates:
        max_seq, last_at = stats.get(r.run_id, (0, r.created_at))
        if stale_after_seconds > 0 and last_at is not None:
            age = (now_utc() - _as_utc_naive(last_at)).total_seconds()
            if age < stale_after_seconds:
                continue  # 末帧仍新鲜 —— 真在飞
        out.append(
            {
                "run_id": r.run_id,
                "user_id": str(r.user_id),
                "thread_id": r.thread_id,
                "max_seq": max_seq,
                "last_activity_at": last_at,
            }
        )
    return out


async def backfill_missing_run_rows(*, limit: int = 50) -> int:
    """补行子路径：事件表有帧但 runs 无行的 run（前 T4 数据/建行失败）有界补行。

    tenant_id 不可知 → `''`（承 notes 先例）；created_at 取首帧时间保 stale 语义。
    """
    async with AsyncSessionLocal() as db:
        has_row = select(OpsLgRagRun.run_id).where(
            OpsLgRagRun.run_id == OpsLgRagRunEvent.run_id
        )
        stmt = (
            select(OpsLgRagRunEvent.run_id)
            .where(~has_row.exists())
            .distinct()
            .limit(limit)
        )
        missing = [row[0] for row in (await db.execute(stmt)).all()]
        added = 0
        for rid in missing:
            first = (
                await db.execute(
                    select(OpsLgRagRunEvent)
                    .where(OpsLgRagRunEvent.run_id == rid)
                    .order_by(OpsLgRagRunEvent.seq.asc())
                    .limit(1)
                )
            ).scalars().first()
            if first is None:
                continue
            db.add(
                OpsLgRagRun(
                    run_id=rid,
                    tenant_id="",
                    user_id=first.user_id,
                    thread_id=first.thread_id or "",
                    status="running",
                    created_at=first.created_at,
                )
            )
            added += 1
        if added:
            await db.commit()
    return added


# ---------------------------------------------------------------------------
# P3-T4 · runs 只读端点数据面（契约 15-p3-contracts.md §3）
# ---------------------------------------------------------------------------

# §4.1：fires 台账（T2 建表）契约钉名；唯一归因真源（§4.4，query 前缀文本非依据）。
_ATTRIBUTION_SQL = text(
    "SELECT f.run_id AS run_id, f.id AS fire_id, "
    "s.schedule_id AS schedule_id, s.name AS schedule_name "
    "FROM ops_schedule_fires f "
    "JOIN ops_schedules s ON s.schedule_id = f.schedule_id "
    "WHERE f.run_id = ANY(:run_ids) "
    "ORDER BY f.fired_at DESC NULLS LAST"
)


async def list_thread_runs_page(
    user_id: str,
    thread_id: str,
    *,
    limit: int,
    after: tuple[datetime, str] | None = None,
) -> list[dict[str, Any]]:
    """thread 属主 runs 一页（§3.1 keyset：created_at desc, run_id desc）。

    返回 ``limit + 1`` 条以内（调用方据超出判定 next_cursor）；每项
    ``{run_id, thread_id, status, created_at, finished_at}``——status 为
    六词表原值直出，不做修补。
    """
    stmt = select(OpsLgRagRun).where(
        OpsLgRagRun.user_id == user_id,
        OpsLgRagRun.thread_id == thread_id,
    )
    if after is not None:
        after_ts, after_rid = after
        stmt = stmt.where(
            or_(
                OpsLgRagRun.created_at < after_ts,
                and_(
                    OpsLgRagRun.created_at == after_ts,
                    OpsLgRagRun.run_id < after_rid,
                ),
            )
        )
    stmt = stmt.order_by(
        OpsLgRagRun.created_at.desc(), OpsLgRagRun.run_id.desc()
    ).limit(limit + 1)
    async with AsyncSessionLocal() as db:
        rows = (await db.execute(stmt)).scalars().all()
    return [
        {
            "run_id": r.run_id,
            "thread_id": r.thread_id,
            "status": r.status,
            "created_at": r.created_at,
            "finished_at": r.finished_at,
        }
        for r in rows
    ]


async def fetch_run_start_queries(run_ids: list[str]) -> dict[str, str]:
    """批量反查各 run 的 run.start payload.query（单次 IN 查询防 N+1 · §3.1）。

    每 run 取最小 seq 的 run.start 帧；无该帧或无 query 键 → 不落键（调用方
    映射 None）。返回 ``{run_id: query}``。
    """
    if not run_ids:
        return {}
    stmt = (
        select(OpsLgRagRunEvent.run_id, OpsLgRagRunEvent.payload)
        .where(
            OpsLgRagRunEvent.run_id.in_(list(run_ids)),
            OpsLgRagRunEvent.event_type == "run.start",
        )
        .order_by(OpsLgRagRunEvent.run_id.asc(), OpsLgRagRunEvent.seq.asc())
    )
    async with AsyncSessionLocal() as db:
        rows = (await db.execute(stmt)).all()
    out: dict[str, str] = {}
    for run_id, payload in rows:
        if run_id in out:
            continue  # 同 run 多 run.start（恢复段）取首帧
        query = (payload or {}).get("query")
        if isinstance(query, str) and query:
            out[run_id] = query
    return out


async def fetch_schedule_attributions(run_ids: list[str]) -> dict[str, dict[str, str]]:
    """批量反查 runs 的 schedule 归因（fires 台账 · 单次 IN 查询防 N+1 · §3.1）。

    返回 ``{run_id: {schedule_id, name, fire_id}}``；无归因 run 不落键
    （调用方映射 None）。

    R-P3-T4-1：fires/schedules 表随 T2 并行未落地时（UndefinedTable
    sqlstate=42P01）降级为空归因 + warning——表在即生效，零改动。
    """
    if not run_ids:
        return {}
    async with AsyncSessionLocal() as db:
        try:
            rows = (
                await db.execute(_ATTRIBUTION_SQL, {"run_ids": list(run_ids)})
            ).all()
        except ProgrammingError as exc:
            if getattr(getattr(exc, "orig", None), "sqlstate", "") != "42P01":
                raise
            logger.warning(
                "ops_schedule_fires/ops_schedules 未落地（T2 在途）· schedule 归因降级空值"
            )
            return {}
    out: dict[str, dict[str, str]] = {}
    for row in rows:
        run_id = str(row.run_id)
        if run_id in out:
            continue  # 同 run 多 fire（重试）取最近 fired_at（SQL 已 desc）
        out[run_id] = {
            "schedule_id": str(row.schedule_id),
            "name": str(row.schedule_name),
            "fire_id": str(row.fire_id),
        }
    return out

