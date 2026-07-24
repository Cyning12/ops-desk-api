"""Tests for graph snapshot read-only endpoint."""
from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import delete

from app.db.models import OpsRepo
from app.db.session import AsyncSessionLocal
from tests.conftest import DB_AVAILABLE


async def test_graph_requires_auth(client: AsyncClient) -> None:
    """GET /graph without cookie returns 401."""
    response = await client.get("/api/ops/graph")
    assert response.status_code == 401


@pytest.mark.skipif(not DB_AVAILABLE, reason="PostgreSQL not available")
async def test_graph_empty_returns_none(
    client: AsyncClient,
    override_auth_maintainer,
    clean_sync_data,
) -> None:
    """Before sync, graph endpoint returns null snapshot."""
    response = await client.get("/api/ops/graph")
    assert response.status_code == 200
    data = response.json()
    assert data["snapshot"] is None
    assert data["module_matrix"] is None
    assert data["repo_id"] is None


@pytest.mark.skipif(not DB_AVAILABLE, reason="PostgreSQL not available")
async def test_graph_returns_latest_snapshot(
    client: AsyncClient,
    override_auth_maintainer,
    sample_sync_payload,
    clean_sync_data,
) -> None:
    """After sync, graph endpoint returns the latest snapshot."""
    sync_response = await client.post(
        "/api/ops/admin/sync",
        json=sample_sync_payload,
    )
    assert sync_response.status_code == 202
    repo_id = sync_response.json()["repo_id"]

    response = await client.get("/api/ops/graph")
    assert response.status_code == 200
    data = response.json()
    assert data["repo_id"] == repo_id
    assert data["snapshot"] == {"nodes": [], "edges": []}
    assert data["module_matrix"] == {"auth": [1]}

    await _cleanup_repo(repo_id)


async def _cleanup_repo(repo_id: str) -> None:
    """Delete a repo and all cascading children."""
    async with AsyncSessionLocal() as db:
        await db.execute(delete(OpsRepo).where(OpsRepo.id == repo_id))
        await db.commit()
