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
    _TOOL_AWARENESS_GUIDANCE,
    SupervisorPlanError,
    _build_catalog_block,
    _format_capability_catalog,
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
    ids = [s.capability_id for s in list_capabilities(filter=BUILDER_CAP_FILTER)]
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
async def test_supervisor_invalid_tool_id_fails_closed():
    """H1-c/D2：首次 plan 含非法 tool id → 整 plan 作废，fail-closed 抛 SupervisorPlanError。"""
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
        pytest.raises(SupervisorPlanError),
    ):
        await supervisor_node(_full_allowlist_state([HumanMessage(content="复合问题")]))
    assert recorded
    assert recorded[0]["supervisor_plan_failed"] is True
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
async def test_supervisor_tool_not_in_allowlist_fails_closed():
    """S1-d/D2：首次 plan 中 tool 不在本轮可见集 → 整 plan 作废，fail-closed。"""
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
        pytest.raises(SupervisorPlanError),
    ):
        await supervisor_node(
                {
                    "messages": [HumanMessage(content="复合问题")],
                    "allowed_capability_ids": ["utc_now_iso"],
                    "run_id": "catrun",
                }
            )


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
        out = await supervisor_node(_full_allowlist_state([HumanMessage(content="几点了")]))
    assert out["subtasks"][0]["type"] == "tool"
    assert out["subtasks"][0]["tool"] == "utc_now_iso"


# ---------------------------------------------------------------- P2c-T1 · 工具感知硬化

#: 引导语锚定词（与 nodes._TOOL_AWARENESS_GUIDANCE 文本一一对应 · 改动需双签）
_GUIDANCE_MARK = "工具选择原则"
_FEWSHOT_MARK = "现在几点了"
_RAG_FALLBACK_MARK = "仅当目录中没有工具能覆盖该问题时才纯 rag"


def test_build_catalog_block_empty_no_guidance() -> None:
    """P2c-T1：空目录零追加——占位文本原样返回、不含引导语（catalog 空时不含）。"""
    block = _build_catalog_block([])
    assert block == "（当前无可用 local_fn 工具）"
    assert _GUIDANCE_MARK not in block


def test_build_catalog_block_injects_guidance_preserves_lines() -> None:
    """P2c-T1：非空目录块首注入引导语 + few-shot + rag 兜底从句，行渲染零 diff。"""
    caps = list_capabilities(filter=_SUPERVISOR_CAP_FILTER)
    raw = _format_capability_catalog(caps)
    block = _build_catalog_block(caps)
    assert block.startswith(_TOOL_AWARENESS_GUIDANCE)
    # 行渲染本体零改：注入后目录行逐字节保持（块以原渲染输出结尾）
    assert block.endswith(raw)
    assert _FEWSHOT_MARK in block
    assert _RAG_FALLBACK_MARK in block


def test_tool_awareness_guidance_no_capability_id_leak() -> None:
    """P2c-T1：引导语静态恒定、不含任何 registry capability id（窄 allowlist 零泄漏）。"""
    ids = [s.capability_id for s in list_capabilities()]
    assert ids  # 防空调用空转
    leaked = [i for i in ids if i in _TOOL_AWARENESS_GUIDANCE]
    assert not leaked, f"引导语泄漏 capability id: {leaked}"


def test_tool_awareness_catalog_budget_anchor() -> None:
    """P2c-T1：注入引导语后默认可见目录 ≤6000 字符（§6.5 合并预算 capability 侧锚）。"""
    caps = list_capabilities(filter=_SUPERVISOR_CAP_FILTER)
    assert len(_build_catalog_block(caps)) <= 6000


@pytest.mark.asyncio
async def test_supervisor_prompt_contains_tool_awareness_guidance():
    """P2c-T1：catalog 含工具时 mock LLM 捕获的 system 含引导语 + few-shot + rag 兜底从句。"""
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
        await supervisor_node(_full_allowlist_state([HumanMessage(content="现在几点了")]))
    system = captured[0][0].content
    assert _GUIDANCE_MARK in system
    assert _FEWSHOT_MARK in system
    assert _RAG_FALLBACK_MARK in system
    # few-shot 结构锚：type=tool + tool 占位指示从目录取 id
    assert '"type": "tool"' in system
    assert "capability_id" in system


@pytest.mark.asyncio
async def test_supervisor_restricted_allowlist_guidance_no_leak():
    """P2c-T1：窄 allowlist 下 system 含引导语且不含被隐藏工具 id（引导语零泄漏）。"""
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
    assert _GUIDANCE_MARK in system
    assert "utc_now_iso" in system
    assert "mock_get_issue_status" not in system
