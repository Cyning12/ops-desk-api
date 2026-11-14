"""lg-rag run 一等实体读写（P0' T4 · issue #23 裁定 A1）。

`ops_lg_rag_runs` 是 run 生命周期的权威状态面：`persist_run_event` 收口按事件
推导状态（done payload 的 status 逐字落列）；`start_run_worker` 起始建行。
**所有写面 best-effort**——调用方吞错，绝不反噬事件插入；缺行/失败由 orphan
两段式扫描兜住。
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, select

from app.db.models import OpsLgRagRun, OpsLgRagRunEvent, now_utc
from app.db.session import AsyncSessionLocal

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
