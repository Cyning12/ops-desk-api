"""P2a-T4 · supervisor plan-JSON 结构断言（mock LLM · 不连真外网）。

设计真源：workspace 08-p2a-tools-design.md §6（CI 结构断言 + 四样例人工冒烟双件制）。
本文件为 CI 半件：钉死 supervisor 面九枚 capability 的 plan-JSON 可选中性（表达力覆盖）
与四设计样例 query → 预期 capability id 对照（预期集 ∩ mock_* = ∅）。真 LLM 选择质量
由四样例冒烟人工判定（invoke 40），不在本文件。

范式承 tests/test_lg_rag_supervisor_capability_catalog.py（H1 闭环测试）。
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import HumanMessage

from app.ops.capability import list_capabilities
from app.ops.lg_rag.multi.nodes import (
    _SUPERVISOR_CAP_FILTER,
    supervisor_node,
)
from app.ops.strategy import BUILDER_CAP_FILTER
from app.ops.strategy.config import CAPABILITY_ALLOWLIST_BY_KEY

EXPECTED_NINE = frozenset(
    {
        "utc_now_iso",
        "mock_get_issue_status",
        "mock_get_deploy_info",
        "get_issue_by_number",
        "get_pr_by_number",
        "query_issues",
        "query_pull_requests",
        "get_overview",
        "graph_snapshot",
    }
)

MOCK_IDS = frozenset({"mock_get_issue_status", "mock_get_deploy_info"})

# 08 §6 四设计样例：query → 预期 capability id（对照表钉死 · 冒烟判定同源）。
DESIGN_SAMPLES = (
    ("最近 issue 吞吐怎么样？", "get_overview"),
    ("open 的 PR 里哪些 CI 挂了？", "query_pull_requests"),
    ("模块 X 依赖哪些模块？", "graph_snapshot"),
    ("现在有哪些 open 的 bug？", "query_issues"),
)


def _full_allowlist_state(messages: list) -> dict:
    """supervisor 单测：模拟 Builder 已写入全量可见 allowlist。"""
    ids = [s.capability_id for s in list_capabilities(filter=BUILDER_CAP_FILTER)]
    return {
        "messages": messages,
        "allowed_capability_ids": ids,
        "run_id": "t4run",
    }


def _span_cm():
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=None)
    cm.__exit__ = MagicMock(return_value=False)
    return cm


def _tool_plan(capability_id: str, query: str) -> str:
    return json.dumps(
        {
            "subtasks": [
                {"id": "t1", "type": "tool", "input": query, "tool": capability_id}
            ]
        },
        ensure_ascii=False,
    )


def test_supervisor_allowlist_exactly_nine() -> None:
    """T4-a：supervisor allowlist 恰好九枚 · 逐名钉死 · 且全部在 manifest 可见集内。"""
    allowlist = CAPABILITY_ALLOWLIST_BY_KEY["supervisor"]
    assert frozenset(allowlist) == EXPECTED_NINE
    visible = {s.capability_id for s in list_capabilities(filter=_SUPERVISOR_CAP_FILTER)}
    assert visible >= EXPECTED_NINE


def test_design_samples_table_pins_non_mock_expected() -> None:
    """T4-b：四样例预期 id 全部 ∈ allowlist 且 ∩ mock_* = ∅（§6 (f) 结构面）。"""
    assert len(DESIGN_SAMPLES) == 4
    for _query, expected in DESIGN_SAMPLES:
        assert expected in EXPECTED_NINE
        assert expected not in MOCK_IDS


@pytest.mark.asyncio
async def test_catalog_shows_all_nine() -> None:
    """T4-c：supervisor system prompt 目录片段含全部九枚 id（选择面可见性）。"""
    captured: list[list] = []

    async def _capture_complete(messages, *, model):
        captured.append(messages)
        return json.dumps(
            {"subtasks": [{"id": "t1", "type": "rag", "input": "占位"}]},
            ensure_ascii=False,
        )

    provider = SimpleNamespace(complete=_capture_complete)
    with (
        patch("app.ops.lg_rag.multi.nodes.get_llm_provider", return_value=provider),
        patch("app.ops.lg_rag.multi.nodes._record_span_metadata"),
        patch("app.ops.lg_rag.multi.nodes.trace_span", return_value=_span_cm()),
    ):
        await supervisor_node(_full_allowlist_state([HumanMessage(content="复合问题")]))
    assert captured
    system = captured[0][0].content
    for cid in EXPECTED_NINE:
        assert cid in system, f"catalog 缺 {cid}"


@pytest.mark.asyncio
@pytest.mark.parametrize("capability_id", sorted(EXPECTED_NINE))
async def test_plan_json_selects_each_capability(capability_id: str) -> None:
    """T4-d：九枚逐枚 plan-JSON 可选中（表达力覆盖全 supervisor 面 · 不 fallback）。"""
    plan = _tool_plan(capability_id, "选择断言")
    provider = SimpleNamespace(complete=AsyncMock(return_value=plan))
    with (
        patch("app.ops.lg_rag.multi.nodes.get_llm_provider", return_value=provider),
        patch("app.ops.lg_rag.multi.nodes._record_span_metadata"),
        patch("app.ops.lg_rag.multi.nodes.trace_span", return_value=_span_cm()),
    ):
        out = await supervisor_node(
            _full_allowlist_state([HumanMessage(content="选择断言")])
        )
    assert out["subtasks"][0]["type"] == "tool"
    assert out["subtasks"][0]["tool"] == capability_id


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("query", "expected"),
    DESIGN_SAMPLES,
    ids=[expected for _q, expected in DESIGN_SAMPLES],
)
async def test_design_sample_query_plan_kept(query: str, expected: str) -> None:
    """T4-e：四设计样例 query · 预期 capability 的 plan 被保留（wiring 面）。"""
    plan = _tool_plan(expected, query)
    provider = SimpleNamespace(complete=AsyncMock(return_value=plan))
    with (
        patch("app.ops.lg_rag.multi.nodes.get_llm_provider", return_value=provider),
        patch("app.ops.lg_rag.multi.nodes._record_span_metadata"),
        patch("app.ops.lg_rag.multi.nodes.trace_span", return_value=_span_cm()),
    ):
        out = await supervisor_node(_full_allowlist_state([HumanMessage(content=query)]))
    assert out["subtasks"][0]["type"] == "tool"
    assert out["subtasks"][0]["tool"] == expected
