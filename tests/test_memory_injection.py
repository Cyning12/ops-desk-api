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

# ---------------- span `memory_facts_injected` 专门单测（memory-embedding-backfill D3） ----------------
# capture-list 模式对齐 tests/test_llm_routing.py:176；发射点 continuity.py:237-243。


def _capture_span(monkeypatch: pytest.MonkeyPatch) -> list[dict]:
    """monkeypatch continuity 命名空间内的 update_current_span_metadata，返回捕获列表。"""
    from app.ops.lg_rag import continuity

    captured: list[dict] = []
    monkeypatch.setattr(
        continuity, "update_current_span_metadata", lambda m: captured.append(m)
    )
    return captured


def _patch_recall(monkeypatch: pytest.MonkeyPatch, *, facts=None, error=None):
    """patch 装配链路实际调用的 memory service 召回（默认确定性通路）。"""
    from unittest.mock import AsyncMock

    mock = (
        AsyncMock(side_effect=error)
        if error is not None
        else AsyncMock(return_value=facts or [])
    )
    monkeypatch.setattr("app.ops.memory.service.recall_active", mock)
    return mock


async def test_span_memory_facts_injected_count(monkeypatch: pytest.MonkeyPatch):
    """有 facts：span 收到 {"memory_facts_injected": N} 且 N == 实际注入条数。"""
    monkeypatch.setenv("MEMORY_FACTS_ENABLED", "true")
    captured = _capture_span(monkeypatch)
    facts = [
        {"key": "project.primary_repo", "value": "cyning/ops-desk"},
        {"key": "user.display_tz", "value": "Asia/Shanghai"},
    ]
    _patch_recall(monkeypatch, facts=facts)

    out = await assemble_graph_messages_with_memory(
        "q", _fixture_turns(), tenant_id="ops-desk-pilot", user_id="u-1"
    )
    assert captured == [{"memory_facts_injected": 2}]
    # N 与实际注入条数一致（注入块真含两条）
    blocks = [str(m.content) for m in out if isinstance(m, SystemMessage)]
    assert any("project.primary_repo=cyning/ops-desk" in b for b in blocks)
    assert any("user.display_tz=Asia/Shanghai" in b for b in blocks)


async def test_span_memory_facts_injected_zero(monkeypatch: pytest.MonkeyPatch):
    """零 facts：span 收到 {"memory_facts_injected": 0}（continuity.py:240 分支）。"""
    monkeypatch.setenv("MEMORY_FACTS_ENABLED", "true")
    captured = _capture_span(monkeypatch)
    _patch_recall(monkeypatch, facts=[])

    out = await assemble_graph_messages_with_memory(
        "q", _fixture_turns(), tenant_id="ops-desk-pilot", user_id="u-1"
    )
    assert captured == [{"memory_facts_injected": 0}]
    assert not any(
        isinstance(m, SystemMessage) and str(m.content).startswith(MEMORY_FACTS_HEADER)
        for m in out
    )


async def test_span_memory_degraded_on_recall_failure(monkeypatch: pytest.MonkeyPatch):
    """召回故障：span 收到 {"memory_degraded": True} 且全程无 memory_facts_injected。"""
    monkeypatch.setenv("MEMORY_FACTS_ENABLED", "true")
    captured = _capture_span(monkeypatch)
    _patch_recall(monkeypatch, error=RuntimeError("db down"))

    out = await assemble_graph_messages_with_memory(
        "q", _fixture_turns(), tenant_id="ops-desk-pilot", user_id="u-1"
    )
    assert captured == [{"memory_degraded": True}]
    assert all("memory_facts_injected" not in m for m in captured)
    baseline = assemble_graph_messages("q", _fixture_turns())
    assert _shape(out) == _shape(baseline)


async def test_span_disabled_zero_calls(monkeypatch: pytest.MonkeyPatch):
    """开关关闭：零 span 调用（与既有逐字节一致断言并存）。"""
    monkeypatch.delenv("MEMORY_FACTS_ENABLED", raising=False)
    captured = _capture_span(monkeypatch)

    history = _fixture_turns()
    baseline = assemble_graph_messages("q", history)
    out = await assemble_graph_messages_with_memory(
        "q", history, tenant_id="ops-desk-pilot", user_id="u-1"
    )
    assert captured == []
    assert _shape(out) == _shape(baseline)

