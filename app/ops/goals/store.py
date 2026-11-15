"""Goal 读写唯一收口（P1-T1 · issue #385 · 设计真源 07-p1-goal-design）。

状态机规则式（07 §1 矩阵），**LLM 不自判 status**：

- ∅ → active：首 turn 懒创建（resolve_goal_for_thread，T4 接线后生效）；
- paused → active：**仅人工 PATCH**（O-1 终裁：不做新 turn 自动复活）；
- active/paused → done/abandoned：仅人工 PATCH；终态不可逆；
- 1 thread : 1 非终态 goal（O-3 · DB 执行面=T4 部分唯一索引，本模块
  catch IntegrityError 重读消化竞态）。

纪律分层（platform 评审修正③ · run_store.py:5-6 先例）：

- **读路径**（resolve/get/list）供装配链路调用：best-effort 吞错 + 日志带
  thread_id，返回 None/[] 绝不反噬主链路；
- **写路径**（patch_goal_status）供 REST 用户显式动作：**显式抛错不吞**
  （GoalNotFoundError → 404 · GoalStateTransitionError → 409），吞错=点了没反应。
"""

from __future__ import annotations

import logging
import re
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.db.models import OpsGoal, now_utc
from app.db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)

# 词表（承 T5 models.py:307-308 docstring 登记 · 07 §1）
TERMINAL_GOAL_STATUSES: frozenset[str] = frozenset({"done", "abandoned"})
NONTERMINAL_GOAL_STATUSES: frozenset[str] = frozenset({"active", "paused"})
ALL_GOAL_STATUSES: frozenset[str] = TERMINAL_GOAL_STATUSES | NONTERMINAL_GOAL_STATUSES

# 合法流转矩阵（07 §1）：active↔paused 人工双向；active/paused→终态人工；终态不可逆
_ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    "active": frozenset({"paused", "done", "abandoned"}),
    "paused": frozenset({"active", "done", "abandoned"}),
    "done": frozenset(),
    "abandoned": frozenset(),
}

# objective 卫生（07 §2.3④）：单行化（换行/控制符→空格）后截 200
# （对齐 EPISODE_ITEM_MAX_CHARS · continuity.py:204）
OBJECTIVE_MAX_CHARS = 200
_CONTROL_CHARS_RE = re.compile(r"[\x00-\x1f\x7f]+")
_WS_RE = re.compile(r"\s+")


class GoalNotFoundError(Exception):
    """goal 不存在或跨租户不可见（REST 映射 404）。"""


class GoalStateTransitionError(Exception):
    """非法状态流转（REST 映射 409）。"""


def sanitize_objective(text: str, *, max_chars: int = OBJECTIVE_MAX_CHARS) -> str:
    """objective 单行化：控制符→空格、折叠空白、截断。空串返回 ""（调用方降级不建行）。"""
    if not isinstance(text, str):
        return ""
    single = _CONTROL_CHARS_RE.sub(" ", text)
    single = _WS_RE.sub(" ", single).strip()
    return single[:max_chars]


def _to_dict(row: OpsGoal) -> dict[str, Any]:
    return {
        "goal_id": str(row.goal_id),
        "tenant_id": row.tenant_id,
        "thread_id": row.thread_id,
        "objective": row.objective,
        "status": row.status,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


async def _find_nonterminal(db: Any, *, tenant_id: str, thread_id: str) -> OpsGoal | None:
    stmt = (
        select(OpsGoal)
        .where(
            OpsGoal.tenant_id == tenant_id,
            OpsGoal.thread_id == thread_id,
            OpsGoal.status.in_(sorted(NONTERMINAL_GOAL_STATUSES)),
        )
        .order_by(OpsGoal.created_at.desc())
        .limit(1)
    )
    return (await db.execute(stmt)).scalars().first()


async def resolve_goal_for_thread(
    *, tenant_id: str, thread_id: str, query: str
) -> dict[str, Any] | None:
    """查非终态 goal；无行则懒创建（objective=query 单行化截 200）。

    best-effort（装配链路纪律）：任何 DB 故障 → 日志带 thread_id + 返回 None，
    绝不阻断请求。竞态：并发懒创建撞唯一约束（T4 索引）→ catch IntegrityError
    重读返回既有行。
    """
    if not tenant_id or not thread_id:
        return None
    try:
        async with AsyncSessionLocal() as db:
            existing = await _find_nonterminal(db, tenant_id=tenant_id, thread_id=thread_id)
            if existing is not None:
                return _to_dict(existing)
            objective = sanitize_objective(query)
            if not objective:
                return None
            row = OpsGoal(
                tenant_id=tenant_id,
                thread_id=thread_id,
                objective=objective,
                status="active",
            )
            db.add(row)
            try:
                await db.commit()
            except IntegrityError:
                # T4 部分唯一索引就位后的并发窗口：另一请求已建行 → 重读返回
                await db.rollback()
                existing = await _find_nonterminal(db, tenant_id=tenant_id, thread_id=thread_id)
                return _to_dict(existing) if existing is not None else None
            await db.refresh(row)
            return _to_dict(row)
    except Exception:
        logger.exception("goal resolve failed thread_id=%s tenant_id=%s", thread_id, tenant_id)
        return None


async def get_goal(*, goal_id: str, tenant_id: str) -> dict[str, Any] | None:
    """按 goal_id+tenant_id 读；跨租户不可见返回 None（REST 映射 404）。best-effort。"""
    if not goal_id or not tenant_id:
        return None
    try:
        async with AsyncSessionLocal() as db:
            row = await db.get(OpsGoal, goal_id)
            if row is None or row.tenant_id != tenant_id:
                return None
            return _to_dict(row)
    except Exception:
        logger.exception("goal get failed goal_id=%s tenant_id=%s", goal_id, tenant_id)
        return None


async def list_goals(*, thread_id: str, tenant_id: str) -> list[dict[str, Any]]:
    """按 thread 列 goal（含终态 · 供 REST 展示历史轨迹）。best-effort → []。"""
    if not thread_id or not tenant_id:
        return []
    try:
        async with AsyncSessionLocal() as db:
            stmt = (
                select(OpsGoal)
                .where(OpsGoal.tenant_id == tenant_id, OpsGoal.thread_id == thread_id)
                .order_by(OpsGoal.created_at.asc())
            )
            rows = (await db.execute(stmt)).scalars().all()
            return [_to_dict(r) for r in rows]
    except Exception:
        logger.exception("goal list failed thread_id=%s tenant_id=%s", thread_id, tenant_id)
        return []


async def find_active_goal(*, tenant_id: str, thread_id: str) -> dict[str, Any] | None:
    """按 thread 查 status=active 的 goal（注入装配只读路径 · **不创建**）。

    仅 active 注入（07 §2.3：paused 目标不应引导新 run）。best-effort：
    任何 DB 故障 → 日志带 thread_id + 返回 None，绝不反噬装配链路。
    """
    if not tenant_id or not thread_id:
        return None
    try:
        async with AsyncSessionLocal() as db:
            stmt = (
                select(OpsGoal)
                .where(
                    OpsGoal.tenant_id == tenant_id,
                    OpsGoal.thread_id == thread_id,
                    OpsGoal.status == "active",
                )
                .order_by(OpsGoal.created_at.desc())
                .limit(1)
            )
            row = (await db.execute(stmt)).scalars().first()
            return _to_dict(row) if row is not None else None
    except Exception:
        logger.exception("goal find_active failed thread_id=%s tenant_id=%s", thread_id, tenant_id)
        return None


async def patch_goal_status(
    *, goal_id: str, tenant_id: str, new_status: str
) -> dict[str, Any]:
    """人工状态流转（REST 面唯一写入口）。**显式抛错不吞**：

    - goal 不存在/跨租户 → GoalNotFoundError（404）
    - 词表外值 / 非法流转 / 终态不可逆 → GoalStateTransitionError（409）
    """
    if new_status not in ALL_GOAL_STATUSES:
        raise GoalStateTransitionError(f"unknown status: {new_status!r}")
    async with AsyncSessionLocal() as db:
        row = await db.get(OpsGoal, goal_id)
        if row is None or row.tenant_id != tenant_id:
            raise GoalNotFoundError(goal_id)
        allowed = _ALLOWED_TRANSITIONS.get(row.status, frozenset())
        if new_status not in allowed:
            raise GoalStateTransitionError(f"{row.status} -> {new_status} not allowed")
        row.status = new_status
        row.updated_at = now_utc()
        await db.commit()
        await db.refresh(row)
        return _to_dict(row)
