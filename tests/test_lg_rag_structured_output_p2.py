"""lg_rag P2 · Structured Output Gateway 接入（mock，不连真 LLM/库）。

覆盖：_parse_route / _parse_subtasks / info_extract 解析路径；
fallback 语义；span metadata 含 structured_output_fallback。
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import HumanMessage

from app.ops.capability import list_capabilities
from app.ops.lg_rag.multi.nodes import (
    _parse_subtasks,
    info_extract_node,
    supervisor_node,
)
from app.ops.lg_rag.nodes import _parse_route, _record_route_metadata
from app.ops.strategy import BUILDER_CAP_FILTER


def _full_allowlist_state(messages: list) -> dict:
    ids = [s.capability_id for s in list_capabilities(filter=BUILDER_CAP_FILTER)]
    return {
        "messages": messages,
        "allowed_capability_ids": ids,
        "run_id": "structrun",
    }


def _span_cm():
    """trace_span 上下文管理器 mock。"""
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=None)
    cm.__exit__ = MagicMock(return_value=False)
    return cm


# ---------------------------------------------------------------------------
# _parse_route：Gateway + 历史宽容
# ---------------------------------------------------------------------------


def test_parse_route_valid_json():
    assert _parse_route('{"route": "direct"}') == "direct"
    assert _parse_route('```json\n{"route": "refuse"}\n```') == "refuse"


def test_parse_route_legacy_quoted_literal_tolerance():
    """非 JSON 文本中出现白名单字面量仍接受（勿收紧）。"""
    assert _parse_route('我认为应选 "rag" 路径') == "rag"
    assert _parse_route('answer: "direct"') == "direct"


def test_parse_route_invalid_falls_none():
    assert _parse_route("我不是 JSON") is None
    assert _parse_route('{"route": "bogus"}') is None
    assert _parse_route("") is None


def test_record_route_metadata_includes_structured_output_fallback():
    client = MagicMock()
    with (
        patch("app.ops.lg_rag.nodes.tracing_enabled", return_value=True),
        patch("langfuse.get_client", return_value=client),
    ):
        _record_route_metadata(route="rag", raw="bad", fallback=True)
    meta = client.update_current_span.call_args.kwargs["metadata"]
    assert meta["router_fallback"] is True
    assert meta["structured_output_fallback"] is True


# ---------------------------------------------------------------------------
# _parse_subtasks：Gateway
# ---------------------------------------------------------------------------


def test_parse_subtasks_valid():
    raw = (
        '{"subtasks": [{"id": "t1", "type": "rag", "input": "超时排查"},'
        ' {"id": "t2", "type": "extract", "input": "发版说明"}]}'
    )
    out = _parse_subtasks(raw)
    assert out == [
        {"id": "t1", "type": "rag", "input": "超时排查"},
        {"id": "t2", "type": "extract", "input": "发版说明"},
    ]


def test_parse_subtasks_unknown_type_coerces_rag():
    raw = '{"subtasks": [{"type": "mystery", "input": "q"}]}'
    out = _parse_subtasks(raw)
    assert out == [{"id": "t1", "type": "rag", "input": "q"}]


def test_parse_subtasks_invalid_returns_none():
    assert _parse_subtasks("不是 JSON") is None
    assert _parse_subtasks('{"subtasks": []}') is None
    assert _parse_subtasks('{"subtasks": [{"type": "rag", "input": ""}]}') is None


def test_parse_subtasks_cap_ignores_extra_bad_items():
    """cap=4：第 5 项起不校验；即使第 5 项缺 input 也不拖垮前 4。"""
    items = [{"id": f"t{i}", "type": "rag", "input": f"q{i}"} for i in range(1, 5)]
    items.append({"id": "t5", "type": "rag"})  # 缺 input，超出 cap
    out = _parse_subtasks(json.dumps({"subtasks": items}, ensure_ascii=False))
    assert out is not None
    assert len(out) == 4


# ---------------------------------------------------------------------------
# supervisor / extract metadata
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_supervisor_fallback_metadata_flag():
    recorded: list[dict] = []
    provider = SimpleNamespace(complete=AsyncMock(return_value="拆不了"))
    with (
        patch("app.ops.lg_rag.multi.nodes.get_llm_provider", return_value=provider),
        patch(
            "app.ops.lg_rag.multi.nodes._record_span_metadata",
            side_effect=lambda m: recorded.append(m),
        ),
        patch("app.ops.lg_rag.multi.nodes.trace_span", return_value=_span_cm()),
    ):
        out = await supervisor_node(_full_allowlist_state([HumanMessage(content="复合问题")]))
    row = out["subtasks"][0]
    assert row["alias"] == "t1"
    assert row["type"] == "rag"
    assert row["input"] == "复合问题"
    assert row["id"] == row["subtask_id"]
    assert row["subtask_id"] == "structrun:1"
    assert recorded
    assert recorded[0]["supervisor_fallback"] is True
    assert recorded[0]["structured_output_fallback"] is True


@pytest.mark.asyncio
async def test_info_extract_invalid_empty_and_metadata():
    recorded: list[dict] = []
    provider = SimpleNamespace(complete=AsyncMock(return_value="不是 JSON"))
    state = {
        "subtasks": [{"id": "t1", "type": "extract", "input": "文本"}],
        "subtask_results": [],
    }
    with (
        patch("app.ops.lg_rag.multi.nodes.get_llm_provider", return_value=provider),
        patch(
            "app.ops.lg_rag.multi.nodes._record_span_metadata",
            side_effect=lambda m: recorded.append(m),
        ),
        patch("app.ops.lg_rag.multi.nodes.trace_span", return_value=_span_cm()),
    ):
        out = await info_extract_node(state)
    assert out["subtask_results"][0]["output"] == {
        "dates": [],
        "versions": [],
        "people": [],
    }
    assert recorded and recorded[0]["structured_output_fallback"] is True


@pytest.mark.asyncio
async def test_info_extract_valid_no_fallback_flag():
    recorded: list[dict] = []
    provider = SimpleNamespace(
        complete=AsyncMock(return_value='{"dates": ["2026-08-20"], "versions": [], "people": []}')
    )
    state = {
        "subtasks": [{"id": "t1", "type": "extract", "input": "文本"}],
        "subtask_results": [],
    }
    with (
        patch("app.ops.lg_rag.multi.nodes.get_llm_provider", return_value=provider),
        patch(
            "app.ops.lg_rag.multi.nodes._record_span_metadata",
            side_effect=lambda m: recorded.append(m),
        ),
        patch("app.ops.lg_rag.multi.nodes.trace_span", return_value=_span_cm()),
    ):
        out = await info_extract_node(state)
    assert out["subtask_results"][0]["output"]["dates"] == ["2026-08-20"]
    assert recorded and recorded[0]["structured_output_fallback"] is False
