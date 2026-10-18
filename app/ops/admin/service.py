"""Admin sync business logic."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    OpsGraphSnapshot,
    OpsIssue,
    OpsPullRequest,
    OpsRepo,
    OpsScanSnapshot,
    OpsSyncRun,
)
from app.ops.admin.schema import SyncPayload, SyncSummaryOut


def _to_naive_utc(value: datetime) -> datetime:
    """Convert an aware datetime to a naive UTC datetime."""
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)  # noqa: UP017


def _normalize_datetimes(obj: dict) -> dict:
    """Recursively convert all aware datetimes in a dict to naive UTC."""
    result = {}
    for key, value in obj.items():
        if isinstance(value, datetime):
            result[key] = _to_naive_utc(value)
        elif isinstance(value, dict):
            result[key] = _normalize_datetimes(value)
        elif isinstance(value, list):
            result[key] = [
                _normalize_datetimes(item)
                if isinstance(item, dict)
                else _to_naive_utc(item)
                if isinstance(item, datetime)
                else item
                for item in value
            ]
        else:
            result[key] = value
    return result


async def process_sync_payload(
    db: AsyncSession,
    payload: SyncPayload,
) -> SyncSummaryOut:
    """Upsert repo/issues/PRs and insert sync_run/snapshots from a GHA payload.

    All operations happen inside the caller-provided session; the caller is
    responsible for commit/rollback.
    """
    summary = {
        "repos_created": 0,
        "repos_updated": 0,
        "issues_created": 0,
        "issues_updated": 0,
        "pulls_created": 0,
        "pulls_updated": 0,
        "sync_runs": 0,
        "scan_snapshots": 0,
        "graph_snapshots": 0,
    }

    # Upsert repo by full_name first, then by github_repo_id if provided.
    result = await db.execute(select(OpsRepo).where(OpsRepo.full_name == payload.repo.full_name))
    repo = result.scalar_one_or_none()
    if repo is None and payload.repo.github_repo_id is not None:
        result = await db.execute(
            select(OpsRepo).where(OpsRepo.github_repo_id == payload.repo.github_repo_id)
        )
        repo = result.scalar_one_or_none()
    repo_data = _normalize_datetimes(payload.repo.model_dump())
    if repo is None:
        repo = OpsRepo(**repo_data)
        db.add(repo)
        summary["repos_created"] = 1
    else:
        for key, value in repo_data.items():
            setattr(repo, key, value)
        summary["repos_updated"] = 1

    await db.flush()
    repo_id = str(repo.id)

    # Upsert issues.
    for issue_in in payload.issues:
        result = await db.execute(
            select(OpsIssue).where(
                OpsIssue.repo_id == repo_id,
                OpsIssue.number == issue_in.number,
            )
        )
        issue = result.scalar_one_or_none()
        issue_data = _normalize_datetimes(issue_in.model_dump())
        if issue is None:
            issue = OpsIssue(repo_id=repo_id, **issue_data)
            db.add(issue)
            summary["issues_created"] += 1
        else:
            for key, value in issue_data.items():
                setattr(issue, key, value)
            summary["issues_updated"] += 1

    # Upsert pull requests.
    for pr_in in payload.pull_requests:
        result = await db.execute(
            select(OpsPullRequest).where(
                OpsPullRequest.repo_id == repo_id,
                OpsPullRequest.number == pr_in.number,
            )
        )
        pr = result.scalar_one_or_none()
        pr_data = _normalize_datetimes(pr_in.model_dump())
        if pr is None:
            pr = OpsPullRequest(repo_id=repo_id, **pr_data)
            db.add(pr)
            summary["pulls_created"] += 1
        else:
            for key, value in pr_data.items():
                setattr(pr, key, value)
            summary["pulls_updated"] += 1

    # Insert sync run.
    sync_run_data = _normalize_datetimes(payload.sync_run.model_dump())
    sync_run = OpsSyncRun(repo_id=repo_id, **sync_run_data)
    db.add(sync_run)
    await db.flush()
    summary["sync_runs"] = 1

    # Insert optional snapshots.
    if payload.scan_snapshot is not None:
        scan_data = _normalize_datetimes(payload.scan_snapshot.model_dump())
        scan = OpsScanSnapshot(
            repo_id=repo_id,
            scan_run_id=sync_run.id,
            **scan_data,
        )
        db.add(scan)
        summary["scan_snapshots"] = 1

    if payload.graph_snapshot is not None:
        graph_data = _normalize_datetimes(payload.graph_snapshot.model_dump())
        graph = OpsGraphSnapshot(
            repo_id=repo_id,
            graph_run_id=sync_run.id,
            **graph_data,
        )
        db.add(graph)
        summary["graph_snapshots"] = 1

    return SyncSummaryOut(repo_id=repo_id, ok=True, **summary)
