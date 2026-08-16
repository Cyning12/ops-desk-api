"""lc_evidence_chain：decide 闸 + LCEL 组装（mock 召回/评级/回答，不连真库）。"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.ops.lc_evidence_chain.answer import EMPTY_EVIDENCE_ANSWER, answer_question
from app.ops.lc_evidence_chain.chain import ainvoke_evidence_answer
from app.ops.lc_evidence_chain.grader import decide_grade
from app.ops.lc_evidence_chain.types import EvidenceItem, Grade, RetrieveResult
from app.ops.rag.grader import Relevance


def _item(
    eid: int,
    *,
    source_id: str | None = None,
    chunk_index: int = 0,
    content: str = "body",
) -> EvidenceItem:
    sid = source_id or str(eid)
    return EvidenceItem(
        id=eid,
        repo="MoonshotAI/kimi-code",
        source_type="issue",
        source_id=sid,
        chunk_index=chunk_index,
        content=content,
        title=f"title-{sid}",
    )


def test_decide_keeps_exact_drops_weak():
    items = [_item(1), _item(2, source_id="2720")]
    grades = [
        Grade(evidence_id=1, relevance=Relevance.WEAK, reason="noise"),
        Grade(evidence_id=2, relevance=Relevance.EXACT, reason="root cause"),
    ]
    d = decide_grade(items, grades)
    assert d.action == "answer"
    assert d.best is Relevance.EXACT
    assert [k.id for k in d.kept] == [2]
    assert d.kept[0].grade is not None
    assert d.kept[0].grade.relevance is Relevance.EXACT
    assert d.kept[0].anchor == "2720#0"


def test_decide_all_weak_refuses():
    items = [_item(1), _item(2)]
    grades = [
        Grade(evidence_id=1, relevance=Relevance.WEAK, reason="w"),
        Grade(evidence_id=2, relevance=Relevance.IRRELEVANT, reason="i"),
    ]
    d = decide_grade(items, grades)
    assert d.action == "refuse"
    assert d.kept == []
    assert d.best in (Relevance.WEAK, Relevance.IRRELEVANT)


def test_decide_partial_is_answer_partial():
    items = [_item(1), _item(3)]
    grades = [
        Grade(evidence_id=1, relevance=Relevance.WEAK, reason="w"),
        Grade(evidence_id=3, relevance=Relevance.RELEVANT, reason="partial"),
    ]
    d = decide_grade(items, grades)
    assert d.action == "answer_partial"
    assert d.best is Relevance.RELEVANT
    assert [k.id for k in d.kept] == [3]


def test_decide_empty_grades_refuses():
    d = decide_grade([_item(1)], [])
    assert d.action == "refuse"
    assert d.kept == []
    assert d.grade_count == 0
    assert d.best is Relevance.IRRELEVANT


def test_decide_skips_ungraded_items():
    """LLM 漏评的条 fail-closed，不进 kept。"""
    items = [_item(1), _item(2)]
    grades = [Grade(evidence_id=2, relevance=Relevance.EXACT, reason="ok")]
    d = decide_grade(items, grades)
    assert d.action == "answer"
    assert [k.id for k in d.kept] == [2]


@pytest.mark.asyncio
async def test_ainvoke_happy_path_mocks_io():
    item = _item(2, source_id="2720", content="auto compaction race")
    grades = [Grade(evidence_id=2, relevance=Relevance.EXACT, reason="ok")]

    with (
        patch(
            "app.ops.lc_evidence_chain.chain.retrieve_evidence",
            new=AsyncMock(return_value=RetrieveResult(query="q", evidence=[item])),
        ),
        patch(
            "app.ops.lc_evidence_chain.chain.grade_chunk",
            new=AsyncMock(return_value=grades),
        ),
        patch(
            "app.ops.lc_evidence_chain.chain.answer_question",
            new=AsyncMock(return_value="mocked answer"),
        ),
    ):
        out = await ainvoke_evidence_answer("q")

    assert out.query == "q"
    assert out.answer == "mocked answer"
    assert len(out.evidence) == 1
    assert out.evidence[0].anchor == "2720#0"
    assert out.evidence[0].snippet
    assert out.meta["gate_action"] == "answer"
    assert out.meta["best_relevance"] == "exact"
    assert out.meta["kept_count"] == 1


@pytest.mark.asyncio
async def test_ainvoke_refuse_yields_empty_evidence_answer():
    """全 weak → refuse → kept 空 → answer 早退文案（不 mock answer）。"""
    items = [_item(1), _item(2)]
    grades = [
        Grade(evidence_id=1, relevance=Relevance.WEAK, reason="w"),
        Grade(evidence_id=2, relevance=Relevance.WEAK, reason="w2"),
    ]

    with (
        patch(
            "app.ops.lc_evidence_chain.chain.retrieve_evidence",
            new=AsyncMock(return_value=RetrieveResult(query="q", evidence=items)),
        ),
        patch(
            "app.ops.lc_evidence_chain.chain.grade_chunk",
            new=AsyncMock(return_value=grades),
        ),
    ):
        out = await ainvoke_evidence_answer("q")

    assert out.meta["gate_action"] == "refuse"
    assert out.evidence == []
    assert out.answer == EMPTY_EVIDENCE_ANSWER


@pytest.mark.asyncio
async def test_answer_question_empty_skips_llm():
    with patch("app.ops.lc_evidence_chain.answer.get_llm_provider") as factory:
        text = await answer_question("q", [])
    assert text == EMPTY_EVIDENCE_ANSWER
    factory.assert_not_called()
