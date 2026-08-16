"""LCEL 组装：retrieve → grade → answer。

``get_llm_provider`` 留在 answer / grader 内，不在本文件创建——
chain 只负责编排步骤；LLM 选型属于各步实现细节（且 grader 与 answer
常用不同 provider/model）。
"""

from __future__ import annotations

from typing import Any

from langchain_core.runnables import RunnableLambda

from app.ops.lc_evidence_chain.answer import answer_question
from app.ops.lc_evidence_chain.grader import decide_grade, grade_chunk
from app.ops.lc_evidence_chain.retrieve import retrieve_evidence
from app.ops.lc_evidence_chain.types import ChainResult, EvidenceItem


async def _retrieve_step(inp: dict[str, Any] | str) -> dict[str, Any]:
    query = inp["query"] if isinstance(inp, dict) else str(inp)
    result = await retrieve_evidence(query)
    return {
        "query": result.query,
        "evidence": result.evidence,
        "meta": {"hit_count": len(result.evidence)},
    }


async def _grade_step(payload: dict[str, Any]) -> dict[str, Any]:
    evidence: list[EvidenceItem] = list(payload.get("evidence") or [])
    meta = dict(payload.get("meta") or {})
    if not evidence:
        meta["graded"] = False
        return {**payload, "meta": meta}

    # LLM/parse_grades 仍按 chunk_id；本包 Grade 映射为 evidence_id（= EvidenceItem.id）
    raw_grades = await grade_chunk(str(payload["query"]), evidence)
    decision = decide_grade(evidence, raw_grades)

    meta["graded"] = True
    meta["grade_count"] = decision.grade_count
    meta["kept_count"] = len(decision.kept)
    meta["gate_action"] = decision.action
    meta["best_relevance"] = decision.best.value
    return {**payload, "evidence": decision.kept, "meta": meta}


async def _answer_step(payload: dict[str, Any]) -> dict[str, Any]:
    evidence: list[EvidenceItem] = list(payload.get("evidence") or [])
    answer = await answer_question(str(payload["query"]), evidence)
    return {
        **payload,
        "answer": answer,
    }


def build_chain():
    """返回可 ``ainvoke`` 的 Runnable：retrieve | grade | answer。"""
    retrieve = RunnableLambda(_retrieve_step)
    grade = RunnableLambda(_grade_step)
    answer = RunnableLambda(_answer_step)
    return retrieve | grade | answer


async def ainvoke_evidence_answer(query: str) -> ChainResult:
    """旁路入口：query → evidence + grade + answer。"""
    out = await build_chain().ainvoke({"query": query})
    return ChainResult.model_validate(out)
