"""R-4 golden eval runner 纯函数单测（零模型零库）。"""

from pathlib import Path

from app.ops.rag.retrieve import RetrievedChunk
from evals.golden.run_eval import (
    CaseResult,
    DenyRule,
    apply_hygiene,
    assert_case,
    build_report,
    contains_golden_query,
    grade_stability_rate,
    is_denylisted,
    load_denylist,
    load_golden,
    quadrant_recall_summary,
    recall_knobs,
)

QUERIES = Path("evals/golden/queries_v1.yaml")
DENYLIST = Path("evals/golden/hygiene_denylist.yaml")


def _chunk(
    *,
    cid: int = 1,
    source_type: str = "issue",
    source_id: str = "2720",
    chunk_index: int = 0,
    content: str = "normal body",
) -> RetrievedChunk:
    return RetrievedChunk(
        id=cid,
        repo="MoonshotAI/kimi-code",
        source_type=source_type,
        source_id=source_id,
        chunk_index=chunk_index,
        content=content,
    )


def test_load_golden_73():
    cases = load_golden(QUERIES)
    # G67 双审后 157 转正样本 G73 → 71+2=73（见 commit cc4f30f）
    assert len(cases) == 73
    quads = {c["quadrant"] for c in cases}
    assert quads == {"zh2en", "zh2zh", "en2en", "negative"}


def test_recall_knobs_default_normal(monkeypatch):
    monkeypatch.delenv("RAG_RERANK_ENABLED", raising=False)
    k, n, on = recall_knobs()
    assert (k, n, on) == (10, 15, False)


def test_recall_knobs_rerank_enabled(monkeypatch):
    monkeypatch.setenv("RAG_RERANK_ENABLED", "true")
    monkeypatch.delenv("RAG_RECALL_K_EACH", raising=False)
    monkeypatch.delenv("RAG_RERANK_CANDIDATES", raising=False)
    k, n, on = recall_knobs()
    assert on is True
    assert k == 20
    assert n == 20


def test_load_denylist():
    rules = load_denylist(DENYLIST)
    assert rules
    assert any(r.source_id_contains == "rag-knowledge-contract" for r in rules)


def test_hygiene_filters_contract_doc_and_query_echo():
    q = "Kimi Code 自动压缩被取消并报错 This operation was aborted 是什么原因?"
    rules = [
        DenyRule(source_type="doc", source_id_contains="rag-knowledge-contract"),
    ]
    chunks = [
        _chunk(cid=1, source_id="2720", content="Root cause: abort"),
        _chunk(
            cid=2,
            source_type="doc",
            source_id="contracts/rag-knowledge-contract-v1.md",
            content="契约正文",
        ),
        _chunk(cid=3, source_id="999", content=f"金样原文抄写：{q}"),
    ]
    kept, removed = apply_hygiene(chunks, [q], rules)
    assert [c.id for c in kept] == [1]
    assert {c.id for c in removed} == {2, 3}


def test_contains_golden_query_short_skipped():
    assert not contains_golden_query("hi there", ["hi"])  # <12 字不触发


def test_is_denylisted_type_mismatch():
    rules = [DenyRule(source_type="doc", source_id_contains="x")]
    assert not is_denylisted(_chunk(source_type="issue", source_id="x"), rules)


def test_assert_positive_pass():
    case = {
        "id": "G01",
        "quadrant": "zh2en",
        "expect_hit": {"source_type": "issue", "source_id": "2720"},
        "assert": {"recall_at": 5, "min_relevance": "relevant", "citation_in_hits": True},
        "expect_relevance": "exact",
    }
    chunks = [_chunk(cid=10, source_id="2720"), _chunk(cid=11, source_id="1")]
    grades = {10: "exact", 11: "weak"}
    r = assert_case(case, chunks, grades, gate_action="answer")
    assert r.verdict == "pass"
    assert r.recall_at5 == "pass"
    assert r.min_relevance == "pass"
    assert r.citation_in_hits == "pass"


def test_assert_positive_recall_fail():
    case = {
        "id": "G01",
        "quadrant": "zh2en",
        "expect_hit": {"source_type": "issue", "source_id": "2720"},
        "assert": {"recall_at": 5, "min_relevance": "relevant", "citation_in_hits": True},
    }
    chunks = [_chunk(cid=1, source_id="1")]
    r = assert_case(case, chunks, {1: "exact"}, gate_action="answer")
    assert r.verdict == "fail"
    assert r.recall_at5 == "fail"


def test_assert_negative_must_refuse():
    case = {
        "id": "G62",
        "quadrant": "negative",
        "expect_hit": None,
        "assert": {"max_relevance": "weak", "must_refuse": True},
    }
    chunks = [_chunk(cid=1, source_id="1")]
    r = assert_case(case, chunks, {1: "weak"}, gate_action="refuse")
    assert r.verdict == "pass"
    assert r.must_refuse == "pass"

    r2 = assert_case(case, chunks, {1: "exact"}, gate_action="answer")
    assert r2.verdict == "fail"


def test_quadrant_recall_and_spec_fields():
    results = [
        CaseResult(
            id="G01",
            quadrant="zh2en",
            top5=["2720#0"],
            filtered_out=[],
            recall_at5="pass",
            best_relevance="exact",
            min_relevance="pass",
            citation_in_hits="pass",
            must_refuse=None,
            gate_action="answer",
            verdict="pass",
        ),
        CaseResult(
            id="G10",
            quadrant="zh2en",
            top5=["1#0"],
            filtered_out=[],
            recall_at5="fail",
            best_relevance="weak",
            min_relevance="fail",
            citation_in_hits="fail",
            must_refuse=None,
            gate_action="refuse",
            verdict="fail",
        ),
        CaseResult(
            id="G62",
            quadrant="negative",
            top5=["1#0"],
            filtered_out=[],
            recall_at5=None,
            best_relevance="weak",
            min_relevance=None,
            citation_in_hits=None,
            must_refuse="pass",
            gate_action="refuse",
            verdict="pass",
        ),
    ]
    assert quadrant_recall_summary(results) == {"zh2en": "1/2"}
    report = build_report(
        results,
        embed_name="BAAI/bge-m3",
        grader_model="qwen",
        stability=0.75,
        corpus_n=100,
    )
    s = report["summary"]
    assert s["measurement_source"] == "observed"
    assert s["confidence"] == "low"
    assert s["comparability"] == "not_comparable"
    assert s["grade_stability_agree"] == 0.75
    assert s["pass"] == "2/3"


def test_grade_stability_rate():
    assert grade_stability_rate([["exact", "weak"], ["exact", "weak"], ["exact", "weak"]]) == 1.0
    assert grade_stability_rate([["exact", "weak"], ["exact", "relevant"]]) == 0.5


def test_parse_eval_log_and_write_report(tmp_path: Path):
    from evals.golden.run_eval import parse_eval_log, write_report

    log = """
[1/2] G01 · zh2en …
  → sem=['2720#0', '1#0']
  → kw =['2720#0']
  → FAIL top5=['2720#0', '1#0', '2#0', '3#0', '4#0'] best=irrelevant filtered=['x#0'] reasons=['min_relevance: got irrelevant < relevant']
[2/2] G62 · negative …
  → sem=['9#0']
  → kw =[]
  → PASS top5=['9#0', '8#0', '7#0', '6#0', '5#0'] best=weak filtered=[] reasons=[]
"""
    results = parse_eval_log(log)
    assert len(results) == 2
    assert results[0].id == "G01"
    assert results[0].verdict == "fail"
    assert results[0].keyword_hits == ["2720#0"]
    assert results[0].recall_at5 == "pass"
    assert results[0].min_relevance == "fail"
    assert results[1].quadrant == "negative"
    assert results[1].must_refuse == "pass"
    assert results[1].recall_at5 is None

    report = build_report(
        results,
        embed_name="BAAI/bge-m3",
        grader_model="qwen",
        stability=None,
        corpus_n=8574,
        extra_summary={"recovered_from_log": "test"},
    )
    out = tmp_path / "partial.yaml"
    write_report(out, report)
    loaded, meta = __import__(
        "evals.golden.run_eval", fromlist=["load_existing_results"]
    ).load_existing_results(out)
    assert len(loaded) == 2
    assert meta["summary"]["recovered_from_log"] == "test"
    assert report["summary"]["pass"] == "1/2"
