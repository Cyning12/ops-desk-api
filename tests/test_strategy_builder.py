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


def test_build_allowlist_default_all_visible():
    """S1-b：候选 None → 全量 Registry ∩ Policy 可见 local_fn。"""
    visible = frozenset(
        s.capability_id
        for s in list_capabilities(filter=BUILDER_CAP_FILTER)
    )
    allowed, stripped = build_allowlist_from_candidates(None, visible_ids=visible)
    assert set(allowed) == visible
    assert stripped == []


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
