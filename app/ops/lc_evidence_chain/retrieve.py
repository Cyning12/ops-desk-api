from __future__ import annotations

import asyncio

from app.db.session import AsyncSessionLocal
from app.ops.lc_evidence_chain.types import EvidenceItem, RetrieveResult
from app.ops.rag.embedder import Embedder, get_query_embedder
from app.ops.rag.reranker import (
    recall_k_each,
    rerank_candidates,
    rerank_chunks,
    rerank_enabled,
)
from app.ops.rag.retrieve import hybrid_recall


def _get_embedder() -> Embedder:
    """查询侧工厂（默认 SiliconFlow；见 ``get_query_embedder``）。"""
    return get_query_embedder()


async def retrieve_evidence(query: str) -> RetrieveResult:
    embedder = _get_embedder()
    qvec = (await asyncio.to_thread(embedder.embed, [query]))[0]
    use_rerank = rerank_enabled()
    k_each = recall_k_each()
    top_n = rerank_candidates()

    async with AsyncSessionLocal() as session:
        coarse = await hybrid_recall(session, query, qvec, k_each=k_each, top_n=top_n)

    if use_rerank:
        chunks = await asyncio.to_thread(rerank_chunks, query, coarse, 5)
    else:
        chunks = coarse

    return RetrieveResult(
        query=query, evidence=[EvidenceItem.from_retrieved_chunk(c) for c in chunks]
    )
