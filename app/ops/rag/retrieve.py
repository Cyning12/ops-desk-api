"""R-3 混合召回（契约 §1 主路径：语义 + 关键词 → RRF 融合）。

- 语义路：pgvector cosine（HNSW 索引）
- 关键词路：PG tsvector（'simple' 配置 · 对应 BM25 角色，方案同构）
- 融合：RRF k=60，两路 1:1 起跑（契约 4c · Ink hybrid_fusion 实证）
- RRF 分数只进日志/返回体供观测，**不进闸**（契约 4b）
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

RRF_K = 60  # 契约 4c：与 Ink hybrid_fusion.RRF_K 对齐

_SEMANTIC_SQL = text(
    "SELECT id, repo, source_type, source_id, chunk_index, content, metadata, images "
    "FROM ops_knowledge_chunks "
    "ORDER BY embedding <=> CAST(:qvec AS vector) "
    "LIMIT :k"
)

_KEYWORD_SQL = text(
    "SELECT id, repo, source_type, source_id, chunk_index, content, metadata, images "
    "FROM ops_knowledge_chunks "
    "WHERE fts_tokens @@ plainto_tsquery('simple'::regconfig, CAST(:q AS text)) "
    "ORDER BY ts_rank(fts_tokens, plainto_tsquery('simple'::regconfig, CAST(:q AS text))) DESC "
    "LIMIT :k"
)


@dataclass
class RetrievedChunk:
    id: int
    repo: str
    source_type: str
    source_id: str
    chunk_index: int
    content: str  # 含前缀；展示时 strip（契约 §1b）
    metadata: dict = field(default_factory=dict)
    images: list = field(default_factory=list)
    semantic_rank: int | None = None
    keyword_rank: int | None = None
    rrf_score: float = 0.0

    @property
    def anchor(self) -> str:
        """golden 断言锚（契约 Q5）：source_id#chunk_index。"""
        return f"{self.source_id}#{self.chunk_index}"


def _row_to_chunk(row) -> RetrievedChunk:
    return RetrievedChunk(
        id=row.id,
        repo=row.repo,
        source_type=row.source_type,
        source_id=row.source_id,
        chunk_index=row.chunk_index,
        content=row.content,
        metadata=row.metadata or {},
        images=row.images or [],
    )


def rrf_fuse(
    semantic: list[RetrievedChunk],
    keyword: list[RetrievedChunk],
    top_n: int,
) -> list[RetrievedChunk]:
    """RRF 融合：score = Σ 1/(K + rank)，两路等权（契约 4c）。"""
    by_id: dict[int, RetrievedChunk] = {}
    for rank, chunk in enumerate(semantic, start=1):
        c = by_id.setdefault(chunk.id, chunk)
        c.semantic_rank = rank
        c.rrf_score += 1.0 / (RRF_K + rank)
    for rank, chunk in enumerate(keyword, start=1):
        c = by_id.setdefault(chunk.id, chunk)
        c.keyword_rank = rank
        c.rrf_score += 1.0 / (RRF_K + rank)
    return sorted(by_id.values(), key=lambda c: c.rrf_score, reverse=True)[:top_n]


@dataclass
class HybridRecallResult:
    """混合召回明细：融合前两路 + 融合后 top_n。"""

    fused: list[RetrievedChunk]
    semantic: list[RetrievedChunk]
    keyword: list[RetrievedChunk]


async def hybrid_recall_detail(
    session: AsyncSession,
    query: str,
    query_vector: list[float],
    k_each: int = 10,
    top_n: int = 5,
) -> HybridRecallResult:
    """混合召回（含融合前两路）；两路串行 await（AsyncSession 禁同会话并发）。"""
    sem_rows = await session.execute(
        _SEMANTIC_SQL, {"qvec": json.dumps(query_vector), "k": k_each}
    )
    kw_rows = await session.execute(_KEYWORD_SQL, {"q": query, "k": k_each})

    semantic = [_row_to_chunk(r) for r in sem_rows]
    keyword = [_row_to_chunk(r) for r in kw_rows]
    fused = rrf_fuse(semantic, keyword, top_n)
    logger.info(
        "hybrid_recall: query=%r semantic=%d keyword=%d fused=%d "
        "sem=%s kw=%s top=%s",
        query[:60],
        len(semantic),
        len(keyword),
        len(fused),
        [c.anchor for c in semantic],
        [c.anchor for c in keyword],
        [(c.anchor, round(c.rrf_score, 4), c.semantic_rank, c.keyword_rank) for c in fused],
    )
    return HybridRecallResult(fused=fused, semantic=semantic, keyword=keyword)


async def hybrid_recall(
    session: AsyncSession,
    query: str,
    query_vector: list[float],
    k_each: int = 10,
    top_n: int = 5,
) -> list[RetrievedChunk]:
    """混合召回入口：两路各取 k_each，RRF 融合后取 top_n（契约：grader 评 top-5）。"""
    return (
        await hybrid_recall_detail(session, query, query_vector, k_each=k_each, top_n=top_n)
    ).fused
