"""R-3 检索增强节点：retrieve → grade → gate（契约 §1 主路径 / Q4 枚举闸）。

路由分工（2026-08-10 人定）：issue_qa 走 load_context 精确取数不动；
general / overview 一律走检索链（闲聊与语料外问题正是负样本拒答的演示面）。
闸失败语义（人定）：fail-closed 倒向拒答，日志区分「闸故障」与「真空命中」。
"""
from __future__ import annotations

import asyncio
import logging
import os

from app.db.session import AsyncSessionLocal
from app.llm.factory import get_llm_provider
from app.ops.chat.state import ChatState
from app.ops.rag.embedder import SentenceTransformerEmbedder
from app.ops.rag.grader import REFUSAL_TEXT, decide, grade_chunks
from app.ops.rag.prefix import strip_doc_context_prefix
from app.ops.rag.retrieve import RetrievedChunk, hybrid_recall
from app.ops.tracing import trace_span, update_current_span_metadata

logger = logging.getLogger(__name__)

GRADER_PROVIDER = os.getenv("RAG_GRADER_PROVIDER", "bailian")
GRADER_MODEL = os.getenv("RAG_GRADER_MODEL", "deepseek-v4-flash")  # 便宜款（契约 4b：每 query +1 次调用）

_embedder: SentenceTransformerEmbedder | None = None


def _get_embedder() -> SentenceTransformerEmbedder:
    """进程内单例 + 懒加载（契约 Q3：首次检索才加载 2.3GB 权重）。"""
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformerEmbedder()
    return _embedder


def _title_of(content: str) -> str:
    """从前缀行取标题（契约 §1b 前缀格式）。"""
    for line in content.splitlines():
        if line.startswith("Title: "):
            return line[len("Title: "):]
    return ""


def _to_source(c: RetrievedChunk, relevance: str) -> dict:
    """引用卡片（契约 4c）：snippet ≤400 字 · 剥前缀 · 用户面不展示分数。"""
    meta = c.metadata or {}
    return {
        "source_type": c.source_type,
        "source_id": c.source_id,
        "chunk_index": c.chunk_index,
        "anchor": c.anchor,
        "title": _title_of(c.content),
        "snippet": strip_doc_context_prefix(c.content)[:400],
        "url": meta.get("html_url"),
        "relevance": relevance,
    }


async def retrieve_node(state: ChatState) -> dict:
    """混合召回：bge-m3 嵌 query → pgvector 语义 + tsvector 关键词 → RRF top-5。"""
    query = state["query"]
    qvec = (await asyncio.to_thread(_get_embedder().embed, [query]))[0]
    async with AsyncSessionLocal() as session:
        chunks = await hybrid_recall(session, query, qvec)
    # 契约 4b：RRF 分数进观测/日志，不进闸
    update_current_span_metadata(
        {
            "hits": [
                {
                    "anchor": c.anchor,
                    "rrf": round(c.rrf_score, 4),
                    "sem_rank": c.semantic_rank,
                    "kw_rank": c.keyword_rank,
                }
                for c in chunks
            ]
        }
    )
    return {
        "retrieved": chunks,
        "events": [
            {
                "event_type": "tool_result",
                "agent_role": "retrieve",
                "payload": {
                    "tool": "retrieve",
                    "ok": bool(chunks),
                    "hits": [c.anchor for c in chunks],
                },
            }
        ],
    }


async def grade_node(state: ChatState) -> dict:
    """枚举评级闸：top-5 批量评级 → decide 三分支；fail-closed。"""
    chunks: list[RetrievedChunk] = state.get("retrieved") or []
    if not chunks:
        logger.info("gate refuse: 真空命中（召回为空）query=%r", state["query"][:60])
        return _gate_result(state, action="refuse", grades=[], chunks=[], rated=False)

    provider = get_llm_provider(GRADER_PROVIDER)
    try:
        with trace_span("grade_llm", run_type="llm", model=GRADER_MODEL):
            grades = await grade_chunks(provider, state["query"], chunks, model=GRADER_MODEL)
        decision = decide(grades)
        action = decision.action
        best = decision.best.value
    except Exception as exc:
        # fail-closed：闸故障倒向拒答；与真空命中在日志层面分流
        logger.exception("gate refuse: 闸故障（fail-closed）query=%r err=%s", state["query"][:60], exc)
        grades = []
        action = "refuse"
        best = "grader_error"

    update_current_span_metadata({"gate_action": action, "best_relevance": best})
    return _gate_result(state, action=action, grades=grades, chunks=chunks, rated=bool(grades))


def _gate_result(
    state: ChatState, *, action: str, grades: list, chunks: list[RetrievedChunk],
    rated: bool = True,
) -> dict:
    relevance_map = {g.chunk_id: g.relevance.value for g in grades}
    # grader 未评（故障/空召回）时标 unrated，不误报 weak（闸故障 ≠ 证据弱）
    default_rel = "weak" if rated else "unrated"
    sources = [_to_source(c, relevance_map.get(c.id, default_rel)) for c in chunks]
    return {
        "gate_action": action,
        "sources": sources,
        "events": [
            {
                "event_type": "tool_result",
                "agent_role": "grade",
                "payload": {
                    "tool": "grade",
                    "gate_action": action,
                    "grades": [
                        {"chunk_id": g.chunk_id, "relevance": g.relevance.value, "reason": g.reason}
                        for g in grades
                    ],
                    "sources": sources,
                },
            }
        ],
    }


def route_by_gate(state: ChatState) -> str:
    """条件边：refuse → 拒答节点；answer / answer_partial → 生成。"""
    return "refuse" if state.get("gate_action") == "refuse" else "generate_answer"


async def refuse_node(state: ChatState) -> dict:
    """拒答：不调 LLM，直接回契约话术（契约 4c）。"""
    return {
        "answer": REFUSAL_TEXT,
        "events": [
            {
                "event_type": "answer",
                "agent_role": "answer",
                "payload": {"content": REFUSAL_TEXT, "refused": True},
            }
        ],
    }
