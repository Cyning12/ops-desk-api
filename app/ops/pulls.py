"""Pull requests list endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import OpsPullRequest, OpsUser
from app.db.session import get_db
from app.ops.deps import CurrentUser
from app.ops.tenant_context import tenant_from_request_state

router = APIRouter(prefix="/pulls", tags=["pulls"])


class PullOut(BaseModel):
    """Pull request list item."""

    id: str
    number: int
    title: str
    state: str
    draft: bool
    ci_status: str | None
    updated_at: str


@router.get("")
async def list_pulls(
    request: Request,
    state: str | None = Query(None),
    ci_status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: OpsUser = CurrentUser,
) -> dict:
    """List pull requests with filtering and pagination.

    W-fix-2（F13）：租户谓词——只读本租户行（F4 口径：跨租户列表得空集；
    ``tenant_id=''`` 历史行从严视同租户外 · 2026-11-02 实扫 ops_pull_requests 0 行）。
    """
    tenant_id = tenant_from_request_state(request)
    stmt = (
        select(OpsPullRequest)
        .where(OpsPullRequest.tenant_id == tenant_id)
        .order_by(OpsPullRequest.updated_at.desc())
    )
    count_stmt = select(func.count(OpsPullRequest.id)).where(
        OpsPullRequest.tenant_id == tenant_id
    )

    filters = []
    if state:
        filters.append(OpsPullRequest.state == state)
    if ci_status:
        filters.append(OpsPullRequest.ci_status == ci_status)

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
            "id": str(pr.id),
            "number": pr.number,
            "title": pr.title,
            "state": pr.state,
            "draft": pr.draft,
            "ci_status": pr.ci_status,
            "updated_at": pr.updated_at.isoformat() if pr.updated_at else None,
        }
        for pr in result.scalars().all()
    ]

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }
