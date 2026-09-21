"""memory-facts-p0 · M3 装配注入（纯装配 · 不连 DB）：开关关闭零 diff / 块格式 / 降级。"""
from __future__ import annotations

import logging

import pytest
from langchain_core.messages import BaseMessage, SystemMessage

from app.ops.lg_rag.continuity import (
    MEMORY_FACTS_HEADER,
    assemble_graph_messages,
    assemble_graph_messages_with_memory,
    inject_memory_facts_block,
    memory_facts_enabled,
    memory_facts_max_items,
    render_memory_facts_block,
)


def _fixture_turns() -> list[dict]:
    """10 轮 user 历史 → 触发窗口压缩（含系统摘要占位）。"""
    return [{"role": "user", "content": f"q{i}"} for i in range(10)]


def _shape(messages: list[BaseMessage]) -> list[tuple[str, str]]:
    return [(type(m).__name__, str(m.content)) for m in messages]


# ---------------- 开关关闭 = 现网逐字节一致（验收 M4-6） ----------------


async def test_disabled_default_is_byte_identical(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("MEMORY_FACTS_ENABLED", raising=False)
    history = _fixture_turns()
    baseline = assemble_graph_messages("本轮问", history)
    with_memory = await assemble_graph_messages_with_memory(
        "本轮问", history, tenant_id="ops-desk-pilot", user_id="u-1"
    )
    assert _shape(with_memory) == _shape(baseline)


@pytest.mark.parametrize("value", ["false", "0", "no", "off", "garbage"])
async def test_disabled_or_invalid_is_byte_identical(
    monkeypatch: pytest.MonkeyPatch, value: str
):
    monkeypatch.setenv("MEMORY_FACTS_ENABLED", value)
    history = _fixture_turns()
    baseline = assemble_graph_messages("q-now", history)
    with_memory = await assemble_graph_messages_with_memory(
        "q-now", history, tenant_id="ops-desk-pilot", user_id="u-1"
    )
    assert _shape(with_memory) == _shape(baseline)


def test_enabled_invalid_value_warns_and_falls_back(
    monkeypatch: pytest.MonkeyPatch, caplog
):
    monkeypatch.setenv("MEMORY_FACTS_ENABLED", "enable plz")
    with caplog.at_level(logging.WARNING, logger="app.ops.lg_rag.continuity"):
        assert memory_facts_enabled() is False
    assert "MEMORY_FACTS_ENABLED" in caplog.text


async def test_enabled_but_missing_identity_skips_injection(
    monkeypatch: pytest.MonkeyPatch, caplog
):
    """身份缺失（无 ctx）→ 不注入、不触 DB；现网输出不变。"""
    monkeypatch.setenv("MEMORY_FACTS_ENABLED", "true")
    history = _fixture_turns()
    baseline = assemble_graph_messages("q", history)
    with caplog.at_level(logging.WARNING, logger="app.ops.lg_rag.continuity"):
        out = await assemble_graph_messages_with_memory("q", history)
    assert _shape(out) == _shape(baseline)
    assert "skip injection" in caplog.text


# ---------------- 渲染与插入 ----------------


def test_render_block_format_one_line_per_fact():
    facts = [
        {"key": "project.primary_repo", "value": "cyning/ops-desk"},
        {"key": "user.retry_limit", "value": 3},
        {"key": "user.multiline", "value": "a\nb"},
    ]
    block = render_memory_facts_block(facts)
    lines = block.split("\n")
    assert lines[0] == MEMORY_FACTS_HEADER
    assert "project.primary_repo=cyning/ops-desk" in lines
    assert "user.retry_limit=3" in lines
    # 值内换行被转义，保住「一行一条」
    assert "user.multiline=a\\nb" in lines


def test_render_empty_facts_returns_empty():
    assert render_memory_facts_block([]) == ""


def test_inject_after_leading_system_messages():
    history = _fixture_turns()
    msgs = assemble_graph_messages("now", history)  # 头部含压缩占位 SystemMessage
    assert isinstance(msgs[0], SystemMessage)
    out = inject_memory_facts_block(msgs, "[已知事实]\nk=v")
    leading_sys = 0
    for m in msgs:
        if isinstance(m, SystemMessage):
            leading_sys += 1
        else:
            break
    # 独立 SystemMessage 插在既有前缀系统消息之后
    assert isinstance(out[leading_sys], SystemMessage)
    assert out[leading_sys].content.startswith(MEMORY_FACTS_HEADER)
    assert _shape(out[:leading_sys]) == _shape(msgs[:leading_sys])
    assert _shape(out[leading_sys + 1 :]) == _shape(msgs[leading_sys:])


def test_inject_without_existing_system_goes_head():
    msgs = assemble_graph_messages("now", [{"role": "user", "content": "hi"}])
    out = inject_memory_facts_block(msgs, "[已知事实]\nk=v")
    assert isinstance(out[0], SystemMessage)
    assert _shape(out[1:]) == _shape(msgs)


def test_inject_empty_block_is_noop():
    msgs = assemble_graph_messages("now", _fixture_turns())
    assert inject_memory_facts_block(msgs, "") == msgs


# ---------------- 预算 env ----------------


def test_max_items_default_and_fallback(monkeypatch: pytest.MonkeyPatch, caplog):
    monkeypatch.delenv("MEMORY_FACTS_MAX_ITEMS", raising=False)
    assert memory_facts_max_items() == 8
    monkeypatch.setenv("MEMORY_FACTS_MAX_ITEMS", "abc")
    with caplog.at_level(logging.WARNING, logger="app.ops.lg_rag.continuity"):
        assert memory_facts_max_items() == 8
    assert "MEMORY_FACTS_MAX_ITEMS" in caplog.text
    monkeypatch.setenv("MEMORY_FACTS_MAX_ITEMS", "0")
    assert memory_facts_max_items() == 8
    monkeypatch.setenv("MEMORY_FACTS_MAX_ITEMS", "3")
    assert memory_facts_max_items() == 3


# ---------------- 召回故障降级（不拖垮请求） ----------------


async def test_recall_failure_degrades_to_no_injection(
    monkeypatch: pytest.MonkeyPatch, caplog
):
    from unittest.mock import AsyncMock, patch

    monkeypatch.setenv("MEMORY_FACTS_ENABLED", "true")
    history = _fixture_turns()
    baseline = assemble_graph_messages("q", history)
    with (
        patch(
            "app.ops.memory.service.recall_active",
            new=AsyncMock(side_effect=RuntimeError("db down")),
        ),
        caplog.at_level(logging.ERROR, logger="app.ops.lg_rag.continuity"),
    ):
        out = await assemble_graph_messages_with_memory(
            "q", history, tenant_id="ops-desk-pilot", user_id="u-1"
        )
    assert _shape(out) == _shape(baseline)
    assert "degrade to no injection" in caplog.text
