"""lg-rag SSE 事件落盘 / 按 after_seq 加载（T4 · 不依赖 chat/session）。"""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import func, select

from app.db.models import OpsLgRagRunEvent
from app.db.session import AsyncSessionLocal
from app.ops.lg_rag.sse_replay import format_sse_event

logger = logging.getLogger(__name__)


class LgRagRunNotFoundError(Exception):
    """未知或跨用户 run_id；HTTP 映射 404。"""


async def persist_run_event(
    *,
    run_id: str,
    seq: int,
    user_id: str,
    thread_id: str,
    ts_ms: int,
    agent_role: str,
    event_type: str,
    payload: dict[str, Any],
) -> None:
    """尽量落盘一帧；失败由调用方吞掉（不阻断 SSE）。"""
    if not run_id or not user_id:
        return
    async with AsyncSessionLocal() as db:
        db.add(
            OpsLgRagRunEvent(
                run_id=run_id,
                seq=seq,
                user_id=user_id,
                thread_id=thread_id or "",
                ts_ms=ts_ms,
                agent_role=agent_role,
                event_type=event_type,
                payload=payload or {},
            )
        )
        await db.commit()


async def run_owner(run_id: str) -> str | None:
    """该 run 的归属用户；run 不存在（还没落过帧）返回 ``None``。

    为什么需要这个反问：HITL 申请行里只有 ``thread_id`` / ``run_id``，
    **没有 user_id**，而 replay 是按 user_id 做归属校验的。
    恢复段要往**同一个 run_id** 里续写事件，归属只能从已有事件反查 ——
    取不到就宁可不写（写了也读不出来：另一个 user_id 永远 replay 不到），
    并且必须把这个"没写"报出来，不能静默。
    """
    if not run_id:
        return None
    async with AsyncSessionLocal() as db:
        row = (
            await db.execute(
                select(OpsLgRagRunEvent.user_id)
                .where(OpsLgRagRunEvent.run_id == run_id)
                .limit(1)
            )
        ).first()
    return str(row[0]) if row else None


async def last_seq(run_id: str) -> int:
    """该 run 当前最大 seq；恢复段从这里**接着编号**（不是从 1 重开）。"""
    if not run_id:
        return 0
    async with AsyncSessionLocal() as db:
        row = (
            await db.execute(
                select(func.max(OpsLgRagRunEvent.seq)).where(
                    OpsLgRagRunEvent.run_id == run_id
                )
            )
        ).first()
    return int(row[0] or 0) if row else 0


async def assert_run_owned(run_id: str, user_id: str) -> None:
    """确认 run 存在且归属当前用户；否则 ``LgRagRunNotFoundError``。"""
    if not run_id or not user_id:
        raise LgRagRunNotFoundError
    owner = await run_owner(run_id)
    if owner is None:
        raise LgRagRunNotFoundError
    if str(owner) != str(user_id):
        raise LgRagRunNotFoundError


async def load_events_after(
    run_id: str,
    user_id: str,
    after_seq: int,
) -> list[dict[str, Any]]:
    """归属校验后返回 ``seq > after_seq`` 的已提交帧（live 形状）。"""
    await assert_run_owned(run_id, user_id)
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(OpsLgRagRunEvent)
            .where(
                OpsLgRagRunEvent.run_id == run_id,
                OpsLgRagRunEvent.user_id == user_id,
                OpsLgRagRunEvent.seq > after_seq,
            )
            .order_by(OpsLgRagRunEvent.seq.asc())
        )
        rows = result.scalars().all()
    return [
        format_sse_event(
            {
                "run_id": row.run_id,
                "seq": row.seq,
                "ts_ms": row.ts_ms,
                "agent_role": row.agent_role,
                "event_type": row.event_type,
                "payload": row.payload or {},
            }
        )
        for row in rows
    ]
