from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, computed_field

from app.ops.rag.grader import Relevance
from app.ops.rag.prefix import strip_doc_context_prefix
from app.ops.rag.retrieve import RetrievedChunk

SNIPPET_CHARS = 1200


class Grade(BaseModel):
    """证据项评级结果。``evidence_id`` = ``EvidenceItem.id``（同源库 chunk 主键）。

    与 LLM/rag.grader 线协议字段 ``chunk_id`` 不同名：那边指检索块；本模型挂在
    EvidenceItem 上，用 evidence_id 避免「evidence 算不算 chunk」的歧义。
    """

    evidence_id: int
    relevance: Relevance
    reason: str = ""

    @property
    def get_reason(self) -> str:
        return self.relevance.get_response() or self.reason


class EvidenceItem(BaseModel):
    id: int
    repo: str
    source_type: str
    source_id: str
    chunk_index: int
    content: str  # 原始内容（含前缀）
    metadata: dict[str, Any] = Field(default_factory=dict)
    # 与入库 jsonb 对齐：[{anchor, url, alt, kind}, ...]；兼容旧数据里的纯 URL 字符串
    images: list[Any] = Field(default_factory=list)
    semantic_rank: int | None = None
    keyword_rank: int | None = None
    rrf_score: float = 0.0
    rerank_score: float | None = None
    title: str | None = None
    url: str | None = None
    grade: Grade | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def anchor(self) -> str:
        return f"{self.source_id}#{self.chunk_index}"

    @property
    def snippet(self) -> str:
        return (strip_doc_context_prefix(self.content)[:SNIPPET_CHARS] or "").strip()

    @classmethod
    def from_retrieved_chunk(
        cls,
        chunk: RetrievedChunk,
        title: str | None = None,
        url: str | None = None,
    ) -> EvidenceItem:
        """将检索层数据转为契约证据项。"""
        meta = chunk.metadata or {}
        if title is None:
            title = ""
            for line in chunk.content.splitlines():
                if line.startswith("Title: "):
                    title = line[len("Title: ") :]
                    break
        if url is None:
            url = meta.get("html_url")
        return cls(
            id=chunk.id,
            repo=chunk.repo,
            source_type=chunk.source_type,
            source_id=chunk.source_id,
            chunk_index=chunk.chunk_index,
            content=chunk.content,
            metadata=meta,
            images=chunk.images or [],
            semantic_rank=chunk.semantic_rank,
            keyword_rank=chunk.keyword_rank,
            rrf_score=chunk.rrf_score,
            rerank_score=chunk.rerank_score,
            title=title or None,
            url=url,
        )


class GateDecision(BaseModel):
    """包内闸结果：过滤后的证据 + 答/拒动作（不依赖 rag.grader.decide）。"""

    kept: list[EvidenceItem]
    action: str  # refuse | answer_partial | answer
    best: Relevance
    grade_count: int = 0


class RetrieveResult(BaseModel):
    query: str
    evidence: list[EvidenceItem]


class ChainResult(BaseModel):
    query: str
    evidence: list[EvidenceItem]
    answer: str
    meta: dict[str, Any] = Field(default_factory=dict)
