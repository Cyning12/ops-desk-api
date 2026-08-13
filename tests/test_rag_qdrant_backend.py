"""Qdrant Flag / fallback / 影子写 enqueue 单测。"""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.ops.rag import backend as backend_mod
from app.ops.rag.backend import VectorBackend, search_dense_with_fallback, vector_backend
from app.ops.rag.retrieve import hybrid_recall_detail
from app.ops.rag.shadow_write import (
    ShadowPoint,
    enqueue_shadow_delete,
    enqueue_shadow_upsert,
    set_enqueue_hook,
    shadow_write_enabled,
)


@pytest.fixture(autouse=True)
def _reset_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("RAG_VECTOR_BACKEND", raising=False)
    monkeypatch.delenv("RAG_QDRANT_SHADOW_WRITE", raising=False)
    monkeypatch.delenv("RAG_SECOND_PATH", raising=False)
    set_enqueue_hook(None)
    backend_mod.rag_vector_backend_fallback_total = 0
    yield
    set_enqueue_hook(None)


def test_vector_backend_default_pgvector():
    assert vector_backend() == VectorBackend.PGVECTOR


def test_vector_backend_invalid_fallback(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("RAG_VECTOR_BACKEND", "diskann")
    assert vector_backend() == VectorBackend.PGVECTOR


def test_shadow_write_default_off():
    assert shadow_write_enabled() is False


@pytest.mark.asyncio
async def test_hybrid_recall_default_uses_pg_semantic(monkeypatch: pytest.MonkeyPatch):
    """默认 pgvector：稠密路走 PG SQL，不触达 Qdrant client。"""
    monkeypatch.delenv("RAG_VECTOR_BACKEND", raising=False)
    calls: list[str] = []

    async def fake_execute(sql, params=None):
        calls.append(str(sql))
        return []

    session = MagicMock()
    session.execute = AsyncMock(side_effect=fake_execute)

    await hybrid_recall_detail(
        session, "自动压缩", query_vector=[0.0] * 8, k_each=3, top_n=2
    )
    assert any("embedding <=>" in c for c in calls)
    assert all("qdrant" not in c.lower() for c in calls)


@pytest.mark.asyncio
async def test_search_dense_fallback_after_retry(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("RAG_VECTOR_BACKEND", "qdrant")
    backend_mod.rag_vector_backend_fallback_total = 0
    attempts = {"n": 0}

    async def boom():
        attempts["n"] += 1
        raise ConnectionError("qdrant down")

    async def pg_ok():
        return ["pg"]

    out = await search_dense_with_fallback(boom, pg_ok)
    assert out == ["pg"]
    assert attempts["n"] == 2
    assert backend_mod.rag_vector_backend_fallback_total == 1


@pytest.mark.asyncio
async def test_qdrant_retriever_hydrates_from_pg():
    from app.ops.rag.retrievers.qdrant_retriever import QdrantRetriever

    hit = SimpleNamespace(id=42, payload={"repo": "x"})
    client = MagicMock()
    client.search = AsyncMock(return_value=[hit])
    client.close = AsyncMock()

    row = SimpleNamespace(
        id=42,
        repo="ops-desk-api",
        source_type="doc",
        source_id="a.md",
        chunk_index=0,
        content="Title: t\n\nbody",
        metadata={},
        images=[],
    )
    result = MagicMock()
    result.all = MagicMock(return_value=[row])
    session = MagicMock()
    session.execute = AsyncMock(return_value=result)

    retriever = QdrantRetriever(session, client=client)
    chunks = await retriever.search([0.1] * 4, k=5)
    assert len(chunks) == 1
    assert chunks[0].id == 42
    assert chunks[0].content.startswith("Title:")
    client.search.assert_awaited()
    # hydrate 走 PG
    session.execute.assert_awaited()


def test_shadow_upsert_enqueue_nonblocking(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("RAG_QDRANT_SHADOW_WRITE", "true")
    seen: list[tuple] = []

    def hook(op, payload):
        seen.append((op, payload))

    set_enqueue_hook(hook)
    pts = [
        ShadowPoint(
            point_id=1,
            vector=[0.1, 0.2],
            payload={
                "source_type": "doc",
                "repo": "r",
                "source_id": "s",
                "chunk_index": 0,
            },
        )
    ]
    enqueue_shadow_upsert(pts)
    assert seen == [("upsert", pts)]


def test_shadow_delete_enqueue(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("RAG_QDRANT_SHADOW_WRITE", "true")
    seen: list[tuple] = []
    set_enqueue_hook(lambda op, payload: seen.append((op, payload)))
    enqueue_shadow_delete([7, 8])
    assert seen == [("delete", [7, 8])]


def test_shadow_disabled_no_enqueue(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("RAG_QDRANT_SHADOW_WRITE", "false")
    seen: list = []
    set_enqueue_hook(lambda *a: seen.append(a))
    enqueue_shadow_upsert(
        [ShadowPoint(1, [0.0], {"source_type": "doc", "repo": "r", "source_id": "s", "chunk_index": 0})]
    )
    assert seen == []
