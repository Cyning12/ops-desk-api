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
    rerank_model_name,
)
from app.ops.rag.retrieve import hybrid_recall
from app.ops.tracing import trace_span


def _get_embedder() -> Embedder:
    """查询侧工厂（默认 SiliconFlow；见 ``get_query_embedder``）。"""
    return get_query_embedder()


async def retrieve_evidence(query: str) -> RetrieveResult:
    embedder = _get_embedder()
    # 自研 ApiEmbedder 不走 LangChain，CallbackHandler 抓不到 → 显式 generation
    with trace_span("query_embed", run_type="llm", model=embedder.name):
        qvec = (await asyncio.to_thread(embedder.embed, [query]))[0]
    use_rerank = rerank_enabled()
    k_each = recall_k_each()
    top_n = rerank_candidates()

    async with AsyncSessionLocal() as session:
        coarse = await hybrid_recall(session, query, qvec, k_each=k_each, top_n=top_n)

    if use_rerank:
        with trace_span("rerank", run_type="llm", model=rerank_model_name()):
            chunks = await asyncio.to_thread(rerank_chunks, query, coarse, 5)
    else:
        chunks = coarse

    return RetrieveResult(
        query=query, evidence=[EvidenceItem.from_retrieved_chunk(c) for c in chunks]
    )
