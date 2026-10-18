"""Graph snapshot endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import OpsGraphSnapshot, OpsUser
from app.db.session import get_db
from app.ops.deps import CurrentUser

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("")
async def get_graph(
    db: AsyncSession = Depends(get_db),
    user: OpsUser = CurrentUser,
) -> dict:
    """Return latest graph snapshot and module × issue matrix."""
    result = await db.execute(
        select(OpsGraphSnapshot).order_by(OpsGraphSnapshot.created_at.desc()).limit(1)
    )
    snapshot = result.scalar_one_or_none()

    if snapshot is None:
        return {
            "snapshot": None,
            "module_matrix": None,
            "repo_id": None,
            "created_at": None,
        }

    return {
        "snapshot": snapshot.payload,
        "module_matrix": snapshot.module_matrix,
        "repo_id": str(snapshot.repo_id),
        "created_at": snapshot.created_at.isoformat() if snapshot.created_at else None,
    }
