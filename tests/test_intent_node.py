"""S2-a · intent_node（mock LLM + SO）与 supervisor 拓扑。"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import HumanMessage

from app.ops.lg_rag.schemas import IntentV1
from app.ops.strategy.intent import fallback_intent_dict, intent_node
from app.ops.structured_output import StructuredFailure


def _span_cm():
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=None)
    cm.__exit__ = MagicMock(return_value=False)
    return cm


def _edge_pairs(graph) -> set[tuple[str, str]]:
    return {(e.source, e.target) for e in graph.get_graph().edges}


@pytest.mark.asyncio
async def test_intent_node_writes_state_on_success():
    """SO 成功 → 写入 state.intent；span 非 fallback。"""
    parsed = IntentV1(
        domain="ops_kb",
        needs_tool=True,
        needs_skill=False,
        is_composite=False,
        risk_hint="low",
        summary="查 issue",
    )
    recorded: list[dict] = []

    async def _fake_complete(*_args, **kwargs):
        assert kwargs["max_retries"] == 1
        assert kwargs["schema"] is IntentV1
        assert kwargs["raise_on_failure"] is False
        assert "三路" in kwargs["system"]
        return parsed

    with (
        patch(
            "app.ops.strategy.intent.acomplete_structured",
            new=AsyncMock(side_effect=_fake_complete),
        ),
        patch(
            "app.ops.strategy.intent._record_intent_span",
            side_effect=lambda m: recorded.append(m),
        ),
        patch("app.ops.strategy.intent.trace_span", return_value=_span_cm()),
    ):
        out = await intent_node({"messages": [HumanMessage(content="issue 128")]})
    assert out["intent"]["domain"] == "ops_kb"
    assert out["intent"]["needs_tool"] is True
    assert out["intent"]["summary"] == "查 issue"
    assert recorded[0]["intent_fallback"] is False
    assert recorded[0]["structured_output_fallback"] is False


@pytest.mark.asyncio
async def test_intent_node_fallback_on_so_failure():
    """SO 失败 → 保守 fallback + span；不抛。"""
    recorded: list[dict] = []
    failure = StructuredFailure(error="bad json", attempts=2, last_raw="nope")

    with (
        patch(
            "app.ops.strategy.intent.acomplete_structured",
            new=AsyncMock(return_value=failure),
        ),
        patch(
            "app.ops.strategy.intent._record_intent_span",
            side_effect=lambda m: recorded.append(m),
        ),
        patch("app.ops.strategy.intent.trace_span", return_value=_span_cm()),
    ):
        out = await intent_node({"messages": [HumanMessage(content="q")]})
    assert out["intent"] == fallback_intent_dict()
    assert out["intent"]["domain"] == "unknown"
    assert out["intent"]["needs_tool"] is False
    assert recorded[0]["intent_fallback"] is True
    assert recorded[0]["structured_output_fallback"] is True


@pytest.mark.asyncio
async def test_intent_node_fallback_on_exception():
    """LLM 异常 → 保守 fallback，不拒图。"""
    recorded: list[dict] = []
    with (
        patch(
            "app.ops.strategy.intent.acomplete_structured",
            new=AsyncMock(side_effect=RuntimeError("llm down")),
        ),
        patch(
            "app.ops.strategy.intent._record_intent_span",
            side_effect=lambda m: recorded.append(m),
        ),
        patch("app.ops.strategy.intent.trace_span", return_value=_span_cm()),
    ):
        out = await intent_node({"messages": [HumanMessage(content="q")]})
    assert out["intent"] == fallback_intent_dict()
    assert recorded[0]["intent_fallback"] is True
    assert recorded[0]["structured_output_fallback"] is True


def test_supervisor_graph_intent_then_builder():
    """supervisor 图：START → intent_node → strategy_builder。

    节点 id 不能叫 intent：与 LgRagState.intent 冲突（LangGraph）。
    """
    from app.ops.lg_rag.multi.graph import build_supervisor_agent

    graph = build_supervisor_agent()
    node_names = set(graph.get_graph().nodes.keys())
    assert "intent_node" in node_names
    assert "strategy_builder" in node_names
    edges = _edge_pairs(graph)
    assert ("__start__", "intent_node") in edges
    assert ("intent_node", "strategy_builder") in edges
    assert ("strategy_builder", "supervisor") in edges
    assert ("__start__", "strategy_builder") not in edges


def test_router_graph_start_still_router():
    """router 图拓扑不回归：START → router；无 intent 节点。"""
    from app.ops.lg_rag.graph import build_router_agent

    graph = build_router_agent()
    node_names = set(graph.get_graph().nodes.keys())
    assert "router" in node_names
    assert "intent" not in node_names
    edges = _edge_pairs(graph)
    assert ("__start__", "router") in edges
