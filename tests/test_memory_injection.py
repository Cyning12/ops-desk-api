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


async def test_recall_failure_degrades_to_no_injection(monkeypatch: pytest.MonkeyPatch, caplog):
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
        isinstance(m, SystemMessage) and str(m.content).startswith(MEMORY_FACTS_HEADER) for m in out
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


async def test_span_dual_counts_mixed_kinds(monkeypatch: pytest.MonkeyPatch):
    """span 双计数：facts/preferences 分别记；注入仍是**单条** SystemMessage 双节。"""
    monkeypatch.setenv("MEMORY_FACTS_ENABLED", "true")
    captured = _capture_span(monkeypatch)
    facts = [
        {"key": "project.primary_repo", "value": "cyning/ops-desk"},
        {"key": "pref.answer_lang", "value": "中文", "kind": "preference"},
    ]
    _patch_recall(monkeypatch, facts=facts)

    out = await assemble_graph_messages_with_memory(
        "q", _fixture_turns(), tenant_id="ops-desk-pilot", user_id="u-1"
    )
    assert captured == [{"memory_facts_injected": 1, "memory_preferences_injected": 1}]
    memory_msgs = [
        m for m in out if isinstance(m, SystemMessage) and MEMORY_FACTS_HEADER in str(m.content)
    ]
    assert len(memory_msgs) == 1  # 单条 SystemMessage
    content = str(memory_msgs[0].content)
    assert MEMORY_PREFERENCES_HEADER in content  # 双节同块


async def test_span_fact_only_no_preferences_key(monkeypatch: pytest.MonkeyPatch):
    """fact-only：span 不带 memory_preferences_injected key（与 P0/P1 观测面一致）。"""
    monkeypatch.setenv("MEMORY_FACTS_ENABLED", "true")
    captured = _capture_span(monkeypatch)
    _patch_recall(monkeypatch, facts=[{"key": "project.primary_repo", "value": "cyning/ops-desk"}])
    await assemble_graph_messages_with_memory(
        "q", _fixture_turns(), tenant_id="ops-desk-pilot", user_id="u-1"
    )
    assert captured == [{"memory_facts_injected": 1}]


async def test_span_preference_only_facts_zero(monkeypatch: pytest.MonkeyPatch):
    """preference-only：facts=0 / preferences=1 并列计数；注入块无事实节。"""
    monkeypatch.setenv("MEMORY_FACTS_ENABLED", "true")
    captured = _capture_span(monkeypatch)
    _patch_recall(
        monkeypatch,
        facts=[{"key": "pref.answer_lang", "value": "中文", "kind": "preference"}],
    )
    out = await assemble_graph_messages_with_memory(
        "q", _fixture_turns(), tenant_id="ops-desk-pilot", user_id="u-1"
    )
    assert captured == [{"memory_facts_injected": 0, "memory_preferences_injected": 1}]
    memory_msgs = [
        str(m.content)
        for m in out
        if isinstance(m, SystemMessage) and MEMORY_PREFERENCES_HEADER in str(m.content)
    ]
    assert len(memory_msgs) == 1
    assert MEMORY_FACTS_HEADER not in memory_msgs[0]
