"""Admin endpoint：ops_memory_facts 按 (tenant,user) 物理删除（合规删除权）。

**首个 admin 面不可逆写端点**——双闸门 + 审计断言为本端点核心否决面：

- 鉴权：`AdminSyncAuth`（Bearer `OPS_ADMIN_SYNC_TOKEN` 或 cookie maintainer ·
  零新鉴权面 · 未授权一律 401/403 且表行零变化）。
- ① **默认干跑**：`dry_run` 缺省/显式 true → 只读计数报告**零写**，响应 echo
  `dry_run` 标志（盲发只读面）。
- ② **实删须范围确认**：`dry_run=false` 时 `expected_count` 必填（缺 → 400 零删除），
  与同谓词当前匹配计数**不等 → 409 零删除**（调用方重新干跑）；计数等 → 200 实删
  且 `deleted == expected_count`。「删多少」是显式对账不是盲发。
- 审计：service 层 `logger.info` 记动作不记内容（无 key/value · 无 PII 泄漏面）。
- 500 不静默：异常 rollback + `logger.exception` + HTTPException（admin/sync.py
  :35-45 先例同形）。

残余风险（承 SPEC §7 如实承认）：expected_count 只锁数量不锁主体（计数碰巧相等
的错目标不可防 · 管理面人工纪律兜底：先干跑核对计数再实删）；同计数内容替换
竞态不可区分（管理面低频操作可接受）。
"""

from __future__ import annotations

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import OpsUser
from app.db.session import get_db
from app.ops.deps import AdminSyncAuth
from app.ops.memory.service import PurgeReport, purge_by_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin/memory", tags=["admin"])


class MemoryPurgePayload(BaseModel):
    """purge 请求体：tenant/user 显式传入但只在 AdminSyncAuth 通过后生效
    （admin/capability.py「替别人看一眼」先例同形态）。"""

    tenant_id: str
    user_id: str
    #: 默认干跑（盲发只读）；实删必须显式 false + expected_count 双闸门
    dry_run: bool = True
    #: 实删必填：与当前匹配计数一致才执行（先干跑取计数再提交）
    expected_count: int | None = Field(default=None, ge=0)


class MemoryPurgeResponse(BaseModel):
    """PurgeReport JSON 面（echo dry_run 标志 · by_status 分桶计数）。"""

    dry_run: bool
    scanned: int
    deleted: int
    by_status: dict[str, int]
    elapsed_s: float
    recorded_at: datetime


def _to_response(report: PurgeReport) -> MemoryPurgeResponse:
    return MemoryPurgeResponse(
        dry_run=report.dry_run,
        scanned=report.scanned,
        deleted=report.deleted,
        by_status=report.by_status,
        elapsed_s=report.elapsed_s,
        recorded_at=report.recorded_at,
    )


@router.post("/purge", response_model=MemoryPurgeResponse)
async def purge_memory(
    payload: MemoryPurgePayload,
    db: AsyncSession = Depends(get_db),
    _user: OpsUser | None = AdminSyncAuth,
) -> MemoryPurgeResponse:
    """按 (tenant,user) 物理删除：默认干跑 + expected_count 双闸门。"""
    tenant_id = payload.tenant_id.strip()
    user_id = payload.user_id.strip()
    if not tenant_id or not user_id:
        # strip 后空 = 400（service.py write_fact :110-115 strip 先例对齐）
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="tenant_id/user_id 空白（strip 后为空）",
        )
    if not payload.dry_run and payload.expected_count is None:
        # 双闸门②前置：缺 expected_count → 400 零删除（不触库）
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="dry_run=false 必须携带 expected_count（先干跑取计数再实删）",
        )
    try:
        if payload.dry_run:
            report = await purge_by_user(tenant_id, user_id, dry_run=True, session=db)
            return _to_response(report)
        # 双闸门②：同谓词当前计数 != expected_count → 409 零删除（调用方重新干跑）
        probe = await purge_by_user(tenant_id, user_id, dry_run=True, session=db)
        if probe.scanned != payload.expected_count:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "reason": "count_mismatch",
                    "expected_count": payload.expected_count,
                    "current_count": probe.scanned,
                },
            )
        report = await purge_by_user(tenant_id, user_id, dry_run=False, session=db)
        await db.commit()
        return _to_response(report)
    except HTTPException:
        raise
    except Exception as exc:
        # 500 不静默：rollback + logger.exception + HTTPException（admin/sync.py 先例）
        await db.rollback()
        logger.exception("Admin memory purge failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"stage": "memory_purge", "message": str(exc)},
        ) from exc
