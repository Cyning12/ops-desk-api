"""memory-golden-eval · CI 测试（全 fake 确定性 · 不连外网 · 不连 DB）。

覆盖（task E4 / SPEC §2 D4）：
- 金样 schema 校验：四类数量下限 / 必填字段 / 非法样本早失败（GoldenSchemaError）
- fake runner 端到端指标三态：全过（仓库金样）/ 全错（构造样本）/ 混合
- fake 确定性：同输入两跑指标逐字节一致
- 扫参 27 组产物完整性 + patched_fusion_constants 覆盖生效 / 默认等价 / 现场恢复
- live 缺 key 显式失败：进程内 preflight 抛错 + CLI 子进程退出码 2
  （key 检查在 preflight 首位，子进程不触网不触 DB）
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from app.ops.memory import service as memory_service
from evals.memory.run_eval import (
    CATEGORIES,
    MIN_CASE_COUNTS,
    THRESHOLDS,
    GoldenSchemaError,
    LiveUnavailableError,
    build_sweep_scenarios,
    compute_metrics,
    evaluate_thresholds,
    live_preflight,
    load_golden,
    now_utc,
    patched_fusion_constants,
    run_fake_eval,
    run_sweep,
    validate_golden,
)

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "evals/memory/golden_v1.yaml"
RUN_EVAL = ROOT / "evals/memory/run_eval.py"


def _shipped_cases() -> list[dict]:
    return validate_golden(load_golden(GOLDEN))


# ---------------------------------------------------------------------------
# 金样 schema 校验
# ---------------------------------------------------------------------------


def test_golden_schema_shipped_counts_and_fields():
    cases = _shipped_cases()
    assert len(cases) >= 40
    counts = dict.fromkeys(CATEGORIES, 0)
    for case in cases:
        counts[case["category"]] += 1
    for cat, minimum in MIN_CASE_COUNTS.items():
        assert counts[cat] >= minimum, f"{cat}: {counts[cat]} < {minimum}"
    ids = [c["id"] for c in cases]
    assert len(ids) == len(set(ids))  # id 唯一
    # 负样本纪律：expect_facts 必须显式为空
    for case in cases:
        if case["category"] == "should_not_remember":
            assert case["expect_facts"] == []
        if case["category"] == "supersede":
            assert case["setup_fact"]["key"] == case["expect_facts"][0]["key"]
        if case["category"] == "paraphrase":
            assert case["expect_hit_key"] == case["fact"]["key"]


def _minimal_valid_cases() -> list[dict]:
    """各类 1 条的合法骨架（再按测试需要变异）。"""
    return [
        {
            "id": "SR1",
            "category": "should_remember",
            "query": "q",
            "answer": "a",
            "expect_facts": [{"key": "project.primary_repo", "value": "x/y"}],
            "fake_facts": [{"key": "project.primary_repo", "value": "x/y"}],
        },
        {
            "id": "NG1",
            "category": "should_not_remember",
            "query": "q",
            "answer": "a",
            "expect_facts": [],
            "fake_facts": [],
        },
        {
            "id": "SP1",
            "category": "supersede",
            "setup_fact": {"key": "deploy.target", "value": "staging"},
            "query": "q",
            "answer": "a",
            "expect_facts": [{"key": "deploy.target", "value": "prod"}],
            "fake_facts": [{"key": "deploy.target", "value": "prod"}],
        },
        {
            "id": "PR1",
            "category": "paraphrase",
            "fact": {"key": "project.primary_repo", "value": "x/y"},
            "query": "我主要负责哪个仓库？",
            "expect_hit_key": "project.primary_repo",
        },
    ]


def test_golden_schema_rejects_bad_samples():
    # 数量不足（骨架各类 1 条 < 下限）
    with pytest.raises(GoldenSchemaError, match="下限"):
        validate_golden({"version": 1, "golden": _minimal_valid_cases()})

    # id 重复 / 非法 category / 负样本带 expect / supersede key 不一致 / 非法 key
    bad = _minimal_valid_cases()
    bad[1] = dict(bad[1], id="SR1")  # 重复 id
    with pytest.raises(GoldenSchemaError, match="id 重复"):
        validate_golden({"version": 1, "golden": bad})

    bad = _minimal_valid_cases()
    bad[0] = dict(bad[0], category="maybe")
    with pytest.raises(GoldenSchemaError, match="category 非法"):
        validate_golden({"version": 1, "golden": bad})

    bad = _minimal_valid_cases()
    bad[1] = dict(bad[1], expect_facts=[{"key": "project.x_y", "value": "z"}])
    with pytest.raises(GoldenSchemaError, match=r"必须为 \[\]"):
        validate_golden({"version": 1, "golden": bad})

    bad = _minimal_valid_cases()
    bad[2] = dict(bad[2], expect_facts=[{"key": "deploy.other", "value": "prod"}])
    with pytest.raises(GoldenSchemaError, match="同 key"):
        validate_golden({"version": 1, "golden": bad})

    bad = _minimal_valid_cases()
    bad[0] = dict(bad[0], expect_facts=[{"key": "Bad Key", "value": "x"}])
    with pytest.raises(GoldenSchemaError, match="不过闸"):
        validate_golden({"version": 1, "golden": bad})

    bad = _minimal_valid_cases()
    bad[3] = dict(bad[3], expect_hit_key="project.other_thing")
    with pytest.raises(GoldenSchemaError, match="expect_hit_key"):
        validate_golden({"version": 1, "golden": bad})


# ---------------------------------------------------------------------------
# fake runner 端到端：三态 + 确定性
# ---------------------------------------------------------------------------


def test_fake_eval_all_pass_on_shipped_golden():
    results = run_fake_eval(_shipped_cases(), run_id="t-all-pass")
    metrics = compute_metrics(results)
    assert metrics["extraction_precision"] == 1.0
    assert metrics["noise_write_rate"] == 0.0
    assert metrics["miss_rate"] == 0.0
    assert metrics["paraphrase_top1"] == 1.0
    assert metrics["paraphrase_top3"] == 1.0
    assert metrics["supersede_accuracy"] == 1.0
    assert metrics["errors"] == 0
    thresholds = evaluate_thresholds(metrics)
    assert set(thresholds) == set(THRESHOLDS)
    assert all(row["met"] for row in thresholds.values())


def test_fake_eval_deterministic_across_runs():
    cases = _shipped_cases()
    first = compute_metrics(run_fake_eval(cases, run_id="t-det"))
    second = compute_metrics(run_fake_eval(cases, run_id="t-det"))
    assert first == second  # 指标逐字节一致（fake 全确定）


def _fail_cases() -> list[dict]:
    """四类各一、全部朝错里构造（指标应全线不达标）。"""
    return [
        {
            "id": "SR-BAD",
            "category": "should_remember",
            "query": "q",
            "answer": "a",
            "expect_facts": [{"key": "project.primary_repo", "value": "cyning/ops-desk"}],
            # 抽错值 → 漏记 + 噪声写入
            "fake_facts": [{"key": "project.primary_repo", "value": "wrong/repo"}],
        },
        {
            "id": "NG-BAD",
            "category": "should_not_remember",
            "query": "q",
            "answer": "a",
            "expect_facts": [],
            # 过闸但语义噪声（prompt 级失守形态）→ 噪声写入
            "fake_facts": [{"key": "general.knowledge", "value": "1991"}],
        },
        {
            "id": "SP-BAD",
            "category": "supersede",
            "setup_fact": {"key": "deploy.target", "value": "staging"},
            "query": "q",
            "answer": "a",
            "expect_facts": [{"key": "deploy.target", "value": "prod-cn"}],
            "fake_facts": [],  # 新值未写入 → supersede 不正确
        },
        {
            "id": "PR-BAD",
            "category": "paraphrase",
            "fact": {"key": "user.display_tz", "value": "Asia/Shanghai"},
            # 复述 query 与事实文本命中不同关键词组 → 向量相似 0 → 不命中
            "query": "我主要负责哪个仓库？",
            "expect_hit_key": "user.display_tz",
        },
    ]


def test_fake_eval_all_fail_metrics_below_thresholds():
    results = run_fake_eval(_fail_cases(), run_id="t-all-fail")
    assert [r.verdict for r in results] == ["fail"] * 4
    metrics = compute_metrics(results)
    assert metrics["extraction_precision"] == 0.0
    assert metrics["noise_write_rate"] == 1.0
    assert metrics["miss_rate"] == 1.0
    assert metrics["paraphrase_top1"] == 0.0
    assert metrics["paraphrase_top3"] == 0.0
    assert metrics["supersede_accuracy"] == 0.0
    thresholds = evaluate_thresholds(metrics)
    assert not any(row["met"] for row in thresholds.values())


def test_fake_eval_mixed_metrics_in_between():
    cases = [
        _minimal_valid_cases()[0],  # SR 过
        _fail_cases()[0],  # SR 错
        _minimal_valid_cases()[1],  # NG 过
        _fail_cases()[1],  # NG 错
        _minimal_valid_cases()[2],  # SP 过
        _fail_cases()[2],  # SP 错
        _minimal_valid_cases()[3],  # PR 过（repo 组对齐）
        _fail_cases()[3],  # PR 错
    ]
    results = run_fake_eval(cases, run_id="t-mixed")
    metrics = compute_metrics(results)
    assert metrics["miss_rate"] == 0.5
    assert metrics["noise_write_rate"] == 0.5
    assert metrics["supersede_accuracy"] == 0.5
    assert metrics["paraphrase_top3"] == 0.5
    # good = SR过1 + SP过1 = 2；noise = SR错值1 + NG噪声1 = 2
    assert metrics["extraction_precision"] == 0.5
    thresholds = evaluate_thresholds(metrics)
    assert not thresholds["noise_write_rate"]["met"]
    assert not thresholds["supersede_accuracy"]["met"]


# ---------------------------------------------------------------------------
# 扫参：27 组完整性 + 常量覆盖语义
# ---------------------------------------------------------------------------


def test_sweep_27_combos_complete_and_recommendation_structure():
    para = [c for c in _shipped_cases() if c["category"] == "paraphrase"]
    sweep = run_sweep(para)
    combos = sweep["combos"]
    assert len(combos) == 27
    triples = {
        (c["half_life_days"], c["sim_floor"], c["source_weight_extract"]) for c in combos
    }
    assert len(triples) == 27  # 网格无重无漏
    for c in combos:
        assert c["paraphrase_top1"] is not None
        assert c["paraphrase_top3"] is not None
        assert c["recency_top1"] is not None
        assert isinstance(c["meets_internal_bar"], bool)
    rec = sweep["recommended"]
    if rec is not None:
        assert set(rec["params"]) == {
            "half_life_days",
            "sim_floor",
            "source_weight_extract",
        }
        assert set(rec["scores"]) == {"paraphrase_top1", "paraphrase_top3", "recency_top1"}
        assert rec["reason"]
    assert sweep["reasons"]  # 理由结构非空（含不推荐时的如实说明）
    assert sweep["current_defaults"] == {
        "half_life_days": memory_service.HALF_LIFE_DAYS,
        "sim_floor": memory_service.SIM_FLOOR,
        "source_weight_extract": memory_service.SOURCE_WEIGHT_EXTRACTED,
    }


def test_patched_fusion_constants_override_and_restore():
    para = [
        {
            "id": "PRX",
            "category": "paraphrase",
            "fact": {"key": "project.primary_repo", "value": "x/y"},
            "query": "我主要负责哪个仓库？",
            "expect_hit_key": "project.primary_repo",
        }
    ]
    now = now_utc()
    scenarios = build_sweep_scenarios(para, now=now)
    aged90 = next(
        s for s in scenarios if s.kind == "paraphrase_aged" and s.target_id.endswith("t-90")
    )
    from evals.memory.run_eval import _rank_scenario

    defaults = (
        memory_service.HALF_LIFE_DAYS,
        memory_service.SIM_FLOOR,
        memory_service.SOURCE_WEIGHT_EXTRACTED,
    )
    # 默认常量：90 天陈化目标被衰减压掉（不在 top3）
    default_rank = _rank_scenario(aged90, limit=3, now=now)
    assert aged90.target_id not in default_rank
    assert defaults[0] == memory_service.HALF_LIFE_DAYS  # 未 patch 不漂移

    # 覆盖（90d 半衰 + 低地板 + 抽取等权）：同一真 _fuse_recall 排名翻转
    with patched_fusion_constants(
        half_life_days=90.0, sim_floor=0.3, source_weight_extract=1.0
    ):
        patched_rank = _rank_scenario(aged90, limit=3, now=now)
        assert patched_rank[0] == aged90.target_id
    # with 块外现场恢复（零生产默认值改动）
    assert defaults == (
        memory_service.HALF_LIFE_DAYS,
        memory_service.SIM_FLOOR,
        memory_service.SOURCE_WEIGHT_EXTRACTED,
    )

    # 默认值覆盖 ≡ 未覆盖（等价性：patch 机制本身不改变语义）
    with patched_fusion_constants(
        half_life_days=defaults[0],
        sim_floor=defaults[1],
        source_weight_extract=defaults[2],
    ):
        assert _rank_scenario(aged90, limit=3, now=now) == default_rank


# ---------------------------------------------------------------------------
# live 缺 key 显式失败（不连外网：key 检查在 preflight 首位）
# ---------------------------------------------------------------------------


def test_live_preflight_missing_key_explicit(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("SILICONFLOW_API_KEY", raising=False)
    with pytest.raises(LiveUnavailableError, match="SILICONFLOW_API_KEY"):
        live_preflight()


def test_live_cli_missing_key_exit_2():
    """子进程真跑 CLI：空 key → 退出码 2 + stderr 显式报错（不静默降级冒充）。

    key 检查在 preflight 首位：本用例不触网、不触 DB。env 置空串可穿透
    app.config 的 load_dotenv（override=False，空串视为已设置）。
    """
    env = os.environ.copy()
    env["SILICONFLOW_API_KEY"] = ""
    proc = subprocess.run(
        [
            sys.executable,
            str(RUN_EVAL),
            "--backend",
            "live",
            "--golden",
            str(GOLDEN),
            "--limit",
            "1",
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert proc.returncode == 2, proc.stderr[-500:]
    assert "SILICONFLOW_API_KEY" in proc.stderr
    assert "显式失败" in proc.stderr
