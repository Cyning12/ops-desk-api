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


async def test_sync_requires_maintainer(
    client: AsyncClient, override_auth_viewer
) -> None:
    """POST /admin/sync as viewer returns 403."""
    response = await client.post("/api/ops/admin/sync", json={})
    assert response.status_code == 403


@pytest.mark.skipif(not DB_AVAILABLE, reason="PostgreSQL not available")
async def test_sync_rejects_missing_repo(
    client: AsyncClient, override_auth_maintainer
) -> None:
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


async def _cleanup_repo(repo_id: str) -> None:
    """Delete a repo and all cascading children."""
    async with AsyncSessionLocal() as db:
        await db.execute(delete(OpsRepo).where(OpsRepo.id == repo_id))
        await db.commit()
