"""E2 金标 runner：mock LLM，喂 fixture 过确定性评估器。"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import yaml
from langchain_core.messages import AIMessage, HumanMessage

from app.ops.lc_evidence_chain.types import ChainResult
from app.ops.lg_rag.nodes import ROUTES
from app.ops.lg_rag.schemas import IntentV1
from tests.eval.eval_agent_graders import (
    eval_allowlist_match,
    eval_plan_schema,
    eval_route_match,
    eval_subtask_types,
    eval_tool_ids_in_allowlist,
    require_expect,
)

GOLDEN_ROOT = Path(__file__).resolve().parents[2] / "evals" / "agent" / "golden"

_PROVIDER_PATCH = "app.ops.lg_rag.nodes.get_llm_provider"
_MULTI_PROVIDER_PATCH = "app.ops.lg_rag.multi.nodes.get_llm_provider"
_CHAIN_PATCH = "app.ops.lg_rag.nodes.ainvoke_evidence_answer"
_INTENT_COMPLETE_PATCH = "app.ops.strategy.intent.acomplete_structured"
_CANDIDATE_PATCH = "app.ops.strategy.builder.get_candidate_capability_ids"


def _load_cases(module: str) -> list[dict[str, Any]]:
    path = GOLDEN_ROOT / module / "cases_v1.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    cases = data.get("cases") if isinstance(data, dict) else None
    if not cases:
        pytest.fail(f"金标缺 cases: {path}")
    return list(cases)


def _span_cm() -> MagicMock:
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=None)
    cm.__exit__ = MagicMock(return_value=False)
    return cm


def _provider(*outputs: str) -> SimpleNamespace:
    return SimpleNamespace(complete=AsyncMock(side_effect=list(outputs)))


def test_eval_agent_golden_min_counts():
    """四切片条数下限（e2e 恰好 1）。"""
    assert len(_load_cases("router")) >= 3
    assert len(_load_cases("strategy_builder")) >= 2
    assert len(_load_cases("supervisor")) >= 2
    assert len(_load_cases("e2e")) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("case", _load_cases("router"), ids=lambda c: c["id"])
async def test_eval_agent_router_golden(case: dict[str, Any]) -> None:
    expect = require_expect(case, "route")
    mock_raw = (case.get("mock") or {}).get("llm_complete")
    if not mock_raw:
        pytest.fail(f"fixture {case['id']} 缺 mock.llm_complete")
    query = case["query"]
    with (
        patch(_PROVIDER_PATCH, return_value=_provider(mock_raw)),
        patch("app.ops.lg_rag.nodes.trace_span", return_value=_span_cm()),
        patch("app.ops.lg_rag.nodes._record_route_metadata"),
    ):
        from app.ops.lg_rag.nodes import router_node

        out = await router_node({"messages": [HumanMessage(content=query)]})
    actual = out["route"]
    assert actual in ROUTES
    assert eval_route_match(actual, expect["route"]) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("case", _load_cases("strategy_builder"), ids=lambda c: c["id"])
async def test_eval_agent_strategy_builder_golden(case: dict[str, Any]) -> None:
    expect = require_expect(case, "allowed_capability_ids")
    setup = case.get("setup") or {}
    intent = setup.get("intent") or {}
    candidates = setup.get("candidate_capability_ids")
    query = case["query"]
    with (
        patch(_CANDIDATE_PATCH, return_value=candidates),
        patch("app.ops.strategy.builder._record_builder_span"),
        patch("app.ops.strategy.builder.trace_span", return_value=_span_cm()),
    ):
        from app.ops.strategy.builder import strategy_builder_node

        out = await strategy_builder_node(
            {"messages": [HumanMessage(content=query)], "intent": intent}
        )
    actual = out["allowed_capability_ids"]
    assert eval_allowlist_match(actual, expect["allowed_capability_ids"]) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("case", _load_cases("supervisor"), ids=lambda c: c["id"])
async def test_eval_agent_supervisor_golden(case: dict[str, Any]) -> None:
    expect = require_expect(case, "subtask_types", "supervisor_fallback")
    setup = case.get("setup") or {}
    allowlist = setup.get("allowed_capability_ids")
    if allowlist is None:
        pytest.fail(f"fixture {case['id']} 缺 setup.allowed_capability_ids")
    mock_raw = (case.get("mock") or {}).get("llm_complete")
    recorded: list[dict] = []
    provider = SimpleNamespace(complete=AsyncMock(return_value=mock_raw or ""))
    query = case["query"]
    with (
        patch(_MULTI_PROVIDER_PATCH, return_value=provider),
        patch(
            "app.ops.lg_rag.multi.nodes._record_span_metadata",
            side_effect=lambda m: recorded.append(m),
        ),
        patch("app.ops.lg_rag.multi.nodes.trace_span", return_value=_span_cm()),
    ):
        from app.ops.lg_rag.multi.nodes import supervisor_node

        out = await supervisor_node(
            {
                "messages": [HumanMessage(content=query)],
                "allowed_capability_ids": allowlist,
            }
        )
    subtasks = out["subtasks"]
    assert eval_plan_schema(subtasks) == 1
    assert eval_subtask_types(subtasks, expect["subtask_types"]) == 1
    assert eval_tool_ids_in_allowlist(subtasks, allowlist) == 1
    assert recorded
    actual_fallback = bool(recorded[0].get("supervisor_fallback"))
    assert actual_fallback is bool(expect["supervisor_fallback"])
    if not allowlist:
        provider.complete.assert_not_called()


@pytest.mark.asyncio
async def test_eval_agent_e2e_golden() -> None:
    """恰好 1 条：mock 全链到 END。CI 无 langchain 元包则 skip（勿挡收集）。"""
    langchain = pytest.importorskip("langchain")
    if not hasattr(langchain, "debug"):
        langchain.debug = False  # 本地包缺此属性，ainvoke 会 AttributeError
    from langgraph.checkpoint.memory import InMemorySaver

    cases = _load_cases("e2e")
    assert len(cases) == 1
    case = cases[0]
    expect = require_expect(case, "reached_end", "critic_outcome", "subtask_types")
    mock = case.get("mock") or {}
    for key in ("intent", "supervisor_plan", "router_route", "aggregator"):
        if key not in mock:
            pytest.fail(f"fixture {case['id']} 缺 mock.{key}")
    intent = IntentV1.model_validate(mock["intent"])
    chain = AsyncMock(
        return_value=ChainResult(
            query="q",
            evidence=[],
            answer="检索答案",
            meta={"gate_action": "answer", "kept_count": 1, "hit_count": 1},
        )
    )
    multi = _provider(mock["supervisor_plan"], mock["aggregator"])
    router = _provider(mock["router_route"])
    from app.ops.lg_rag.multi.graph import build_supervisor_agent

    graph = build_supervisor_agent(checkpointer=InMemorySaver())
    with (
        patch(_INTENT_COMPLETE_PATCH, new=AsyncMock(return_value=intent)),
        patch(_MULTI_PROVIDER_PATCH, return_value=multi),
        patch(_PROVIDER_PATCH, return_value=router),
        patch(_CHAIN_PATCH, new=chain),
    ):
        out = await graph.ainvoke(
            {"messages": [HumanMessage(content=case["query"])]},
            {"configurable": {"thread_id": "t-eval-e2e"}},
        )
    assert expect["reached_end"] is True
    verdict = out.get("critic_verdict") or {}
    assert verdict.get("outcome") == expect["critic_outcome"]
    assert eval_plan_schema(out["subtasks"]) == 1
    assert eval_subtask_types(out["subtasks"], expect["subtask_types"]) == 1
    last = out["messages"][-1]
    assert isinstance(last, AIMessage)
    assert last.content == mock["aggregator"]
    chain.assert_awaited_once()
