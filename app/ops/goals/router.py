"""Goal REST 面（P1-T2 · issue #390 · 设计真源 07-p1-goal-design §4/§5）。

人工目标管理唯一 HTTP 入口（O-1 终裁：paused 仅人工 PATCH 复活，无自动复活）。
错误映射纪律：

- 词表外 status → 422（pydantic Literal 前置校验，不进 store）；
- goal 不存在 / 跨租户 → 404（store 查询带 tenant_id 谓词，存在性不外泄，
  防跨租户探测——不用 403）；
- 非法流转 / 终态不可逆 → 409；
- 未登录 → 401（CurrentUser 前置）。
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel

from app.db.models import OpsUser
from app.ops.deps import CurrentUser
from app.ops.tenant_context import (
    TENANT_A,
    TENANT_HEADER,
    resolve_header_against_session,
)

from .store import (
    GoalNotFoundError,
    GoalStateTransitionError,
    list_goals,
    patch_goal_status,
)

router = APIRouter(prefix="/goals", tags=["goals"])

GoalStatus = Literal["active", "paused", "done", "abandoned"]


class GoalPatchRequest(BaseModel):
    """人工状态流转请求体（07 §1 矩阵由 store 执行）。"""

    status: GoalStatus


def _resolve_request_tenant(request: Request) -> str:
    """F1=C：session 真源；头不一致 → 403；未知租户 → 422（lg_rag/router.py:376-384 先例）。"""
    session_tenant = getattr(request.state, "ops_tenant_id", TENANT_A)
    try:
        return resolve_header_against_session(session_tenant, request.headers.get(TENANT_HEADER))
    except ValueError as exc:
        detail = str(exc)
        code = 403 if "mismatch" in detail else 422
        raise HTTPException(status_code=code, detail=detail) from exc


@router.get("")
async def list_thread_goals(
    request: Request,
    thread_id: str = Query(..., min_length=1),
    user: OpsUser = CurrentUser,
) -> dict:
    """按 thread 列 goal（含终态 · 供前端目标面板展示历史轨迹）。"""
    tenant_id = _resolve_request_tenant(request)
    goals = await list_goals(thread_id=thread_id, tenant_id=tenant_id)
    return {"goals": goals}


@router.patch("/{goal_id}")
async def patch_goal(
    goal_id: str,
    body: GoalPatchRequest,
    request: Request,
    user: OpsUser = CurrentUser,
) -> dict:
    """人工状态流转（O-1：paused→active 唯一复活通道）。"""
    tenant_id = _resolve_request_tenant(request)
    try:
        return await patch_goal_status(
            goal_id=goal_id, tenant_id=tenant_id, new_status=body.status
        )
    except GoalNotFoundError as exc:
        raise HTTPException(status_code=404, detail="goal not found") from exc
    except GoalStateTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
