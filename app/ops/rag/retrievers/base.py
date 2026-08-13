"""检索器抽象基类。"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.ops.rag.retrieve import RetrievedChunk


class BaseRetriever(ABC):
    """稠密向量检索器：返回已 hydrate 的 RetrievedChunk。"""

    @abstractmethod
    async def search(
        self,
        query_vector: list[float],
        *,
        k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[RetrievedChunk]:
        raise NotImplementedError
