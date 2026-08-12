"""RAG_RERANK：Cross-Encoder 精排开关与排序稳定性。"""
from __future__ import annotations

from collections.abc import Sequence
from unittest.mock import MagicMock

import pytest

from app.ops.rag.reranker import (
    recall_k_each,
    rerank_candidates,
    rerank_chunks,
    rerank_enabled,
    rerank_min_score,
    rerank_score_ratio,
)
from app.ops.rag.retrieve import RetrievedChunk


def _chunk(i: int, content: str = "") -> RetrievedChunk:
    return RetrievedChunk(
        id=i,
        repo="r",
        source_type="issue",
        source_id=str(1000 + i),
        chunk_index=0,
        content=content or f"body-{i}",
        rrf_score=1.0 / (60 + i),
    )


@pytest.fixture(autouse=True)
def _clear_rerank_env(monkeypatch: pytest.MonkeyPatch):
    for key in (
        "RAG_RERANK_ENABLED",
        "RAG_RERANK_MODEL",
        "RAG_RERANK_CANDIDATES",
        "RAG_RECALL_K_EACH",
        "RAG_RERANK_MIN_SCORE",
        "RAG_RERANK_SCORE_RATIO",
    ):
        monkeypatch.delenv(key, raising=False)


def test_rerank_disabled_by_default():
    assert rerank_enabled() is False


def test_rerank_enabled_true(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("RAG_RERANK_ENABLED", "true")
    assert rerank_enabled() is True


def test_candidates_and_k_each_defaults_and_override(monkeypatch: pytest.MonkeyPatch):
    assert rerank_candidates() == 20
    assert recall_k_each() == 20
    monkeypatch.setenv("RAG_RERANK_CANDIDATES", "15")
    monkeypatch.setenv("RAG_RECALL_K_EACH", "12")
    assert rerank_candidates() == 15
    assert recall_k_each() == 12


def test_rerank_floor_and_ratio_defaults_and_override(monkeypatch: pytest.MonkeyPatch):
    assert rerank_min_score() == 0.6
    assert rerank_score_ratio() == 0.75
    monkeypatch.setenv("RAG_RERANK_MIN_SCORE", "0.45")
    monkeypatch.setenv("RAG_RERANK_SCORE_RATIO", "0.8")
    assert rerank_min_score() == 0.45
    assert rerank_score_ratio() == 0.8


def test_rerank_chunks_fake_scores_order_and_top5():
    cands = [_chunk(i) for i in range(1, 8)]  # 7 条

    def score_fn(_query: str, texts: Sequence[str]) -> list[float]:
        # 故意逆序：正文 body-7 最高分（max 远高于地板）
        return [float(t.split("-")[1]) for t in texts]

    # ratio=0 → 仅地板；分数 7..3 均保留至 top5
    out = rerank_chunks("q", cands, top_n=5, score_fn=score_fn, score_ratio=0.0)
    assert len(out) == 5
    assert [c.id for c in out] == [7, 6, 5, 4, 3]
    assert out[0].rerank_score == 7.0


def test_rerank_chunks_short_list():
    cands = [_chunk(1), _chunk(2)]
    out = rerank_chunks(
        "q",
        cands,
        top_n=5,
        score_fn=lambda _q, t: [0.1, 0.9],
        min_score=0.0,
        score_ratio=0.0,
    )
    assert [c.id for c in out] == [2, 1]


def test_rerank_chunks_floor_empties_when_max_low():
    cands = [_chunk(i) for i in range(1, 5)]
    empty = rerank_chunks(
        "q",
        cands,
        top_n=5,
        score_fn=lambda _q, _t: [0.4, 0.55, 0.5, 0.49],
        min_score=0.6,
        score_ratio=0.75,
    )
    assert empty == []


def test_rerank_chunks_relative_cut_after_floor():
    cands = [_chunk(i) for i in range(1, 5)]
    # max=0.9 >= 0.6；cut=0.9*0.75=0.675 → 保留 0.9, 0.7
    out = rerank_chunks(
        "q",
        cands,
        top_n=5,
        score_fn=lambda _q, _t: [0.4, 0.55, 0.7, 0.9],
        min_score=0.6,
        score_ratio=0.75,
    )
    assert [c.id for c in out] == [4, 3]
    assert out[0].rerank_score == 0.9


def test_rerank_chunks_load_failure_falls_back():
    cands = [_chunk(i) for i in range(1, 6)]

    def boom(_q: str, _t: Sequence[str]) -> list[float]:
        raise RuntimeError("no weights")

    out = rerank_chunks("q", cands, top_n=5, score_fn=boom)
    assert [c.id for c in out] == [1, 2, 3, 4, 5]


@pytest.mark.asyncio
async def test_retrieve_node_disabled_does_not_call_rerank(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("RAG_RERANK_ENABLED", raising=False)
    from app.ops.chat import rag_nodes

    fake_chunks = [_chunk(i) for i in range(1, 6)]
    monkeypatch.setattr(
        rag_nodes,
        "_get_embedder",
        lambda: MagicMock(embed=MagicMock(return_value=[[0.1] * 8])),
    )

    class _CM:
        async def __aenter__(self):
            return MagicMock()

        async def __aexit__(self, *args):
            return None

    monkeypatch.setattr(rag_nodes, "AsyncSessionLocal", lambda: _CM())
    hybrid = MagicMock()

    async def _hybrid(*args, **kwargs):
        hybrid(*args, **kwargs)
        return fake_chunks

    monkeypatch.setattr(rag_nodes, "hybrid_recall", _hybrid)
    monkeypatch.setattr(rag_nodes, "update_current_span_metadata", lambda *_a, **_k: None)

    called = {"n": 0}

    def _should_not(*_a, **_k):
        called["n"] += 1
        raise AssertionError("rerank_chunks must not be called when disabled")

    monkeypatch.setattr(rag_nodes, "rerank_chunks", _should_not)

    result = await rag_nodes.retrieve_node({"query": "hello"})
    assert called["n"] == 0
    assert [c.id for c in result["retrieved"]] == [1, 2, 3, 4, 5]
    assert hybrid.call_args.kwargs.get("k_each") == 10
    assert hybrid.call_args.kwargs.get("top_n") == 5


@pytest.mark.asyncio
async def test_retrieve_node_enabled_reranks(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("RAG_RERANK_ENABLED", "true")
    from app.ops.chat import rag_nodes

    coarse = [_chunk(i) for i in range(1, 8)]
    monkeypatch.setattr(
        rag_nodes,
        "_get_embedder",
        lambda: MagicMock(embed=MagicMock(return_value=[[0.1] * 8])),
    )

    class _CM:
        async def __aenter__(self):
            return MagicMock()

        async def __aexit__(self, *args):
            return None

    monkeypatch.setattr(rag_nodes, "AsyncSessionLocal", lambda: _CM())

    async def _hybrid(*_a, **kwargs):
        assert kwargs.get("k_each") == 20
        assert kwargs.get("top_n") == 20
        return coarse

    monkeypatch.setattr(rag_nodes, "hybrid_recall", _hybrid)
    monkeypatch.setattr(rag_nodes, "update_current_span_metadata", lambda *_a, **_k: None)

    def fake_rerank(query, cands, top_n=5, **_k):
        assert query == "hello"
        assert len(cands) == 7
        return list(reversed(list(cands)))[:top_n]

    monkeypatch.setattr(rag_nodes, "rerank_chunks", fake_rerank)

    result = await rag_nodes.retrieve_node({"query": "hello"})
    assert [c.id for c in result["retrieved"]] == [7, 6, 5, 4, 3]
    assert result["events"][0]["payload"]["rerank_enabled"] is True
