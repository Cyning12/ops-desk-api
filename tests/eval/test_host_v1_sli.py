"""Host v1.0 SLI 四项：定义表机读 + 聚合有数 + Cost 对拍。"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from app.llm.budget import UsageCostRow, cost_per_successful_task
from evals.agent.sli.aggregate_sli import (
    DICT_KEYS,
    KEY_CAPABILITY_HIT,
    KEY_COST,
    KEY_E2E_P99,
    KEY_TASK_COMPLETION,
    aggregate_all_from_fixture,
    aggregate_capability_hit,
    aggregate_cost,
    aggregate_e2e_p99,
    aggregate_task_completion,
    percentile_nearest_rank,
)

ROOT = Path(__file__).resolve().parents[2]
SLI_YAML = ROOT / "docs" / "spec" / "agent-infra" / "eval" / "sli_host_v1_four_metrics_v1.yaml"
SLI_MD = ROOT / "docs" / "spec" / "agent-infra" / "eval" / "SLI_host_v1_four_metrics_v1.md"
GUIDE = ROOT / "docs" / "spec" / "agent-infra" / "eval" / "GUIDE_host_v1_sli_dashboard_v1.md"
FIXTURE = ROOT / "evals" / "agent" / "sli" / "fixtures" / "sli_sample.json"


def test_sli_definition_yaml_four_keys_aligned():
    data = yaml.safe_load(SLI_YAML.read_text(encoding="utf-8"))
    metrics = data["metrics"]
    assert len(metrics) == 4
    keys = [m["dict_key"] for m in metrics]
    assert keys == list(DICT_KEYS)
    assert data["cost_unknown_policy"].startswith("missing unit price")
    assert "done" in data["success_task_basis"]
    # E1 对齐：完成率/命中率用 avail.*；Cost 非 cost.usd_est；P99 扩展 latency.*
    align = data["e1_alignment"]
    assert align["avail.success"] == "task_completion"
    assert align["avail.capability_ok"] == "capability_hit"
    assert align["latency.e2e_p99_ms"] == "e2e_p99"
    assert "cost.usd_est" in align


def test_sli_definition_md_and_guide_exist():
    text = SLI_MD.read_text(encoding="utf-8")
    for key in DICT_KEYS:
        assert key in text
    guide = GUIDE.read_text(encoding="utf-8")
    assert "三步打开看板" in guide
    assert "字段清单" in guide
    for key in DICT_KEYS:
        assert key in guide


def test_percentile_nearest_rank_p99():
    # n=10 → ceil(0.99*10)=10 → 最大元
    vals = [100, 200, 150, 300, 120, 180, 220, 90, 400, 250]
    assert percentile_nearest_rank(vals, 99.0) == 400.0
    assert percentile_nearest_rank([], 99.0) is None


def test_aggregate_e2e_p99_from_fixture():
    out = aggregate_e2e_p99(
        [
            {"run_id": "a", "duration_ms": 10},
            {"run_id": "b", "duration_ms": 50},
            {"run_id": "c", "duration_ms": 30},
        ]
    )
    assert out["dict_key"] == KEY_E2E_P99
    assert out["value"] == 50.0
    assert out["sample_size"] == 3


def test_aggregate_task_completion_done_rate():
    out = aggregate_task_completion(
        [
            {"run_id": "1", "terminal_status": "done"},
            {"run_id": "2", "terminal_status": "done"},
            {"run_id": "3", "terminal_status": "error"},
            {"run_id": "4", "terminal_status": "done"},
            {"run_id": "5", "terminal_status": "cancelled"},
        ]
    )
    assert out["dict_key"] == KEY_TASK_COMPLETION
    assert out["successful_tasks"] == 3
    assert out["total_tasks"] == 5
    assert out["value"] == pytest.approx(0.6)


def test_aggregate_capability_hit_and_unknown():
    ok = aggregate_capability_hit(
        [
            {"capability_id": "a", "ok": True},
            {"capability_id": "b", "ok": True},
            {"capability_id": "c", "ok": False},
            {"capability_id": "d", "ok": True},
        ]
    )
    assert ok["dict_key"] == KEY_CAPABILITY_HIT
    assert ok["value"] == pytest.approx(0.75)
    unknown = aggregate_capability_hit(
        [{"capability_id": "a", "ok": True}, {"capability_id": "b"}]
    )
    assert unknown["value"] == "unknown"


def test_cost_parity_with_budget_function():
    rows = [
        {"run_id": "r1", "model": "deepseek-ai/DeepSeek-V4-Flash", "prompt_tokens": 1000, "completion_tokens": 1000},
        {"run_id": "r1", "model": "deepseek-ai/DeepSeek-V4-Flash", "prompt_tokens": 1000, "completion_tokens": 1000},
        {"run_id": "r2", "model": "Qwen/Qwen3.6-27B", "prompt_tokens": 1000, "completion_tokens": 0},
    ]
    via_sli = aggregate_cost(rows)
    via_budget = cost_per_successful_task(
        [
            UsageCostRow("r1", "deepseek-ai/DeepSeek-V4-Flash", 1000, 1000),
            UsageCostRow("r1", "deepseek-ai/DeepSeek-V4-Flash", 1000, 1000),
            UsageCostRow("r2", "Qwen/Qwen3.6-27B", 1000, 0),
        ]
    )
    assert via_sli["dict_key"] == KEY_COST
    assert via_sli["value"] == via_budget["cost_per_successful_task"]
    assert via_sli["value"] == pytest.approx(0.004)
    assert via_sli["basis"] == "estimate_only_not_billing"


def test_cost_missing_price_unknown_not_zero():
    out = aggregate_cost(
        [
            {"run_id": "r1", "model": "deepseek-ai/DeepSeek-V4-Flash", "prompt_tokens": 1000, "completion_tokens": 1000},
            {"run_id": "r2", "model": "no/such-model", "prompt_tokens": 1000, "completion_tokens": 1000},
        ]
    )
    assert out["value"] == "unknown"
    assert out["total_cost"] == "unknown"


def test_fixture_aggregate_all_four_metrics():
    assert FIXTURE.is_file()
    all_out = aggregate_all_from_fixture(FIXTURE)
    assert set(all_out) == set(DICT_KEYS)
    assert all_out[KEY_E2E_P99]["value"] == 400.0
    assert all_out[KEY_TASK_COMPLETION]["value"] == pytest.approx(0.6)
    assert all_out[KEY_CAPABILITY_HIT]["value"] == pytest.approx(0.75)
    assert all_out[KEY_COST]["value"] == pytest.approx(0.004)
