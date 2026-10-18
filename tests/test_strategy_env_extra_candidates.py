"""T3 · strategy 候选 map env 追加口（OPS_STRATEGY_EXTRA_CANDIDATE_CAPABILITY_IDS）验收。

TC1：①不设 env 各 key（含未知 key）解析结果对 master 逐字节零 diff（字面量断言）
     ②设 env 追加语义（map 命中 + 未知 key 两例 · ∩visible/stripped 不变）
     ③解析四例（strip / 去空 / 保序去重 / 全空白=不设）④覆盖口隔离（env 不混入）
TC2：FP-5 三层——env 含高危/写 id 仍被 ∩visible + deny 判序 + Policy 写闸裁
TC3：env 生效台账断言（设则记 · 未设不记）+ 调用点读取（monkeypatch 直读生效）
"""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import HumanMessage

from app.ops.capability.policy import check_invoke
from app.ops.capability.registry import _match_filter
from app.ops.capability.types import CapabilityFilter, CapabilitySpec
from app.ops.strategy import config as strategy_config
from app.ops.strategy.builder import (
    BUILDER_CAP_FILTER,
    build_allowlist_from_candidates,
    strategy_builder_node,
)

_ENV = strategy_config.EXTRA_CANDIDATE_CAPABILITY_IDS_ENV

# master 基线字面量（TC1① 对拍锚 · CAPABILITY_ALLOWLIST_BY_KEY 静态成员）
_SUPERVISOR_IDS = [
    "utc_now_iso",
    "mock_get_issue_status",
    "mock_get_deploy_info",
    "get_issue_by_number",
    "get_pr_by_number",
]
_DEFAULT_IDS = ["utc_now_iso"]

_SCHEMA = {"type": "object", "properties": {}}


@pytest.fixture(autouse=True)
def _clean_env_and_override(monkeypatch: pytest.MonkeyPatch):
    """每用例隔离：env 不设 · 覆盖口 None（防跨文件全局漂移）。"""
    monkeypatch.delenv(_ENV, raising=False)
    monkeypatch.setattr(strategy_config, "CANDIDATE_CAPABILITY_IDS", None)


def _span_cm():
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=None)
    cm.__exit__ = MagicMock(return_value=False)
    return cm


def _spec(cid: str, **over) -> CapabilitySpec:
    base: dict = {
        "capability_id": cid,
        "kind": "local_fn",
        "description": "单测",
        "args_schema": dict(_SCHEMA),
        "tags": ("testing",),
        "side_effect": "read",
        "when_to_use": "单测",
    }
    base.update(over)
    return CapabilitySpec(**base)


# ---------------- TC1① 不设 env · 逐字节零 diff（字面量对拍） ----------------


def test_tc1_unset_env_supervisor_byte_identical():
    """不设 env → supervisor 解析结果与 master 静态五枚逐字节一致（内容+顺序）。"""
    assert strategy_config.get_candidate_capability_ids(mode="supervisor") == _SUPERVISOR_IDS
    assert strategy_config.get_candidate_capability_ids(agent_type="supervisor") == _SUPERVISOR_IDS


def test_tc1_unset_env_default_byte_identical():
    assert strategy_config.get_candidate_capability_ids(mode="default") == _DEFAULT_IDS


def test_tc1_unset_env_unknown_key_fail_closed():
    """未知 key → 空列表（fail-closed · env 不设时零 diff）。"""
    assert strategy_config.get_candidate_capability_ids(agent_type="no_such_agent") == []
    assert strategy_config.get_candidate_capability_ids(mode="mystery") == []


def test_tc1_blank_env_equals_unset(monkeypatch: pytest.MonkeyPatch):
    """全空白 / 全逗号空白 env = 不设（追加集为空 · 两态结果相等）。"""
    for blank in ("   ", "  , ,  ", ",,,"):
        monkeypatch.setenv(_ENV, blank)
        assert strategy_config.get_candidate_capability_ids(mode="supervisor") == _SUPERVISOR_IDS
        assert strategy_config.get_candidate_capability_ids(agent_type="no_such_agent") == []


# ---------------- TC1② 设 env · 追加语义 ----------------


def test_tc1_env_appended_after_map_hit(monkeypatch: pytest.MonkeyPatch):
    """map 命中 key：env 追加集在静态成员之后（保序）。"""
    monkeypatch.setenv(_ENV, "testing.write.echo")
    got = strategy_config.get_candidate_capability_ids(mode="supervisor")
    assert got == _SUPERVISOR_IDS + ["testing.write.echo"]
    # map 本体不被改（返回新 list）
    assert strategy_config.CAPABILITY_ALLOWLIST_BY_KEY["supervisor"] == _SUPERVISOR_IDS


def test_tc1_env_appended_for_unknown_key(monkeypatch: pytest.MonkeyPatch):
    """未知 key（map 未命中=[]）也追加——env 是运维显式声明，fail-closed 管默认不管显式。"""
    monkeypatch.setenv(_ENV, "extra.alpha")
    assert strategy_config.get_candidate_capability_ids(agent_type="no_such_agent") == [
        "extra.alpha",
    ]


def test_tc1_env_intersection_visible_semantics_unchanged(monkeypatch: pytest.MonkeyPatch):
    """∩visible/stripped 语义不变：env id 不可见仍剔除，可见则放行。"""
    monkeypatch.setenv(_ENV, "extra.visible_tool, testing.write.echo")
    candidates = strategy_config.get_candidate_capability_ids(mode="supervisor")
    visible = frozenset({"utc_now_iso", "extra.visible_tool"})
    allowed, stripped = build_allowlist_from_candidates(candidates, visible_ids=visible)
    assert allowed == ["utc_now_iso", "extra.visible_tool"]
    assert stripped == [
        "mock_get_issue_status",
        "mock_get_deploy_info",
        "get_issue_by_number",
        "get_pr_by_number",
        "testing.write.echo",
    ]


# ---------------- TC1③ 解析四例（strip / 去空 / 保序去重 / 全空白） ----------------


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("alpha, beta ,gamma", ["alpha", "beta", "gamma"]),  # 逐项 strip
        ("alpha,,beta,,", ["alpha", "beta"]),  # 连续逗号去空
        ("alpha,beta,alpha,beta", ["alpha", "beta"]),  # 保序去重
        (" , , ", []),  # 全空白=不设
    ],
)
def test_tc1_env_parse_cases(monkeypatch: pytest.MonkeyPatch, raw: str, expected: list[str]):
    monkeypatch.setenv(_ENV, raw)
    assert strategy_config.get_candidate_capability_ids(agent_type="no_such_agent") == expected


# ---------------- TC1④ 覆盖口隔离 ----------------


def test_tc1_override_not_polluted_by_env(monkeypatch: pytest.MonkeyPatch):
    """CANDIDATE_CAPABILITY_IDS 生效时 env 集不混入（测试钩子纯净 · 分支一行不动）。"""
    monkeypatch.setenv(_ENV, "extra.alpha,extra.beta")
    monkeypatch.setattr(strategy_config, "CANDIDATE_CAPABILITY_IDS", ["utc_now_iso"])
    assert strategy_config.get_candidate_capability_ids(mode="supervisor") == ["utc_now_iso"]
    assert strategy_config.get_candidate_capability_ids(agent_type="no_such_agent") == [
        "utc_now_iso",
    ]


# ---------------- 实操-B · 调用点读取 ----------------


def test_env_read_at_call_point_no_reload(monkeypatch: pytest.MonkeyPatch):
    """env 在调用点读取：monkeypatch 后**直接生效**，无需 reload / 重 import。"""
    assert strategy_config.get_candidate_capability_ids(agent_type="late.key") == []
    monkeypatch.setenv(_ENV, "late.bound")
    assert strategy_config.get_candidate_capability_ids(agent_type="late.key") == [
        "late.bound",
    ]
    monkeypatch.delenv(_ENV)
    assert strategy_config.get_candidate_capability_ids(agent_type="late.key") == []


# ---------------- TC2 · FP-5 三层：env 含高危/写 id 仍被裁 ----------------


@pytest.mark.asyncio
async def test_tc2_fp5_env_write_id_stripped_by_visible_intersection(
    monkeypatch: pytest.MonkeyPatch,
):
    """层 1（真实 builder 路径 · 不打 patch 候选函数）：env 注入写 id → ∩visible 裁掉。"""
    monkeypatch.setenv(_ENV, "testing.write.echo")
    recorded: list[dict] = []
    with (
        patch(
            "app.ops.strategy.builder._record_builder_span",
            side_effect=lambda m: recorded.append(m),
        ),
        patch("app.ops.strategy.builder.trace_span", return_value=_span_cm()),
    ):
        out = await strategy_builder_node({"messages": [HumanMessage(content="q")]})
    # env id 确实进了候选层（追加口生效）
    assert strategy_config.get_candidate_capability_ids(mode="supervisor") == (
        _SUPERVISOR_IDS + ["testing.write.echo"]
    )
    # 但下游 ∩visible 仍裁：不进 allowlist，进 stripped 台账
    assert "testing.write.echo" not in out["allowed_capability_ids"]
    assert recorded
    assert recorded[0]["strategy_builder_stripped_ids"] == ["testing.write.echo"]


def test_tc2_fp5_deny_order_still_cuts_write_and_high_risk():
    """层 2（deny 判序）：即便可见，deny_high_risk（在前）/ deny_write 仍裁。"""
    write_spec = _spec("testing.write.echo", side_effect="write")
    high_spec = _spec("x.local.high", risk_level="high")
    # Builder 基线 filter：写与高危皆不可见（env 抬候选层不影响本层判定）
    assert _match_filter(write_spec, BUILDER_CAP_FILTER) is False
    assert _match_filter(high_spec, BUILDER_CAP_FILTER) is False
    # allow_write_tags_any 只豁免 deny_write 一层；deny_high_risk 永不豁免
    flt = CapabilityFilter(
        kinds=frozenset({"local_fn"}),
        deny_high_risk=True,
        deny_write=True,
        allow_write_tags_any=frozenset({"testing"}),
    )
    assert _match_filter(write_spec, flt) is True  # deny_write 被 tags 豁免（既有语义）
    assert (
        _match_filter(_spec("x.local.high_write", risk_level="high", side_effect="write"), flt)
        is False
    )  # deny_high_risk 判序在前 · 不豁免


def test_tc2_fp5_policy_write_gate_still_blocks():
    """层 3（Policy 写闸）：invoke 前写能力无确认仍 policy_blocked。"""
    decision = check_invoke(_spec("testing.write.echo", side_effect="write"))
    assert decision.allowed is False
    assert decision.reason is not None and "write_not_confirmed" in decision.reason


# ---------------- TC3 · env 生效台账（设则记 · 未设不记） ----------------


def test_tc3_env_effective_audit_logged(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
):
    """设 env → 记候选 id 列表 + 基数（logger · 配置非敏感）。"""
    monkeypatch.setenv(_ENV, "extra.alpha,extra.beta")
    with caplog.at_level(logging.INFO, logger="app.ops.strategy.config"):
        strategy_config.get_candidate_capability_ids(agent_type="no_such_agent")
    records = [r for r in caplog.records if r.name == "app.ops.strategy.config"]
    assert len(records) == 1
    msg = records[0].getMessage()
    assert "count=2" in msg
    assert "extra.alpha" in msg and "extra.beta" in msg


def test_tc3_no_audit_log_when_env_unset(caplog: pytest.LogCaptureFixture):
    """未设 env → 不记（零 diff 口径含台账面）。"""
    with caplog.at_level(logging.INFO, logger="app.ops.strategy.config"):
        strategy_config.get_candidate_capability_ids(mode="supervisor")
        strategy_config.get_candidate_capability_ids(agent_type="no_such_agent")
    assert [r for r in caplog.records if r.name == "app.ops.strategy.config"] == []
