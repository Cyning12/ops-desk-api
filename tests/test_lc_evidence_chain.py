"""lc_evidence_chain：decide 闸 + LCEL 组装（mock 召回/评级/回答，不连真库）。"""

from __future__ import annotations

import sys
import types
from contextlib import contextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.llm.schema import LlmProviderError
from app.ops.lc_evidence_chain.answer import EMPTY_EVIDENCE_ANSWER, answer_question
from app.ops.lc_evidence_chain.chain import _trace_config, ainvoke_evidence_answer
from app.ops.lc_evidence_chain.grader import decide_grade
from app.ops.lc_evidence_chain.retrieve import retrieve_evidence
from app.ops.lc_evidence_chain.types import EvidenceItem, Grade, RetrieveResult
from app.ops.rag.grader import Relevance
from app.ops.rag.retrieve import RetrievedChunk


def _fake_langfuse_langchain_module(handler: MagicMock) -> types.ModuleType:
    """注入假 ``langfuse.langchain``，避免 CI 缺 ``langchain`` 包时真实 import 失败。"""
    mod = types.ModuleType("langfuse.langchain")
    mod.CallbackHandler = MagicMock(return_value=handler)
    return mod


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


def test_from_retrieved_chunk_accepts_media_dicts():
    """入库 images 为 {alt,url,anchor}，不得当 list[str] 校验失败（联调 500）。"""
    chunk = RetrievedChunk(
        id=1,
        repo="MoonshotAI/kimi-code",
        source_type="issue",
        source_id="2720",
        chunk_index=4,
        content="Title: img\n---\nContent: body",
        images=[
            {
                "alt": "Image",
                "url": "https://example.com/1.png",
                "anchor": "[IMAGE#1]",
                "kind": "image",
            }
        ],
    )
    item = EvidenceItem.from_retrieved_chunk(chunk)
    assert item.images[0]["anchor"] == "[IMAGE#1]"
    assert item.snippet


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


def test_decide_kept_orders_exact_before_relevant_stable():
    """exact 在 relevant 前；同档保持原相对序。"""
    items = [_item(1), _item(2), _item(3), _item(4)]
    grades = [
        Grade(evidence_id=1, relevance=Relevance.RELEVANT, reason="r1"),
        Grade(evidence_id=2, relevance=Relevance.EXACT, reason="e1"),
        Grade(evidence_id=3, relevance=Relevance.RELEVANT, reason="r2"),
        Grade(evidence_id=4, relevance=Relevance.EXACT, reason="e2"),
    ]
    d = decide_grade(items, grades)
    assert d.action == "answer"
    assert [k.id for k in d.kept] == [2, 4, 1, 3]


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
async def test_ainvoke_grader_llm_error_refuses():
    """grader complete 抛 LlmProviderError → 链内 refuse，不 500。"""
    items = [_item(1), _item(2)]

    class _Boom:
        async def complete(self, messages, model=None):
            raise LlmProviderError("grader down", retryable=True, status_code=503)

    with (
        patch(
            "app.ops.lc_evidence_chain.chain.retrieve_evidence",
            new=AsyncMock(return_value=RetrieveResult(query="q", evidence=items)),
        ),
        patch(
            "app.ops.lc_evidence_chain.grader.get_llm_provider",
            return_value=_Boom(),
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


@pytest.mark.asyncio
async def test_answer_partial_injects_partial_evidence_note():
    captured: list = []

    class _Prov:
        async def complete(self, messages, model=None):
            captured.extend(messages)
            return "仅部分证据。根据资料……"

    with patch(
        "app.ops.lc_evidence_chain.answer.get_llm_provider",
        return_value=_Prov(),
    ):
        text = await answer_question(
            "q",
            [_item(3, source_id="2720", content="partial body")],
            gate_action="answer_partial",
        )

    assert "仅部分证据" in text or text
    assert any("仅部分证据" in m.content for m in captured if m.role == "system")
    assert captured[-1].role == "user" and captured[-1].content.startswith("仅部分证据")


@pytest.mark.asyncio
async def test_ainvoke_partial_passes_gate_action_to_answer():
    item = _item(3, source_id="2720")
    grades = [Grade(evidence_id=3, relevance=Relevance.RELEVANT, reason="partial")]
    seen: dict = {}

    async def _fake_answer(query, evidence, *, gate_action=None, **kwargs):
        seen["gate_action"] = gate_action
        return "仅部分证据。ok"

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
            new=_fake_answer,
        ),
    ):
        out = await ainvoke_evidence_answer("q")

    assert out.meta["gate_action"] == "answer_partial"
    assert seen.get("gate_action") == "answer_partial"


def test_trace_config_off_returns_none():
    with patch("app.ops.lc_evidence_chain.chain.tracing_enabled", return_value=False):
        assert _trace_config() is None


def test_trace_config_on_has_callbacks_tags_run_name():
    handler = MagicMock(name="CallbackHandler")
    fake = _fake_langfuse_langchain_module(handler)
    with (
        patch("app.ops.lc_evidence_chain.chain.tracing_enabled", return_value=True),
        patch.dict(sys.modules, {"langfuse.langchain": fake}),
    ):
        cfg = _trace_config()
    assert cfg is not None
    assert cfg["run_name"] == "lc-evidence-chain"
    assert "lc-evidence-chain" in cfg["metadata"]["langfuse_tags"]
    assert cfg["callbacks"] == [handler]
    fake.CallbackHandler.assert_called_once_with()


@pytest.mark.asyncio
async def test_ainvoke_tracing_off_omits_config():
    """关闭 tracing：ainvoke 不传 config（无 CallbackHandler）。"""
    captured: dict = {}

    class _FakeChain:
        async def ainvoke(self, inp, **kwargs):
            captured["kwargs"] = kwargs
            return {
                "query": "q",
                "evidence": [],
                "answer": EMPTY_EVIDENCE_ANSWER,
                "meta": {},
            }

    with (
        patch("app.ops.lc_evidence_chain.chain.tracing_enabled", return_value=False),
        patch(
            "app.ops.lc_evidence_chain.chain.build_chain",
            return_value=_FakeChain(),
        ),
    ):
        out = await ainvoke_evidence_answer("q")

    assert "config" not in captured["kwargs"]
    assert out.answer == EMPTY_EVIDENCE_ANSWER


@pytest.mark.asyncio
async def test_ainvoke_tracing_on_injects_config():
    """开启 tracing：config 含 callbacks + tags + run_name（mock，不连云）。"""
    captured: dict = {}
    handler = MagicMock(name="CallbackHandler")
    fake = _fake_langfuse_langchain_module(handler)

    class _FakeChain:
        async def ainvoke(self, inp, **kwargs):
            captured["kwargs"] = kwargs
            return {
                "query": "q",
                "evidence": [],
                "answer": "ok",
                "meta": {"gate_action": "refuse"},
            }

    with (
        patch("app.ops.lc_evidence_chain.chain.tracing_enabled", return_value=True),
        patch.dict(sys.modules, {"langfuse.langchain": fake}),
        patch(
            "app.ops.lc_evidence_chain.chain.build_chain",
            return_value=_FakeChain(),
        ),
    ):
        out = await ainvoke_evidence_answer("q")

    cfg = captured["kwargs"].get("config")
    assert cfg is not None
    assert cfg["run_name"] == "lc-evidence-chain"
    assert "lc-evidence-chain" in cfg["metadata"]["langfuse_tags"]
    assert cfg["callbacks"] == [handler]
    assert out.answer == "ok"


def _coarse_chunk() -> RetrievedChunk:
    return RetrievedChunk(
        id=1,
        repo="MoonshotAI/kimi-code",
        source_type="issue",
        source_id="2720",
        chunk_index=0,
        content="Title: t\n---\nContent: body",
    )


def _session_cm() -> MagicMock:
    session = AsyncMock()
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=session)
    cm.__aexit__ = AsyncMock(return_value=None)
    return MagicMock(return_value=cm)


@pytest.mark.asyncio
async def test_retrieve_evidence_wraps_embed_as_query_embed_generation():
    """tracing 路径：embed 由 query_embed / run_type=llm 包裹；rerank 关则无 rerank span。"""
    spans: list[tuple[str, dict]] = []

    @contextmanager
    def fake_trace_span(name: str, **kwargs):
        spans.append((name, kwargs))
        yield

    embedder = MagicMock()
    embedder.name = "test-embed-model"
    embedder.embed = MagicMock(return_value=[[0.1, 0.2, 0.3]])
    coarse = [_coarse_chunk()]

    with (
        patch("app.ops.lc_evidence_chain.retrieve.trace_span", fake_trace_span),
        patch(
            "app.ops.lc_evidence_chain.retrieve._get_embedder",
            return_value=embedder,
        ),
        patch(
            "app.ops.lc_evidence_chain.retrieve.rerank_enabled",
            return_value=False,
        ),
        patch(
            "app.ops.lc_evidence_chain.retrieve.AsyncSessionLocal",
            _session_cm(),
        ),
        patch(
            "app.ops.lc_evidence_chain.retrieve.hybrid_recall",
            new=AsyncMock(return_value=coarse),
        ),
        patch(
            "app.ops.lc_evidence_chain.retrieve.rerank_chunks",
            side_effect=AssertionError("rerank must not run when disabled"),
        ),
    ):
        out = await retrieve_evidence("q")

    assert out.query == "q"
    assert len(out.evidence) == 1
    embed_spans = [s for s in spans if s[0] == "query_embed"]
    assert len(embed_spans) == 1
    assert embed_spans[0][1].get("run_type") == "llm"
    assert embed_spans[0][1].get("model") == "test-embed-model"
    assert not any(s[0] == "rerank" for s in spans)


@pytest.mark.asyncio
async def test_retrieve_evidence_wraps_rerank_when_enabled():
    """RAG_RERANK_ENABLED=true：rerank 亦为 generation；embed 仍有 query_embed。"""
    spans: list[tuple[str, dict]] = []

    @contextmanager
    def fake_trace_span(name: str, **kwargs):
        spans.append((name, kwargs))
        yield

    embedder = MagicMock()
    embedder.name = "test-embed-model"
    embedder.embed = MagicMock(return_value=[[0.1, 0.2]])
    coarse = [_coarse_chunk()]
    reranked = [
        RetrievedChunk(
            id=2,
            repo="MoonshotAI/kimi-code",
            source_type="issue",
            source_id="99",
            chunk_index=1,
            content="Title: r\n---\nContent: reranked",
        )
    ]

    with (
        patch("app.ops.lc_evidence_chain.retrieve.trace_span", fake_trace_span),
        patch(
            "app.ops.lc_evidence_chain.retrieve._get_embedder",
            return_value=embedder,
        ),
        patch(
            "app.ops.lc_evidence_chain.retrieve.rerank_enabled",
            return_value=True,
        ),
        patch(
            "app.ops.lc_evidence_chain.retrieve.rerank_model_name",
            return_value="BAAI/bge-reranker-v2-m3",
        ),
        patch(
            "app.ops.lc_evidence_chain.retrieve.AsyncSessionLocal",
            _session_cm(),
        ),
        patch(
            "app.ops.lc_evidence_chain.retrieve.hybrid_recall",
            new=AsyncMock(return_value=coarse),
        ),
        patch(
            "app.ops.lc_evidence_chain.retrieve.rerank_chunks",
            return_value=reranked,
        ),
    ):
        out = await retrieve_evidence("q")

    assert [e.id for e in out.evidence] == [2]
    assert any(
        name == "query_embed" and kw.get("run_type") == "llm" for name, kw in spans
    )
    rerank_spans = [s for s in spans if s[0] == "rerank"]
    assert len(rerank_spans) == 1
    assert rerank_spans[0][1].get("run_type") == "llm"
    assert rerank_spans[0][1].get("model") == "BAAI/bge-reranker-v2-m3"
