"""LCEL 组装：retrieve → grade → answer。

``get_llm_provider`` 留在 answer / grader 内，不在本文件创建——
chain 只负责编排步骤；LLM 选型属于各步实现细节（且 grader 与 answer
常用不同 provider/model）。

可选 Langfuse：复用 ``OPS_CHAT_TRACER`` + keys（见 ``app.ops.tracing``）；
``run_name`` / tags = ``lc-evidence-chain``，与 Chat ``ops-chat`` 可区分。
"""

from __future__ import annotations

from typing import Any

from langchain_core.runnables import RunnableLambda

from app.ops.lc_evidence_chain.answer import answer_question
from app.ops.lc_evidence_chain.grader import decide_grade, grade_chunk
from app.ops.lc_evidence_chain.retrieve import retrieve_evidence
from app.ops.lc_evidence_chain.types import ChainResult, EvidenceItem
from app.ops.tracing import tracing_enabled, update_current_span_metadata

_RUN_NAME = "lc-evidence-chain"
_TAG = "lc-evidence-chain"


def _trace_config() -> dict | None:
    """旁路专用 Langfuse CallbackHandler config；未开启时返回 None。"""
    if not tracing_enabled():
        return None
    from langfuse.langchain import CallbackHandler  # 延迟导入：SDK 为可选依赖

    return {
        "callbacks": [CallbackHandler()],
        "metadata": {"langfuse_tags": [_TAG]},
        "run_name": _RUN_NAME,
    }


def _meta_span_update(meta: dict[str, Any]) -> None:
    """把 gate / 计数写到当前 observation；失败静默。"""
    payload = {
        k: meta[k]
        for k in ("gate_action", "hit_count", "kept_count", "best_relevance", "grade_count")
        if k in meta
    }
    if payload:
        update_current_span_metadata(payload)


async def _retrieve_step(inp: dict[str, Any] | str) -> dict[str, Any]:
    query = inp["query"] if isinstance(inp, dict) else str(inp)
    result = await retrieve_evidence(query)
    meta = {"hit_count": len(result.evidence)}
    _meta_span_update(meta)
    return {
        "query": result.query,
        "evidence": result.evidence,
        "meta": meta,
    }


async def _grade_step(payload: dict[str, Any]) -> dict[str, Any]:
    evidence: list[EvidenceItem] = list(payload.get("evidence") or [])
    meta = dict(payload.get("meta") or {})
    if not evidence:
        meta["graded"] = False
        _meta_span_update(meta)
        return {**payload, "meta": meta}

    # LLM/parse_grades 仍按 chunk_id；本包 Grade 映射为 evidence_id（= EvidenceItem.id）
    raw_grades = await grade_chunk(str(payload["query"]), evidence)
    decision = decide_grade(evidence, raw_grades)

    meta["graded"] = True
    meta["grade_count"] = decision.grade_count
    meta["kept_count"] = len(decision.kept)
    meta["gate_action"] = decision.action
    meta["best_relevance"] = decision.best.value
    _meta_span_update(meta)
    return {**payload, "evidence": decision.kept, "meta": meta}


async def _answer_step(payload: dict[str, Any]) -> dict[str, Any]:
    evidence: list[EvidenceItem] = list(payload.get("evidence") or [])
    meta = dict(payload.get("meta") or {})
    gate_action = str(meta.get("gate_action") or "")
    answer = await answer_question(
        str(payload["query"]),
        evidence,
        gate_action=gate_action or None,
    )
    _meta_span_update(meta)
    return {
        **payload,
        "answer": answer,
    }


def build_chain():
    """返回可 ``ainvoke`` 的 Runnable：retrieve | grade | answer。"""
    retrieve = RunnableLambda(_retrieve_step, name="retrieve")
    grade = RunnableLambda(_grade_step, name="grade")
    answer = RunnableLambda(_answer_step, name="answer")
    return retrieve | grade | answer


async def ainvoke_evidence_answer(query: str) -> ChainResult:
    """旁路入口：query → evidence + grade + answer。"""
    ainvoke_kwargs: dict[str, Any] = {}
    if config := _trace_config():
        ainvoke_kwargs["config"] = config
    out = await build_chain().ainvoke({"query": query}, **ainvoke_kwargs)
    return ChainResult.model_validate(out)
