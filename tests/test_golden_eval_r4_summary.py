"""R-4 结案汇总脚本确定性测试（task rag-golden-eval-r4-r5 · E4）。

fake 报告样例喂入；不连真库 / 真 LLM / 外网。
覆盖：四象限分组 · zh2en ≥1/3 门槛三态（MET/NOT_MET/NO_DATA）·
拒答正确率与误拒/误答分类 · 小样本 confidence 标注存在性 · FP-2 显式失败。
"""

from pathlib import Path

import pytest
import yaml

from evals.golden.summarize_r4 import (
    aggregate,
    build_final_report,
    confidence_note,
    load_report,
    main,
    render_markdown,
    wilson_interval,
)


def _case(
    cid: str,
    quadrant: str,
    *,
    recall_at5: str | None = "pass",
    min_relevance: str | None = "pass",
    citation_in_hits: str | None = "pass",
    must_refuse: str | None = None,
    gate_action: str | None = "answer",
    verdict: str = "pass",
    fail_reasons: list[str] | None = None,
) -> dict:
    return {
        "id": cid,
        "quadrant": quadrant,
        "top5": ["1#0"],
        "filtered_out": [],
        "recall_at5": recall_at5,
        "best_relevance": "exact",
        "min_relevance": min_relevance,
        "citation_in_hits": citation_in_hits,
        "must_refuse": must_refuse,
        "gate_action": gate_action,
        "verdict": verdict,
        "fail_reasons": fail_reasons or [],
        "semantic_hits": [],
        "keyword_hits": [],
    }


def _fake_report(results: list[dict]) -> dict:
    return {
        "run": "eval-rag-fake-0001",
        "embed": "BAAI/bge-m3",
        "grader": "fake-grader",
        "corpus": "ops_knowledge_chunks(N=100)",
        "results": results,
        "summary": {
            "measurement_source": "observed",
            "confidence": "low",
            "comparability": "not_comparable",
        },
    }


def _write(tmp_path: Path, report: dict) -> Path:
    p = tmp_path / "fake_r4.yaml"
    p.write_text(yaml.safe_dump(report, allow_unicode=True), encoding="utf-8")
    return p


def test_quadrant_grouping():
    results = [
        _case("G01", "zh2en"),
        _case("G02", "zh2en", recall_at5="fail", verdict="fail", fail_reasons=["recall@5: miss"]),
        _case("G20", "zh2zh"),
        _case(
            "G40",
            "en2en",
            min_relevance="fail",
            verdict="fail",
            fail_reasons=["min_relevance: got weak < relevant"],
        ),
        _case(
            "G62",
            "negative",
            recall_at5=None,
            min_relevance=None,
            citation_in_hits=None,
            must_refuse="pass",
            gate_action="refuse",
        ),
    ]
    agg = aggregate(results)
    quads = agg["quadrants"]
    assert quads["zh2en"]["n"] == 2
    assert quads["zh2en"]["recall_at5"] == {
        "pass": 1,
        "total": 2,
        "rate": 0.5,
        "confidence": quads["zh2en"]["recall_at5"]["confidence"],
    }
    assert quads["zh2zh"]["recall_at5"]["rate"] == 1.0
    assert quads["en2en"]["min_relevance"] == {"pass": 0, "total": 1, "rate": 0.0}
    # negative 象限 recall/cite 分母为 0（全 null）
    assert quads["negative"]["recall_at5"]["total"] == 0
    assert quads["negative"]["recall_at5"]["rate"] is None
    assert quads["negative"]["verdict_pass"] == "1/1"
    assert [f["id"] for f in agg["failures"]] == ["G02", "G40"]


@pytest.mark.parametrize(
    ("hits", "n", "expected"),
    [
        (9, 26, "MET"),  # 9/26 ≈ 0.346 ≥ 1/3
        (8, 26, "NOT_MET"),  # 8/26 ≈ 0.308 < 1/3
        (1, 3, "MET"),  # 边界：恰好 1/3
    ],
)
def test_zh2en_gate_three_states(hits, n, expected):
    results = [
        _case(
            f"G{i:02d}",
            "zh2en",
            recall_at5="pass" if i <= hits else "fail",
            verdict="pass" if i <= hits else "fail",
        )
        for i in range(1, n + 1)
    ]
    gate = aggregate(results)["gates"]["zh2en_crosslingual_recall_at5"]
    assert gate["verdict"] == expected
    assert gate["hits"] == hits and gate["n"] == n


def test_zh2en_gate_no_data():
    results = [
        _case(
            "G62",
            "negative",
            recall_at5=None,
            min_relevance=None,
            citation_in_hits=None,
            must_refuse="pass",
            gate_action="refuse",
        )
    ]
    gate = aggregate(results)["gates"]["zh2en_crosslingual_recall_at5"]
    assert gate["verdict"] == "NO_DATA"
    assert gate["n"] == 0
    # zh2en 象限不出现在逐象限表
    assert "zh2en" not in aggregate(results)["quadrants"]


def test_refusal_classification():
    results = [
        # 负样本：2 正确拒答 + 1 误答
        _case(
            "G62",
            "negative",
            recall_at5=None,
            min_relevance=None,
            citation_in_hits=None,
            must_refuse="pass",
            gate_action="refuse",
        ),
        _case(
            "G63",
            "negative",
            recall_at5=None,
            min_relevance=None,
            citation_in_hits=None,
            must_refuse="pass",
            gate_action="refuse",
        ),
        _case(
            "G67",
            "negative",
            recall_at5=None,
            min_relevance=None,
            citation_in_hits=None,
            must_refuse="fail",
            gate_action="answer_partial",
            verdict="fail",
            fail_reasons=["must_refuse: gate_action=answer_partial"],
        ),
        # 正样本：1 疑似误拒
        _case(
            "G16",
            "zh2en",
            gate_action="refuse",
            verdict="fail",
            min_relevance="fail",
            fail_reasons=["min_relevance: got irrelevant"],
        ),
    ]
    rf = aggregate(results)["refusal"]
    assert rf["negative_n"] == 3
    assert rf["refuse_correct"] == 2
    assert rf["accuracy"] == round(2 / 3, 4)
    assert rf["false_answer_ids"] == ["G67"]  # 误答
    assert rf["false_refusal_ids"] == ["G16"]  # 疑似误拒


def test_confidence_annotation_present():
    note = confidence_note(19, 26)
    assert "n=26" in note
    assert "Wilson 95% CI" in note
    assert "confidence=low" in note  # 小样本老实标
    assert confidence_note(0, 0).startswith("n=0")
    lo, hi = wilson_interval(1, 3)
    assert 0.0 <= lo < 1 / 3 < hi <= 1.0


def test_load_report_rejects_malformed(tmp_path: Path):
    # FP-2：残缺/非法报告显式失败，不静默冒充
    empty = tmp_path / "empty.yaml"
    empty.write_text("run: x\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="results 缺失或为空"):
        load_report(empty)

    bad = tmp_path / "bad.yaml"
    bad.write_text(
        yaml.safe_dump({"results": [{"id": "G01", "quadrant": "xx", "verdict": "pass"}]}),
        encoding="utf-8",
    )
    with pytest.raises(SystemExit, match="quadrant 非法"):
        load_report(bad)

    bad2 = tmp_path / "bad2.yaml"
    bad2.write_text(
        yaml.safe_dump(
            {
                "results": [
                    {"id": "G01", "quadrant": "zh2en", "verdict": "pass", "recall_at5": "maybe"}
                ]
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(SystemExit, match="recall_at5 非法"):
        load_report(bad2)

    with pytest.raises(SystemExit, match="报告不存在"):
        load_report(tmp_path / "nope.yaml")


def test_build_final_report_header_passthrough(tmp_path: Path):
    results = [_case("G01", "zh2en")]
    src = _write(tmp_path, _fake_report(results))
    data = load_report(src)
    report = build_final_report(data, src)
    assert report["run"] == "eval-rag-fake-0001"
    assert report["embed"] == "BAAI/bge-m3"
    assert report["corpus"] == "ops_knowledge_chunks(N=100)"
    assert report["thresholds"]["zh2en_crosslingual_recall_at5"].startswith(">=1/3")
    obs = report["observation"]
    assert obs["measurement_source"] == "observed"
    assert obs["confidence"] == "low"
    assert "照登：无实证" in obs["spec_note"]  # FP-8 注记


def test_render_markdown_sections(tmp_path: Path):
    results = [
        _case("G01", "zh2en"),
        _case("G02", "zh2en", recall_at5="fail", verdict="fail", fail_reasons=["recall@5: miss"]),
        _case(
            "G62",
            "negative",
            recall_at5=None,
            min_relevance=None,
            citation_in_hits=None,
            must_refuse="pass",
            gate_action="refuse",
        ),
    ]
    src = _write(tmp_path, _fake_report(results))
    md = render_markdown(build_final_report(load_report(src), src))
    assert "逐象限指标" in md
    assert "zh2en" in md and "negative" in md
    assert "门槛判定" in md and "≥ 1/3" in md or ">=1/3" in md
    assert "拒答正确率" in md
    assert "误答" in md and "疑似误拒" in md
    assert "Wilson 95% CI" in md  # confidence 老实标
    assert "未达成项与原因" in md and "G02" in md
    assert "契约漂移" in md
    assert "观测口径" in md


def test_cli_end_to_end(tmp_path: Path):
    results = [
        _case("G01", "zh2en"),
        _case(
            "G62",
            "negative",
            recall_at5=None,
            min_relevance=None,
            citation_in_hits=None,
            must_refuse="pass",
            gate_action="refuse",
        ),
    ]
    src = _write(tmp_path, _fake_report(results))
    out_yaml = tmp_path / "final.yaml"
    out_md = tmp_path / "final.md"
    rc = main(
        [
            "--report",
            str(src),
            "--out-yaml",
            str(out_yaml),
            "--out-md",
            str(out_md),
        ]
    )
    assert rc == 0
    loaded = yaml.safe_load(out_yaml.read_text(encoding="utf-8"))
    assert loaded["gates"]["zh2en_crosslingual_recall_at5"]["verdict"] == "MET"
    assert loaded["refusal"]["accuracy"] == 1.0
    md = out_md.read_text(encoding="utf-8")
    assert "**MET**" in md
    # 确定性：同输入重跑产物逐字节一致
    rc2 = main(
        [
            "--report",
            str(src),
            "--out-yaml",
            str(out_yaml),
            "--out-md",
            str(out_md),
        ]
    )
    assert rc2 == 0
    assert yaml.safe_load(out_yaml.read_text(encoding="utf-8")) == loaded


def test_real_report_r4_1_smoke():
    """存量过程稿 r4-1.yaml 可聚合（结构性冒烟 · 不对数值下结论）。"""
    src = Path("reports/r4-1.yaml")
    if not src.exists():
        pytest.skip("reports/r4-1.yaml 不在仓内")
    report = build_final_report(load_report(src), src)
    gate = report["gates"]["zh2en_crosslingual_recall_at5"]
    assert gate["n"] > 0
    assert gate["verdict"] in {"MET", "NOT_MET"}
    assert report["refusal"]["negative_n"] > 0
