"""lg-rag SSE 事件落盘 / 按 after_seq 加载（T4 · 不依赖 chat/session）。"""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import select

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


async def assert_run_owned(run_id: str, user_id: str) -> None:
    """确认 run 存在且归属当前用户；否则 ``LgRagRunNotFoundError``。"""
    if not run_id or not user_id:
        raise LgRagRunNotFoundError
    async with AsyncSessionLocal() as db:
        row = (
            await db.execute(
                select(OpsLgRagRunEvent.user_id)
                .where(OpsLgRagRunEvent.run_id == run_id)
                .limit(1)
            )
        ).first()
        if row is None:
            raise LgRagRunNotFoundError
        if str(row[0]) != str(user_id):
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
