"""Admin endpoint for receiving GitHub sync payloads."""
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.ops.deps import MaintainerUser

router = APIRouter(prefix="/admin/sync", tags=["admin"])


class SyncPayload(BaseModel):
    """Generic sync payload from GitHub Actions."""

    repo_full_name: str
    sync_type: str
    data: dict


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def receive_sync(
    payload: SyncPayload,
    db: AsyncSession = Depends(get_db),
    user=MaintainerUser,
) -> dict:
    """Receive sync payload and persist to PostgreSQL."""
    # TODO: upsert repo/issues/pulls/sync_runs/snapshots
    return {"ok": True, "sync_type": payload.sync_type}
