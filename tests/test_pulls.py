"""Tests for pull requests read-only endpoint."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import delete

from app.db.models import OpsRepo
from app.db.session import AsyncSessionLocal
from tests.conftest import DB_AVAILABLE


async def test_list_pulls_requires_auth(client: AsyncClient) -> None:
    """GET /pulls without cookie returns 401."""
    response = await client.get("/api/ops/pulls")
    assert response.status_code == 401


@pytest.mark.skipif(not DB_AVAILABLE, reason="PostgreSQL not available")
async def test_list_pulls_schema(
    client: AsyncClient,
    override_auth_maintainer,
    sample_sync_payload,
    clean_sync_data,
) -> None:
    """Pulls endpoint returns imported PR with expected schema."""
    sync_response = await client.post(
        "/api/ops/admin/sync",
        json=sample_sync_payload,
    )
    assert sync_response.status_code == 202
    repo_id = sync_response.json()["repo_id"]

    response = await client.get("/api/ops/pulls")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1

    pr = data["items"][0]
    assert pr["number"] == 2
    assert pr["title"] == "Fix login crash"
    assert pr["state"] == "open"
    assert pr["draft"] is False
    assert pr["ci_status"] == "success"

    await _cleanup_repo(repo_id)


@pytest.mark.skipif(not DB_AVAILABLE, reason="PostgreSQL not available")
async def test_list_pulls_filter_by_state(
    client: AsyncClient,
    override_auth_maintainer,
    sample_sync_payload,
    clean_sync_data,
) -> None:
    """State filter returns only matching PRs."""
    sync_response = await client.post(
        "/api/ops/admin/sync",
        json=sample_sync_payload,
    )
    repo_id = sync_response.json()["repo_id"]

    response = await client.get("/api/ops/pulls?state=open")
    assert response.status_code == 200
    assert response.json()["total"] == 1

    response = await client.get("/api/ops/pulls?state=closed")
    assert response.status_code == 200
    assert response.json()["total"] == 0

    await _cleanup_repo(repo_id)


async def _cleanup_repo(repo_id: str) -> None:
    """Delete a repo and all cascading children."""
    async with AsyncSessionLocal() as db:
        await db.execute(delete(OpsRepo).where(OpsRepo.id == repo_id))
        await db.commit()
