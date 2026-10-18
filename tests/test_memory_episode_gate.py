"""host-v1-episodic-memory-feedback · D2 情景记忆独立闸纯函数（无 DB）+ 零互写 import 守护。

覆盖（逐块映射 task 验收 D2）：
- 闸五判据逐条：缺归因 / 非法 outcome / 非法·超长序列 / 超长摘要 /
  failure 缺 class · class 词表非法（含 success 带非法 class 同拒）全拒不落库
- 词表钉死：outcome 三值 · failure_class 六值 · 拒绝原因码稳定可枚举
- 零互写 import 守护：episode_gate / episode_service **不 import** 事实记忆
  写面（memory/gate.py · memory/service.py），源码零引用 OpsMemoryFact
- 指纹确定性：同输入同 hash · 三元（domain+意图特征+工具序列骨架）任一变则异
- 变异检验②锚点：本文件的「闸拒」断言 + test_memory_episode_recall.py 的
  「闸拒不落库（查表为零）」断言，在闸恒放行时必挂（破坏→必挂→恢复留痕
  见提交说明）。
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from app.ops.memory.episode_gate import (
    ALLOWED_FAILURE_CLASSES,
    ALLOWED_OUTCOMES,
    REJECT_REASONS,
    Decision,
    EpisodeCandidate,
    compute_context_fingerprint,
    should_write_episode,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]


def _candidate(**over) -> EpisodeCandidate:
    base = {
        "tenant_id": "ops-desk-pilot",
        "run_id": "run-123",
        "task_domain": "ops_kb",
        "context_fingerprint": "f" * 64,
        "plan_summary": "先查日志再重启服务",
        "tool_sequence": ["logs.read", "svc.restart"],
        "outcome": "success",
    }
    base.update(over)
    return EpisodeCandidate(**base)


# ---------------- 放行面 ----------------


def test_valid_episode_allowed():
    d = should_write_episode(_candidate())
    assert d == Decision(allowed=True, reason_code="")


@pytest.mark.parametrize("outcome", ["success", "failure", "partial"])
def test_all_outcomes_allowed_when_valid(outcome):
    over = {"outcome": outcome}
    if outcome == "failure":
        over["failure_class"] = "capability_blocked"
    assert should_write_episode(_candidate(**over)).allowed is True


@pytest.mark.parametrize("cls", sorted(ALLOWED_FAILURE_CLASSES))
def test_failure_with_each_vocab_class_allowed(cls):
    d = should_write_episode(_candidate(outcome="failure", failure_class=cls))
    assert d.allowed is True


# ---------------- 判据① run 归因齐全 ----------------


@pytest.mark.parametrize(
    "tenant_id,run_id",
    [("", "run-1"), ("t", ""), ("  ", "run-1"), ("t", "  "), ("", "")],
)
def test_missing_attribution(tenant_id, run_id):
    d = should_write_episode(_candidate(tenant_id=tenant_id, run_id=run_id))
    assert d.allowed is False
    assert d.reason_code == "missing_attribution"


# ---------------- 判据② outcome 词表合法 ----------------


@pytest.mark.parametrize("outcome", ["ok", "SUCCESS", "failed", "", "done"])
def test_invalid_outcome(outcome):
    d = should_write_episode(_candidate(outcome=outcome))
    assert d.allowed is False
    assert d.reason_code == "invalid_outcome"


# ---------------- 判据③ 工具序列（str 列表 · ≤16） ----------------


def test_tool_sequence_exactly_16_allowed():
    d = should_write_episode(_candidate(tool_sequence=[f"t{i}" for i in range(16)]))
    assert d.allowed is True


def test_tool_sequence_too_long():
    d = should_write_episode(_candidate(tool_sequence=[f"t{i}" for i in range(17)]))
    assert d.allowed is False
    assert d.reason_code == "tool_sequence_too_long"


@pytest.mark.parametrize("seq", ["not-a-list", ["a", 1, "b"], [None]])
def test_tool_sequence_invalid_type(seq):
    d = should_write_episode(_candidate(tool_sequence=seq))
    assert d.allowed is False
    assert d.reason_code == "tool_sequence_invalid"


# ---------------- 判据④ plan 摘要 ≤200（超长拒，非落库后截断） ----------------


def test_plan_summary_exactly_200_allowed():
    d = should_write_episode(_candidate(plan_summary="摘" * 200))
    assert d.allowed is True


def test_plan_summary_too_long():
    d = should_write_episode(_candidate(plan_summary="摘" * 201))
    assert d.allowed is False
    assert d.reason_code == "plan_summary_too_long"


# ---------------- 判据⑤ failure 必填合法（非法值同拒） ----------------


@pytest.mark.parametrize("cls", [None, "", "   "])
def test_failure_missing_class(cls):
    d = should_write_episode(_candidate(outcome="failure", failure_class=cls))
    assert d.allowed is False
    assert d.reason_code == "failure_class_missing"


@pytest.mark.parametrize("cls", ["llm_error", "CAPABILITY_BLOCKED", "unknown", "timeout"])
def test_failure_invalid_class_vocab(cls):
    d = should_write_episode(_candidate(outcome="failure", failure_class=cls))
    assert d.allowed is False
    assert d.reason_code == "failure_class_invalid"


def test_success_with_invalid_class_also_rejected():
    """非法 failure_class 值同拒（不只 failure 才校验词表）。"""
    d = should_write_episode(_candidate(outcome="success", failure_class="llm_error"))
    assert d.allowed is False
    assert d.reason_code == "failure_class_invalid"


def test_success_with_valid_class_allowed():
    """success/partial 带合法 class 放行（词表内 nullable 语义）。"""
    d = should_write_episode(_candidate(outcome="partial", failure_class="other"))
    assert d.allowed is True


# ---------------- 词表钉死 ----------------


def test_vocabularies_pinned():
    assert sorted(ALLOWED_OUTCOMES) == ["failure", "partial", "success"]
    assert sorted(ALLOWED_FAILURE_CLASSES) == [
        "budget_exhausted",
        "capability_blocked",
        "contract_violation",
        "other",
        "so_failure",
        "upstream_error",
    ]
    assert sorted(REJECT_REASONS) == [
        "failure_class_invalid",
        "failure_class_missing",
        "invalid_outcome",
        "missing_attribution",
        "plan_summary_too_long",
        "tool_sequence_invalid",
        "tool_sequence_too_long",
    ]


# ---------------- 零互写 import 守护（U4） ----------------

_FACT_WRITE_SURFACE = (
    "app.ops.memory.gate",
    "app.ops.memory.service",
    "app.ops.memory.extract",
)


def _imports_of(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


@pytest.mark.parametrize(
    "module_path",
    [
        _REPO_ROOT / "app/ops/memory/episode_gate.py",
        _REPO_ROOT / "app/ops/memory/episode_service.py",
    ],
)
def test_no_fact_write_surface_import(module_path):
    """episode 闸/service 源码零 import 事实记忆写面（物理分立 · 变异检验①兜底）。"""
    imports = _imports_of(module_path)
    for surface in _FACT_WRITE_SURFACE:
        assert surface not in imports, f"{module_path.name} 不得 import {surface}"
    source = module_path.read_text(encoding="utf-8")
    assert "OpsMemoryFact" not in source  # 零引用事实表模型
    assert "ops_memory_facts" not in source  # 零引用事实表名


# ---------------- 指纹确定性 ----------------


def test_fingerprint_deterministic_same_input_same_hash():
    a = compute_context_fingerprint("ops_kb", {"needs_tool": True}, ["logs.read"])
    b = compute_context_fingerprint("ops_kb", {"needs_tool": True}, ["logs.read"])
    assert a == b
    assert len(a) == 64 and all(c in "0123456789abcdef" for c in a)


def test_fingerprint_triple_any_change_differs():
    base = compute_context_fingerprint("ops_kb", {"needs_tool": True}, ["logs.read"])
    assert compute_context_fingerprint("general", {"needs_tool": True}, ["logs.read"]) != base
    assert compute_context_fingerprint("ops_kb", {"needs_tool": False}, ["logs.read"]) != base
    assert compute_context_fingerprint("ops_kb", {"needs_tool": True}, ["svc.restart"]) != base
    # 工具序列骨架保序：顺序不同 = 不同指纹
    assert compute_context_fingerprint("ops_kb", {}, ["a", "b"]) != compute_context_fingerprint(
        "ops_kb", {}, ["b", "a"]
    )


def test_fingerprint_normalization():
    # domain 大小写/空白归一
    assert compute_context_fingerprint(" OPS_KB ", {}, []) == compute_context_fingerprint(
        "ops_kb", {}, []
    )
    # 非标量意图特征被忽略（弱指纹方向 = 宁可不召回）
    assert compute_context_fingerprint(
        "ops_kb", {"nested": {"x": 1}}, []
    ) == compute_context_fingerprint("ops_kb", {}, [])
    # 工具骨架截到 16（与闸上限同源）：前 16 相同 → 同指纹
    assert compute_context_fingerprint(
        "d", {}, [f"t{i}" for i in range(20)]
    ) == compute_context_fingerprint("d", {}, [f"t{i}" for i in range(16)])
