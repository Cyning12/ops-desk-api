"""Pull requests list endpoint."""

from fastapi import APIRouter, Query
from pydantic import BaseModel

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
    state: str | None = Query(None),
    ci_status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> dict:
    """List pull requests with filtering and pagination."""
    # TODO: query ops_pull_requests with filters
    return {
        "items": [],
        "total": 0,
        "page": page,
        "page_size": page_size,
    }
