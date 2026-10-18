"""Tests for admin sync endpoint."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import delete, func, select

from app.db.models import OpsIssue, OpsPullRequest, OpsRepo
from app.db.session import AsyncSessionLocal
from tests.conftest import DB_AVAILABLE


async def test_sync_requires_auth(client: AsyncClient) -> None:
    """POST /admin/sync without cookie returns 401."""
    response = await client.post("/api/ops/admin/sync", json={})
    assert response.status_code == 401


async def test_sync_requires_maintainer(client: AsyncClient, override_auth_viewer) -> None:
    """POST /admin/sync as viewer returns 403."""
    response = await client.post("/api/ops/admin/sync", json={})
    assert response.status_code == 403


@pytest.mark.skipif(not DB_AVAILABLE, reason="PostgreSQL not available")
async def test_sync_rejects_missing_repo(client: AsyncClient, override_auth_maintainer) -> None:
    """Payload missing repo returns 422."""
    response = await client.post(
        "/api/ops/admin/sync",
        json={"sync_run": {"sync_type": "full"}},
    )
    assert response.status_code == 422


@pytest.mark.skipif(not DB_AVAILABLE, reason="PostgreSQL not available")
async def test_sync_imports_and_returns_counts(
    client: AsyncClient,
    override_auth_maintainer,
    sample_sync_payload,
    clean_sync_data,
) -> None:
    """Sync imports repo/issue/PR/snapshots and returns summary."""
    response = await client.post(
        "/api/ops/admin/sync",
        json=sample_sync_payload,
    )
    assert response.status_code == 202
    data = response.json()
    assert data["ok"] is True
    assert data["repos_created"] == 1
    assert data["issues_created"] == 1
    assert data["pulls_created"] == 1
    assert data["sync_runs"] == 1
    assert data["scan_snapshots"] == 1
    assert data["graph_snapshots"] == 1

    # Cleanup
    await _cleanup_repo(data["repo_id"])


@pytest.mark.skipif(not DB_AVAILABLE, reason="PostgreSQL not available")
async def test_sync_upsert_is_idempotent(
    client: AsyncClient,
    override_auth_maintainer,
    sample_sync_payload,
    clean_sync_data,
) -> None:
    """Calling sync twice updates existing rows instead of duplicating."""
    response1 = await client.post("/api/ops/admin/sync", json=sample_sync_payload)
    assert response1.status_code == 202
    repo_id = response1.json()["repo_id"]

    response2 = await client.post("/api/ops/admin/sync", json=sample_sync_payload)
    assert response2.status_code == 202
    data2 = response2.json()
    assert data2["repos_updated"] == 1
    assert data2["issues_updated"] == 1
    assert data2["pulls_updated"] == 1
    assert data2["sync_runs"] == 1

    # Verify only one issue and one PR row exist.
    async with AsyncSessionLocal() as db:
        issue_count = await db.scalar(
            select(func.count(OpsIssue.id)).where(OpsIssue.repo_id == repo_id)
        )
        pr_count = await db.scalar(
            select(func.count(OpsPullRequest.id)).where(OpsPullRequest.repo_id == repo_id)
        )
    assert issue_count == 1
    assert pr_count == 1

    # Cleanup
    await _cleanup_repo(repo_id)


@pytest.mark.skipif(not DB_AVAILABLE, reason="PostgreSQL not available")
async def test_sync_accepts_bearer_token(
    client: AsyncClient,
    sample_sync_payload,
    clean_sync_data,
    monkeypatch,
) -> None:
    """正确 Bearer 与 cookie 一样返回 202。"""
    from app.config import settings

    monkeypatch.setattr(settings, "ops_admin_sync_token", "test-sync-token")
    response = await client.post(
        "/api/ops/admin/sync",
        json=sample_sync_payload,
        headers={"Authorization": "Bearer test-sync-token"},
    )
    assert response.status_code == 202
    data = response.json()
    assert data["ok"] is True
    await _cleanup_repo(data["repo_id"])


async def test_sync_rejects_wrong_bearer(client: AsyncClient, monkeypatch) -> None:
    """错误 Bearer → 401。"""
    from app.config import settings

    monkeypatch.setattr(settings, "ops_admin_sync_token", "correct-token")
    response = await client.post(
        "/api/ops/admin/sync",
        json={},
        headers={"Authorization": "Bearer wrong-token"},
    )
    assert response.status_code == 401


async def test_sync_rejects_bearer_when_token_unconfigured(
    client: AsyncClient, monkeypatch
) -> None:
    """未配置 token 时带 Bearer → 401。"""
    from app.config import settings

    monkeypatch.setattr(settings, "ops_admin_sync_token", "")
    response = await client.post(
        "/api/ops/admin/sync",
        json={},
        headers={"Authorization": "Bearer any-token"},
    )
    assert response.status_code == 401


@pytest.mark.skipif(not DB_AVAILABLE, reason="PostgreSQL not available")
async def test_sync_cookie_works_when_bearer_configured(
    client: AsyncClient,
    override_auth_maintainer,
    sample_sync_payload,
    clean_sync_data,
    monkeypatch,
) -> None:
    """配置了机读 token 时，cookie maintainer 仍可用。"""
    from app.config import settings

    monkeypatch.setattr(settings, "ops_admin_sync_token", "test-sync-token")
    response = await client.post("/api/ops/admin/sync", json=sample_sync_payload)
    assert response.status_code == 202
    await _cleanup_repo(response.json()["repo_id"])


@pytest.mark.skipif(not DB_AVAILABLE, reason="PostgreSQL not available")
async def test_sync_accepts_github_ids_beyond_int32(
    client: AsyncClient,
    override_auth_maintainer,
    sample_sync_payload,
    clean_sync_data,
) -> None:
    """GitHub issue/PR id 超过 int32 时不得 500（生产 kimi-code id=5275397263）。"""
    payload = sample_sync_payload
    payload["issues"][0]["github_issue_id"] = 5_275_397_263
    payload["pull_requests"][0]["github_pr_id"] = 5_275_397_264
    response = await client.post("/api/ops/admin/sync", json=payload)
    assert response.status_code == 202, response.text
    await _cleanup_repo(response.json()["repo_id"])


async def _cleanup_repo(repo_id: str) -> None:
    """Delete a repo and all cascading children."""
    async with AsyncSessionLocal() as db:
        await db.execute(delete(OpsRepo).where(OpsRepo.id == repo_id))
        await db.commit()
