"""Sender 编排：拉取 GitHub → 组装 SyncPayload → POST（不写库）。"""

from __future__ import annotations

import os
import sys
from datetime import UTC, datetime, timedelta
from typing import TextIO

import httpx

from app.ops.admin.sender.github_client import GitHubClient, GitHubSyncError
from app.ops.admin.sender.mapper import build_sync_payload
from app.ops.admin.sender.post import payload_body_bytes, post_sync_payload
from app.ops.admin.sender.snapshots import load_graph_snapshot, load_scan_snapshot

INCREMENTAL_OVERLAP = timedelta(hours=48)


def _require_env(name: str) -> str:
    value = (os.getenv(name) or "").strip()
    if not value:
        raise GitHubSyncError(f"缺少 {name}", fail_fast=True)
    return value


def run_sync(
    *,
    sync_type: str,
    github: GitHubClient | None = None,
    http_client: httpx.Client | None = None,
    scan_path: str | None = None,
    graph_path: str | None = None,
    api_base_url: str | None = None,
    admin_token: str | None = None,
    err: TextIO | None = None,
) -> int:
    """增量 since=utcnow-48h；full since=None。非 2xx 返回非 0。"""
    log = err or sys.stderr
    started_at = datetime.now(UTC)
    since = started_at - INCREMENTAL_OVERLAP if sync_type == "incremental" else None

    try:
        token = admin_token if admin_token is not None else _require_env("OPS_ADMIN_SYNC_TOKEN")
        base_url = api_base_url if api_base_url is not None else _require_env("OPS_API_BASE_URL")
        gh = github or GitHubClient.from_env(http_client=http_client)

        issues = gh.fetch_issues(since)
        pulls = gh.fetch_pull_requests(since)

        scan = load_scan_snapshot(
            scan_path if scan_path is not None else os.getenv("OPS_SCAN_INDEX_PATH")
        )
        graph = load_graph_snapshot(
            graph_path if graph_path is not None else os.getenv("OPS_GRAPH_JSON_PATH")
        )

        finished_at = datetime.now(UTC)
        payload = build_sync_payload(
            owner=gh.owner,
            name=gh.name,
            issues=issues,
            pull_requests=pulls,
            sync_type=sync_type,
            started_at=started_at,
            finished_at=finished_at,
            since=since,
            scan_snapshot=scan,
            graph_snapshot=graph,
        )
        body_len = len(payload_body_bytes(payload))
        print(
            f"POST sync bytes={body_len} issues={len(issues)} prs={len(pulls)}",
            file=log,
        )
        resp = post_sync_payload(
            base_url=base_url,
            token=token,
            payload=payload,
            http_client=http_client,
        )
    except (GitHubSyncError, OSError, ValueError, httpx.HTTPError) as exc:
        print(f"sync failed: {exc}", file=log)
        return 1

    if not (200 <= resp.status_code < 300):
        body = (resp.text or "")[:500]
        print(f"POST sync HTTP {resp.status_code}: {body}", file=log)
        return 1

    print(
        f"sync ok status={resp.status_code} type={sync_type} "
        f"issues={len(issues)} prs={len(pulls)} "
        f"scan={'yes' if scan is not None else 'skip'} "
        f"graph={'yes' if graph is not None else 'skip'}",
        file=log,
    )
    return 0
