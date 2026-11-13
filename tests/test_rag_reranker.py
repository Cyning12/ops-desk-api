"""RAG_RERANK：精排开关、方案 B 过滤与 SiliconFlow 打分后端。"""

from __future__ import annotations

from collections.abc import Sequence

import httpx
import pytest

from app.ops.rag import reranker as reranker_mod
from app.ops.rag.reranker import (
    recall_k_each,
    rerank_backend,
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
        "RAG_RERANK_BACKEND",
        "RAG_RERANK_CANDIDATES",
        "RAG_RECALL_K_EACH",
        "RAG_RERANK_MIN_SCORE",
        "RAG_RERANK_SCORE_RATIO",
        "SILICONFLOW_API_KEY",
        "SILICONFLOW_BASE_URL",
    ):
        monkeypatch.delenv(key, raising=False)


def test_rerank_disabled_by_default():
    assert rerank_enabled() is False


def test_rerank_backend_defaults_to_siliconflow(monkeypatch: pytest.MonkeyPatch):
    assert rerank_backend() == "siliconflow"
    monkeypatch.setenv("RAG_RERANK_BACKEND", "")
    assert rerank_backend() == "siliconflow"
    monkeypatch.setenv("RAG_RERANK_BACKEND", "local")
    assert rerank_backend() == "local"


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
    assert rerank_min_score() == 0.4
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


def _forbid_cross_encoder(monkeypatch: pytest.MonkeyPatch) -> dict[str, int]:
    calls = {"n": 0}

    def boom(*_a, **_k):
        calls["n"] += 1
        raise AssertionError("sentence_transformers.CrossEncoder must not be loaded")

    monkeypatch.setattr(reranker_mod, "_load_cross_encoder", boom)
    return calls


def _mock_siliconflow_post(
    monkeypatch: pytest.MonkeyPatch,
    *,
    results: list[dict] | None = None,
    error: BaseException | None = None,
    status_code: int = 200,
) -> dict:
    capture: dict = {"n": 0, "calls": []}

    def fake_post(url, json=None, headers=None, timeout=None):
        capture["n"] += 1
        capture["calls"].append({"url": url, "json": json, "headers": headers, "timeout": timeout})
        if error is not None:
            raise error
        request = httpx.Request("POST", str(url))
        if status_code >= 400:
            resp = httpx.Response(status_code, request=request, json={"error": "fail"})
            return resp
        resp = httpx.Response(
            status_code,
            request=request,
            json={"results": results or []},
        )
        return resp

    monkeypatch.setattr(reranker_mod.httpx, "post", fake_post)
    return capture


def test_siliconflow_backend_skips_cross_encoder(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("RAG_RERANK_ENABLED", "true")
    monkeypatch.setenv("RAG_RERANK_BACKEND", "siliconflow")
    monkeypatch.setenv("SILICONFLOW_API_KEY", "sk-test")
    ce = _forbid_cross_encoder(monkeypatch)
    capture = _mock_siliconflow_post(
        monkeypatch,
        results=[
            {"index": 0, "relevance_score": 0.9},
            {"index": 1, "relevance_score": 0.85},
        ],
    )
    cands = [_chunk(1), _chunk(2)]
    out = rerank_chunks("q", cands, top_n=5, min_score=0.0, score_ratio=0.0)
    assert ce["n"] == 0
    assert capture["n"] == 1
    assert [c.id for c in out] == [1, 2]


def test_siliconflow_unordered_index_then_scheme_b(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("SILICONFLOW_API_KEY", "sk-test")
    monkeypatch.setenv("SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1")
    _forbid_cross_encoder(monkeypatch)
    capture = _mock_siliconflow_post(
        monkeypatch,
        results=[
            {"index": 2, "relevance_score": 0.95},
            {"index": 0, "relevance_score": 0.50},
            {"index": 1, "relevance_score": 0.80},
            {"index": 3, "relevance_score": 0.70},
        ],
    )
    cands = [_chunk(i) for i in range(1, 5)]
    # max=0.95 >= 0.4；cut=0.95*0.75=0.7125 → 保留 0.95, 0.80
    out = rerank_chunks("hello query", cands, top_n=5)
    req = capture["calls"][0]
    assert req["url"] == "https://api.siliconflow.cn/v1/rerank"
    assert req["json"]["top_n"] == 4
    assert req["json"]["query"] == "hello query"
    assert req["json"]["documents"] == ["body-1", "body-2", "body-3", "body-4"]
    assert req["json"]["model"] == "BAAI/bge-reranker-v2-m3"
    assert req["headers"]["Authorization"] == "Bearer sk-test"
    assert req["timeout"] == 12.0
    assert [c.id for c in out] == [3, 2]
    assert out[0].rerank_score == 0.95
    assert out[1].rerank_score == 0.80


def test_siliconflow_http_failure_falls_back_coarse(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("SILICONFLOW_API_KEY", "sk-test")
    _forbid_cross_encoder(monkeypatch)
    _mock_siliconflow_post(
        monkeypatch,
        error=httpx.TimeoutException("rerank timeout"),
    )
    cands = [_chunk(i) for i in range(1, 8)]
    out = rerank_chunks("q", cands, top_n=5)
    assert [c.id for c in out] == [1, 2, 3, 4, 5]


def test_siliconflow_http_5xx_falls_back_coarse(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("SILICONFLOW_API_KEY", "sk-test")
    _forbid_cross_encoder(monkeypatch)
    _mock_siliconflow_post(monkeypatch, status_code=500)
    cands = [_chunk(i) for i in range(1, 7)]
    out = rerank_chunks("q", cands, top_n=5)
    assert [c.id for c in out] == [1, 2, 3, 4, 5]


def test_siliconflow_missing_api_key_falls_back_coarse(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
):
    _forbid_cross_encoder(monkeypatch)
    http_calls = {"n": 0}

    def _no_http(*_a, **_k):
        http_calls["n"] += 1
        raise AssertionError("缺 key 时不得发 /rerank")

    monkeypatch.setattr(reranker_mod.httpx, "post", _no_http)
    cands = [_chunk(i) for i in range(1, 6)]
    with caplog.at_level("ERROR", logger="app.ops.rag.reranker"):
        out = rerank_chunks("q", cands, top_n=5)
    assert [c.id for c in out] == [1, 2, 3, 4, 5]
    assert http_calls["n"] == 0
    assert "rerank failed; fallback to coarse" in caplog.text
    assert "SILICONFLOW_API_KEY" in caplog.text
