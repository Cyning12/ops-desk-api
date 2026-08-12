"""R-3 混合召回（契约 §1 主路径：语义 + 第二路 → RRF 融合）。

- 语义路：pgvector cosine（HNSW 索引）
- 第二路（默认 FTS）：PG tsvector（默认 'simple'；可用 RAG_FTS_CONFIG 切到 chinese 等）
- 第二路（C 臂）：`RAG_SECOND_PATH=sparse` 时走 `sparse_embedding`（pgvector sparsevec 内积）
- 融合：RRF k=60，两路 1:1 起跑（契约 4c · Ink hybrid_fusion 实证）
- RRF 分数只进日志/返回体供观测，**不进闸**（契约 4b）
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from dataclasses import dataclass, field

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.ops.rag.glossary import expand_query_for_fts

logger = logging.getLogger(__name__)

RRF_K = 60  # 契约 4c：与 Ink hybrid_fusion.RRF_K 对齐

# text search config 标识符（防 SQL 注入；非法则回退 simple）
_FTS_CONFIG_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

_SEMANTIC_SQL = text(
    "SELECT id, repo, source_type, source_id, chunk_index, content, metadata, images "
    "FROM ops_knowledge_chunks "
    "ORDER BY embedding <=> CAST(:qvec AS vector) "
    "LIMIT :k"
)

# C 臂：<# > = negative inner product；ASC → 相似度高者优先（与 dense 内积索引同惯例）
_SPARSE_SQL = text(
    "SELECT id, repo, source_type, source_id, chunk_index, content, metadata, images "
    "FROM ops_knowledge_chunks "
    "WHERE sparse_embedding IS NOT NULL "
    "ORDER BY sparse_embedding <#> CAST(:qsparse AS sparsevec) "
    "LIMIT :k"
)


def _fts_config() -> str:
    """关键词路 regconfig：env RAG_FTS_CONFIG，默认 simple（生产）；影子 A 臂可设 chinese。"""
    raw = (os.getenv("RAG_FTS_CONFIG") or "simple").strip() or "simple"
    if not _FTS_CONFIG_RE.fullmatch(raw):
        logger.warning("invalid RAG_FTS_CONFIG=%r; fallback to simple", raw)
        return "simple"
    return raw


def _second_path() -> str:
    """第二路：fts（默认，现网）| sparse（C 臂）。非法值回退 fts。"""
    raw = (os.getenv("RAG_SECOND_PATH") or "fts").strip().lower() or "fts"
    if raw not in ("fts", "sparse"):
        logger.warning("invalid RAG_SECOND_PATH=%r; fallback to fts", raw)
        return "fts"
    return raw


def _keyword_sql_plain(cfg: str):
    return text(
        "SELECT id, repo, source_type, source_id, chunk_index, content, metadata, images "
        "FROM ops_knowledge_chunks "
        f"WHERE fts_tokens @@ plainto_tsquery('{cfg}'::regconfig, CAST(:q AS text)) "
        f"ORDER BY ts_rank(fts_tokens, plainto_tsquery('{cfg}'::regconfig, CAST(:q AS text))) DESC "
        "LIMIT :k"
    )


def _keyword_sql_expanded(cfg: str):
    # 方案 D（glossary 展开 · env RAG_KW_EXPAND=true 启用）：组内 OR 组间 AND
    return text(
        "SELECT id, repo, source_type, source_id, chunk_index, content, metadata, images "
        "FROM ops_knowledge_chunks "
        f"WHERE fts_tokens @@ to_tsquery('{cfg}'::regconfig, CAST(:q AS text)) "
        f"ORDER BY ts_rank(fts_tokens, to_tsquery('{cfg}'::regconfig, CAST(:q AS text))) DESC "
        "LIMIT :k"
    )


def _keyword_query(query: str):
    """关键词路查询构造：默认 plainto_tsquery 原文；RAG_KW_EXPAND=true 时走 glossary 展开。

    返回 (SQL 对象, 查询参数)。展开无可用词项时回退原文查询。
    regconfig 由 RAG_FTS_CONFIG 决定（默认 simple）。
    """
    cfg = _fts_config()
    if os.getenv("RAG_KW_EXPAND", "").strip().lower() in ("1", "true", "yes"):
        expanded = expand_query_for_fts(query)
        if expanded:
            return _keyword_sql_expanded(cfg), expanded
    return _keyword_sql_plain(cfg), query


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
    query_sparse: str | None = None,
) -> HybridRecallResult:
    """混合召回（含融合前两路）；两路串行 await（AsyncSession 禁同会话并发）。

    `query_sparse`：可选预编码的 sparsevec 文本；`RAG_SECOND_PATH=sparse` 且未传时
    进程内懒加载 FlagEmbedding 编码（实验依赖，默认 fts 路径不触达）。
    """
    sem_rows = await session.execute(
        _SEMANTIC_SQL, {"qvec": json.dumps(query_vector), "k": k_each}
    )
    path = _second_path()
    if path == "sparse":
        svec = query_sparse
        if svec is None:
            from app.ops.rag.sparse_vec import encode_query_sparse

            svec = await asyncio.to_thread(encode_query_sparse, query)
        kw_rows = await session.execute(_SPARSE_SQL, {"qsparse": svec, "k": k_each})
    else:
        kw_sql, kw_param = _keyword_query(query)
        kw_rows = await session.execute(kw_sql, {"q": kw_param, "k": k_each})

    semantic = [_row_to_chunk(r) for r in sem_rows]
    keyword = [_row_to_chunk(r) for r in kw_rows]
    fused = rrf_fuse(semantic, keyword, top_n)
    logger.info(
        "hybrid_recall: path=%s query=%r semantic=%d keyword=%d fused=%d "
        "sem=%s kw=%s top=%s",
        path,
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
    query_sparse: str | None = None,
) -> list[RetrievedChunk]:
    """混合召回入口：两路各取 k_each，RRF 融合后取 top_n（契约：grader 评 top-5）。"""
    return (
        await hybrid_recall_detail(
            session,
            query,
            query_vector,
            k_each=k_each,
            top_n=top_n,
            query_sparse=query_sparse,
        )
    ).fused
