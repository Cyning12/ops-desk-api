"""H1 · supervisor ↔ Capability 目录闭环（mock LLM，不连真外网）。"""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import HumanMessage

from app.ops.capability import invoke, list_capabilities
from app.ops.lg_rag.multi.nodes import (
    _SUPERVISOR_CAP_FILTER,
    _subtasks_have_valid_tool_ids,
    supervisor_node,
)
from app.ops.strategy import BUILDER_CAP_FILTER


def _assert_host_rag(subtasks: list[dict], query: str) -> None:
    assert len(subtasks) == 1
    row = subtasks[0]
    assert row["alias"] == "t1"
    assert row["type"] == "rag"
    assert row["input"] == query
    assert row["id"] == row["subtask_id"]
    assert row["subtask_id"] == "catrun:1"


def _full_allowlist_state(messages: list) -> dict:
    """supervisor 单测：模拟 Builder 已写入全量可见 allowlist。"""
    ids = [
        s.capability_id for s in list_capabilities(filter=BUILDER_CAP_FILTER)
    ]
    return {
        "messages": messages,
        "allowed_capability_ids": ids,
        "run_id": "catrun",
    }


def _span_cm():
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=None)
    cm.__exit__ = MagicMock(return_value=False)
    return cm


def test_supervisor_cap_filter_lists_local_fn():
    """H1-a：supervisor filter 含 node_role + kinds local_fn。"""
    assert _SUPERVISOR_CAP_FILTER.node_role == "supervisor"
    assert _SUPERVISOR_CAP_FILTER.kinds == frozenset({"local_fn"})
    specs = list_capabilities(filter=_SUPERVISOR_CAP_FILTER)
    ids = {s.capability_id for s in specs}
    assert "mock_get_issue_status" in ids
    assert "utc_now_iso" in ids


def test_utc_now_iso_invoke_readonly():
    """H1-d：非 mock 低危 local_fn 可 invoke。"""
    result = invoke("utc_now_iso", "")
    assert result.ok
    assert result.output["tool"] == "utc_now_iso"
    assert "utc" in result.output


def test_subtasks_valid_tool_ids():
    allowed = frozenset({"mock_get_issue_status", "utc_now_iso"})
    assert _subtasks_have_valid_tool_ids(
        [{"id": "t1", "type": "tool", "input": "q", "tool": "utc_now_iso"}],
        allowed,
    )
    assert not _subtasks_have_valid_tool_ids(
        [{"id": "t1", "type": "tool", "input": "q", "tool": "bogus_tool"}],
        allowed,
    )
    assert not _subtasks_have_valid_tool_ids(
        [{"id": "t1", "type": "tool", "input": "q"}],
        allowed,
    )


@pytest.mark.asyncio
async def test_supervisor_messages_include_capability_catalog():
    """H1-b：mock LLM messages 含 capability 目录片段。"""
    captured: list[list] = []
    plan = json.dumps(
        {
            "subtasks": [
                {"id": "t1", "type": "rag", "input": "查部署"},
            ]
        },
        ensure_ascii=False,
    )

    async def _capture_complete(messages, *, model):
        captured.append(messages)
        return plan

    provider = SimpleNamespace(complete=_capture_complete)
    with (
        patch("app.ops.lg_rag.multi.nodes.get_llm_provider", return_value=provider),
        patch("app.ops.lg_rag.multi.nodes._record_span_metadata"),
        patch("app.ops.lg_rag.multi.nodes.trace_span", return_value=_span_cm()),
    ):
        await supervisor_node(_full_allowlist_state([HumanMessage(content="复合问题")]))
    assert captured
    system = captured[0][0].content
    assert "Capability 目录" in system
    assert "mock_get_issue_status" in system
    assert "utc_now_iso" in system
    assert "risk=" in system


@pytest.mark.asyncio
async def test_supervisor_invalid_tool_id_fallback_single_rag():
    """H1-c：非法 tool id → 整 plan fallback 单 rag。"""
    recorded: list[dict] = []
    plan = json.dumps(
        {
            "subtasks": [
                {
                    "id": "t1",
                    "type": "tool",
                    "input": "查状态",
                    "tool": "not_a_real_capability",
                }
            ]
        },
        ensure_ascii=False,
    )
    provider = SimpleNamespace(complete=AsyncMock(return_value=plan))
    with (
        patch("app.ops.lg_rag.multi.nodes.get_llm_provider", return_value=provider),
        patch(
            "app.ops.lg_rag.multi.nodes._record_span_metadata",
            side_effect=lambda m: recorded.append(m),
        ),
        patch("app.ops.lg_rag.multi.nodes.trace_span", return_value=_span_cm()),
    ):
        out = await supervisor_node(
            _full_allowlist_state([HumanMessage(content="复合问题")])
        )
    _assert_host_rag(out["subtasks"], "复合问题")
    assert recorded
    assert recorded[0]["supervisor_fallback"] is True
    assert recorded[0]["supervisor_invalid_tool_id"] is True
    assert recorded[0]["capability_catalog_count"] >= 1


@pytest.mark.asyncio
async def test_supervisor_empty_allowlist_fallback_single_rag():
    """S1-c：空 allowlist → 整 plan fallback 单 rag（不调 LLM）。"""
    recorded: list[dict] = []
    provider = SimpleNamespace(complete=AsyncMock())
    with (
        patch("app.ops.lg_rag.multi.nodes.get_llm_provider", return_value=provider),
        patch(
            "app.ops.lg_rag.multi.nodes._record_span_metadata",
            side_effect=lambda m: recorded.append(m),
        ),
        patch("app.ops.lg_rag.multi.nodes.trace_span", return_value=_span_cm()),
    ):
        out = await supervisor_node(
            {
                "messages": [HumanMessage(content="复合问题")],
                "allowed_capability_ids": [],
                "run_id": "catrun",
            }
        )
    _assert_host_rag(out["subtasks"], "复合问题")
    assert recorded[0]["supervisor_empty_allowlist"] is True
    provider.complete.assert_not_called()


@pytest.mark.asyncio
async def test_supervisor_restricted_allowlist_hides_tool_from_catalog():
    """S1-c：窄 allowlist → system prompt 不含未授权 tool。"""
    captured: list[list] = []
    plan = json.dumps(
        {"subtasks": [{"id": "t1", "type": "rag", "input": "查部署"}]},
        ensure_ascii=False,
    )

    async def _capture_complete(messages, *, model):
        captured.append(messages)
        return plan

    provider = SimpleNamespace(complete=_capture_complete)
    with (
        patch("app.ops.lg_rag.multi.nodes.get_llm_provider", return_value=provider),
        patch("app.ops.lg_rag.multi.nodes._record_span_metadata"),
        patch("app.ops.lg_rag.multi.nodes.trace_span", return_value=_span_cm()),
    ):
        await supervisor_node(
            {
                "messages": [HumanMessage(content="复合问题")],
                "allowed_capability_ids": ["utc_now_iso"],
                "run_id": "catrun",
            }
        )
    system = captured[0][0].content
    assert "utc_now_iso" in system
    assert "mock_get_issue_status" not in system


@pytest.mark.asyncio
async def test_supervisor_tool_not_in_allowlist_fallback_single_rag():
    """S1-d：plan 中 tool 不在本轮可见集 → fallback 单 rag。"""
    plan = json.dumps(
        {
            "subtasks": [
                {
                    "id": "t1",
                    "type": "tool",
                    "input": "查 issue",
                    "tool": "mock_get_issue_status",
                }
            ]
        },
        ensure_ascii=False,
    )
    provider = SimpleNamespace(complete=AsyncMock(return_value=plan))
    with (
        patch("app.ops.lg_rag.multi.nodes.get_llm_provider", return_value=provider),
        patch("app.ops.lg_rag.multi.nodes._record_span_metadata"),
        patch("app.ops.lg_rag.multi.nodes.trace_span", return_value=_span_cm()),
    ):
        out = await supervisor_node(
            {
                "messages": [HumanMessage(content="复合问题")],
                "allowed_capability_ids": ["utc_now_iso"],
                "run_id": "catrun",
            }
        )
    _assert_host_rag(out["subtasks"], "复合问题")


@pytest.mark.asyncio
async def test_supervisor_valid_tool_plan_kept():
    """合法 tool id 时保留 plan。"""
    plan = json.dumps(
        {
            "subtasks": [
                {
                    "id": "t1",
                    "type": "tool",
                    "input": "当前 UTC",
                    "tool": "utc_now_iso",
                }
            ]
        },
        ensure_ascii=False,
    )
    provider = SimpleNamespace(complete=AsyncMock(return_value=plan))
    with (
        patch("app.ops.lg_rag.multi.nodes.get_llm_provider", return_value=provider),
        patch("app.ops.lg_rag.multi.nodes._record_span_metadata"),
        patch("app.ops.lg_rag.multi.nodes.trace_span", return_value=_span_cm()),
    ):
        out = await supervisor_node(
            _full_allowlist_state([HumanMessage(content="几点了")])
        )
    assert out["subtasks"][0]["type"] == "tool"
    assert out["subtasks"][0]["tool"] == "utc_now_iso"
