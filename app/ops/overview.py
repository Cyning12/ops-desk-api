"""Overview metrics endpoint."""
from fastapi import APIRouter

router = APIRouter(prefix="/overview", tags=["overview"])


@router.get("")
async def get_overview() -> dict:
    """Return overview metrics, sync status, scan summary and trend."""
    # TODO: query ops_repos, ops_issues, ops_pull_requests, ops_sync_runs, ops_scan_snapshots
    return {
        "pr_cycle_time_days": None,
        "review_time_days": None,
        "issue_throughput": None,
        "sync_status": "idle",
        "scan_summary": None,
        "trend": [],
    }
