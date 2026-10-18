"""Issues list endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import OpsIssue, OpsUser
from app.db.session import get_db
from app.ops.deps import CurrentUser

router = APIRouter(prefix="/issues", tags=["issues"])


class IssueOut(BaseModel):
    """Issue list item."""

    id: str
    number: int
    title: str
    state: str
    labels: list[str]
    module_tag: str | None
    updated_at: str


@router.get("")
async def list_issues(
    state: str | None = Query(None),
    label: str | None = Query(None),
    scan_status: str | None = Query(None),
    module: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: OpsUser = CurrentUser,
) -> dict:
    """List issues with filtering and pagination."""
    stmt = select(OpsIssue).order_by(OpsIssue.updated_at.desc())
    count_stmt = select(func.count(OpsIssue.id))

    filters = []
    if state:
        filters.append(OpsIssue.state == state)
    if scan_status:
        filters.append(OpsIssue.scan_status == scan_status)
    if module:
        filters.append(OpsIssue.module_tag == module)
    if label:
        filters.append(OpsIssue.labels.contains([label]))

    if filters:
        stmt = stmt.where(*filters)
        count_stmt = count_stmt.where(*filters)

    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)

    result = await db.execute(stmt)
    items = [
        {
            "id": str(issue.id),
            "number": issue.number,
            "title": issue.title,
            "state": issue.state,
            "labels": issue.labels or [],
            "module_tag": issue.module_tag,
            "updated_at": issue.updated_at.isoformat() if issue.updated_at else None,
        }
        for issue in result.scalars().all()
    ]

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }
