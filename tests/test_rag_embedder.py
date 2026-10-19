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


# ---------- ApiEmbedder 内部批切（task_api_embedder_internal_batching · 红测先行） ----------


def _batch_payload(n: int, dim: int = 1024, shuffle: bool = False):
    """构造 n 条响应 data；shuffle=True 时乱序 index（跨批保序断言用）。"""

    def _payload(batch_start: int):
        idxs = list(range(n))
        if shuffle:
            idxs = idxs[::-1]
        return {
            "data": [
                {"index": i, "embedding": [float(batch_start + i)] * dim} for i in idxs
            ]
        }

    return _payload


def test_api_embedder_splits_into_batches(monkeypatch: pytest.MonkeyPatch):
    """多批切分：5 条 · batch_size=2 → 3 次 POST，各批 input 切片正确。"""
    monkeypatch.setenv("SILICONFLOW_API_KEY", "sk-test")
    calls: list[list[str]] = []

    def _post(url, **kwargs):
        batch = kwargs["json"]["input"]
        calls.append(list(batch))
        resp = MagicMock()
        resp.raise_for_status = MagicMock()
        n = len(batch)
        start = len([t for c in calls[:-1] for t in c])
        resp.json = MagicMock(
            return_value={
                "data": [
                    {"index": i, "embedding": [float(start + i)] * 1024}
                    for i in range(n)
                ]
            }
        )
        return resp

    monkeypatch.setattr(embedder_mod.httpx, "post", _post)
    emb = ApiEmbedder(max_retries=1, batch_size=2)
    out = emb.embed(["a", "b", "c", "d", "e"])
    assert calls == [["a", "b"], ["c", "d"], ["e"]]  # ceil(5/2)==3 批 · 切片正确
    assert len(out) == 5
    assert [v[0] for v in out] == [0.0, 1.0, 2.0, 3.0, 4.0]


def test_api_embedder_cross_batch_order_preserved(monkeypatch: pytest.MonkeyPatch):
    """跨批保序：各批响应乱序 index，拼接后全序仍与输入序一致（ingest zip strict 依赖）。"""
    monkeypatch.setenv("SILICONFLOW_API_KEY", "sk-test")
    seen: list[list[str]] = []

    def _post(url, **kwargs):
        batch = kwargs["json"]["input"]
        seen.append(list(batch))
        resp = MagicMock()
        resp.raise_for_status = MagicMock()
        # 批内乱序返回 index
        resp.json = MagicMock(
            return_value={
                "data": [
                    {"index": i, "embedding": [float(ord(t))] * 1024}
                    for i, t in reversed(list(enumerate(batch)))
                ]
            }
        )
        return resp

    monkeypatch.setattr(embedder_mod.httpx, "post", _post)
    emb = ApiEmbedder(max_retries=1, batch_size=2)
    texts = ["a", "b", "c", "d", "e"]
    out = emb.embed(texts)
    assert seen == [["a", "b"], ["c", "d"], ["e"]]
    assert len(out) == len(texts)
    assert [v[0] for v in out] == [float(ord(t)) for t in texts]


def test_api_embedder_batch_size_default_and_env(monkeypatch: pytest.MonkeyPatch):
    """配置解析：默认钉死 128 · env 生效 · 非法/≤0 回退默认+warning · 构造参数优先于 env。"""
    monkeypatch.setenv("SILICONFLOW_API_KEY", "sk-test")
    monkeypatch.delenv("RAG_EMBED_API_BATCH_SIZE", raising=False)
    assert ApiEmbedder()._batch_size == 128

    monkeypatch.setenv("RAG_EMBED_API_BATCH_SIZE", " 7 ")
    assert ApiEmbedder()._batch_size == 7

    for bad in ("abc", "0", "-5", "3.5"):
        monkeypatch.setenv("RAG_EMBED_API_BATCH_SIZE", bad)
        assert ApiEmbedder()._batch_size == 128

    # 构造参数优先于 env
    monkeypatch.setenv("RAG_EMBED_API_BATCH_SIZE", "7")
    assert ApiEmbedder(batch_size=3)._batch_size == 3
    # 构造参数非法（≤0）→ warning + 视为未设，沿链回退（env 未设落默认 128 · 已设落 env）
    monkeypatch.delenv("RAG_EMBED_API_BATCH_SIZE", raising=False)
    assert ApiEmbedder(batch_size=0)._batch_size == 128
    monkeypatch.setenv("RAG_EMBED_API_BATCH_SIZE", "7")
    assert ApiEmbedder(batch_size=0)._batch_size == 7


def test_api_embedder_invalid_batch_size_env_warns(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
):
    monkeypatch.setenv("SILICONFLOW_API_KEY", "sk-test")
    monkeypatch.setenv("RAG_EMBED_API_BATCH_SIZE", "abc")
    with caplog.at_level("WARNING", logger="app.ops.rag.embedder"):
        emb = ApiEmbedder()
    assert emb._batch_size == 128
    assert any("RAG_EMBED_API_BATCH_SIZE" in r.message for r in caplog.records)


def test_api_embedder_batch_failure_fails_fast(monkeypatch: pytest.MonkeyPatch):
    """失败纪律 fail-fast：中间批重试耗尽 → 整单 raise · 不部分返回。"""
    monkeypatch.setenv("SILICONFLOW_API_KEY", "sk-test")
    monkeypatch.setattr(embedder_mod.time, "sleep", lambda *_a, **_k: None)
    calls = {"n": 0}

    def _post(url, **kwargs):
        calls["n"] += 1
        batch = kwargs["json"]["input"]
        if batch[0] == "c":  # 第二批永远失败
            raise httpx.HTTPError("batch boom")
        resp = MagicMock()
        resp.raise_for_status = MagicMock()
        resp.json = MagicMock(
            return_value={
                "data": [
                    {"index": i, "embedding": [0.1] * 1024} for i in range(len(batch))
                ]
            }
        )
        return resp

    monkeypatch.setattr(embedder_mod.httpx, "post", _post)
    emb = ApiEmbedder(max_retries=2, batch_size=2)
    with pytest.raises(httpx.HTTPError):
        emb.embed(["a", "b", "c", "d"])
    # 第一批 1 次成功 + 第二批 2 次重试耗尽 = 3 次；后续批不再发起
    assert calls["n"] == 3


def test_api_embedder_small_payload_byte_equivalent(monkeypatch: pytest.MonkeyPatch):
    """小规模等价：≤batch_size 输入 POST 次数==1 且 payload 与批切前逐字节等价。"""
    monkeypatch.setenv("SILICONFLOW_API_KEY", "sk-test")
    monkeypatch.delenv("RAG_EMBED_API_BATCH_SIZE", raising=False)
    calls: list[dict] = []

    def _post(url, **kwargs):
        calls.append(kwargs["json"])
        resp = MagicMock()
        resp.raise_for_status = MagicMock()
        resp.json = MagicMock(
            return_value={
                "data": [{"index": 0, "embedding": [0.1] * 1024}]
            }
        )
        return resp

    monkeypatch.setattr(embedder_mod.httpx, "post", _post)
    emb = ApiEmbedder(max_retries=1)
    out = emb.embed(["q"])
    assert calls == [{"model": "BAAI/bge-m3", "input": ["q"]}]  # 逐字节等价原 payload 形态
    assert len(out) == 1
