"""Admin sync sender：映射、GitHub mock、POST mock（无外网）。"""

from __future__ import annotations

import io
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
import pytest

from app.ops.admin.sender.github_client import GitHubClient, GitHubSyncError
from app.ops.admin.sender.mapper import build_sync_payload, map_issue, map_pull_request
from app.ops.admin.sender.post import DEFAULT_POST_TIMEOUT, post_sync_payload
from app.ops.admin.sender.runner import run_sync
from app.ops.admin.sender.snapshots import load_graph_snapshot, load_scan_snapshot

ISSUE_FIXTURE: dict[str, Any] = {
    "id": 42,
    "number": 7,
    "title": "Fix crash",
    "body": "details",
    "state": "open",
    "labels": [{"name": "bug"}, {"name": "ios"}],
    "user": {"login": "alice"},
    "assignees": [{"login": "bob"}, {"login": "carol"}],
    "html_url": "https://github.com/MoonshotAI/kimi-code/issues/7",
    "created_at": "2026-08-01T00:00:00Z",
    "updated_at": "2026-08-02T00:00:00Z",
    "closed_at": None,
    "milestone": {"title": "v1"},
}

PR_FIXTURE: dict[str, Any] = {
    "id": 99,
    "number": 8,
    "title": "Add feature",
    "body": "pr body",
    "state": "closed",
    "draft": False,
    "merged_at": "2026-08-03T00:00:00Z",
    "user": {"login": "dave"},
    "html_url": "https://github.com/MoonshotAI/kimi-code/pull/8",
    "created_at": "2026-08-01T00:00:00Z",
    "updated_at": "2026-08-03T00:00:00Z",
    "closed_at": "2026-08-03T00:00:00Z",
    "labels": [{"name": "feat"}],
    "head": {"ref": "feat/x"},
    "base": {"ref": "main"},
}

PR_ISSUE_ROW: dict[str, Any] = {
    "id": 100,
    "number": 9,
    "title": "PR disguised as issue",
    "state": "open",
    "pull_request": {"url": "https://api.github.com/repos/MoonshotAI/kimi-code/pulls/9"},
    "updated_at": "2026-08-12T00:00:00Z",
}


class _FakeGitHub:
    owner = "MoonshotAI"
    name = "kimi-code"

    def fetch_issues(self, since: datetime | None) -> list[dict[str, Any]]:
        return [ISSUE_FIXTURE]

    def fetch_pull_requests(self, since: datetime | None) -> list[dict[str, Any]]:
        return [PR_FIXTURE]


def test_map_issue_fields() -> None:
    issue = map_issue(ISSUE_FIXTURE)
    assert issue.number == 7
    assert issue.title == "Fix crash"
    assert issue.labels == ["bug", "ios"]
    assert issue.author == "alice"
    assert issue.assignees == ["bob", "carol"]
    assert issue.github_issue_id == 42
    assert issue.html_url == ISSUE_FIXTURE["html_url"]
    assert issue.raw_payload == ISSUE_FIXTURE
    assert not hasattr(issue, "milestone") or "milestone" not in issue.model_fields_set
    dumped = issue.model_dump()
    assert "milestone" not in dumped
    assert dumped["raw_payload"]["milestone"]["title"] == "v1"


def test_map_pull_request_fields() -> None:
    pr = map_pull_request(PR_FIXTURE)
    assert pr.number == 8
    assert pr.draft is False
    assert pr.state == "closed"
    assert pr.merged_at is not None
    assert pr.github_pr_id == 99
    assert pr.ci_status is None
    assert pr.reviewers == []
    dumped = pr.model_dump()
    assert "labels" not in dumped
    assert "head_ref" not in dumped
    assert "base_ref" not in dumped
    assert dumped["raw_payload"]["labels"][0]["name"] == "feat"
    assert dumped["raw_payload"]["head"]["ref"] == "feat/x"
    assert dumped["raw_payload"]["base"]["ref"] == "main"


def test_build_payload_skips_missing_snapshots(tmp_path: Path) -> None:
    payload = build_sync_payload(
        owner="MoonshotAI",
        name="kimi-code",
        issues=[ISSUE_FIXTURE],
        pull_requests=[PR_FIXTURE],
        sync_type="incremental",
        started_at=datetime(2026, 8, 28, tzinfo=UTC),
        finished_at=datetime(2026, 8, 28, 1, tzinfo=UTC),
        since=datetime(2026, 8, 26, tzinfo=UTC),
        scan_snapshot=load_scan_snapshot(str(tmp_path / "missing.md")),
        graph_snapshot=load_graph_snapshot(str(tmp_path / "missing.json")),
    )
    assert payload.repo.full_name == "MoonshotAI/kimi-code"
    assert payload.sync_run.sync_type == "incremental"
    assert payload.scan_snapshot is None
    assert payload.graph_snapshot is None
    assert payload.issues[0].github_issue_id == 42
    assert payload.pull_requests[0].github_pr_id == 99


def test_load_snapshots_when_files_exist(tmp_path: Path) -> None:
    md = tmp_path / "scan.md"
    md.write_text("# scan", encoding="utf-8")
    graph = tmp_path / "graph.json"
    graph.write_text(json.dumps({"nodes": [1]}), encoding="utf-8")
    scan = load_scan_snapshot(str(md))
    snap = load_graph_snapshot(str(graph))
    assert scan is not None
    assert scan.raw_markdown == "# scan"
    assert snap is not None
    assert snap.payload == {"nodes": [1]}


def test_fetch_issues_excludes_pull_request_rows() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/issues")
        return httpx.Response(200, json=[ISSUE_FIXTURE, PR_ISSUE_ROW])

    client = httpx.Client(transport=httpx.MockTransport(handler))
    gh = GitHubClient(token="t", http_client=client)
    rows = gh.fetch_issues(None)
    assert len(rows) == 1
    assert rows[0]["number"] == 7


def test_fetch_pull_requests_filters_updated_at() -> None:
    older = {**PR_FIXTURE, "id": 1, "number": 1, "updated_at": "2026-08-09T00:00:00Z"}
    newer = {**PR_FIXTURE, "id": 2, "number": 2, "updated_at": "2026-08-11T00:00:00Z"}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/pulls")
        return httpx.Response(200, json=[newer, older])

    client = httpx.Client(transport=httpx.MockTransport(handler))
    gh = GitHubClient(token="t", http_client=client)
    since = datetime(2026, 8, 10, tzinfo=UTC)
    rows = gh.fetch_pull_requests(since)
    assert [row["number"] for row in rows] == [2]


def test_fetch_pull_requests_stops_pagination_after_stale_row() -> None:
    """updated desc：本页已出现 since 之前的行则不再请求下一页。"""
    newer = {**PR_FIXTURE, "id": 2, "number": 2, "updated_at": "2026-08-11T00:00:00Z"}
    older = {**PR_FIXTURE, "id": 1, "number": 1, "updated_at": "2026-08-09T00:00:00Z"}
    pages: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        page = int(request.url.params.get("page", "1"))
        pages.append(page)
        if page >= 2:
            return httpx.Response(500, text="should not paginate")
        return httpx.Response(200, json=[newer, older] + [{}] * 98)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    gh = GitHubClient(token="t", http_client=client)
    since = datetime(2026, 8, 10, tzinfo=UTC)
    rows = gh.fetch_pull_requests(since)
    assert [row["number"] for row in rows] == [2]
    assert pages == [1]


def test_default_post_timeout_allows_slow_write() -> None:
    assert DEFAULT_POST_TIMEOUT.write == 180.0
    assert DEFAULT_POST_TIMEOUT.read == 180.0


def test_github_401_fail_fast(monkeypatch: pytest.MonkeyPatch) -> None:
    sleeps: list[float] = []
    monkeypatch.setattr("app.ops.admin.sender.github_client.time.sleep", sleeps.append)
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(401, text="bad creds")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    gh = GitHubClient(token="t", http_client=client)
    with pytest.raises(GitHubSyncError) as excinfo:
        gh.fetch_issues(None)
    assert excinfo.value.fail_fast is True
    assert excinfo.value.status_code == 401
    assert calls["n"] == 1
    assert sleeps == []


def test_github_403_retries_then_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    sleeps: list[float] = []
    monkeypatch.setattr("app.ops.admin.sender.github_client.time.sleep", sleeps.append)
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] < 3:
            return httpx.Response(403, text="rate limit")
        return httpx.Response(200, json=[ISSUE_FIXTURE])

    client = httpx.Client(transport=httpx.MockTransport(handler))
    gh = GitHubClient(token="t", http_client=client)
    rows = gh.fetch_issues(None)
    assert len(rows) == 1
    assert calls["n"] == 3
    assert sleeps == [2.0, 4.0]


def test_post_sync_sends_bearer_header() -> None:
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["auth"] = request.headers.get("authorization", "")
        seen["url"] = str(request.url)
        return httpx.Response(202, json={"ok": True})

    payload = build_sync_payload(
        owner="MoonshotAI",
        name="kimi-code",
        issues=[ISSUE_FIXTURE],
        pull_requests=[],
        sync_type="full",
        started_at=datetime(2026, 8, 28, tzinfo=UTC),
        finished_at=datetime(2026, 8, 28, 1, tzinfo=UTC),
        since=None,
    )
    client = httpx.Client(transport=httpx.MockTransport(handler))
    resp = post_sync_payload(
        base_url="https://api.example",
        token="secret-token",
        payload=payload,
        http_client=client,
    )
    assert resp.status_code == 202
    assert seen["auth"] == "Bearer secret-token"
    assert seen["url"] == "https://api.example/api/ops/admin/sync"


def test_run_sync_nonzero_on_non_2xx() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="upstream fail")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    code = run_sync(
        sync_type="full",
        github=_FakeGitHub(),
        http_client=client,
        scan_path="",
        graph_path="",
        api_base_url="https://api.example",
        admin_token="tok",
        err=io.StringIO(),
    )
    assert code == 1


def test_run_sync_ok_without_scan_graph(tmp_path: Path) -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content)
        return httpx.Response(202, json={"ok": True})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    err = io.StringIO()
    code = run_sync(
        sync_type="incremental",
        github=_FakeGitHub(),
        http_client=client,
        scan_path=str(tmp_path / "nope.md"),
        graph_path=str(tmp_path / "nope.json"),
        api_base_url="https://api.example",
        admin_token="tok",
        err=err,
    )
    assert code == 0
    assert "POST sync bytes=" in err.getvalue()
    body = captured["body"]
    assert body["scan_snapshot"] is None
    assert body["graph_snapshot"] is None
    assert body["sync_run"]["sync_type"] == "incremental"
    assert body["sync_run"]["summary"]["since"] is not None
    assert body["issues"][0]["github_issue_id"] == 42
    assert body["pull_requests"][0]["github_pr_id"] == 99
