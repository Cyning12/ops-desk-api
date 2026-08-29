"""E5：价表加载 + usage×单价导出（离线 · 禁止 LLM 估费）。"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest
import yaml

from evals.agent.cost.export_cost import (
    STATUS_OK,
    STATUS_PRICE_MISSING,
    STATUS_USAGE_MISSING,
    compute_cost_rows,
    exit_code_for,
    load_price_table,
    load_usage_records,
    main,
)

COST_DIR = Path(__file__).resolve().parents[2] / "evals" / "agent" / "cost"
PRICE_TABLE = COST_DIR / "price_table_v1.yaml"
USAGE_FIXTURE = COST_DIR / "fixtures" / "usage_sample.json"


def test_eval_cost_load_default_price_table():
    rows = load_price_table(PRICE_TABLE)
    assert len(rows) >= 1
    keys = {(r.provider, r.model) for r in rows}
    assert ("siliconflow", "deepseek-ai/DeepSeek-V4-Pro") in keys


def test_eval_cost_compute_ok_and_flags():
    table = load_price_table(PRICE_TABLE)
    usage = load_usage_records(USAGE_FIXTURE)
    out = compute_cost_rows(usage, table, as_of=date(2026, 8, 20))
    by_id = {r["id"]: r for r in out}

    ok = by_id["ok-sf"]
    assert ok["status"] == STATUS_OK
    assert ok["currency"] == "CNY"
    assert ok["cost_est"] != ""
    # 1000/1e6*4 + 500/1e6*16 = 0.004 + 0.008 = 0.012
    assert float(ok["cost_est"]) == pytest.approx(0.012)

    assert by_id["price-miss"]["status"] == STATUS_PRICE_MISSING
    assert by_id["price-miss"]["cost_est"] == ""

    assert by_id["usage-miss"]["status"] == STATUS_USAGE_MISSING
    assert by_id["usage-miss"]["cost_est"] == ""

    assert exit_code_for(out) == 1


def test_eval_cost_price_missing_only(tmp_path: Path):
    table = load_price_table(PRICE_TABLE)
    usage = [
        {
            "id": "x",
            "provider": "siliconflow",
            "model": "no-such-model",
            "input_tokens": 10,
            "output_tokens": 5,
        }
    ]
    out = compute_cost_rows(usage, table)
    assert out[0]["status"] == STATUS_PRICE_MISSING
    assert exit_code_for(out) == 1


def test_eval_cost_usage_missing_tokens_no_fake_price():
    table = load_price_table(PRICE_TABLE)
    usage = [
        {
            "id": "u",
            "provider": "siliconflow",
            "model": "deepseek-ai/DeepSeek-V4-Pro",
            # 故意缺 tokens
        }
    ]
    out = compute_cost_rows(usage, table)
    assert out[0]["status"] == STATUS_USAGE_MISSING
    assert out[0]["cost_est"] == ""
    assert exit_code_for(out) == 0


def test_eval_cost_invalid_price_table_raises(tmp_path: Path):
    bad = tmp_path / "bad.yaml"
    bad.write_text(
        yaml.dump(
            {
                "version": 1,
                "rows": [
                    {
                        "provider": "siliconflow",
                        "model": "m",
                        "input_per_1m": -1,
                        "output_per_1m": 1,
                        "currency": "CNY",
                        "effective_from": "2026-01-01",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="不可为负"):
        load_price_table(bad)


def test_eval_cost_cli_writes_csv(tmp_path: Path):
    out = tmp_path / "cost.csv"
    # 样例含 price_missing → exit 1，但仍写出文件
    code = main(
        [
            "--price-table",
            str(PRICE_TABLE),
            "--usage",
            str(USAGE_FIXTURE),
            "--out",
            str(out),
        ]
    )
    assert code == 1
    text = out.read_text(encoding="utf-8")
    assert "status" in text
    assert STATUS_PRICE_MISSING in text
    assert STATUS_USAGE_MISSING in text


def test_eval_cost_cli_load_error(tmp_path: Path):
    missing = tmp_path / "nope.json"
    code = main(
        [
            "--price-table",
            str(PRICE_TABLE),
            "--usage",
            str(missing),
        ]
    )
    assert code == 2


def test_eval_cost_fixture_json_is_list():
    data = json.loads(USAGE_FIXTURE.read_text(encoding="utf-8"))
    assert isinstance(data, list)
    assert len(data) >= 1
