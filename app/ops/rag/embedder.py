"""embedder 抽象（契约 Q3 · R-2 D1/D4）。

查询路径默认 ``ApiEmbedder``（SiliconFlow OpenAI 兼容 ``/embeddings``），
消除生产小机本地 bge-m3 冷启动；``RAG_EMBED_BACKEND=local`` 显式切回
``SentenceTransformerEmbedder``。ingest CLI 仍可独立选本地/API，本模块工厂仅服务查询侧。

``name`` 作为 fingerprint 戳写进 chunk metadata——防换模型后新旧向量混库
的静默腐烂（Ink rag_embedding_guard 教训）。
"""

from __future__ import annotations

import logging
import os
import time
from typing import Protocol

import httpx

logger = logging.getLogger(__name__)

BGE_M3_MODEL = "BAAI/bge-m3"
DEFAULT_EMBED_BACKEND = "siliconflow"
DEFAULT_SILICONFLOW_BASE = "https://api.siliconflow.cn/v1"


class Embedder(Protocol):
    name: str

    def embed(self, texts: list[str]) -> list[list[float]]: ...


class SentenceTransformerEmbedder:
    """bge-m3 自部署。懒加载：首次 embed 才加载 ~2.3GB 权重（契约 Q3 风险注记）。"""

    def __init__(self, model_name: str = BGE_M3_MODEL, batch_size: int = 32):
        self.name = model_name
        self._batch_size = batch_size
        self._model = None

    def _load(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer  # 延迟导入，保持模块轻量

            logger.info("loading embedding model %s ...", self.name)
            self._model = SentenceTransformer(self.name)
        return self._model

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        filtered = [t for t in texts if t and t.strip()]
        if not filtered:
            return []
        vectors = self._load().encode(
            texts,
            batch_size=self._batch_size,
            normalize_embeddings=True,  # 归一化后 cosine 等价点积；pgvector cosine 语义无差
            show_progress_bar=len(texts) > self._batch_size,
        )
        return [v.tolist() for v in vectors]


class ApiEmbedder:
    """托管嵌入（OpenAI 兼容 /embeddings）。环境变量与精排 SiliconFlow 对齐。"""

    def __init__(
        self,
        model: str = BGE_M3_MODEL,
        base_url: str | None = None,
        api_key: str | None = None,
        max_retries: int = 3,
    ) -> None:
        self.name = model
        self._base = (
            base_url or os.getenv("SILICONFLOW_BASE_URL", DEFAULT_SILICONFLOW_BASE)
        ).rstrip("/")
        self._key = api_key if api_key is not None else os.getenv("SILICONFLOW_API_KEY", "")
        if not self._key:
            logger.error("ApiEmbedder missing SILICONFLOW_API_KEY; refusing local ST fallback")
            raise RuntimeError("缺少 SILICONFLOW_API_KEY")
        self._max_retries = max_retries

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        payload = {"model": self.name, "input": texts}
        headers = {"Authorization": f"Bearer {self._key}"}
        last_exc: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                resp = httpx.post(
                    f"{self._base}/embeddings", json=payload, headers=headers, timeout=60
                )
                resp.raise_for_status()
                data = resp.json()["data"]
                return [d["embedding"] for d in sorted(data, key=lambda d: d["index"])]
            except (httpx.HTTPError, KeyError, TypeError) as exc:
                last_exc = exc
                if attempt == self._max_retries - 1:
                    logger.error(
                        "embed HTTP failed after %d attempts (no local ST fallback): %s",
                        self._max_retries,
                        exc,
                    )
                    raise
                wait = 2**attempt
                logger.warning("embed 第 %d 次失败: %s；%ds 后重试", attempt + 1, exc, wait)
                time.sleep(wait)
        raise RuntimeError(f"embed failed: {last_exc}")


def embed_backend() -> str:
    """查询嵌入后端：``siliconflow``（默认，含空/未设）或 ``local``。"""
    raw = (os.getenv("RAG_EMBED_BACKEND") or "").strip().lower()
    if not raw:
        return DEFAULT_EMBED_BACKEND
    if raw in ("siliconflow", "local"):
        return raw
    logger.warning(
        "invalid RAG_EMBED_BACKEND=%r; fallback to %s",
        raw,
        DEFAULT_EMBED_BACKEND,
    )
    return DEFAULT_EMBED_BACKEND


def embed_model_name() -> str:
    """查询/API 模型名；默认 ``BAAI/bge-m3``（须与库 fingerprint 一致）。"""
    raw = (os.getenv("RAG_EMBED_MODEL") or BGE_M3_MODEL).strip()
    return raw or BGE_M3_MODEL


_query_embedder: Embedder | None = None
_query_embedder_backend: str | None = None
_query_embedder_model: str | None = None


def reset_query_embedder_cache() -> None:
    """测试用：清空查询侧 embedder 单例。"""
    global _query_embedder, _query_embedder_backend, _query_embedder_model
    _query_embedder = None
    _query_embedder_backend = None
    _query_embedder_model = None


def get_query_embedder() -> Embedder:
    """查询路径工厂：默认 SiliconFlow ``ApiEmbedder``；``local`` 才加载 ST。

    失败不隐式回落本地 ST（避免再次引入冷启动）。缺 key / HTTP 错误向上抛出。
    """
    global _query_embedder, _query_embedder_backend, _query_embedder_model
    backend = embed_backend()
    model = embed_model_name()
    if (
        _query_embedder is not None
        and _query_embedder_backend == backend
        and _query_embedder_model == model
    ):
        return _query_embedder

    if backend == "local":
        logger.info("query embedder backend=local model=%s", model)
        embedder: Embedder = SentenceTransformerEmbedder(model_name=model)
    else:
        logger.info("query embedder backend=siliconflow model=%s", model)
        embedder = ApiEmbedder(model=model)

    _query_embedder = embedder
    _query_embedder_backend = backend
    _query_embedder_model = model
    return embedder
