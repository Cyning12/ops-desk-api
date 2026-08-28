#!/usr/bin/env python3
"""E3 Experiment runner：git 金标 → 字典 score；默认 dry-run。

SoT: evals/agent/golden/<module>/cases_v1.yaml
Dataset: golden-<module>-v1（router / strategy_builder / supervisor；e2e 不建）
Score: acc.route_match / acc.strategy.allowlist_match / acc.plan_match

用法：
  python evals/agent/run_experiment.py --module router
  python evals/agent/run_experiment.py --push
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Sequence
from contextlib import suppress
from pathlib import Path
from typing import Any, Protocol

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.eval.eval_agent_graders import (  # noqa: E402
    eval_allowlist_match,
    eval_plan_schema,
    eval_route_match,
    eval_subtask_types,
    eval_tool_ids_in_allowlist,
    require_expect,
)

GOLDEN_ROOT = Path(__file__).resolve().parent / "golden"
DATASET_MODULES = ("router", "strategy_builder", "supervisor")
SCORE_BY_MODULE = {
    "router": "acc.route_match",
    "strategy_builder": "acc.strategy.allowlist_match",
    "supervisor": "acc.plan_match",
}


def dataset_name(module: str) -> str:
    """git module → Langfuse Dataset 名。"""
    return f"golden-{module}-v1"


def langfuse_keys_present() -> bool:
    pub = (os.environ.get("LANGFUSE_PUBLIC_KEY") or "").strip().strip('"').strip("'")
    sec = (os.environ.get("LANGFUSE_SECRET_KEY") or "").strip().strip('"').strip("'")
    return bool(pub and sec)


class ExperimentSink(Protocol):
    def upsert_item(
        self, *, dataset: str, item_id: str, input: dict[str, Any], expected: dict[str, Any]
    ) -> None: ...

    def score(self, *, dataset: str, item_id: str, name: str, value: int) -> None: ...

    def flush(self) -> None: ...


class DryRunSink:
    """dry-run：零网络。"""

    def upsert_item(
        self, *, dataset: str, item_id: str, input: dict[str, Any], expected: dict[str, Any]
    ) -> None:
        return None

    def score(self, *, dataset: str, item_id: str, name: str, value: int) -> None:
        return None

    def flush(self) -> None:
        return None


class LangfuseSdkSink:
    """v3 client 薄封装；测试用 MagicMock 注入，不升 SDK v4。"""

    def __init__(self, client: Any) -> None:
        self._client = client
        self._datasets: set[str] = set()

    def upsert_item(
        self, *, dataset: str, item_id: str, input: dict[str, Any], expected: dict[str, Any]
    ) -> None:
        if dataset not in self._datasets:
            create_ds = getattr(self._client, "create_dataset", None)
            if create_ds is not None:
                with suppress(Exception):
                    create_ds(name=dataset)
            self._datasets.add(dataset)
        create_item = getattr(self._client, "create_dataset_item", None)
        if create_item is not None:
            create_item(
                dataset_name=dataset,
                input=input,
                expected_output=expected,
                id=item_id,
            )

    def score(self, *, dataset: str, item_id: str, name: str, value: int) -> None:
        fn = getattr(self._client, "create_score", None) or getattr(self._client, "score", None)
        if fn is None:
            raise RuntimeError("Langfuse client 无 score / create_score")
        fn(name=name, value=value, comment=f"{dataset}:{item_id}")

    def flush(self) -> None:
        flush = getattr(self._client, "flush", None)
        if flush is not None:
            flush()


def build_langfuse_sink() -> LangfuseSdkSink:
    from langfuse import Langfuse

    return LangfuseSdkSink(Langfuse())


def load_cases(module: str, *, golden_root: Path | None = None) -> list[dict[str, Any]]:
    root = golden_root or GOLDEN_ROOT
    path = root / module / "cases_v1.yaml"
    try:
        import yaml
    except ImportError as exc:
        raise SystemExit("需要 PyYAML") from exc
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    cases = data.get("cases") if isinstance(data, dict) else None
    if not cases:
        raise SystemExit(f"金标缺 cases: {path}")
    return list(cases)


def _replay_builder(case: dict[str, Any]) -> list[str]:
    setup = case.get("setup") or {}
    intent = setup.get("intent") or {}
    if intent.get("needs_tool") is False:
        return []
    candidates = setup.get("candidate_capability_ids")
    from app.ops.strategy.builder import (
        build_allowlist_from_candidates,
        get_policy_visible_ids,
    )

    allowed, _ = build_allowlist_from_candidates(
        candidates, visible_ids=get_policy_visible_ids()
    )
    return allowed


def _replay_supervisor(case: dict[str, Any]) -> list[dict[str, Any]]:
    setup = case.get("setup") or {}
    allowlist = setup.get("allowed_capability_ids")
    query = str(case.get("query") or "")
    if not allowlist:
        return [{"id": "t1", "type": "rag", "input": query}]
    raw = (case.get("mock") or {}).get("llm_complete")
    if not raw:
        raise ValueError(f"fixture {case.get('id')} 缺 mock.llm_complete")
    payload = json.loads(raw)
    subtasks = payload.get("subtasks")
    if not isinstance(subtasks, list):
        raise ValueError(f"fixture {case.get('id')} mock 缺 subtasks")
    return list(subtasks)


def replay_actual(
    module: str,
    case: dict[str, Any],
    overrides: dict[str, Any] | None = None,
) -> Any:
    """从 fixture mock/setup 得到 actual；overrides 按 case id 覆盖（测失败路径）。"""
    case_id = str(case.get("id") or "")
    if overrides is not None and case_id in overrides:
        return overrides[case_id]
    if module == "router":
        raw = (case.get("mock") or {}).get("llm_complete")
        if not raw:
            raise ValueError(f"fixture {case_id} 缺 mock.llm_complete")
        payload = json.loads(raw)
        return payload["route"]
    if module == "strategy_builder":
        return _replay_builder(case)
    if module == "supervisor":
        return _replay_supervisor(case)
    raise ValueError(f"未知 module: {module}")


def score_case(module: str, case: dict[str, Any], actual: Any) -> tuple[str, int]:
    """对照 expect 打字典 score；缺 expect 由 require_expect 抛错。"""
    name = SCORE_BY_MODULE[module]
    if module == "router":
        expect = require_expect(case, "route")
        return name, eval_route_match(str(actual), str(expect["route"]))
    if module == "strategy_builder":
        expect = require_expect(case, "allowed_capability_ids")
        return name, eval_allowlist_match(list(actual), list(expect["allowed_capability_ids"]))
    if module == "supervisor":
        expect = require_expect(case, "subtask_types")
        subtasks = list(actual)
        allowlist = (case.get("setup") or {}).get("allowed_capability_ids") or []
        ok = (
            eval_plan_schema(subtasks) == 1
            and eval_subtask_types(subtasks, expect["subtask_types"]) == 1
            and eval_tool_ids_in_allowlist(subtasks, allowlist) == 1
        )
        return name, int(ok)
    raise ValueError(f"未知 module: {module}")


def run_experiment(
    *,
    modules: Sequence[str] | None = None,
    push: bool = False,
    actuals: dict[str, Any] | None = None,
    sink: ExperimentSink | None = None,
    keys_present: bool | None = None,
    golden_root: Path | None = None,
    stdout_json: bool = True,
) -> tuple[int, dict[str, Any]]:
    """跑 Dataset 映射 + grader。返回 (exit_code, report)。"""
    has_keys = langfuse_keys_present() if keys_present is None else keys_present
    if push and not has_keys:
        print(
            "--push 需要 LANGFUSE_PUBLIC_KEY 与 LANGFUSE_SECRET_KEY；未打网",
            file=sys.stderr,
        )
        report = {"ok": False, "mode": "push", "error": "missing_langfuse_keys"}
        if stdout_json:
            print(json.dumps(report, ensure_ascii=False))
        return 2, report

    chosen = list(modules) if modules else list(DATASET_MODULES)
    unknown = [m for m in chosen if m not in DATASET_MODULES]
    if unknown:
        print(f"非法 module: {unknown}；仅 {DATASET_MODULES}", file=sys.stderr)
        return 2, {"ok": False, "error": "unknown_module"}

    if sink is None:
        sink = build_langfuse_sink() if push else DryRunSink()

    module_rows: list[dict[str, Any]] = []
    any_fail = False
    try:
        for module in chosen:
            cases = load_cases(module, golden_root=golden_root)
            ds = dataset_name(module)
            items: list[dict[str, Any]] = []
            failed = 0
            for case in cases:
                case_id = str(case.get("id") or "<unknown>")
                actual = replay_actual(module, case, actuals)
                score_name, value = score_case(module, case, actual)
                if value != 1:
                    failed += 1
                    any_fail = True
                expect = case.get("expect") if isinstance(case.get("expect"), dict) else {}
                sink.upsert_item(
                    dataset=ds,
                    item_id=case_id,
                    input={"query": case.get("query"), "module": module},
                    expected=dict(expect),
                )
                sink.score(dataset=ds, item_id=case_id, name=score_name, value=value)
                items.append(
                    {
                        "id": case_id,
                        "dataset": ds,
                        "score_name": score_name,
                        "value": value,
                    }
                )
            module_rows.append(
                {
                    "module": module,
                    "dataset": ds,
                    "score_name": SCORE_BY_MODULE[module],
                    "passed": len(cases) - failed,
                    "failed": failed,
                    "items": items,
                }
            )
        sink.flush()
    except (AssertionError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        report = {"ok": False, "mode": "push" if push else "dry-run", "error": str(exc)}
        if stdout_json:
            print(json.dumps(report, ensure_ascii=False))
        return 1, report

    report = {
        "ok": not any_fail,
        "mode": "push" if push else "dry-run",
        "sot": "git",
        "modules": module_rows,
    }
    if stdout_json:
        print(json.dumps(report, ensure_ascii=False))
    return (1 if any_fail else 0), report


def _load_actuals(path: str) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit("--actuals 须为 JSON object（case_id → actual）")
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="E3 Langfuse Experiment runner（默认 dry-run）")
    parser.add_argument(
        "--module",
        action="append",
        choices=DATASET_MODULES,
        help="可重复；默认 router + strategy_builder + supervisor",
    )
    parser.add_argument("--push", action="store_true", help="写入 Langfuse；须已有 key")
    parser.add_argument("--actuals", default="", help="可选 JSON：case_id → 覆盖 actual")
    args = parser.parse_args(argv)
    actuals = _load_actuals(args.actuals) if args.actuals else None
    code, _ = run_experiment(modules=args.module, push=args.push, actuals=actuals)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
