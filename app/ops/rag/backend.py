"""稠密向量后端 Flag + 即时降级（SPEC-qdrant-migration v1.1）。

默认 qdrant；失败即时回退 pgvector。禁止跨进程 fail_streak 作唯一熔断。
"""
from __future__ import annotations

import logging
import os
from collections.abc import Awaitable, Callable
from enum import StrEnum
from typing import TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

# 观测计数（进程内；非跨 worker 熔断）
rag_vector_backend_fallback_total = 0


class VectorBackend(StrEnum):
    PGVECTOR = "pgvector"
    QDRANT = "qdrant"


def vector_backend() -> VectorBackend:
    raw = (os.getenv("RAG_VECTOR_BACKEND") or "qdrant").strip().lower()
    if raw not in ("pgvector", "qdrant"):
        logger.warning("invalid RAG_VECTOR_BACKEND=%r; fallback to qdrant", raw)
        return VectorBackend.QDRANT
    return VectorBackend(raw)


def qdrant_url() -> str:
    return (os.getenv("QDRANT_URL") or "http://127.0.0.1:6333").strip()


def qdrant_collection() -> str:
    return (os.getenv("QDRANT_COLLECTION") or "ops_knowledge").strip() or "ops_knowledge"


def qdrant_api_key() -> str | None:
    raw = (os.getenv("QDRANT_API_KEY") or "").strip()
    return raw or None


def qdrant_hnsw_ef() -> int:
    """查询期 HNSW ef（SearchParams.hnsw_ef）。默认 30（延迟优先；原 64）。"""
    raw = (os.getenv("QDRANT_HNSW_EF") or "30").strip()
    try:
        value = int(raw)
    except ValueError:
        return 30
    return value if value > 0 else 30


async def search_dense_with_fallback(
    qdrant_search: Callable[[], Awaitable[T]],
    pg_search: Callable[[], Awaitable[T]],
) -> T:
    """Qdrant 最多再试 1 次；仍失败则本请求立刻走 PG。"""
    global rag_vector_backend_fallback_total
    if vector_backend() != VectorBackend.QDRANT:
        return await pg_search()
    last_exc: Exception | None = None
    for attempt in range(2):
        try:
            return await qdrant_search()
        except Exception as exc:
            last_exc = exc
            logger.warning("qdrant search failed attempt=%s err=%s", attempt + 1, exc)
    rag_vector_backend_fallback_total += 1
    logger.error(
        "qdrant fallback to pgvector fallback_total=%s err=%s",
        rag_vector_backend_fallback_total,
        last_exc,
    )
    return await pg_search()
