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
DEFAULT_EMBED_API_BATCH_SIZE = 128  # 签注裁定钉死（safe zone ≈500 的 1/4 · ~4s/批 << timeout 60s）


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
        batch_size: int | None = None,
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
        if batch_size is not None and batch_size <= 0:
            logger.warning(
                "invalid batch_size=%d; fallback to %d",
                batch_size,
                DEFAULT_EMBED_API_BATCH_SIZE,
            )
            batch_size = None
        self._batch_size = (
            batch_size if batch_size is not None else _embed_api_batch_size()
        )

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        # 内部批切：≤batch_size 逐批 POST，跨批保序拼接（ingest zip strict 强依赖）；
        # ≤batch_size 时恰一批发出，payload 与批切前逐字节等价。
        batches = [
            texts[i : i + self._batch_size]
            for i in range(0, len(texts), self._batch_size)
        ]
        total = len(batches)
        started = time.monotonic()
        vectors: list[list[float]] = []
        for i, batch in enumerate(batches, 1):
            t0 = time.monotonic()
            # 批级失败纪律 fail-fast：批内重试耗尽即整单 raise，不缓存/不部分返回
            vectors.extend(self._embed_batch(batch))
            logger.info(
                "embed batch %d/%d: %d chunks in %.1fs",
                i,
                total,
                len(batch),
                time.monotonic() - t0,
            )
        elapsed = time.monotonic() - started
        logger.info(
            "embed done: %d chunks in %d batches, %.1fs total (%.1f chunks/s)",
            len(texts),
            total,
            elapsed,
            len(texts) / elapsed if elapsed > 0 else 0.0,
        )
        return vectors

    def _embed_batch(self, texts: list[str]) -> list[list[float]]:
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


def _embed_api_batch_size() -> int:
    """RAG_EMBED_API_BATCH_SIZE 解析：未设/空 → 默认 128；非法/≤0 → warning + 回退默认
    （承 embed_backend env 解析先例）。"""
    raw = (os.getenv("RAG_EMBED_API_BATCH_SIZE") or "").strip()
    if not raw:
        return DEFAULT_EMBED_API_BATCH_SIZE
    try:
        value = int(raw)
    except ValueError:
        value = -1
    if value <= 0:
        logger.warning(
            "invalid RAG_EMBED_API_BATCH_SIZE=%r; fallback to %d",
            raw,
            DEFAULT_EMBED_API_BATCH_SIZE,
        )
        return DEFAULT_EMBED_API_BATCH_SIZE
    return value


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
