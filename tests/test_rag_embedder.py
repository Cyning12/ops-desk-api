"""RAG_EMBED：查询路径 SiliconFlow ApiEmbedder 工厂与失败路径。"""

from __future__ import annotations

from unittest.mock import MagicMock

import httpx
import pytest

from app.ops.rag import embedder as embedder_mod
from app.ops.rag.embedder import (
    ApiEmbedder,
    SentenceTransformerEmbedder,
    embed_backend,
    embed_model_name,
    get_query_embedder,
    reset_query_embedder_cache,
)


@pytest.fixture(autouse=True)
def _clear_embed_env(monkeypatch: pytest.MonkeyPatch):
    for key in (
        "RAG_EMBED_BACKEND",
        "RAG_EMBED_MODEL",
        "SILICONFLOW_API_KEY",
        "SILICONFLOW_BASE_URL",
    ):
        monkeypatch.delenv(key, raising=False)
    reset_query_embedder_cache()
    yield
    reset_query_embedder_cache()


def test_embed_backend_defaults_to_siliconflow(monkeypatch: pytest.MonkeyPatch):
    assert embed_backend() == "siliconflow"
    monkeypatch.setenv("RAG_EMBED_BACKEND", "")
    assert embed_backend() == "siliconflow"
    monkeypatch.setenv("RAG_EMBED_BACKEND", "local")
    assert embed_backend() == "local"
    monkeypatch.setenv("RAG_EMBED_BACKEND", "weird")
    assert embed_backend() == "siliconflow"


def test_embed_model_name_defaults_bge_m3(monkeypatch: pytest.MonkeyPatch):
    assert embed_model_name() == "BAAI/bge-m3"
    monkeypatch.setenv("RAG_EMBED_MODEL", "BAAI/bge-m3")
    assert embed_model_name() == "BAAI/bge-m3"


def test_get_query_embedder_siliconflow_no_sentence_transformer(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("SILICONFLOW_API_KEY", "sk-test")
    st_calls = {"n": 0}

    def _no_st(*_a, **_k):
        st_calls["n"] += 1
        raise AssertionError("must not construct SentenceTransformer on siliconflow path")

    monkeypatch.setattr(
        "sentence_transformers.SentenceTransformer",
        _no_st,
        raising=False,
    )
    # 延迟导入路径：patch 到 ST 类 _load 内会用的符号
    import sys

    fake_st = MagicMock()
    fake_st.SentenceTransformer = _no_st
    monkeypatch.setitem(sys.modules, "sentence_transformers", fake_st)

    emb = get_query_embedder()
    assert isinstance(emb, ApiEmbedder)
    assert emb.name == "BAAI/bge-m3"
    assert st_calls["n"] == 0


def test_api_embedder_preserves_index_order_and_dim(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("SILICONFLOW_API_KEY", "sk-test")
    monkeypatch.setenv("SILICONFLOW_BASE_URL", "https://api.example/v1")

    dim = 1024
    # 乱序 index：1 再 0
    payload = {
        "data": [
            {"index": 1, "embedding": [0.2] * dim},
            {"index": 0, "embedding": [0.1] * dim},
        ]
    }

    def _post(url, **kwargs):
        assert url.endswith("/embeddings")
        assert kwargs["json"]["model"] == "BAAI/bge-m3"
        assert kwargs["json"]["input"] == ["a", "b"]
        resp = MagicMock()
        resp.raise_for_status = MagicMock()
        resp.json = MagicMock(return_value=payload)
        return resp

    monkeypatch.setattr(embedder_mod.httpx, "post", _post)
    emb = ApiEmbedder(max_retries=1)
    out = emb.embed(["a", "b"])
    assert len(out) == 2
    assert out[0][0] == 0.1
    assert out[1][0] == 0.2
    assert len(out[0]) == dim


def test_api_embedder_missing_key_raises_no_st(monkeypatch: pytest.MonkeyPatch):
    st_calls = {"n": 0}

    def _no_st(*_a, **_k):
        st_calls["n"] += 1
        raise AssertionError("must not load ST when key missing")

    import sys

    fake_st = MagicMock()
    fake_st.SentenceTransformer = _no_st
    monkeypatch.setitem(sys.modules, "sentence_transformers", fake_st)

    with pytest.raises(RuntimeError, match="SILICONFLOW_API_KEY"):
        get_query_embedder()
    assert st_calls["n"] == 0


def test_api_embedder_http_failure_no_st_fallback(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("SILICONFLOW_API_KEY", "sk-test")
    monkeypatch.setattr(embedder_mod.time, "sleep", lambda *_a, **_k: None)

    def _boom(*_a, **_k):
        raise httpx.HTTPError("down")

    monkeypatch.setattr(embedder_mod.httpx, "post", _boom)

    emb = ApiEmbedder(max_retries=2)
    with pytest.raises(httpx.HTTPError):
        emb.embed(["q"])


def test_get_query_embedder_local_uses_stub(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("RAG_EMBED_BACKEND", "local")
    stub = MagicMock(spec=SentenceTransformerEmbedder)
    stub.name = "BAAI/bge-m3"
    stub.embed = MagicMock(return_value=[[0.5] * 8])

    constructed = {"n": 0}

    def _factory(*_a, **_k):
        constructed["n"] += 1
        return stub

    monkeypatch.setattr(embedder_mod, "SentenceTransformerEmbedder", _factory)
    emb = get_query_embedder()
    assert emb is stub
    assert constructed["n"] == 1
    assert emb.embed(["x"])[0][0] == 0.5


@pytest.mark.asyncio
async def test_rag_nodes_wiring_uses_factory(monkeypatch: pytest.MonkeyPatch):
    from app.ops.chat import rag_nodes

    fake = MagicMock()
    fake.embed = MagicMock(return_value=[[0.1] * 8])
    monkeypatch.setattr(rag_nodes, "_get_embedder", lambda: fake)

    class _CM:
        async def __aenter__(self):
            return MagicMock()

        async def __aexit__(self, *args):
            return None

    monkeypatch.setattr(rag_nodes, "AsyncSessionLocal", lambda: _CM())

    async def _hybrid(*_a, **_k):
        return []

    monkeypatch.setattr(rag_nodes, "hybrid_recall", _hybrid)
    monkeypatch.setattr(rag_nodes, "update_current_span_metadata", lambda *_a, **_k: None)
    monkeypatch.setattr(rag_nodes, "rerank_enabled", lambda: False)

    result = await rag_nodes.retrieve_node({"query": "hello"})
    fake.embed.assert_called_once_with(["hello"])
    assert result["retrieved"] == []


@pytest.mark.asyncio
async def test_lc_retrieve_wiring_uses_factory(monkeypatch: pytest.MonkeyPatch):
    from app.ops.lc_evidence_chain import retrieve as retrieve_mod

    fake = MagicMock()
    fake.embed = MagicMock(return_value=[[0.3] * 8])
    monkeypatch.setattr(retrieve_mod, "_get_embedder", lambda: fake)

    class _CM:
        async def __aenter__(self):
            return MagicMock()

        async def __aexit__(self, *args):
            return None

    monkeypatch.setattr(retrieve_mod, "AsyncSessionLocal", lambda: _CM())

    async def _hybrid(*_a, **_k):
        return []

    monkeypatch.setattr(retrieve_mod, "hybrid_recall", _hybrid)
    monkeypatch.setattr(retrieve_mod, "rerank_enabled", lambda: False)

    out = await retrieve_mod.retrieve_evidence("q")
    fake.embed.assert_called_once_with(["q"])
    assert out.evidence == []
