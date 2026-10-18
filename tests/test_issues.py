"""Tests for issues read-only endpoint."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import delete

from app.db.models import OpsRepo
from app.db.session import AsyncSessionLocal
from tests.conftest import DB_AVAILABLE


async def test_list_issues_requires_auth(client: AsyncClient) -> None:
    """GET /issues without cookie returns 401."""
    response = await client.get("/api/ops/issues")
    assert response.status_code == 401


@pytest.mark.skipif(not DB_AVAILABLE, reason="PostgreSQL not available")
async def test_list_issues_schema(
    client: AsyncClient,
    override_auth_maintainer,
    sample_sync_payload,
    clean_sync_data,
) -> None:
    """Issues endpoint returns imported issue with expected schema."""
    sync_response = await client.post(
        "/api/ops/admin/sync",
        json=sample_sync_payload,
    )
    assert sync_response.status_code == 202
    repo_id = sync_response.json()["repo_id"]

    response = await client.get("/api/ops/issues")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["page"] == 1
    assert len(data["items"]) == 1

    issue = data["items"][0]
    assert issue["number"] == 1
    assert issue["title"] == "登录页面闪退"
    assert issue["state"] == "open"
    assert issue["module_tag"] == "auth"
    assert "bug" in issue["labels"]

    await _cleanup_repo(repo_id)


@pytest.mark.skipif(not DB_AVAILABLE, reason="PostgreSQL not available")
async def test_list_issues_filter_by_label(
    client: AsyncClient,
    override_auth_maintainer,
    sample_sync_payload,
    clean_sync_data,
) -> None:
    """Label filter returns only matching issues."""
    sync_response = await client.post(
        "/api/ops/admin/sync",
        json=sample_sync_payload,
    )
    repo_id = sync_response.json()["repo_id"]

    response = await client.get("/api/ops/issues?label=ios")
    assert response.status_code == 200
    assert response.json()["total"] == 1

    response = await client.get("/api/ops/issues?label=backend")
    assert response.status_code == 200
    assert response.json()["total"] == 0

    await _cleanup_repo(repo_id)


@pytest.mark.skipif(not DB_AVAILABLE, reason="PostgreSQL not available")
async def test_list_issues_pagination(
    client: AsyncClient,
    override_auth_maintainer,
    sample_sync_payload,
    clean_sync_data,
) -> None:
    """Pagination returns correct page_size and total."""
    sync_response = await client.post(
        "/api/ops/admin/sync",
        json=sample_sync_payload,
    )
    repo_id = sync_response.json()["repo_id"]

    response = await client.get("/api/ops/issues?page=1&page_size=1")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["total"] == 1

    await _cleanup_repo(repo_id)


async def _cleanup_repo(repo_id: str) -> None:
    """Delete a repo and all cascading children."""
    async with AsyncSessionLocal() as db:
        await db.execute(delete(OpsRepo).where(OpsRepo.id == repo_id))
        await db.commit()
