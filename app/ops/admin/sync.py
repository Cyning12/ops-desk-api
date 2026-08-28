"""Admin endpoint for receiving GitHub sync payloads."""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import OpsUser
from app.db.session import get_db
from app.ops.admin.schema import SyncPayload, SyncSummaryOut
from app.ops.admin.service import process_sync_payload
from app.ops.deps import AdminSyncAuth

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin/sync", tags=["admin"])


class MinimalSyncPayload(BaseModel):
    """Minimal payload for backward-compatible health checks."""

    repo_full_name: str
    sync_type: str
    data: dict


@router.post("", status_code=status.HTTP_202_ACCEPTED, response_model=SyncSummaryOut)
async def receive_sync(
    payload: SyncPayload,
    db: AsyncSession = Depends(get_db),
    _user: OpsUser | None = AdminSyncAuth,
) -> SyncSummaryOut:
    """Receive sync payload and persist to PostgreSQL."""
    try:
        summary = await process_sync_payload(db, payload)
        await db.commit()
        return summary
    except Exception as exc:
        await db.rollback()
        logger.exception("Admin sync failed", extra={"repo": payload.repo.full_name})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"stage": "sync", "message": str(exc)},
        ) from exc
