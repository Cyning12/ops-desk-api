"""Overview metrics endpoint."""

from __future__ import annotations

from datetime import datetime, timedelta
from statistics import median

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    OpsIssue,
    OpsPullRequest,
    OpsScanSnapshot,
    OpsSyncRun,
    OpsUser,
)
from app.db.session import get_db
from app.ops.admin.service import _to_naive_utc
from app.ops.deps import CurrentUser
from app.ops.tenant_context import tenant_from_request_state

router = APIRouter(prefix="/overview", tags=["overview"])

# PR cycle/review time are medians over this lookback window.
_CYCLE_REVIEW_WINDOW_DAYS = 90
# Issue throughput and trend cover this many days (trend includes today).
_TREND_WINDOW_DAYS = 30


def _median_days(pairs: list[tuple]) -> dict:
    """Median of (end - start) in days over valid pairs.

    The DB mixes TIMESTAMP WITH/WITHOUT TIME ZONE columns; normalize both
    ends to naive UTC before comparing.
    """
    days = []
    for start, end in pairs:
        if start is None or end is None:
            continue
        start = _to_naive_utc(start)
        end = _to_naive_utc(end)
        if end >= start:
            days.append((end - start).total_seconds() / 86400)
    if not days:
        return {"median_days": None, "sample_size": 0}
    return {"median_days": round(median(days), 2), "sample_size": len(days)}


def _build_trend(issue_counts: dict, pr_counts: dict, today: datetime) -> list[dict]:
    """Daily closed-issue / merged-PR counts for the trend window, zero-filled."""
    start = (today - timedelta(days=_TREND_WINDOW_DAYS - 1)).date()
    trend = []
    for offset in range(_TREND_WINDOW_DAYS):
        day = start + timedelta(days=offset)
        trend.append(
            {
                "date": day.isoformat(),
                "closed_issues": issue_counts.get(day, 0),
                "merged_prs": pr_counts.get(day, 0),
            }
        )
    return trend


@router.get("")
async def get_overview(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: OpsUser = CurrentUser,
) -> dict:
    """Return overview metrics, sync status, scan summary and trend.

    W-fix-2（F13）：issue/PR 派生指标接租户谓词（F4 口径：跨租户归零）；
    sync_run/scan_snapshot 模型无 tenant_id 列，属全局 repo 级状态，不在谓词面。
    """
    tenant_id = tenant_from_request_state(request)
    now = datetime.utcnow()
    cycle_since = now - timedelta(days=_CYCLE_REVIEW_WINDOW_DAYS)
    trend_since = now - timedelta(days=_TREND_WINDOW_DAYS)

    # PR cycle time: created -> merged, merged within the window.
    result = await db.execute(
        select(OpsPullRequest.created_at, OpsPullRequest.merged_at).where(
            OpsPullRequest.tenant_id == tenant_id,
            OpsPullRequest.merged_at.is_not(None),
            OpsPullRequest.merged_at >= cycle_since,
        )
    )
    cycle_time = _median_days(list(result.all()))

    # PR review time: created -> first review, reviewed within the window.
    result = await db.execute(
        select(OpsPullRequest.created_at, OpsPullRequest.first_review_at).where(
            OpsPullRequest.tenant_id == tenant_id,
            OpsPullRequest.first_review_at.is_not(None),
            OpsPullRequest.first_review_at >= cycle_since,
        )
    )
    review_time = _median_days(list(result.all()))

    # Issue throughput: issues closed within the trend window.
    throughput_count = await db.scalar(
        select(func.count(OpsIssue.id)).where(
            OpsIssue.tenant_id == tenant_id,
            OpsIssue.closed_at.is_not(None),
            OpsIssue.closed_at >= trend_since,
        )
    )

    # Trend: per-day closed issues and merged PRs.
    result = await db.execute(
        select(func.date(OpsIssue.closed_at), func.count())
        .where(
            OpsIssue.tenant_id == tenant_id,
            OpsIssue.closed_at.is_not(None),
            OpsIssue.closed_at >= trend_since,
        )
        .group_by(func.date(OpsIssue.closed_at))
    )
    issue_counts = dict(result.all())
    result = await db.execute(
        select(func.date(OpsPullRequest.merged_at), func.count())
        .where(
            OpsPullRequest.tenant_id == tenant_id,
            OpsPullRequest.merged_at.is_not(None),
            OpsPullRequest.merged_at >= trend_since,
        )
        .group_by(func.date(OpsPullRequest.merged_at))
    )
    pr_counts = dict(result.all())
    trend = _build_trend(issue_counts, pr_counts, now)

    # Latest sync run; records read from the GHA summary JSONB.
    sync_run_row = await db.scalar(
        select(OpsSyncRun).order_by(OpsSyncRun.started_at.desc()).limit(1)
    )
    if sync_run_row is None:
        sync_status = "idle"
        sync_run = None
    else:
        sync_status = sync_run_row.status
        summary = sync_run_row.summary or {}
        sync_run = {
            "id": str(sync_run_row.id),
            "started_at": (
                sync_run_row.started_at.isoformat() if sync_run_row.started_at else None
            ),
            "finished_at": (
                sync_run_row.finished_at.isoformat() if sync_run_row.finished_at else None
            ),
            "status": sync_run_row.status,
            "records_issue": summary.get("issues"),
            "records_pr": summary.get("pulls"),
        }

    # Latest scan snapshot.
    scan_row = await db.scalar(
        select(OpsScanSnapshot).order_by(OpsScanSnapshot.created_at.desc()).limit(1)
    )
    scan_snapshot = None
    if scan_row is not None:
        scan_snapshot = {
            "parsed_summary": scan_row.parsed_summary,
            "created_at": scan_row.created_at.isoformat() if scan_row.created_at else None,
        }

    return {
        "cycle_time": cycle_time,
        "review_time": review_time,
        "issue_throughput": {
            "count": throughput_count or 0,
            "period_days": _TREND_WINDOW_DAYS,
        },
        "as_of": now.isoformat() + "Z",
        "sync_status": sync_status,
        "sync_run": sync_run,
        "scan_snapshot": scan_snapshot,
        "trend": trend,
    }
