"""Schedule REST 面（P3-T2 · issue #23 · 契约真源 15-p3-contracts §1）。

四端点（§1.1）：

- POST   /api/ops/schedules            创建（201 · {"ok":true,"data":{"schedule":{...}}}）
- GET    /api/ops/schedules            列表（?thread_id=&status= · 谓词 tenant+user · v1 不分页）
- GET    /api/ops/schedules/{id}       详情 + recent_fires（最近 10 条 planned_fire_at 倒序）
- PATCH  /api/ops/schedules/{id}       状态机 + 改排期（全可选至少一项 · cancelled 终态）

错误映射纪律（§1.1 错误壳 {"detail":...} · 422 文案逐字用词表）：

- 未登录 → 401（CurrentUser 前置）；
- schedule 不存在 / 跨 tenant / 跨 user → 404（存在性不外泄 · 防探测 · 不用 403）；
- 词表外 / 校验失败 / 配额超限 / 终态再改 → 422（store 抛 ScheduleValidationError
  携带 §1.8 逐字文案 · 前端不做二次包装）；
- 词表校验刻意不放 pydantic Literal（其默认 422 detail 为列表结构且文案不可控），
  一律进 store 用词表校验。

OPS_SCHEDULE_ENABLED 只管 worker（T3），不闸本 REST 面（15 §7.1）。
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict

from app.db.models import OpsUser
from app.ops.deps import CurrentUser
from app.ops.tenant_context import (
    TENANT_A,
    TENANT_HEADER,
    resolve_header_against_session,
)

from .store import (
    DEFAULT_TIMEZONE,
    ScheduleNotFoundError,
    ScheduleValidationError,
    create_schedule,
    get_schedule_with_fires,
    list_schedules,
    patch_schedule,
)

router = APIRouter(prefix="/schedules", tags=["schedules"])


class ScheduleCreateRequest(BaseModel):
    """创建请求体（15 §1.3 · additionalProperties:false → extra="forbid"）。"""

    model_config = ConfigDict(extra="forbid")

    thread_id: str
    name: str
    instruction: str
    schedule_kind: str
    run_at: datetime | None = None
    interval_seconds: int | None = None
    time_of_day: str | None = None
    timezone: str = DEFAULT_TIMEZONE
    max_fires: int | None = None


class SchedulePatchRequest(BaseModel):
    """PATCH 请求体（15 §1.6 · 全可选但至少一项 · max_fires 显式 null = 清除）。"""

    model_config = ConfigDict(extra="forbid")

    status: str | None = None
    name: str | None = None
    instruction: str | None = None
    run_at: datetime | None = None
    interval_seconds: int | None = None
    time_of_day: str | None = None
    timezone: str | None = None
    max_fires: int | None = None


def _resolve_request_tenant(request: Request) -> str:
    """F1=C：session 真源；头不一致 → 403；未知租户 → 422（goals/router.py 先例）。"""
    session_tenant = getattr(request.state, "ops_tenant_id", TENANT_A)
    try:
        return resolve_header_against_session(session_tenant, request.headers.get(TENANT_HEADER))
    except ValueError as exc:
        detail = str(exc)
        code = 403 if "mismatch" in detail else 422
        raise HTTPException(status_code=code, detail=detail) from exc


@router.post("", status_code=201)
async def create_schedule_endpoint(
    body: ScheduleCreateRequest,
    request: Request,
    user: OpsUser = CurrentUser,
) -> dict:
    """创建定时任务（§1.3：next_fire_at 即算 · status=active · fire_count=0）。"""
    tenant_id = _resolve_request_tenant(request)
    try:
        schedule = await create_schedule(
            tenant_id=tenant_id,
            user_id=user.id,
            thread_id=body.thread_id,
            name=body.name,
            instruction=body.instruction,
            schedule_kind=body.schedule_kind,
            run_at=body.run_at,
            interval_seconds=body.interval_seconds,
            time_of_day=body.time_of_day,
            tz_name=body.timezone,
            max_fires=body.max_fires,
        )
    except ScheduleValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"ok": True, "data": {"schedule": schedule}}


@router.get("")
async def list_schedules_endpoint(
    request: Request,
    thread_id: str | None = Query(default=None, min_length=1),
    status: str | None = Query(default=None),
    user: OpsUser = CurrentUser,
) -> dict:
    """当前用户 schedule 列表（§1.4：谓词 tenant+user · v1 不分页）。"""
    tenant_id = _resolve_request_tenant(request)
    try:
        schedules = await list_schedules(
            tenant_id=tenant_id,
            user_id=user.id,
            thread_id=thread_id,
            status=status,
        )
    except ScheduleValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"ok": True, "data": {"schedules": schedules}}


@router.get("/{schedule_id}")
async def get_schedule_endpoint(
    schedule_id: str,
    request: Request,
    user: OpsUser = CurrentUser,
) -> dict:
    """单条详情 + recent_fires（§1.5 · 404 不泄露存在性）。"""
    tenant_id = _resolve_request_tenant(request)
    try:
        payload = await get_schedule_with_fires(
            schedule_id=schedule_id,
            tenant_id=tenant_id,
            user_id=user.id,
        )
    except ScheduleNotFoundError as exc:
        raise HTTPException(status_code=404, detail="schedule not found") from exc
    return {"ok": True, "data": payload}


@router.patch("/{schedule_id}")
async def patch_schedule_endpoint(
    schedule_id: str,
    body: SchedulePatchRequest,
    request: Request,
    user: OpsUser = CurrentUser,
) -> dict:
    """状态机 + 改排期（§1.6：全可选至少一项 · cancelled 终态不可逆）。"""
    if not body.model_fields_set:
        raise HTTPException(status_code=422, detail="PATCH 请求体至少要包含一个字段")
    tenant_id = _resolve_request_tenant(request)
    clear_max_fires = "max_fires" in body.model_fields_set and body.max_fires is None
    try:
        schedule = await patch_schedule(
            schedule_id=schedule_id,
            tenant_id=tenant_id,
            user_id=user.id,
            status=body.status,
            name=body.name,
            instruction=body.instruction,
            run_at=body.run_at,
            interval_seconds=body.interval_seconds,
            time_of_day=body.time_of_day,
            tz_name=body.timezone,
            max_fires=body.max_fires,
            clear_max_fires=clear_max_fires,
        )
    except ScheduleNotFoundError as exc:
        raise HTTPException(status_code=404, detail="schedule not found") from exc
    except ScheduleValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"ok": True, "data": {"schedule": schedule}}
