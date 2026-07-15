"""Issues list endpoint."""

from fastapi import APIRouter, Query
from pydantic import BaseModel

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
) -> dict:
    """List issues with filtering and pagination."""
    # TODO: query ops_issues with filters
    return {
        "items": [],
        "total": 0,
        "page": page,
        "page_size": page_size,
    }
