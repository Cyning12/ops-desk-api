"""HITL 对外端点。

| 端点 | 谁调 | 鉴权 |
|---|---|---|
| ``GET /api/ops/hitl/requests`` | OA / 审批端拉待办 | HMAC 签名 |
| ``GET /api/ops/hitl/requests/{id}`` | 运维 / 前端 | 管理员 |
| ``POST /api/ops/hitl/callback`` | OA 回调审批结果 | HMAC 签名 |
| ``POST /api/ops/hitl/requests/{id}/resume`` | 运维 / 前端 | 管理员 |

**为什么"接收审批结果"要单独做成一个接口，而不是轮询**：
审批是**外部系统**的行为，它发生时本进程可能已经不在同一轮执行里了。
回调让"批准"这件事成为一个**有凭据的事件**（落库 + 签名），
而不是"某次轮询恰好看到了状态变了"。
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any

from fastapi import APIRouter, Body, Header, HTTPException, Query, Request, status

from app.db.models import OpsUser
from app.ops.deps import AdminSyncAuth
from app.ops.hitl import get_hitl_store, new_request_id
from app.ops.hitl.persistence import describe_hitl_persistence
from app.ops.hitl.signature import (
    HEADER_NONCE,
    HEADER_SIGNATURE,
    HEADER_TIMESTAMP,
    SignatureError,
    secret_configured,
    verify,
)
from app.ops.hitl.store import (
    STATUS_APPROVED,
    STATUS_PENDING,
    STATUS_REJECTED,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/hitl", tags=["hitl"])


def _require_signed(request: Request, body: bytes) -> None:
    """外部系统调用的两个端点共用：签名不通过直接 401。"""
    try:
        verify(body=body, headers=request.headers)
    except SignatureError as exc:
        logger.warning("hitl 回调鉴权失败：%s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        ) from exc


@router.get("/runtime")
async def runtime(_user: OpsUser | None = AdminSyncAuth) -> dict[str, Any]:
    """**审批申请到底落不落库**——不落库时一切照常运行、只是人永远等不到。"""
    info = describe_hitl_persistence()
    info["callback_secret_configured"] = secret_configured()
    return info


@router.get("/requests")
async def list_requests(
    request: Request,
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    x_ops_signature: str | None = Header(default=None, alias=HEADER_SIGNATURE),
    x_ops_timestamp: str | None = Header(default=None, alias=HEADER_TIMESTAMP),
    x_ops_nonce: str | None = Header(default=None, alias=HEADER_NONCE),
) -> dict[str, Any]:
    """拉审批申请（OA / 审批端）。``status=pending`` 即"待我批的"。"""
    _require_signed(request, b"")
    rows = await get_hitl_store().alist(status=status_filter, limit=limit)
    return {"items": rows, "count": len(rows)}


@router.get("/requests/{request_id}")
async def get_request(
    request_id: str, _user: OpsUser | None = AdminSyncAuth
) -> dict[str, Any]:
    row = await get_hitl_store().aget(request_id)
    if row is None:
        raise HTTPException(status_code=404, detail="申请不存在")
    return row


@router.post("/callback")
async def callback(
    request: Request,
    payload: dict[str, Any] = Body(...),
) -> dict[str, Any]:
    """接收 OA 的审批结果。

    请求体里带**关联标识**（``request_id`` / ``thread_id`` / ``run_id`` /
    ``checkpoint_id``），它们指明"这次批准的是哪一次 run"；
    **鉴权靠签名头**，不靠这些标识——标识是明文可读的，密钥不是。
    """
    raw = await request.body()
    _require_signed(request, raw)

    request_id = str(payload.get("request_id") or "").strip()
    decision = str(payload.get("decision") or "").strip().lower()
    if not request_id:
        raise HTTPException(status_code=400, detail="缺少 request_id")
    if decision not in (STATUS_APPROVED, STATUS_REJECTED):
        raise HTTPException(
            status_code=400,
            detail=f"decision 必须是 {STATUS_APPROVED} / {STATUS_REJECTED}",
        )

    row = await get_hitl_store().adecide(
        request_id,
        decision=decision,
        by=str(payload.get("decision_by") or payload.get("approver") or "oa"),
        note=str(payload.get("note") or ""),
    )
    if row is None:
        # 要么是 id 不存在，要么已经决过了 —— 后者必须**区分开**，
        # 否则"重复回调"会被当成"申请丢了"
        existing = await get_hitl_store().aget(request_id)
        if existing is None:
            raise HTTPException(status_code=404, detail="申请不存在")
        raise HTTPException(
            status_code=409,
            detail=f"申请已是 {existing.get('status')}，不接受重复决定",
        )
    return {"ok": True, "request": row}


@router.post("/requests/{request_id}/resume")
async def resume_request(
    request_id: str, _user: OpsUser | None = AdminSyncAuth
) -> dict[str, Any]:
    """批准后**恢复**执行：把被锁的那一步从不可变前缀里摘出来。

    审批通过的**唯一**效果就是"授权改历史"——它不会自动帮你改，
    也不会自动继续跑（继续跑要显式调这个端点，且要人来调）。
    """
    row = await get_hitl_store().aget(request_id)
    if row is None:
        raise HTTPException(status_code=404, detail="申请不存在")
    if row.get("status") != STATUS_APPROVED:
        raise HTTPException(
            status_code=409,
            detail=f"申请状态为 {row.get('status')}，只有 approved 才能恢复",
        )
    unlock = str(row.get("unlock_subtask_id") or "").strip()
    if not unlock:
        raise HTTPException(status_code=409, detail="申请里没有待解锁的步骤")
    # 恢复 = 新开一个 run，前缀**排除**被解锁的那一步 ⇒ 可恢复点回退到它
    return {
        "ok": True,
        "resume_run_id": f"{row.get('run_id') or 'run'}-resume-{uuid.uuid4().hex[:8]}",
        "thread_id": row.get("thread_id"),
        "checkpoint_id": row.get("checkpoint_id"),
        "unlock_subtask_id": unlock,
        # 可恢复点**回退**到被解锁的那一步：它不再是不可变前缀
        "recoverable_point_subtask_id": unlock,
        "ts": time.time(),
    }


@router.post("/requests")
async def create_request_manual(
    payload: dict[str, Any] = Body(...),
    _user: OpsUser | None = AdminSyncAuth,
) -> dict[str, Any]:
    """手工登记一条审批申请（运维补录 / 联调用）。

    正常路径是编排层自动落库；这个端点只为"人需要补一条"存在。
    """
    request = {
        "id": str(payload.get("id") or new_request_id()),
        "run_id": str(payload.get("run_id") or ""),
        "thread_id": str(payload.get("thread_id") or ""),
        "checkpoint_id": payload.get("checkpoint_id"),
        "tenant_id": str(payload.get("tenant_id") or ""),
        "subtask_id": str(payload.get("subtask_id") or ""),
        "blocked_by": str(payload.get("blocked_by") or "prefix_touch_required"),
        "unlock_subtask_id": str(payload.get("unlock_subtask_id") or ""),
        "reason": str(payload.get("reason") or ""),
        "detail": str(payload.get("detail") or ""),
        "payload": payload.get("payload") or {},
        "status": STATUS_PENDING,
        "created_at": time.time(),
    }
    created = await get_hitl_store().acreate(request)
    return {"ok": True, "request": created}

