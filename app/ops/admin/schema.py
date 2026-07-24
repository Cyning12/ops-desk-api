"""Schemas for the admin sync endpoint."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RepoIn(BaseModel):
    """Repository metadata used to upsert ops_repos."""

    model_config = ConfigDict(extra="ignore")

    owner: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    full_name: str = Field(..., min_length=1)
    github_repo_id: int | None = None
    default_branch: str | None = None
    description: str | None = None


class IssueIn(BaseModel):
    """Single issue used to upsert ops_issues."""

    model_config = ConfigDict(extra="ignore")

    number: int = Field(..., ge=1)
    title: str = Field(..., min_length=1)
    body: str | None = None
    state: str = Field(default="open")
    labels: list[str] = Field(default_factory=list)
    scan_status: str | None = None
    module_tag: str | None = None
    author: str | None = None
    assignees: list[str] = Field(default_factory=list)
    html_url: str | None = None
    github_issue_id: int | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    closed_at: datetime | None = None
    raw_payload: dict | None = None


class PullRequestIn(BaseModel):
    """Single pull request used to upsert ops_pull_requests."""

    model_config = ConfigDict(extra="ignore")

    number: int = Field(..., ge=1)
    title: str = Field(..., min_length=1)
    body: str | None = None
    state: str = Field(default="open")
    draft: bool = False
    ci_status: str | None = None
    author: str | None = None
    reviewers: list[str] = Field(default_factory=list)
    html_url: str | None = None
    github_pr_id: int | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    merged_at: datetime | None = None
    closed_at: datetime | None = None
    raw_payload: dict | None = None


class SyncRunIn(BaseModel):
    """Sync execution record inserted into ops_sync_runs."""

    model_config = ConfigDict(extra="ignore")

    sync_type: str = Field(..., min_length=1)
    status: str = Field(default="completed")
    started_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: datetime | None = None
    summary: dict | None = None
    error_message: str | None = None


class ScanSnapshotIn(BaseModel):
    """Optional scan snapshot inserted into ops_scan_snapshots."""

    model_config = ConfigDict(extra="ignore")

    parsed_summary: dict = Field(default_factory=dict)
    raw_markdown: str | None = None


class GraphSnapshotIn(BaseModel):
    """Optional graph snapshot inserted into ops_graph_snapshots."""

    model_config = ConfigDict(extra="ignore")

    payload: dict = Field(default_factory=dict)
    module_matrix: dict | None = None


class SyncPayload(BaseModel):
    """Top-level payload received from GitHub Actions."""

    repo: RepoIn
    issues: list[IssueIn] = Field(default_factory=list)
    pull_requests: list[PullRequestIn] = Field(default_factory=list)
    sync_run: SyncRunIn
    scan_snapshot: ScanSnapshotIn | None = None
    graph_snapshot: GraphSnapshotIn | None = None


class SyncSummaryOut(BaseModel):
    """Response body returned from POST /api/ops/admin/sync."""

    ok: bool
    repo_id: str
    repos_created: int
    repos_updated: int
    issues_created: int
    issues_updated: int
    pulls_created: int
    pulls_updated: int
    sync_runs: int
    scan_snapshots: int
    graph_snapshots: int
