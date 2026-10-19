"""Host V1-B · 场景维第二阶段裁剪（D2 scenario_trim / D3 剔除台账）。

覆盖（task 验收 D2/D3 映射）：
- 规则表 S1–S5 裁剪矩阵 × risk_level 组合（S1 fallback→∅ · S2 needs_tool=False→∅ ·
  S3 unknown+needs_tool→∅ · S4 high→剔 medium 留 low · S5 low/medium 不追加）；
- 安全默认：fallback/歧义 → 空集 + 台账可查（变异检验①的靶断言）；
- 畸形 intent：缺 risk_hint 视同 high · 缺 domain 视同 unknown；
- 三档模式：off 零 diff 零日志 · observe would_strip 不生效 · enforce 生效；
- 剔除台账：id+reason+计数（caplog）· 不记 query/intent 原文（变异检验③的靶断言）；
- Builder 集成 + supervisor 交集输入=场景维后有效可见集（R1 审查 B-1）；
- 计时 smoke（注记级 · SPEC FP-4 · 不设硬 CI 阈值）。
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import HumanMessage

from app.ops.capability import (
    CapabilitySpec,
    LocalFnAdapter,
    ensure_default_capabilities,
    get_registry,
    register,
)
from app.ops.capability import delegation as dl
from app.ops.strategy import scenario as sc
from app.ops.strategy.builder import _apply_scenario_stage, strategy_builder_node

MEDIUM_CAP = "test_scenario_medium_read"


def _spec(cid: str, risk: str) -> CapabilitySpec:
    return CapabilitySpec(
        capability_id=cid,
        kind="local_fn",
        description="探针",
        risk_level=risk,
        side_effect="read",
    )


@pytest.fixture(autouse=True)
def _restore_registry():
    yield
    get_registry().clear()
    ensure_default_capabilities()


@pytest.fixture
def base_visible() -> list[CapabilitySpec]:
    # 基线（stage 1）已剔 high risk + write；此处含 low/medium 模拟基线输出
    return [_spec("cap.low.a", "low"), _spec("cap.medium.b", "medium")]


def _span_cm():
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=None)
    cm.__exit__ = MagicMock(return_value=False)
    return cm


# ---------------------------------------------------------------------------
# 规则表 S1–S5（裁剪矩阵）
# ---------------------------------------------------------------------------


def test_s1_fallback_empties_visible_set(base_visible):
    final, stripped = sc.scenario_trim(
        base_visible, {"needs_tool": True, "domain": "ops_kb", "risk_hint": "low"}, True
    )
    assert final == []
    assert stripped == [
        ("cap.low.a", sc.REASON_INTENT_FALLBACK),
        ("cap.medium.b", sc.REASON_INTENT_FALLBACK),
    ]


def test_s2_needs_tool_false_empties(base_visible):
    final, stripped = sc.scenario_trim(
        base_visible, {"needs_tool": False, "domain": "ops_kb", "risk_hint": "low"}, False
    )
    assert final == []
    assert {r for _, r in stripped} == {sc.REASON_NEEDS_TOOL_FALSE}


def test_s3_unknown_domain_with_needs_tool_empties(base_visible):
    final, stripped = sc.scenario_trim(
        base_visible, {"needs_tool": True, "domain": "unknown", "risk_hint": "low"}, False
    )
    assert final == []
    assert {r for _, r in stripped} == {sc.REASON_DOMAIN_UNKNOWN}
    # unknown 域但不需要工具 → S2 语义（非 S3）
    final2, stripped2 = sc.scenario_trim(
        base_visible, {"needs_tool": False, "domain": "unknown"}, False
    )
    assert final2 == []
    assert {r for _, r in stripped2} == {sc.REASON_NEEDS_TOOL_FALSE}
    # 已知域 + 需要工具 → 不空
    final3, _ = sc.scenario_trim(
        base_visible, {"needs_tool": True, "domain": "ops_kb", "risk_hint": "low"}, False
    )
    assert len(final3) == 2


def test_s4_high_risk_trims_medium_keeps_low():
    visible = [
        _spec("cap.low.a", "low"),
        _spec("cap.medium.b", "medium"),
        _spec("cap.high.c", "high"),
    ]
    final, stripped = sc.scenario_trim(
        visible, {"needs_tool": True, "domain": "ops_kb", "risk_hint": "high"}, False
    )
    assert [s.capability_id for s in final] == ["cap.low.a"]
    assert stripped == [
        ("cap.medium.b", sc.REASON_RISK_HIGH_TIGHTEN),
        ("cap.high.c", sc.REASON_RISK_HIGH_TIGHTEN),
    ]


@pytest.mark.parametrize("hint", ["low", "medium"])
def test_s5_low_medium_no_extra_trim(base_visible, hint):
    final, stripped = sc.scenario_trim(
        base_visible, {"needs_tool": True, "domain": "ops_kb", "risk_hint": hint}, False
    )
    assert final == base_visible
    assert stripped == []


# ---------------------------------------------------------------------------
# 畸形 intent（安全默认）
# ---------------------------------------------------------------------------


def test_malformed_intent_missing_risk_hint_treated_as_high(base_visible):
    final, stripped = sc.scenario_trim(
        base_visible, {"needs_tool": True, "domain": "ops_kb"}, False
    )
    assert [s.capability_id for s in final] == ["cap.low.a"]
    assert {r for _, r in stripped} == {sc.REASON_RISK_HIGH_TIGHTEN}


def test_malformed_intent_missing_domain_treated_as_unknown(base_visible):
    final, stripped = sc.scenario_trim(
        base_visible, {"needs_tool": True, "risk_hint": "low"}, False
    )
    assert final == []
    assert {r for _, r in stripped} == {sc.REASON_DOMAIN_UNKNOWN}


def test_malformed_intent_non_dict(base_visible):
    """非 dict intent：缺 domain→unknown · needs_tool 缺失非 True → S3 不触发 ·
    缺 risk_hint→视同 high → 剔 medium（安全默认方向：只收紧不放宽）。"""
    final, stripped = sc.scenario_trim(base_visible, "garbage", False)
    assert [s.capability_id for s in final] == ["cap.low.a"]
    assert {r for _, r in stripped} == {sc.REASON_RISK_HIGH_TIGHTEN}


def test_is_composite_and_summary_not_trim_keys(base_visible):
    """Q2 裁定：is_composite/summary 不作裁剪键（自由文本不作安全键）。"""
    final, stripped = sc.scenario_trim(
        base_visible,
        {
            "needs_tool": True,
            "domain": "ops_kb",
            "risk_hint": "low",
            "is_composite": True,
            "summary": "看起来很危险的描述",
        },
        False,
    )
    assert final == base_visible
    assert stripped == []


# ---------------------------------------------------------------------------
# 三档模式（Builder stage 2 接线）
# ---------------------------------------------------------------------------


def test_mode_off_zero_diff_zero_log(monkeypatch, base_visible, caplog):
    monkeypatch.setenv(sc.ENV_SCENARIO_MODE, "off")
    state = {
        "intent": {"needs_tool": True, "domain": "ops_kb", "risk_hint": "high"},
        "intent_fallback": True,
    }
    with caplog.at_level(logging.WARNING, logger="app.ops.strategy.scenario"):
        out = _apply_scenario_stage(base_visible, state)
    assert out is base_visible  # off = 现状零 diff（fallback 也不裁）
    assert "visibility_scenario" not in caplog.text  # off 零日志


def test_mode_invalid_falls_back_off(monkeypatch, base_visible):
    monkeypatch.setenv(sc.ENV_SCENARIO_MODE, "bogus")
    out = _apply_scenario_stage(base_visible, {"intent_fallback": True})
    assert out is base_visible


def test_mode_observe_would_strip_not_applied(monkeypatch, base_visible, caplog):
    monkeypatch.setenv(sc.ENV_SCENARIO_MODE, "observe")
    state = {"intent": {"needs_tool": True, "domain": "ops_kb", "risk_hint": "high"}}
    with caplog.at_level(logging.WARNING, logger="app.ops.strategy.scenario"):
        out = _apply_scenario_stage(base_visible, state)
    assert out is base_visible  # observe 不生效
    assert "visibility_scenario_would_strip" in caplog.text
    assert "risk_high_tighten" in caplog.text
    assert "cap.medium.b" in caplog.text


def test_mode_enforce_applies_and_audits(monkeypatch, base_visible, caplog):
    monkeypatch.setenv(sc.ENV_SCENARIO_MODE, "enforce")
    state = {"intent": {"needs_tool": True, "domain": "ops_kb", "risk_hint": "high"}}
    with caplog.at_level(logging.WARNING, logger="app.ops.strategy.scenario"):
        out = _apply_scenario_stage(base_visible, state)
    assert [s.capability_id for s in out] == ["cap.low.a"]
    assert "visibility_scenario_stripped" in caplog.text
    assert "cap.medium.b" in caplog.text


def test_audit_does_not_log_intent_content(monkeypatch, base_visible, caplog):
    """记动作不记内容：剔除台账不含 query/intent 原文（summary 等自由文本）。"""
    monkeypatch.setenv(sc.ENV_SCENARIO_MODE, "enforce")
    secret_text = "用户敏感原始问句xyz"
    state = {
        "intent": {
            "needs_tool": True,
            "domain": "ops_kb",
            "risk_hint": "high",
            "summary": secret_text,
        }
    }
    with caplog.at_level(logging.WARNING, logger="app.ops.strategy.scenario"):
        _apply_scenario_stage(base_visible, state)
    assert "visibility_scenario_stripped" in caplog.text
    assert secret_text not in caplog.text


def test_enforce_fallback_empties_with_audit(monkeypatch, base_visible, caplog):
    """fallback 裂缝堵死（FP-5）：fallback=意图不可信 → 空集 + 台账。"""
    monkeypatch.setenv(sc.ENV_SCENARIO_MODE, "enforce")
    state = {
        "intent": {"needs_tool": True, "domain": "ops_kb", "risk_hint": "low"},
        "intent_fallback": True,
    }
    with caplog.at_level(logging.WARNING, logger="app.ops.strategy.scenario"):
        out = _apply_scenario_stage(base_visible, state)
    assert out == []
    assert sc.REASON_INTENT_FALLBACK in caplog.text


@pytest.mark.parametrize("mode", ["off", "observe", "enforce"])
def test_no_intent_short_circuits_all_modes(monkeypatch, base_visible, caplog, mode):
    """D3/TC6：无 intent（supervisor-first 主路径形态）→ S1–S5 全短路不裁。

    visible 进=出逐 id 对拍；enforce 档同样短路（含 S4 缺省 risk_hint→high
    收紧路径——无 intent 即无裁剪依据，只放行基线可见集）；零 warning 台账。
    """
    monkeypatch.setenv(sc.ENV_SCENARIO_MODE, mode)
    with caplog.at_level(logging.WARNING, logger="app.ops.strategy.scenario"):
        out = _apply_scenario_stage(base_visible, {})
    assert [s.capability_id for s in out] == [s.capability_id for s in base_visible]
    assert "visibility_scenario" not in caplog.text


@pytest.mark.asyncio
async def test_builder_enforce_no_intent_passes_baseline_through(monkeypatch, caplog):
    """D3/TC6（Builder 集成）：enforce 档 + 无 intent → allowlist ≡ 基线 ∩ candidates，
    不被 S4 缺省 high 收紧路径裁掉 medium（收紧≠基线∩candidates 即红）。"""
    monkeypatch.setenv(sc.ENV_SCENARIO_MODE, "enforce")
    register(
        CapabilitySpec(
            capability_id=MEDIUM_CAP,
            kind="local_fn",
            description="中风险读探针",
            risk_level="medium",
            side_effect="read",
        ),
        LocalFnAdapter(lambda args: {"echo": args}),
    )
    state = {"messages": [HumanMessage(content="q")]}
    with (
        patch(
            "app.ops.strategy.builder.get_candidate_capability_ids",
            return_value=[MEDIUM_CAP, "utc_now_iso"],
        ),
        patch("app.ops.strategy.builder._record_builder_span"),
        patch("app.ops.strategy.builder.trace_span", return_value=_span_cm()),
        caplog.at_level(logging.WARNING, logger="app.ops.strategy.scenario"),
    ):
        out = await strategy_builder_node(state)
    assert sorted(out["allowed_capability_ids"]) == sorted([MEDIUM_CAP, "utc_now_iso"])
    assert "visibility_scenario" not in caplog.text


# ---------------------------------------------------------------------------
# Builder 集成 + supervisor 交集输入 = 场景维后有效可见集（B-1）
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_builder_enforce_high_intent_trims_medium_candidate(monkeypatch, caplog):
    monkeypatch.setenv(sc.ENV_SCENARIO_MODE, "enforce")
    register(
        CapabilitySpec(
            capability_id=MEDIUM_CAP,
            kind="local_fn",
            description="中风险读探针",
            risk_level="medium",
            side_effect="read",
        ),
        LocalFnAdapter(lambda args: {"echo": args}),
    )
    state = {
        "messages": [HumanMessage(content="q")],
        "intent": {"needs_tool": True, "domain": "ops_kb", "risk_hint": "high"},
        "intent_fallback": False,
    }
    with (
        patch(
            "app.ops.strategy.builder.get_candidate_capability_ids",
            return_value=[MEDIUM_CAP, "utc_now_iso"],
        ),
        patch("app.ops.strategy.builder._record_builder_span"),
        patch("app.ops.strategy.builder.trace_span", return_value=_span_cm()),
        caplog.at_level(logging.WARNING, logger="app.ops.strategy.scenario"),
    ):
        out = await strategy_builder_node(state)
    assert out["allowed_capability_ids"] == ["utc_now_iso"]
    assert MEDIUM_CAP in caplog.text
    assert sc.REASON_RISK_HIGH_TIGHTEN in caplog.text


@pytest.mark.asyncio
async def test_supervisor_delegation_scope_never_exceeds_scenario_trim(monkeypatch):
    """B-1 钉死：delegation_scope = requested_scope ∩ 场景维后有效可见集。

    Builder 已在场景维裁掉 MEDIUM_CAP（allowlist 不含它）；模型声明
    requested_scope 含被裁 id → 不进入 delegation_scope（委派令牌不越场景维）。
    """
    monkeypatch.setenv(sc.ENV_SCENARIO_MODE, "enforce")
    monkeypatch.setenv(dl.ENV_MODE, "observe")
    monkeypatch.setenv(dl.ENV_SECRET, "scenario-b1-secret")
    register(
        CapabilitySpec(
            capability_id=MEDIUM_CAP,
            kind="local_fn",
            description="中风险读探针",
            risk_level="medium",
            side_effect="read",
        ),
        LocalFnAdapter(lambda args: {"echo": args}),
    )
    from app.ops.lg_rag.multi.nodes import supervisor_node

    plan = {
        "subtasks": [{"id": "t1", "type": "tool", "input": "查时间", "tool": "utc_now_iso"}],
        "requested_scope": [MEDIUM_CAP, "utc_now_iso"],
    }
    provider = SimpleNamespace(
        complete=AsyncMock(return_value=json.dumps(plan, ensure_ascii=False))
    )
    state = {
        "messages": [HumanMessage(content="查时间")],
        "run_id": f"run-{uuid.uuid4().hex[:8]}",
        # Builder 场景维裁后形态：MEDIUM_CAP 已不在 allowlist
        "allowed_capability_ids": ["utc_now_iso"],
    }
    with patch("app.ops.lg_rag.multi.nodes.get_llm_provider", return_value=provider):
        out = await supervisor_node(state)
    assert out["delegation_scope"] == ["utc_now_iso"]


# ---------------------------------------------------------------------------
# 计时 smoke（注记级 · SPEC FP-4 <10ms · 不设硬 CI 阈值）
# ---------------------------------------------------------------------------


def test_scenario_trim_timing_smoke(base_visible):
    intent = {"needs_tool": True, "domain": "ops_kb", "risk_hint": "high"}
    rounds = 1000
    started = time.perf_counter()
    for _ in range(rounds):
        final, stripped = sc.scenario_trim(base_visible, intent, False)
        assert len(final) == 1 and len(stripped) == 1
    avg_ms = (time.perf_counter() - started) * 1000.0 / rounds
    # 注记：纯代码无 IO，实测微秒级（量级声明 <10ms · SPEC FP-4 · 不设硬阈值）。
    print(f"scenario_trim avg {avg_ms:.4f} ms/call over {rounds} calls")
