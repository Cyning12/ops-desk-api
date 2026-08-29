#!/usr/bin/env python3
"""E5 费用导出：fixture usage × Host 价表 → CSV/stdout。

禁止用 LLM 估费。缺键 → status=price_missing；缺 tokens → usage_missing。

用法：
  python evals/agent/cost/export_cost.py
  python evals/agent/cost/export_cost.py --usage evals/agent/cost/fixtures/usage_sample.json
  python evals/agent/cost/export_cost.py --out /tmp/cost.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DEFAULT_PRICE_TABLE = Path(__file__).resolve().parent / "price_table_v1.yaml"
DEFAULT_USAGE = Path(__file__).resolve().parent / "fixtures" / "usage_sample.json"

STATUS_OK = "ok"
STATUS_PRICE_MISSING = "price_missing"
STATUS_USAGE_MISSING = "usage_missing"

CSV_FIELDS = [
    "id",
    "provider",
    "model",
    "module",
    "date",
    "input_tokens",
    "output_tokens",
    "currency",
    "cost_est",
    "status",
]


@dataclass(frozen=True)
class PriceRow:
    """价表一行。"""

    provider: str
    model: str
    input_per_1m: Decimal
    output_per_1m: Decimal
    currency: str
    effective_from: date


def _parse_date(raw: Any, *, field: str) -> date:
    """解析 YYYY-MM-DD；非法则抛 ValueError。"""
    if raw is None or raw == "":
        raise ValueError(f"{field} 缺失")
    if isinstance(raw, date) and not isinstance(raw, datetime):
        return raw
    text = str(raw).strip()
    try:
        return date.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"{field} 非法: {raw!r}") from exc


def _as_decimal(raw: Any, *, field: str) -> Decimal:
    try:
        value = Decimal(str(raw))
    except (InvalidOperation, TypeError) as exc:
        raise ValueError(f"{field} 非法: {raw!r}") from exc
    if value < 0:
        raise ValueError(f"{field} 不可为负: {raw!r}")
    return value


def load_price_table(path: Path | str) -> list[PriceRow]:
    """加载价表；结构/单价/生效日非法 → ValueError。"""
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("需要 PyYAML") from exc

    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("rows"), list):
        raise ValueError("价表须含 rows: list")

    rows: list[PriceRow] = []
    for i, item in enumerate(payload["rows"]):
        if not isinstance(item, dict):
            raise ValueError(f"rows[{i}] 须为 mapping")
        provider = str(item.get("provider") or "").strip()
        model = str(item.get("model") or "").strip()
        if not provider or not model:
            raise ValueError(f"rows[{i}] 缺 provider/model")
        rows.append(
            PriceRow(
                provider=provider,
                model=model,
                input_per_1m=_as_decimal(item.get("input_per_1m"), field=f"rows[{i}].input_per_1m"),
                output_per_1m=_as_decimal(
                    item.get("output_per_1m"), field=f"rows[{i}].output_per_1m"
                ),
                currency=str(item.get("currency") or "CNY").strip(),
                effective_from=_parse_date(
                    item.get("effective_from"), field=f"rows[{i}].effective_from"
                ),
            )
        )
    if not rows:
        raise ValueError("价表 rows 为空")
    return rows


def load_usage_records(path: Path | str) -> list[dict[str, Any]]:
    """加载 usage fixture（JSON 数组）。"""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("usage 须为 JSON 数组")
    out: list[dict[str, Any]] = []
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            raise ValueError(f"usage[{i}] 须为 object")
        out.append(item)
    return out


def _lookup_price(
    table: list[PriceRow],
    *,
    provider: str,
    model: str,
    on: date,
) -> PriceRow | None:
    """取 provider+model 且 effective_from≤on 的最新一行。"""
    candidates = [
        row
        for row in table
        if row.provider == provider and row.model == model and row.effective_from <= on
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda r: r.effective_from)


def _tokens_present(record: dict[str, Any]) -> bool:
    """input/output tokens 均存在且可解析为非负整数。"""
    for key in ("input_tokens", "output_tokens"):
        if key not in record or record[key] is None:
            return False
        try:
            if int(record[key]) < 0:
                return False
        except (TypeError, ValueError):
            return False
    return True


def compute_cost_rows(
    usage: list[dict[str, Any]],
    table: list[PriceRow],
    *,
    as_of: date | None = None,
) -> list[dict[str, Any]]:
    """usage × 价表 → 账本行；不算假价。"""
    today = as_of or date.today()
    million = Decimal("1000000")
    results: list[dict[str, Any]] = []

    for idx, rec in enumerate(usage):
        rid = str(rec.get("id") or f"row-{idx}")
        provider = str(rec.get("provider") or "").strip()
        model = str(rec.get("model") or "").strip()
        module = str(rec.get("module") or "")
        raw_date = rec.get("date")
        on = _parse_date(raw_date, field=f"usage[{idx}].date") if raw_date else today

        base: dict[str, Any] = {
            "id": rid,
            "provider": provider,
            "model": model,
            "module": module,
            "date": on.isoformat(),
            "input_tokens": "",
            "output_tokens": "",
            "currency": "",
            "cost_est": "",
            "status": STATUS_OK,
        }

        if not _tokens_present(rec):
            base["status"] = STATUS_USAGE_MISSING
            results.append(base)
            continue

        input_tokens = int(rec["input_tokens"])
        output_tokens = int(rec["output_tokens"])
        base["input_tokens"] = input_tokens
        base["output_tokens"] = output_tokens

        price = _lookup_price(table, provider=provider, model=model, on=on)
        if price is None:
            base["status"] = STATUS_PRICE_MISSING
            results.append(base)
            continue

        cost = (Decimal(input_tokens) / million) * price.input_per_1m + (
            Decimal(output_tokens) / million
        ) * price.output_per_1m
        base["currency"] = price.currency
        # 固定小数，避免科学计数；禁止 LLM 估价
        base["cost_est"] = format(cost.quantize(Decimal("0.000001")), "f")
        base["status"] = STATUS_OK
        results.append(base)

    return results


def rows_to_csv(rows: list[dict[str, Any]], out: Any) -> None:
    """写 CSV（含表头）。"""
    writer = csv.DictWriter(out, fieldnames=CSV_FIELDS, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({k: row.get(k, "") for k in CSV_FIELDS})


def exit_code_for(rows: list[dict[str, Any]]) -> int:
    """有 price_missing → 1；仅 usage_missing/ok → 0。"""
    if any(r.get("status") == STATUS_PRICE_MISSING for r in rows):
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="E5 usage×价表费用导出（非 LLM）")
    parser.add_argument(
        "--price-table",
        type=Path,
        default=DEFAULT_PRICE_TABLE,
        help="价表 YAML 路径",
    )
    parser.add_argument(
        "--usage",
        type=Path,
        default=DEFAULT_USAGE,
        help="usage fixture JSON 路径",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="写出 CSV；默认 stdout",
    )
    args = parser.parse_args(argv)

    try:
        table = load_price_table(args.price_table)
        usage = load_usage_records(args.usage)
        rows = compute_cost_rows(usage, table)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"export_cost error: {exc}", file=sys.stderr)
        return 2

    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open("w", encoding="utf-8", newline="") as fh:
            rows_to_csv(rows, fh)
        print(f"wrote {len(rows)} rows → {args.out}", file=sys.stderr)
    else:
        rows_to_csv(rows, sys.stdout)

    return exit_code_for(rows)


if __name__ == "__main__":
    raise SystemExit(main())
