"""Qdrant 稠密检索 + PG hydrate（禁止从 Qdrant 读 content/metadata/images）。"""
from __future__ import annotations

import logging
from typing import Any

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qm
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.ops.rag.backend import qdrant_api_key, qdrant_collection, qdrant_hnsw_ef, qdrant_url
from app.ops.rag.retrieve import RetrievedChunk
from app.ops.rag.retrievers.base import BaseRetriever

logger = logging.getLogger(__name__)

_HYDRATE_SQL = text(
    "SELECT id, repo, source_type, source_id, chunk_index, content, metadata, images "
    "FROM ops_knowledge_chunks WHERE id = ANY(:ids)"
)


class QdrantRetriever(BaseRetriever):
    def __init__(
        self,
        session: AsyncSession,
        *,
        url: str | None = None,
        collection: str | None = None,
        api_key: str | None = None,
        ef: int | None = None,
        client: AsyncQdrantClient | None = None,
    ) -> None:
        self._session = session
        self._url = url or qdrant_url()
        self._collection = collection or qdrant_collection()
        self._api_key = api_key if api_key is not None else qdrant_api_key()
        self._ef = ef if ef is not None else qdrant_hnsw_ef()
        self._client = client

    def _get_client(self) -> AsyncQdrantClient:
        if self._client is None:
            self._client = AsyncQdrantClient(url=self._url, api_key=self._api_key)
        return self._client

    async def _reconnect(self) -> None:
        if self._client is not None:
            try:
                await self._client.close()
            except Exception:
                logger.debug("qdrant client close failed", exc_info=True)
        self._client = None
        self._get_client()

    def _build_filter(self, filters: dict[str, Any] | None) -> qm.Filter | None:
        if not filters:
            return None
        must = [
            qm.FieldCondition(key=k, match=qm.MatchValue(value=v))
            for k, v in filters.items()
        ]
        return qm.Filter(must=must)

    async def _search_hits(
        self,
        query_vector: list[float],
        *,
        k: int,
        query_filter: qm.Filter | None,
    ) -> list[Any]:
        client = self._get_client()
        return await client.search(
            collection_name=self._collection,
            query_vector=query_vector,
            query_filter=query_filter,
            limit=k,
            with_payload=True,  # 仅含 filter 小字段
            with_vectors=False,
            search_params=qm.SearchParams(hnsw_ef=self._ef),
        )

    async def search(
        self,
        query_vector: list[float],
        *,
        k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[RetrievedChunk]:
        query_filter = self._build_filter(filters)
        try:
            hits = await self._search_hits(query_vector, k=k, query_filter=query_filter)
        except Exception:
            await self._reconnect()
            hits = await self._search_hits(query_vector, k=k, query_filter=query_filter)

        ids = [int(h.id) for h in hits]
        if not ids:
            return []

        rows = (await self._session.execute(_HYDRATE_SQL, {"ids": ids})).all()
        by_id = {int(r.id): r for r in rows}
        out: list[RetrievedChunk] = []
        for hid in ids:
            r = by_id.get(hid)
            if r is None:
                logger.warning("qdrant hit id=%s missing in PG hydrate", hid)
                continue
            out.append(
                RetrievedChunk(
                    id=r.id,
                    repo=r.repo,
                    source_type=r.source_type,
                    source_id=r.source_id,
                    chunk_index=r.chunk_index,
                    content=r.content,
                    metadata=r.metadata or {},
                    images=r.images or [],
                )
            )
        return out
