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
from app.llm.model_catalog import resolve_task_model
from app.llm.usage import use_run_context
from app.ops.chat.state import ChatState
from app.ops.rag.embedder import Embedder, get_query_embedder
from app.ops.rag.grader import REFUSAL_TEXT, decide, grade_chunks
from app.ops.rag.prefix import strip_doc_context_prefix
from app.ops.rag.reranker import (
    recall_k_each,
    rerank_candidates,
    rerank_chunks,
    rerank_enabled,
    rerank_min_score,
    rerank_score_ratio,
)
from app.ops.rag.retrieve import RetrievedChunk, hybrid_recall
from app.ops.tracing import trace_span, update_current_span_metadata

logger = logging.getLogger(__name__)

GRADER_PROVIDER = os.getenv("RAG_GRADER_PROVIDER", "siliconflow")
# 兼容常量：evals/golden/run_eval.py 仍 import 本名；运行期解析走
# resolve_task_model("grader")（OPS_LLM_TIER_GRADER_MODEL > RAG_GRADER_MODEL > 档默认）
GRADER_MODEL = os.getenv("RAG_GRADER_MODEL", "Qwen/Qwen3.6-27B")  # 契约 4b：每 query +1 次调用


def _get_embedder() -> Embedder:
    """查询侧工厂（默认 SiliconFlow ApiEmbedder；``RAG_EMBED_BACKEND=local`` 才加载 ST）。"""
    return get_query_embedder()


def _title_of(content: str) -> str:
    """从前缀行取标题（契约 §1b 前缀格式）。"""
    for line in content.splitlines():
        if line.startswith("Title: "):
            return line[len("Title: ") :]
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
    """混合召回：bge-m3 嵌 query → 语义+第二路 RRF →（可选）CE 精排 → top-5。"""
    with trace_span("retrieve", run_type="retriever"):
        query = state["query"]
        qvec = (await asyncio.to_thread(_get_embedder().embed, [query]))[0]
        use_rerank = rerank_enabled()
        k_each = recall_k_each() if use_rerank else 10
        top_n = rerank_candidates() if use_rerank else 5
        async with AsyncSessionLocal() as session:
            coarse = await hybrid_recall(session, query, qvec, k_each=k_each, top_n=top_n)
        rrf_top = list(coarse)
        if use_rerank:
            chunks = await asyncio.to_thread(rerank_chunks, query, coarse, 5)
        else:
            chunks = coarse
        # 契约 4b：RRF/rerank 分数进观测/日志，不进闸
        meta: dict = {
            "rerank_enabled": use_rerank,
            "hits": [
                {
                    "anchor": c.anchor,
                    "rrf": round(c.rrf_score, 4),
                    "rerank": None if c.rerank_score is None else round(c.rerank_score, 4),
                    "sem_rank": c.semantic_rank,
                    "kw_rank": c.keyword_rank,
                }
                for c in chunks
            ],
        }
        if use_rerank:
            meta["rrf_top"] = [c.anchor for c in rrf_top]
            meta["rerank_top"] = [c.anchor for c in chunks]
            meta["rerank_min_score"] = rerank_min_score()
            meta["rerank_score_ratio"] = rerank_score_ratio()
        update_current_span_metadata(meta)
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
                        "rerank_enabled": use_rerank,
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
    # 分层路由（D3）：OPS_LLM_TIER_GRADER_MODEL > RAG_GRADER_MODEL > 档默认
    # （= 现网 GRADER_MODEL 语义；两个 env 全不设时逐字节一致）
    grader_model, route_source = resolve_task_model("grader")
    try:
        with trace_span("grade_llm", run_type="llm", model=grader_model):
            # 路由决策写 span metadata；tracing 关时 no-op
            update_current_span_metadata(
                {
                    "llm_route": {
                        "task_type": "grader",
                        "model": grader_model,
                        "source": route_source,
                    }
                }
            )
            # D4：usage 落表上下文（grader 档 · 同一 run_id）
            with use_run_context(run_id=state.get("run_id"), surface="chat", task_type="grader"):
                grades = await grade_chunks(provider, state["query"], chunks, model=grader_model)
        decision = decide(grades)
        action = decision.action
        best = decision.best.value
    except Exception as exc:
        # fail-closed：闸故障倒向拒答；与真空命中在日志层面分流
        logger.exception(
            "gate refuse: 闸故障（fail-closed）query=%r err=%s", state["query"][:60], exc
        )
        grades = []
        action = "refuse"
        best = "grader_error"

    update_current_span_metadata({"gate_action": action, "best_relevance": best})
    return _gate_result(state, action=action, grades=grades, chunks=chunks, rated=bool(grades))


def _gate_result(
    state: ChatState,
    *,
    action: str,
    grades: list,
    chunks: list[RetrievedChunk],
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
