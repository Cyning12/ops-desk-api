"""RAG_SECOND_PATH：第二路 fts（默认）| sparse（C 臂）；默认不回归现网 FTS。"""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.ops.rag.retrieve import (
    _SPARSE_SQL,
    _keyword_query,
    _second_path,
    hybrid_recall_detail,
)
from app.ops.rag.sparse_vec import lexical_weights_to_sparsevec


@pytest.fixture(autouse=True)
def _clear_path_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("RAG_SECOND_PATH", raising=False)
    monkeypatch.delenv("RAG_FTS_CONFIG", raising=False)
    monkeypatch.delenv("RAG_KW_EXPAND", raising=False)


def test_second_path_default_fts():
    assert _second_path() == "fts"


def test_second_path_unset_matches_fts_keyword(monkeypatch: pytest.MonkeyPatch):
    """未设 RAG_SECOND_PATH 时与现网一致：走 plainto_tsquery(simple)。"""
    monkeypatch.delenv("RAG_SECOND_PATH", raising=False)
    sql, param = _keyword_query("自动压缩")
    assert param == "自动压缩"
    assert "plainto_tsquery('simple'::regconfig" in str(sql)


def test_second_path_fts_explicit(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("RAG_SECOND_PATH", "fts")
    assert _second_path() == "fts"
    sql, _ = _keyword_query("自动压缩")
    assert "plainto_tsquery('simple'::regconfig" in str(sql)
    assert "sparse_embedding" not in str(sql)


def test_second_path_sparse(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("RAG_SECOND_PATH", "sparse")
    assert _second_path() == "sparse"


def test_second_path_invalid_fallback(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("RAG_SECOND_PATH", "bm25")
    assert _second_path() == "fts"


def test_sparse_sql_uses_inner_product_op():
    s = str(_SPARSE_SQL)
    assert "sparse_embedding" in s
    assert "<#>" in s
    assert "CAST(:qsparse AS sparsevec)" in s


def test_lexical_weights_to_sparsevec_format_and_truncation():
    # token_id 0 → index 1；按 |w| 截断
    weights = {i: float(i + 1) for i in range(1200)}
    s = lexical_weights_to_sparsevec(weights, max_nnz=10)
    assert s.endswith("/250002")
    body = s[1 : s.index("}/")]
    pairs = body.split(",")
    assert len(pairs) == 10
    # 截断后应按 index 升序
    idxs = [int(p.split(":")[0]) for p in pairs]
    assert idxs == sorted(idxs)


def test_lexical_weights_empty():
    assert lexical_weights_to_sparsevec({}) == "{}/250002"
    assert lexical_weights_to_sparsevec(None) == "{}/250002"


@pytest.mark.asyncio
async def test_hybrid_recall_sparse_path_sql(monkeypatch: pytest.MonkeyPatch):
    """sparse 路径使用预编码 query_sparse，不加载 FlagEmbedding。"""
    monkeypatch.setenv("RAG_SECOND_PATH", "sparse")

    calls: list[tuple] = []

    async def fake_execute(sql, params=None):
        calls.append((str(sql), params))
        return []

    session = MagicMock()
    session.execute = AsyncMock(side_effect=fake_execute)

    svec = "{1:0.5,3:0.2}/250002"
    result = await hybrid_recall_detail(
        session,
        "自动压缩",
        query_vector=[0.0] * 8,
        k_each=3,
        top_n=2,
        query_sparse=svec,
    )
    assert result.fused == []
    assert len(calls) == 2
    assert "embedding <=>" in calls[0][0]
    assert "sparse_embedding" in calls[1][0]
    assert "<#>" in calls[1][0]
    assert calls[1][1]["qsparse"] == svec
    assert "plainto_tsquery" not in calls[1][0]


@pytest.mark.asyncio
async def test_hybrid_recall_default_fts_sql(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("RAG_SECOND_PATH", raising=False)

    calls: list[tuple] = []

    async def fake_execute(sql, params=None):
        calls.append((str(sql), params))
        row = SimpleNamespace(
            id=1,
            repo="r",
            source_type="issue",
            source_id="1",
            chunk_index=0,
            content="x",
            metadata={},
            images=[],
        )
        return [row]

    session = MagicMock()
    session.execute = AsyncMock(side_effect=fake_execute)

    result = await hybrid_recall_detail(
        session, "自动压缩", query_vector=[0.1, 0.2], k_each=2, top_n=1
    )
    assert len(result.fused) == 1
    assert "plainto_tsquery('simple'::regconfig" in calls[1][0]
    assert "sparse_embedding" not in calls[1][0]
