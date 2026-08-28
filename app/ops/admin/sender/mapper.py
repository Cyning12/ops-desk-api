"""GitHub JSON → IssueIn / PullRequestIn / SyncPayload。"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.ops.admin.schema import (
    GraphSnapshotIn,
    IssueIn,
    PullRequestIn,
    RepoIn,
    ScanSnapshotIn,
    SyncPayload,
    SyncRunIn,
)
from app.ops.admin.sender.github_client import GitHubClient


def _label_names(raw: Any) -> list[str]:
    names: list[str] = []
    if not isinstance(raw, list):
        return names
    for item in raw:
        if isinstance(item, dict) and item.get("name"):
            names.append(str(item["name"]))
        elif isinstance(item, str) and item:
            names.append(item)
    return names


def _login(raw: Any) -> str | None:
    if isinstance(raw, dict):
        login = raw.get("login")
        return str(login) if login else None
    return None


def _assignee_logins(raw: Any) -> list[str]:
    if not isinstance(raw, list):
        return []
    logins: list[str] = []
    for item in raw:
        login = _login(item)
        if login:
            logins.append(login)
    return logins


def _ts(value: str | None, *, fallback: datetime | None = None) -> datetime:
    parsed = GitHubClient.parse_github_ts(value)
    if parsed is not None:
        return parsed
    if fallback is not None:
        return fallback
    return datetime.now(UTC)


def map_issue(raw: dict[str, Any]) -> IssueIn:
    """GitHub issue JSON → IssueIn；milestone 只留在 raw_payload。"""
    number = int(raw["number"])
    title = (raw.get("title") or "").strip() or f"issue-{number}"
    return IssueIn(
        number=number,
        title=title,
        body=raw.get("body"),
        state=raw.get("state") or "open",
        labels=_label_names(raw.get("labels")),
        author=_login(raw.get("user")),
        assignees=_assignee_logins(raw.get("assignees")),
        html_url=raw.get("html_url"),
        github_issue_id=raw.get("id"),
        created_at=_ts(raw.get("created_at")),
        updated_at=_ts(raw.get("updated_at")),
        closed_at=GitHubClient.parse_github_ts(raw.get("closed_at")),
        raw_payload=raw,
    )


def map_pull_request(raw: dict[str, Any]) -> PullRequestIn:
    """GitHub PR JSON → PullRequestIn；state 保持 open/closed，不改成 merged。

    labels / head_ref / base_ref 只进 raw_payload；ci_status / reviewers 本波可空。
    """
    number = int(raw["number"])
    title = (raw.get("title") or "").strip() or f"pr-{number}"
    return PullRequestIn(
        number=number,
        title=title,
        body=raw.get("body"),
        state=raw.get("state") or "open",
        draft=bool(raw.get("draft", False)),
        ci_status=None,
        author=_login(raw.get("user")),
        reviewers=[],
        html_url=raw.get("html_url"),
        github_pr_id=raw.get("id"),
        created_at=_ts(raw.get("created_at")),
        updated_at=_ts(raw.get("updated_at")),
        merged_at=GitHubClient.parse_github_ts(raw.get("merged_at")),
        closed_at=GitHubClient.parse_github_ts(raw.get("closed_at")),
        raw_payload=raw,
    )


def build_sync_payload(
    *,
    owner: str,
    name: str,
    issues: list[dict[str, Any]],
    pull_requests: list[dict[str, Any]],
    sync_type: str,
    started_at: datetime,
    finished_at: datetime,
    since: datetime | None,
    scan_snapshot: ScanSnapshotIn | None = None,
    graph_snapshot: GraphSnapshotIn | None = None,
) -> SyncPayload:
    """组装完整 SyncPayload；scan/graph 由调用方决定是否传入。"""
    since_iso = since.isoformat() if since is not None else None
    return SyncPayload(
        repo=RepoIn(
            owner=owner,
            name=name,
            full_name=f"{owner}/{name}",
            github_repo_id=None,
        ),
        issues=[map_issue(row) for row in issues],
        pull_requests=[map_pull_request(row) for row in pull_requests],
        sync_run=SyncRunIn(
            sync_type=sync_type,
            status="completed",
            started_at=started_at,
            finished_at=finished_at,
            summary={
                "issues": len(issues),
                "pulls": len(pull_requests),
                "since": since_iso,
            },
        ),
        scan_snapshot=scan_snapshot,
        graph_snapshot=graph_snapshot,
    )
