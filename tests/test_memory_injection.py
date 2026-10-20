"""memory-facts-p0 · M3 装配注入（纯装配 · 不连 DB）：开关关闭零 diff / 块格式 / 降级。"""

from __future__ import annotations

import logging

import pytest
from langchain_core.messages import BaseMessage, SystemMessage

from app.ops.lg_rag.continuity import (
    MEMORY_FACTS_HEADER,
    MEMORY_PREFERENCES_GUIDE,
    MEMORY_PREFERENCES_HEADER,
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
async def test_disabled_or_invalid_is_byte_identical(monkeypatch: pytest.MonkeyPatch, value: str):
    monkeypatch.setenv("MEMORY_FACTS_ENABLED", value)
    history = _fixture_turns()
    baseline = assemble_graph_messages("q-now", history)
    with_memory = await assemble_graph_messages_with_memory(
        "q-now", history, tenant_id="ops-desk-pilot", user_id="u-1"
    )
    assert _shape(with_memory) == _shape(baseline)


def test_enabled_invalid_value_warns_and_falls_back(monkeypatch: pytest.MonkeyPatch, caplog):
    monkeypatch.setenv("MEMORY_FACTS_ENABLED", "enable plz")
    with caplog.at_level(logging.WARNING, logger="app.ops.lg_rag.continuity"):
        assert memory_facts_enabled() is False
    assert "MEMORY_FACTS_ENABLED" in caplog.text


async def test_enabled_but_missing_identity_no_skip_warning_dormant(
    monkeypatch: pytest.MonkeyPatch, caplog
):
    """④b 休眠断言：装配面不再走注入路径——身份缺失场景无 skip 告警、输出逐字节不变。

    （④a 复活时按 docs/tasks/deferred/task_memory_facts_build_4a.md 清单恢复 skip 告警断言。）
    """
    monkeypatch.setenv("MEMORY_FACTS_ENABLED", "true")
    history = _fixture_turns()
    baseline = assemble_graph_messages("q", history)
    with caplog.at_level(logging.WARNING, logger="app.ops.lg_rag.continuity"):
        out = await assemble_graph_messages_with_memory("q", history)
    assert _shape(out) == _shape(baseline)
    assert "skip injection" not in caplog.text


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


async def test_recall_never_called_no_degrade_dormant(monkeypatch: pytest.MonkeyPatch, caplog):
    """④b 休眠断言：注入开下 recall 零调用（stub 触达即炸）、无降级告警、输出逐字节不变。"""
    from unittest.mock import AsyncMock

    monkeypatch.setenv("MEMORY_FACTS_ENABLED", "true")
    monkeypatch.delenv("MEMORY_FACTS_VECTOR_RECALL_ENABLED", raising=False)
    stub = AsyncMock(side_effect=AssertionError("④b 休眠：recall 不应被调用"))
    monkeypatch.setattr("app.ops.memory.service.recall_active", stub)
    history = _fixture_turns()
    baseline = assemble_graph_messages("q", history)
    with caplog.at_level(logging.ERROR, logger="app.ops.lg_rag.continuity"):
        out = await assemble_graph_messages_with_memory(
            "q", history, tenant_id="ops-desk-pilot", user_id="u-1"
        )
    stub.assert_not_awaited()
    assert _shape(out) == _shape(baseline)
    assert "degrade to no injection" not in caplog.text


# ---------------- span `memory_facts_injected` 专门单测（memory-embedding-backfill D3） ----------------
# capture-list 模式对齐 tests/test_llm_routing.py:176；发射点 continuity.py:237-243。


def _capture_span(monkeypatch: pytest.MonkeyPatch) -> list[dict]:
    """monkeypatch continuity 命名空间内的 update_current_span_metadata，返回捕获列表。"""
    from app.ops.lg_rag import continuity

    captured: list[dict] = []
    monkeypatch.setattr(continuity, "update_current_span_metadata", lambda m: captured.append(m))
    return captured


def _patch_recall(monkeypatch: pytest.MonkeyPatch, *, facts=None, error=None):
    """patch 装配链路实际调用的 memory service 召回（默认确定性通路）。

    连带钉 off 向量召回开关（test-baseline-reds 全量回归 unmask）：宿主 .env
    若设 MEMORY_FACTS_VECTOR_RECALL_ENABLED=true 且网络可用，装配会改走
    recall_with_vector（真 embed + 向量 SQL + 与 mocked dicts 融合崩溃 →
    memory_degraded），与「本文件只测确定性装配通路」意图不符。向量通路
    有 test_memory_vector_p1.py 的 FakeEmbedder 专测覆盖。
    """
    from unittest.mock import AsyncMock

    monkeypatch.delenv("MEMORY_FACTS_VECTOR_RECALL_ENABLED", raising=False)

    mock = (
        AsyncMock(side_effect=error) if error is not None else AsyncMock(return_value=facts or [])
    )
    monkeypatch.setattr("app.ops.memory.service.recall_active", mock)
    return mock


async def test_span_no_memory_facts_count_dormant(monkeypatch: pytest.MonkeyPatch):
    """④b 休眠断言：注入开下零 span 计数、零注入块、recall 零调用、输出逐字节不变。"""
    monkeypatch.setenv("MEMORY_FACTS_ENABLED", "true")
    captured = _capture_span(monkeypatch)
    stub = _patch_recall(
        monkeypatch,
        facts=[
            {"key": "project.primary_repo", "value": "cyning/ops-desk"},
            {"key": "user.display_tz", "value": "Asia/Shanghai"},
        ],
    )

    history = _fixture_turns()
    baseline = assemble_graph_messages("q", history)
    out = await assemble_graph_messages_with_memory(
        "q", history, tenant_id="ops-desk-pilot", user_id="u-1"
    )
    stub.assert_not_awaited()
    assert captured == []
    assert _shape(out) == _shape(baseline)


async def test_span_zero_recall_also_zero_span_dormant(monkeypatch: pytest.MonkeyPatch):
    """④b 休眠断言：零 facts 桩同样零触达——无 span 计数、无注入块（:240 分支已收窄）。"""
    monkeypatch.setenv("MEMORY_FACTS_ENABLED", "true")
    captured = _capture_span(monkeypatch)
    stub = _patch_recall(monkeypatch, facts=[])

    history = _fixture_turns()
    baseline = assemble_graph_messages("q", history)
    out = await assemble_graph_messages_with_memory(
        "q", history, tenant_id="ops-desk-pilot", user_id="u-1"
    )
    stub.assert_not_awaited()
    assert captured == []
    assert _shape(out) == _shape(baseline)


async def test_span_no_degraded_no_recall_dormant(monkeypatch: pytest.MonkeyPatch):
    """④b 休眠断言：故障桩零触达——无 memory_degraded、无任何记忆 span、输出逐字节不变。"""
    monkeypatch.setenv("MEMORY_FACTS_ENABLED", "true")
    captured = _capture_span(monkeypatch)
    stub = _patch_recall(monkeypatch, error=AssertionError("④b 休眠：recall 不应被调用"))

    history = _fixture_turns()
    baseline = assemble_graph_messages("q", history)
    out = await assemble_graph_messages_with_memory(
        "q", history, tenant_id="ops-desk-pilot", user_id="u-1"
    )
    stub.assert_not_awaited()
    assert captured == []
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


# ---------------- memory-preference-profile · 分节渲染（方案 B1 单块双节） ----------------


def test_render_fact_only_byte_identical_to_legacy():
    """fact 节与现网**逐字节一致**（对拍 · 一次性钉串）：显式 kind=fact 与
    缺省 kind（旧 dict 语义）渲染结果完全相同。"""
    facts = [
        {"key": "project.primary_repo", "value": "cyning/ops-desk"},
        {"key": "user.retry_limit", "value": 3},
        {"key": "user.multiline", "value": "a\nb"},
    ]
    expected = (
        "[已知事实]\nproject.primary_repo=cyning/ops-desk\nuser.retry_limit=3\nuser.multiline=a\\nb"
    )
    assert render_memory_facts_block(facts) == expected
    with_kind = [dict(f, kind="fact") for f in facts]
    assert render_memory_facts_block(with_kind) == expected  # 显式 fact 同字节


def test_render_sections_no_cross_contamination():
    """分节互不串：fact 行进 [已知事实] 节、preference 行进 [用户偏好] 节。"""
    facts = [
        {"key": "project.primary_repo", "value": "cyning/ops-desk"},
        {"key": "pref.answer_lang", "value": "中文", "kind": "preference"},
    ]
    block = render_memory_facts_block(facts)
    lines = block.split("\n")
    pref_idx = lines.index(MEMORY_PREFERENCES_HEADER)
    fact_idx = lines.index(MEMORY_FACTS_HEADER)
    # 事实节在偏好节之前；各行归属正确
    assert fact_idx < pref_idx
    fact_section = lines[fact_idx:pref_idx]
    pref_section = lines[pref_idx:]
    assert "project.primary_repo=cyning/ops-desk" in fact_section
    assert "pref.answer_lang=中文" in pref_section
    assert not any(line.startswith("pref.") for line in fact_section)  # 偏好不污染事实节
    assert not any(line.startswith("project.") for line in pref_section)


def test_render_no_preference_section_physically_absent():
    """红线结构断言：无 preference → 偏好节**物理不存在**（非空节）。"""
    facts = [{"key": "project.primary_repo", "value": "cyning/ops-desk"}]
    block = render_memory_facts_block(facts)
    assert MEMORY_PREFERENCES_HEADER not in block
    assert MEMORY_PREFERENCES_GUIDE not in block


def test_render_preference_only_no_fact_section():
    """对称结构断言：无 fact → 事实节物理不存在，偏好节独立成块。"""
    facts = [{"key": "pref.answer_lang", "value": "中文", "kind": "preference"}]
    block = render_memory_facts_block(facts)
    assert MEMORY_FACTS_HEADER not in block
    assert block.startswith(MEMORY_PREFERENCES_HEADER)


def test_render_preference_section_anchors():
    """锚点断言（非全文快照）：偏好节含「用户偏好」节名与「非客观事实」级
    锚点 + 「无偏好不要假设/编造」语义；改文案不挂，改变量语义必挂。"""
    facts = [{"key": "pref.answer_lang", "value": "中文", "kind": "preference"}]
    block = render_memory_facts_block(facts)
    assert "[用户偏好]" in block
    assert "非客观事实" in block
    assert "无偏好" in block and ("假设" in block or "编造" in block)


async def test_span_no_dual_counts_dormant(monkeypatch: pytest.MonkeyPatch):
    """④b 休眠断言：混合 kind 桩零触达——无 facts/preferences 双计数、无注入块。"""
    monkeypatch.setenv("MEMORY_FACTS_ENABLED", "true")
    captured = _capture_span(monkeypatch)
    stub = _patch_recall(
        monkeypatch,
        facts=[
            {"key": "project.primary_repo", "value": "cyning/ops-desk"},
            {"key": "pref.answer_lang", "value": "中文", "kind": "preference"},
        ],
    )

    history = _fixture_turns()
    baseline = assemble_graph_messages("q", history)
    out = await assemble_graph_messages_with_memory(
        "q", history, tenant_id="ops-desk-pilot", user_id="u-1"
    )
    stub.assert_not_awaited()
    assert captured == []
    assert _shape(out) == _shape(baseline)


async def test_span_fact_only_also_zero_dormant(monkeypatch: pytest.MonkeyPatch):
    """④b 休眠断言：fact-only 桩零触达——无任何记忆 span key、输出逐字节不变。"""
    monkeypatch.setenv("MEMORY_FACTS_ENABLED", "true")
    captured = _capture_span(monkeypatch)
    stub = _patch_recall(
        monkeypatch, facts=[{"key": "project.primary_repo", "value": "cyning/ops-desk"}]
    )
    history = _fixture_turns()
    baseline = assemble_graph_messages("q", history)
    out = await assemble_graph_messages_with_memory(
        "q", history, tenant_id="ops-desk-pilot", user_id="u-1"
    )
    stub.assert_not_awaited()
    assert captured == []
    assert _shape(out) == _shape(baseline)


async def test_span_preference_only_also_zero_dormant(monkeypatch: pytest.MonkeyPatch):
    """④b 休眠断言：preference-only 桩零触达——无并列计数、无偏好节块。"""
    monkeypatch.setenv("MEMORY_FACTS_ENABLED", "true")
    captured = _capture_span(monkeypatch)
    stub = _patch_recall(
        monkeypatch,
        facts=[{"key": "pref.answer_lang", "value": "中文", "kind": "preference"}],
    )
    history = _fixture_turns()
    baseline = assemble_graph_messages("q", history)
    out = await assemble_graph_messages_with_memory(
        "q", history, tenant_id="ops-desk-pilot", user_id="u-1"
    )
    stub.assert_not_awaited()
    assert captured == []
    assert _shape(out) == _shape(baseline)
