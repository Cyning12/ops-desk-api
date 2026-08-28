"""E3 Experiment runner：dry-run / mock Langfuse / 失败非 0。"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock

from evals.agent.run_experiment import (
    DATASET_MODULES,
    SCORE_BY_MODULE,
    dataset_name,
    langfuse_keys_present,
    run_experiment,
)


class RecordingSink:
    """记录 upsert/score，不联网。"""

    def __init__(self) -> None:
        self.items: list[tuple[str, str]] = []
        self.scores: list[dict[str, Any]] = []
        self.flushed = False

    def upsert_item(
        self, *, dataset: str, item_id: str, input: dict[str, Any], expected: dict[str, Any]
    ) -> None:
        self.items.append((dataset, item_id))

    def score(self, *, dataset: str, item_id: str, name: str, value: int) -> None:
        self.scores.append(
            {"dataset": dataset, "item_id": item_id, "name": name, "value": value}
        )

    def flush(self) -> None:
        self.flushed = True


def test_eval_experiment_dataset_and_score_names() -> None:
    assert dataset_name("router") == "golden-router-v1"
    assert dataset_name("strategy_builder") == "golden-strategy_builder-v1"
    assert dataset_name("supervisor") == "golden-supervisor-v1"
    assert SCORE_BY_MODULE["router"] == "acc.route_match"
    assert SCORE_BY_MODULE["strategy_builder"] == "acc.strategy.allowlist_match"
    assert SCORE_BY_MODULE["supervisor"] == "acc.plan_match"
    assert "e2e" not in DATASET_MODULES


def test_eval_experiment_dry_run_all_pass_no_keys(monkeypatch, capsys) -> None:
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    assert langfuse_keys_present() is False
    code, report = run_experiment(keys_present=False, stdout_json=True)
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert code == 0
    assert report["ok"] is True
    assert report["mode"] == "dry-run"
    assert report["sot"] == "git"
    assert payload["ok"] is True
    names = {row["score_name"] for row in report["modules"]}
    assert names == set(SCORE_BY_MODULE.values())
    for row in report["modules"]:
        assert row["failed"] == 0
        assert row["passed"] >= 1
        for item in row["items"]:
            assert item["value"] == 1


def test_eval_experiment_router_route_match(capsys) -> None:
    code, report = run_experiment(modules=["router"], stdout_json=True)
    capsys.readouterr()
    assert code == 0
    row = report["modules"][0]
    assert row["dataset"] == "golden-router-v1"
    assert row["score_name"] == "acc.route_match"
    assert row["passed"] == 3
    assert {i["id"] for i in row["items"]} == {
        "router_rag_compaction",
        "router_direct_hello",
        "router_refuse_password",
    }


def test_eval_experiment_grader_mismatch_nonzero(capsys) -> None:
    code, report = run_experiment(
        modules=["router"],
        actuals={"router_rag_compaction": "direct"},
        stdout_json=True,
    )
    capsys.readouterr()
    assert code == 1
    assert report["ok"] is False
    values = {i["id"]: i["value"] for i in report["modules"][0]["items"]}
    assert values["router_rag_compaction"] == 0
    assert values["router_direct_hello"] == 1


def test_eval_experiment_push_without_keys_no_network(monkeypatch, capsys) -> None:
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    sink = RecordingSink()
    code, report = run_experiment(push=True, sink=sink, keys_present=False, stdout_json=True)
    err = capsys.readouterr().err
    assert code == 2
    assert report["error"] == "missing_langfuse_keys"
    assert "未打网" in err
    assert sink.scores == []
    assert sink.flushed is False


def test_eval_experiment_push_mock_langfuse(capsys) -> None:
    client = MagicMock()
    from evals.agent.run_experiment import LangfuseSdkSink

    sink = LangfuseSdkSink(client)
    code, report = run_experiment(
        modules=["router"],
        push=True,
        sink=sink,
        keys_present=True,
        stdout_json=True,
    )
    capsys.readouterr()
    assert code == 0
    assert report["mode"] == "push"
    client.create_dataset.assert_called_once_with(name="golden-router-v1")
    assert client.create_dataset_item.call_count == 3
    score_fn = client.create_score
    assert score_fn.call_count == 3
    names = {c.kwargs["name"] for c in score_fn.call_args_list}
    assert names == {"acc.route_match"}
    values = {c.kwargs["value"] for c in score_fn.call_args_list}
    assert values == {1}


def test_eval_experiment_missing_expect_nonzero(tmp_path, capsys) -> None:
    (tmp_path / "router").mkdir()
    (tmp_path / "router" / "cases_v1.yaml").write_text(
        "version: test\nmodule: router\ncases:\n"
        "  - id: broken\n    query: x\n    mock:\n      llm_complete: '{\"route\": \"rag\"}'\n",
        encoding="utf-8",
    )
    code, report = run_experiment(
        modules=["router"],
        golden_root=tmp_path,
        stdout_json=True,
    )
    err = capsys.readouterr().err
    assert code == 1
    assert report["ok"] is False
    assert "expect" in err
