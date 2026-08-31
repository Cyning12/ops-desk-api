"""lg-rag thread SoT：独立表加载 / 归属校验 / 落盘（不依赖 chat/session）。"""
from __future__ import annotations

import logging

from sqlalchemy import select

from app.db.models import OpsLgRagThread, OpsLgRagTurn, now_utc
from app.db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)


class LgRagThreadForbiddenError(Exception):
    """thread_id 属于其他用户；HTTP 映射 404，不泄露是否存在。"""


async def resolve_thread_for_user(thread_id: str, user_id: str) -> bool:
    """确保 thread 归属当前用户。

    返回 True：已存在且属本用户，或新建成功（可加载历史）。
    返回 False：存储不可用，调用方按无历史继续。
    跨用户：抛 ``LgRagThreadForbiddenError``。
    """
    if not thread_id or not user_id:
        return False
    try:
        async with AsyncSessionLocal() as db:
            row = await db.get(OpsLgRagThread, thread_id)
            if row is not None:
                if str(row.user_id) != str(user_id):
                    raise LgRagThreadForbiddenError
                return True
            db.add(OpsLgRagThread(id=thread_id, user_id=user_id))
            await db.commit()
            return True
    except LgRagThreadForbiddenError:
        raise
    except Exception:
        logger.exception("lg-rag resolve thread failed thread_id=%s", thread_id)
        return False


async def load_thread_turns(thread_id: str) -> list[dict]:
    """按时间升序加载该 thread 的 user/assistant/system 轮次；失败返回空。"""
    if not thread_id:
        return []
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(OpsLgRagTurn)
                .where(OpsLgRagTurn.thread_id == thread_id)
                .order_by(OpsLgRagTurn.created_at.asc())
            )
            rows = result.scalars().all()
        return [{"role": row.role, "content": row.content} for row in rows]
    except Exception:
        logger.exception("lg-rag load turns failed thread_id=%s", thread_id)
        return []


async def persist_thread_turns(
    thread_id: str,
    user_id: str,
    query: str,
    answer: str,
) -> None:
    """done 后尽量落盘本轮；失败只打日志。跨用户 thread 跳过。"""
    if not thread_id or not user_id:
        return
    try:
        async with AsyncSessionLocal() as db:
            row = await db.get(OpsLgRagThread, thread_id)
            if row is None:
                db.add(OpsLgRagThread(id=thread_id, user_id=user_id))
                await db.flush()
            elif str(row.user_id) != str(user_id):
                logger.warning(
                    "lg-rag persist skipped foreign thread_id=%s", thread_id
                )
                return
            if query:
                db.add(
                    OpsLgRagTurn(
                        thread_id=thread_id, role="user", content=query
                    )
                )
            if answer:
                db.add(
                    OpsLgRagTurn(
                        thread_id=thread_id, role="assistant", content=answer
                    )
                )
            owned = await db.get(OpsLgRagThread, thread_id)
            if owned is not None:
                owned.updated_at = now_utc()
            await db.commit()
    except Exception:
        logger.exception("lg-rag persist turns failed thread_id=%s", thread_id)
