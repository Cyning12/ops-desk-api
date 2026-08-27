"""从 ops_runs 加载 session 消息历史。"""

from __future__ import annotations

from sqlalchemy import select

from app.db.models import OpsRun
from app.db.session import AsyncSessionLocal


async def load_session_turns(
    session_id: str,
    *,
    limit: int = 20,
) -> list[dict]:
    """按 session 加载最近 ``limit`` 条 run 的 user/assistant 轮次。

    返回 chronological 列表；无 answer 的 run 仅含 user 轮。
    """
    if not session_id:
        return []

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(OpsRun)
            .where(OpsRun.session_id == session_id)
            .order_by(OpsRun.created_at.desc())
            .limit(limit)
        )
        runs = list(reversed(result.scalars().all()))

    turns: list[dict] = []
    for run in runs:
        query = (run.query or "").strip()
        if query:
            turns.append({"role": "user", "content": query})
        answer = (run.answer or "").strip()
        if answer:
            turns.append({"role": "assistant", "content": answer})
    return turns
