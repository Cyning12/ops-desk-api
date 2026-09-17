"""Strategy Builder S1 · allowlist 规则/配置（mock registry，不连外网）。"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import HumanMessage

from app.ops.capability import list_capabilities
from app.ops.strategy import BUILDER_CAP_FILTER, build_allowlist_from_candidates
from app.ops.strategy import config as strategy_config
from app.ops.strategy.builder import strategy_builder_node


def _span_cm():
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=None)
    cm.__exit__ = MagicMock(return_value=False)
    return cm


def test_lg_rag_state_has_allowlist_fields():
    """S1-a：LgRagState 含 allowed_capability_ids / allowed_skill_ids。"""
    from app.ops.lg_rag.state import LgRagState

    hints = LgRagState.__annotations__
    assert "allowed_capability_ids" in hints
    assert "allowed_skill_ids" in hints


def test_build_allowlist_none_is_empty_not_full_open():
    """阶段 H：candidates=None 不再全开，安全默认空。"""
    visible = frozenset(
        s.capability_id
        for s in list_capabilities(filter=BUILDER_CAP_FILTER)
    )
    allowed, stripped = build_allowlist_from_candidates(None, visible_ids=visible)
    assert allowed == []
    assert stripped == []


def test_get_candidate_unknown_key_fail_closed():
    """未知 agent_type/mode → 空 allowlist。"""
    assert strategy_config.get_candidate_capability_ids(agent_type="no_such_agent") == []
    assert strategy_config.get_candidate_capability_ids(mode="mystery") == []


def test_get_candidate_supervisor_map_is_explicit():
    ids = strategy_config.get_candidate_capability_ids(mode="supervisor")
    assert "utc_now_iso" in ids
    assert "get_issue_by_number" in ids
    # 非 None（全开语义已废）
    assert isinstance(ids, list)


def test_build_allowlist_strips_illegal_ids():
    """S1-b：非法 id 剔除，不写入 allowlist。"""
    visible = frozenset({"utc_now_iso", "mock_get_issue_status"})
    allowed, stripped = build_allowlist_from_candidates(
        ["utc_now_iso", "not_registered", "mock_get_issue_status"],
        visible_ids=visible,
    )
    assert allowed == ["utc_now_iso", "mock_get_issue_status"]
    assert stripped == ["not_registered"]


@pytest.mark.asyncio
async def test_strategy_builder_writes_allowlist_and_span():
    """S1-b：Builder 写 allowlist + strategy_builder_catalog_count span。"""
    recorded: list[dict] = []
    with (
        patch(
            "app.ops.strategy.builder.get_candidate_capability_ids",
            return_value=["utc_now_iso", "bogus_tool"],
        ),
        patch(
            "app.ops.strategy.builder._record_builder_span",
            side_effect=lambda m: recorded.append(m),
        ),
        patch("app.ops.strategy.builder.trace_span", return_value=_span_cm()),
    ):
        out = await strategy_builder_node({"messages": [HumanMessage(content="q")]})
    assert "utc_now_iso" in out["allowed_capability_ids"]
    assert "bogus_tool" not in out["allowed_capability_ids"]
    assert out["allowed_skill_ids"] == []
    assert recorded
    assert recorded[0]["strategy_builder_catalog_count"] >= 1
    assert recorded[0]["strategy_builder_stripped_ids"] == ["bogus_tool"]


@pytest.mark.asyncio
async def test_strategy_builder_empty_config_yields_empty_allowlist():
    """空候选配置 → 空 allowlist（supervisor 路径 fallback 单 rag）。"""
    with (
        patch(
            "app.ops.strategy.builder.get_candidate_capability_ids",
            return_value=[],
        ),
        patch("app.ops.strategy.builder._record_builder_span"),
        patch("app.ops.strategy.builder.trace_span", return_value=_span_cm()),
    ):
        out = await strategy_builder_node({"messages": [HumanMessage(content="q")]})
    assert out["allowed_capability_ids"] == []


@pytest.mark.asyncio
async def test_strategy_builder_restricted_config():
    """配置窄 allowlist → supervisor 仅见子集。"""
    strategy_config.CANDIDATE_CAPABILITY_IDS = ["utc_now_iso"]
    try:
        with (
            patch("app.ops.strategy.builder._record_builder_span"),
            patch("app.ops.strategy.builder.trace_span", return_value=_span_cm()),
        ):
            out = await strategy_builder_node({"messages": [HumanMessage(content="q")]})
        assert out["allowed_capability_ids"] == ["utc_now_iso"]
    finally:
        strategy_config.CANDIDATE_CAPABILITY_IDS = None


@pytest.mark.asyncio
async def test_builder_needs_tool_false_empty_allowlist():
    """S2：needs_tool=False → 空 capability allowlist。"""
    with (
        patch("app.ops.strategy.builder._record_builder_span"),
        patch("app.ops.strategy.builder.trace_span", return_value=_span_cm()),
    ):
        out = await strategy_builder_node(
            {
                "messages": [HumanMessage(content="q")],
                "intent": {
                    "domain": "general",
                    "needs_tool": False,
                    "needs_skill": False,
                    "is_composite": False,
                    "risk_hint": "low",
                    "summary": "",
                },
            }
        )
    assert out["allowed_capability_ids"] == []
    assert out["allowed_skill_ids"] == []


@pytest.mark.asyncio
async def test_builder_needs_tool_true_intersects_policy():
    """S2：needs_tool=True → 非空且 ⊆ Policy 可见；非法 id 剔除。"""
    visible = frozenset(
        s.capability_id
        for s in list_capabilities(filter=BUILDER_CAP_FILTER)
    )
    with (
        patch(
            "app.ops.strategy.builder.get_candidate_capability_ids",
            return_value=["utc_now_iso", "bogus_tool"],
        ),
        patch("app.ops.strategy.builder._record_builder_span"),
        patch("app.ops.strategy.builder.trace_span", return_value=_span_cm()),
    ):
        out = await strategy_builder_node(
            {
                "messages": [HumanMessage(content="q")],
                "intent": {
                    "domain": "ops_kb",
                    "needs_tool": True,
                    "needs_skill": True,
                    "is_composite": False,
                    "risk_hint": "high",
                    "summary": "查时间",
                },
            }
        )
    allowed = out["allowed_capability_ids"]
    assert "utc_now_iso" in allowed
    assert "bogus_tool" not in allowed
    assert set(allowed) <= visible
    assert out["allowed_skill_ids"] == []


@pytest.mark.asyncio
async def test_builder_risk_hint_high_does_not_bypass_policy():
    """S2：risk_hint=high 不得把非法/高危 id 放进 allowlist。"""
    with (
        patch(
            "app.ops.strategy.builder.get_candidate_capability_ids",
            return_value=["utc_now_iso", "dangerous_unregistered"],
        ),
        patch("app.ops.strategy.builder._record_builder_span"),
        patch("app.ops.strategy.builder.trace_span", return_value=_span_cm()),
    ):
        out = await strategy_builder_node(
            {
                "messages": [HumanMessage(content="q")],
                "intent": {
                    "domain": "ops_kb",
                    "needs_tool": True,
                    "needs_skill": False,
                    "is_composite": False,
                    "risk_hint": "high",
                    "summary": "",
                },
            }
        )
    assert "dangerous_unregistered" not in out["allowed_capability_ids"]
    assert "utc_now_iso" in out["allowed_capability_ids"]
