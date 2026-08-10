"""embedder 抽象（契约 Q3 · R-2 D1/D4）。

首选自部署 SentenceTransformerEmbedder；兜底托管 ApiEmbedder（Ink 实证路径：
SiliconFlow OpenAI 兼容接口）。替换只换实现，调用方不动。
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
    """托管兜底（OpenAI 兼容 /embeddings）。环境变量与 Ink 对齐。"""

    def __init__(
        self,
        model: str = BGE_M3_MODEL,
        base_url: str | None = None,
        api_key: str | None = None,
        max_retries: int = 3,
    ) -> None:
        self.name = model
        self._base = (
            base_url or os.getenv("SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1")
        ).rstrip("/")
        self._key = api_key or os.getenv("SILICONFLOW_API_KEY", "")
        if not self._key:
            raise RuntimeError("缺少 SILICONFLOW_API_KEY")
        self._max_retries = max_retries

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        payload = {"model": self.name, "input": texts}
        headers = {"Authorization": f"Bearer {self._key}"}
        for attempt in range(self._max_retries):
            try:
                resp = httpx.post(
                    f"{self._base}/embeddings", json=payload, headers=headers, timeout=60
                )
                resp.raise_for_status()
                data = resp.json()["data"]
                return [d["embedding"] for d in sorted(data, key=lambda d: d["index"])]
            except (httpx.HTTPError, KeyError) as exc:
                if attempt == self._max_retries - 1:
                    raise
                wait = 2**attempt
                logger.warning("embed 第 %d 次失败: %s；%ds 后重试", attempt + 1, exc, wait)
                time.sleep(wait)
        raise RuntimeError("unreachable")
