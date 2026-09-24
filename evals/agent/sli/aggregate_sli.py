"""Host v1.0 出口 SLI 四项聚合（离线 · 纯函数）。

定义真值：docs/spec/agent-infra/eval/SLI_host_v1_four_metrics_v1.md
Cost：对拍 app.llm.budget.cost_per_successful_task（缺单价 unknown 不伪造 0）。
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from app.llm.budget import UsageCostRow, cost_per_successful_task

FIXTURE_DEFAULT = Path(__file__).resolve().parent / "fixtures" / "sli_sample.json"

# 与机读定义表 dict_key 对齐（禁止同义异名）
KEY_E2E_P99 = "latency.e2e_p99_ms"
KEY_TASK_COMPLETION = "avail.success"
KEY_CAPABILITY_HIT = "avail.capability_ok"
KEY_COST = "host.cost_per_successful_task"

DICT_KEYS = (KEY_E2E_P99, KEY_TASK_COMPLETION, KEY_CAPABILITY_HIT, KEY_COST)


def percentile_nearest_rank(values: list[float], pct: float) -> float | None:
    """Pxx nearest-rank：ceil(pct/100 * n) 位（1-indexed）；空表 → None。"""
    if not values:
        return None
    if pct <= 0 or pct > 100:
        raise ValueError(f"pct must be in (0, 100], got {pct}")
    ordered = sorted(float(v) for v in values)
    n = len(ordered)
    rank = max(1, min(n, math.ceil(pct / 100.0 * n)))
    return ordered[rank - 1]


def aggregate_e2e_p99(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """端到端 P99：rows 须含 duration_ms（根/e2e span 投影）。"""
    durations = [float(r["duration_ms"]) for r in rows if r.get("duration_ms") is not None]
    value = percentile_nearest_rank(durations, 99.0)
    return {
        "dict_key": KEY_E2E_P99,
        "value": value,
        "sample_size": len(durations),
        "unit": "ms",
        "method": "nearest_rank_p99",
    }


def aggregate_task_completion(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """任务完成率：terminal_status=done 为成功（承 V1-C）。"""
    terminals = [r for r in rows if r.get("terminal_status")]
    if not terminals:
        return {
            "dict_key": KEY_TASK_COMPLETION,
            "value": None,
            "successful_tasks": 0,
            "total_tasks": 0,
            "basis": "done_over_terminal_runs",
        }
    done = sum(1 for r in terminals if str(r["terminal_status"]).strip().lower() == "done")
    total = len(terminals)
    return {
        "dict_key": KEY_TASK_COMPLETION,
        "value": done / total,
        "successful_tasks": done,
        "total_tasks": total,
        "basis": "done_over_terminal_runs",
    }


def aggregate_capability_hit(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """能力命中率：mean(ok)；缺 ok → unknown 不伪造 0。"""
    if not rows:
        return {
            "dict_key": KEY_CAPABILITY_HIT,
            "value": None,
            "hits": 0,
            "calls": 0,
            "basis": "mean_metadata_ok",
        }
    if any("ok" not in r or r.get("ok") is None for r in rows):
        return {
            "dict_key": KEY_CAPABILITY_HIT,
            "value": "unknown",
            "hits": None,
            "calls": len(rows),
            "basis": "mean_metadata_ok",
        }
    hits = sum(1 for r in rows if bool(r["ok"]))
    calls = len(rows)
    return {
        "dict_key": KEY_CAPABILITY_HIT,
        "value": hits / calls,
        "hits": hits,
        "calls": calls,
        "basis": "mean_metadata_ok",
    }


def aggregate_cost(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Cost per Successful Task：对拍 budget.cost_per_successful_task。"""
    usage_rows = [
        UsageCostRow(
            run_id=r.get("run_id"),
            model=r.get("model"),
            prompt_tokens=int(r.get("prompt_tokens") or 0),
            completion_tokens=int(r.get("completion_tokens") or 0),
        )
        for r in rows
    ]
    result = cost_per_successful_task(usage_rows)
    return {
        "dict_key": KEY_COST,
        "value": result["cost_per_successful_task"],
        "successful_tasks": result["successful_tasks"],
        "total_cost": result["total_cost"],
        "basis": result["basis"],
    }


def load_fixture(path: Path | None = None) -> dict[str, Any]:
    p = path or FIXTURE_DEFAULT
    return json.loads(p.read_text(encoding="utf-8"))


def aggregate_all(fixture: dict[str, Any]) -> dict[str, Any]:
    return {
        KEY_E2E_P99: aggregate_e2e_p99(list(fixture.get("e2e_latency") or [])),
        KEY_TASK_COMPLETION: aggregate_task_completion(list(fixture.get("task_terminals") or [])),
        KEY_CAPABILITY_HIT: aggregate_capability_hit(list(fixture.get("capability_calls") or [])),
        KEY_COST: aggregate_cost(list(fixture.get("cost_rows") or [])),
    }


def aggregate_all_from_fixture(path: Path | None = None) -> dict[str, Any]:
    return aggregate_all(load_fixture(path))
