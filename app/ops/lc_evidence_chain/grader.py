"""
评分：为检索到的证据片段打分，并做答/拒闸（包内自洽，不调用 rag.grader.decide）。
"""

import logging
import os

from app.llm.factory import get_llm_provider
from app.llm.schema import BaseProvider, LlmMessage
from app.ops.lc_evidence_chain.types import EvidenceItem, GateDecision, Grade
from app.ops.rag.grader import (
    Relevance,
    grader_prompt_version,
    grader_system_prompt,
    parse_grades,
    user_prompt,
)
from app.ops.rag.prefix import strip_doc_context_prefix
from app.ops.tracing import trace_span

logger = logging.getLogger(__name__)

GRADER_PROVIDER = os.getenv("RAG_GRADER_PROVIDER", "bailian")
GRADER_MODEL = os.getenv("RAG_GRADER_MODEL", "qwen3.7-flash")


async def grade_chunk(query: str, evidence: list[EvidenceItem]) -> list[Grade]:
    llm = get_llm_provider(GRADER_PROVIDER)
    return await _grade_chunks_llm(llm, query, evidence, model=GRADER_MODEL)


def decide_grade(evidence: list[EvidenceItem], grades: list[Grade]) -> GateDecision:
    """按评级过滤证据：只保留 relevant（部分）与 exact；挂上 grade。

    契约对齐：最高档 ≤ weak → refuse；relevant → answer_partial；exact → answer。
    未评到的条 fail-closed 丢弃。refuse 时 kept 为空。
    """
    by_id = {g.evidence_id: g for g in grades}
    for item in evidence:
        g = by_id.get(item.id)
        if g is not None:
            item.grade = g

    if not grades:
        return GateDecision(
            kept=[],
            action="refuse",
            best=Relevance.IRRELEVANT,
            grade_count=0,
        )

    best_grade = max(grades, key=lambda g: g.relevance.level)
    best = best_grade.relevance
    if best.should_reject:
        action = "refuse"
    elif best.is_partial:
        action = "answer_partial"
    elif best.is_exact:
        action = "answer"
    else:
        # unrated 等非预期档：拒答
        action = "refuse"

    kept: list[EvidenceItem] = []
    if action != "refuse":
        for item in evidence:
            g = item.grade
            if g is not None and (g.relevance.is_partial or g.relevance.is_exact):
                kept.append(item)

    logger.info(
        "decide: action=%s best=%s kept=%d/%d",
        action,
        best.value,
        len(kept),
        len(evidence),
    )
    return GateDecision(
        kept=kept,
        action=action,
        best=best,
        grade_count=len(grades),
    )


async def _grade_chunks_llm(
    provider: BaseProvider,
    query: str,
    evidence: list[EvidenceItem],
    model: str | None = None,
    snippet_chars: int = 1200,
    prompt_version: str | None = None,
) -> list[Grade]:
    ver = (prompt_version or grader_prompt_version()).strip().lower()
    system = grader_system_prompt(ver)
    blocks = []
    for c in evidence:
        body = strip_doc_context_prefix(c.content)[:snippet_chars]
        # 线协议仍用 chunk_id=（复用 rag grader prompt / parse_grades）
        blocks.append(f"### chunk_id={c.id}（{c.source_type} {c.anchor}）\n{body}")
    user = user_prompt(query, blocks)
    # 自研 provider 不走 LangChain LLM 类，CallbackHandler 抓不到 → 显式 generation
    with trace_span("grade_llm", run_type="llm", model=model):
        raw = await provider.complete(
            [LlmMessage(role="system", content=system), LlmMessage(role="user", content=user)],
            model=model,
        )
    parsed = parse_grades(raw, {c.id for c in evidence})
    grades = [Grade(evidence_id=g.chunk_id, relevance=g.relevance, reason=g.reason) for g in parsed]
    logger.info(
        "grader: prompt=%s query=%r grades=%s",
        ver,
        query[:60],
        [(g.evidence_id, g.relevance.value) for g in grades],
    )
    return grades
