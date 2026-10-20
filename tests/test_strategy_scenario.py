"""scenario stage 摘除后回归（task_scenario-stage-rewire · 裁定 (a) 摘除 · 2026-10-20）。

覆盖（TC 映射）：
- scenario_trim 纯函数规则表 S1–S5 × risk_level 组合 + 畸形 intent 安全默认 +
  Q2（is_composite/summary 不作裁剪键）——dormant 模块本体保绿（TC4 前半）；
- Builder 直出 allowlist 逐值回归：无 intent × candidates 矩阵 →
  allowlist ≡ candidates ∩ 基线可见集（逐 id 对拍含顺序 · 与摘除前恒短路输出
  逐值等价 · TC2/FP-1）；
- env 失效断言：LG_RAG_VISIBILITY_SCENARIO_MODE ∈ {未设/off/observe/enforce/
  bogus} × intent {无/有含 high} → strategy_builder_node 输出逐值相等（TC3/FP-2）；
- delegation_scope ⊆ allowlist（requested_scope 越界剔除 · 承 B-1 交集语义）；
- 摘除面机断：builder.py 无 scenario 残留 · multi/nodes.py 无 scenario_trim
  注释残留（TC1）；
- dormant 存活：scenario.py 可 import + 文件头 dormant 注释含废弃 env 键名与
  日期（TC4 后半）；
- 图谱/env 台账同步字样断言（TC6）；
- diff 白名单（TC8 · _resolve_base 三级探测 · 蓝本
  tests/test_memory_injection_consumer.py:585-609）；
- 计时 smoke（注记级 · 不设硬 CI 阈值）。
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import time
import uuid
from pathlib import Path
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
from app.ops.strategy.builder import strategy_builder_node

MEDIUM_CAP = "test_scenario_medium_read"

_ROOT = Path(__file__).resolve().parents[1]


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
# 规则表 S1–S5（裁剪矩阵 · dormant 模块本体保绿）
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
# Builder 直出 allowlist 逐值回归（scenario 阶段已摘除 · 2026-10-20）
# allowlist 语义固定 = candidates ∩ 基线可见集直接求交
#（与摘除前恒短路输出逐值等价 · TC2/FP-1）
# ---------------------------------------------------------------------------

_BUILDER_CANDIDATES = [MEDIUM_CAP, "utc_now_iso"]


def _register_medium_probe() -> None:
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


async def _run_builder(state: dict, candidates: list[str]) -> dict:
    with (
        patch(
            "app.ops.strategy.builder.get_candidate_capability_ids",
            return_value=candidates,
        ),
        patch("app.ops.strategy.builder._record_builder_span"),
        patch("app.ops.strategy.builder.trace_span", return_value=_span_cm()),
    ):
        return await strategy_builder_node(state)


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["off", "observe", "enforce"])
async def test_builder_no_intent_allowlist_equals_baseline_intersection(
    monkeypatch, caplog, mode
):
    """承 TC6 短路断言改造：无 intent（supervisor-first 主路径形态）× env 任意档 →
    Builder 直出 allowlist ≡ candidates ∩ 基线可见集（逐 id 对拍含顺序）；
    零 scenario 台账。"""
    monkeypatch.setenv(sc.ENV_SCENARIO_MODE, mode)
    _register_medium_probe()
    state = {"messages": [HumanMessage(content="q")]}
    with caplog.at_level(logging.WARNING, logger="app.ops.strategy.scenario"):
        out = await _run_builder(state, list(_BUILDER_CANDIDATES))
    assert out["allowed_capability_ids"] == _BUILDER_CANDIDATES
    assert "visibility_scenario" not in caplog.text


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("candidates", "expected"),
    [
        ([MEDIUM_CAP, "utc_now_iso"], [MEDIUM_CAP, "utc_now_iso"]),
        (["utc_now_iso", MEDIUM_CAP], ["utc_now_iso", MEDIUM_CAP]),  # 顺序随 candidates
        (["bogus.cap", "utc_now_iso"], ["utc_now_iso"]),  # 未知 id 剔除
        ([], []),  # 空 candidates → 空（非全开）
    ],
)
async def test_builder_allowlist_value_regression_candidates_matrix(candidates, expected):
    """TC2/FP-1：无 intent × candidates 矩阵 → allowlist ≡ candidates ∩ 基线可见集
    （逐 id 对拍含顺序 · 与摘除前恒短路输出逐值等价）。"""
    _register_medium_probe()
    state = {"messages": [HumanMessage(content="q")]}
    out = await _run_builder(state, candidates)
    assert out["allowed_capability_ids"] == expected


@pytest.mark.asyncio
async def test_builder_no_intent_passes_baseline_through(caplog):
    """摘除后无 intent → allowlist ≡ 基线 ∩ candidates，medium 读探针不被裁
    （不存在 S4 缺省 high 收紧路径 · 收紧≠基线∩candidates 即红）。"""
    _register_medium_probe()
    state = {"messages": [HumanMessage(content="q")]}
    with caplog.at_level(logging.WARNING, logger="app.ops.strategy.scenario"):
        out = await _run_builder(state, list(_BUILDER_CANDIDATES))
    assert out["allowed_capability_ids"] == _BUILDER_CANDIDATES
    assert "visibility_scenario" not in caplog.text


@pytest.mark.asyncio
async def test_builder_high_intent_present_no_trim():
    """摘除后语义钉死：intent 在场（含 risk_hint=high）亦不裁——
    allowlist 仍 ≡ candidates ∩ 基线可见集（scenario 阶段已摘除 · 死行为不回魂）。"""
    _register_medium_probe()
    state = {
        "messages": [HumanMessage(content="q")],
        "intent": {"needs_tool": True, "domain": "ops_kb", "risk_hint": "high"},
        "intent_fallback": False,
    }
    out = await _run_builder(state, list(_BUILDER_CANDIDATES))
    assert out["allowed_capability_ids"] == _BUILDER_CANDIDATES


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", [None, "off", "observe", "enforce", "bogus"])
@pytest.mark.parametrize("with_intent", [False, True])
async def test_env_mode_has_no_effect_on_builder_output(monkeypatch, mode, with_intent):
    """TC3/FP-2 env 失效断言：LG_RAG_VISIBILITY_SCENARIO_MODE 任意值
    （含未设/非法）× intent {无/有含 high} → strategy_builder_node 输出逐值相等
    （摘除后生产路径不再消费该 env）。"""
    if mode is None:
        monkeypatch.delenv(sc.ENV_SCENARIO_MODE, raising=False)
    else:
        monkeypatch.setenv(sc.ENV_SCENARIO_MODE, mode)
    _register_medium_probe()
    state: dict = {"messages": [HumanMessage(content="q")]}
    if with_intent:
        state["intent"] = {"needs_tool": True, "domain": "ops_kb", "risk_hint": "high"}
        state["intent_fallback"] = False
    out = await _run_builder(state, list(_BUILDER_CANDIDATES))
    assert out["allowed_capability_ids"] == _BUILDER_CANDIDATES
    assert out["allowed_skill_ids"] == []


# ---------------------------------------------------------------------------
# delegation_scope ⊆ allowlist（承 B-1 交集语义 · 去 env 耦合）
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_supervisor_delegation_scope_never_exceeds_allowlist(monkeypatch):
    """B-1 钉死：delegation_scope = requested_scope ∩ Builder 直出 allowlist。

    Builder 直出 allowlist 不含 MEDIUM_CAP 形态下，模型声明 requested_scope
    含越界 id → 不进入 delegation_scope（委派令牌不越 allowlist）。
    """
    monkeypatch.setenv(dl.ENV_MODE, "observe")
    monkeypatch.setenv(dl.ENV_SECRET, "scenario-b1-secret")
    _register_medium_probe()
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
        # Builder 直出形态：MEDIUM_CAP 不在 allowlist
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


# ---------------------------------------------------------------------------
# 摘除面机断（TC1）· dormant 存活（TC4）· 图谱/env 台账同步（TC6）
# ---------------------------------------------------------------------------


def test_builder_has_no_scenario_residue():
    """TC1：builder.py 无 scenario 摘除面残留（import/调用/注释引用全清）；
    multi/nodes.py 无 scenario_trim 注释残留。
    TC3 grep 半：app/ 生产路径 env 键 LG_RAG_VISIBILITY_SCENARIO_MODE
    仅命中 dormant scenario.py（生产消费侧读取调用已删除）。"""
    builder_src = (_ROOT / "app/ops/strategy/builder.py").read_text(encoding="utf-8")
    for token in (
        "_apply_scenario_stage",
        "scenario_mode",
        "scenario_trim",
        "audit_scenario_stripped",
    ):
        assert token not in builder_src, f"builder.py 残留 {token}"
    nodes_src = (_ROOT / "app/ops/lg_rag/multi/nodes.py").read_text(encoding="utf-8")
    assert "scenario_trim" not in nodes_src, "multi/nodes.py 残留 scenario_trim 注释"
    env_key_hits = [
        p.relative_to(_ROOT).as_posix()
        for p in (_ROOT / "app").rglob("*.py")
        if "LG_RAG_VISIBILITY_SCENARIO_MODE" in p.read_text(encoding="utf-8")
    ]
    assert env_key_hits == ["app/ops/strategy/scenario.py"], (
        f"app/ env 键命中越 dormant 面: {env_key_hits}"
    )


def test_scenario_module_dormant_but_importable():
    """TC4：scenario.py 模块本体保留可 import；文件头 dormant 注释含
    废弃 env 键名与 2026-10-20 日期；三件符号仍在（本体不删）。"""
    assert callable(sc.scenario_trim)
    assert callable(sc.scenario_mode)
    assert callable(sc.audit_scenario_stripped)
    doc = sc.__doc__ or ""
    assert "dormant" in doc
    assert "LG_RAG_VISIBILITY_SCENARIO_MODE" in doc
    assert "2026-10-20" in doc


def test_graph_and_env_inventory_synced():
    """TC6：01_modules.md lg_rag 行备注含「scenario 裁剪已摘除」；
    GUIDE_env_inventory LG_RAG_VISIBILITY_SCENARIO_MODE 行含 deprecated 标注。"""
    modules = (_ROOT / "docs/_tech_graph/l1/01_modules.md").read_text(encoding="utf-8")
    assert "scenario 裁剪已摘除" in modules
    guide = (_ROOT / "docs/guides/GUIDE_env_inventory_v1.md").read_text(encoding="utf-8")
    env_line = next(
        line for line in guide.splitlines() if "LG_RAG_VISIBILITY_SCENARIO_MODE" in line
    )
    assert "已废弃" in env_line


# ---------------------------------------------------------------------------
# TC8 diff 白名单（#2 教训 · _resolve_base 式三级探测强制 ·
# 蓝本 tests/test_memory_injection_consumer.py:585-609 形态照抄）
# 改动面 ⊆ {builder.py, scenario.py(仅文件头注释), multi/nodes.py(仅注释行),
# 本测试文件, 01_modules.md, GUIDE_env_inventory_v1.md, invoke 目录, task 文件}；
# scripts/ alembic/ 及其余 app/ 显式禁现（含 untracked，防新文件绕过）
# ---------------------------------------------------------------------------

_BASE = "a1591e9"  # 钉锚：文档线尖端（master 51e75c9 + 文档线 · 30 分支自此切出）
_APP_ALLOWED = {
    "app/ops/strategy/builder.py",
    "app/ops/strategy/scenario.py",  # 仅文件头 dormant 注释
    "app/ops/lg_rag/multi/nodes.py",  # 仅注释行改写
}
_TREE_ALLOWED_FILES = {
    "tests/test_strategy_scenario.py",
    # 00 裁定（2026-10-20 · 跨波次基线修正）：#2 白名单闸追加第四态
    #（钉锚命中 ∧ 越出面全为后续波次产物 → 可审计 skip），触及本文件。
    "tests/test_memory_injection_consumer.py",
    "docs/_tech_graph/l1/01_modules.md",
    "docs/guides/GUIDE_env_inventory_v1.md",
    "docs/tasks/active/task_scenario_stage_rewire.md",
    # 00 裁定 O1（2026-10-20 · 同款前车预防）：CLOSE 时 task 文件自 active/
    # 移入 done/（00 落签面同类 · 同 #2 done/task_memory_injection_consumer.md 处置）。
    "docs/tasks/done/task_scenario_stage_rewire.md",
    # 40 落签面同类（00 裁定 A）：review40 审查文随本波次入库。
    "docs/harness/reviews/task_scenario_stage_rewire_review40_20261020.md",
}
_TREE_ALLOWED_PREFIXES = ("docs/harness/invokes/by-task/scenario-stage-rewire/",)
_BANNED_PREFIXES = ("scripts/", "alembic/")

# 00 裁定 O1（语义照抄 #2 四态）：波次窗 = a1591e9.._WAVE_TIP（#3 合并
# commit · 由 00 于 CLOSE 时钉死）。合并 commit 未定期间以「钉锚后仅本波次
# 文件」判定逻辑等价处理——本闸在波次内即钉死改动面 ⊆ 声明面（_allowed），
# 故越界路径只可能来自后续波次（foreign → 可审计 skip）；_WAVE_TIP 钉死后
# _touched_in_wave 恢复全量历史判定（波次窗内未登记面被触碰 → fail 保牙）。
_WAVE_TIP: str | None = "63bad3d"  # 00 钉锚 2026-10-20：#3 合并 commit（PR #286）· 态 2 牙全量生效


def _allowed(path: str) -> bool:
    return (
        path in _APP_ALLOWED
        or path in _TREE_ALLOWED_FILES
        or path.startswith(_TREE_ALLOWED_PREFIXES)
    )


def _banned(path: str) -> bool:
    # 00 裁定（2026-10-20 · 跨波次碰撞修正 · #4 delegation-naming-boundary）：
    # 前置硬 fail 仅限 _BANNED_PREFIXES；app/ 白名单越界一律走下波次分类
    # （foreign → 态③可审计 skip · 波内 → 态② fail 保牙）——O2 本意是禁区
    # （scripts//alembic/）不被 skip 掩盖，而非把后续波次登记面演进钉死。
    return path.startswith(_BANNED_PREFIXES)


def _git(root: Path, *args: str) -> list[str]:
    out = subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, check=True
    )
    return [line.strip() for line in out.stdout.splitlines() if line.strip()]


def _git_ok(root: Path, *args: str) -> tuple[bool, str]:
    proc = subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, check=False
    )
    return proc.returncode == 0, proc.stdout.strip()


def _touched_in_wave(root: Path, path: str) -> bool:
    """path 是否在 #3 波次窗内被触碰（越界分类：True=internal → fail 保牙）。

    _WAVE_TIP 未钉（None · 合并 commit 未知）：等价判定「钉锚后仅本波次
    文件」——声明面（_allowed）内且钉锚后有触碰史视为波次内；声明面外的
    越界路径视为后续波次产物（foreign → skip  eligible）。
    _WAVE_TIP 已钉：git log a1591e9.._WAVE_TIP -- <path> 非空即波次内
    （锚点不可解析/命令异常 → 保守 True 保牙 · 口径照抄 #2）。
    """
    if _WAVE_TIP is None:
        if not _allowed(path):
            return False
        ok, out = _git_ok(root, "log", "--format=%H", f"{_BASE}..HEAD", "--", path)
        return ok and bool(out)
    ok, _ = _git_ok(root, "rev-parse", "--verify", f"{_WAVE_TIP}^{{commit}}")
    if not ok:
        return True  # 钉锚不可解析 → 保守保牙
    ok, out = _git_ok(root, "log", "--format=%H", f"{_BASE}..{_WAVE_TIP}", "--", path)
    return (not ok) or bool(out)


def _resolve_base(root: Path) -> str:
    """基线锚点解析（CI 浅克隆健壮化 · 承 test_memory_injection_consumer.py:585-609）。

    探测序：
    1. 本地全量历史：钉死 {_BASE}（文档线尖端 · 30 分支切出点）；
    2. 浅克隆（fetch-depth=1 对象库无该提交）退化：merge-base HEAD
       origin/{GITHUB_BASE_REF}（未设则 origin/master）；
    3. 仍不可得：pytest.skip 并带实测 ref 状态——绝不静默 pass 也不 fail。
    """
    ok, _ = _git_ok(root, "rev-parse", "--verify", f"{_BASE}^{{commit}}")
    if ok:
        return _BASE
    tried = [f"{_BASE}^{{commit}} 不在对象库（浅克隆?）"]
    base_ref = os.environ.get("GITHUB_BASE_REF", "").strip() or "master"
    for ref in dict.fromkeys((f"origin/{base_ref}", "origin/master")):
        ok, _ = _git_ok(root, "rev-parse", "--verify", f"{ref}^{{commit}}")
        if not ok:
            tried.append(f"{ref} 不可用")
            continue
        ok, mb = _git_ok(root, "merge-base", "HEAD", ref)
        if ok and mb:
            print(f"[TC8] 基线退化：{_BASE} 不可用，取 merge-base HEAD {ref} = {mb[:12]}")
            return mb
        tried.append(f"{ref} 在册但 merge-base HEAD 不可得（浅克隆无共祖）")
    pytest.skip("TC8 基线锚点不可解析（" + "；".join(tried) + "）")


def test_diff_whitelist_scenario_stage_rewire() -> None:
    root = _ROOT
    base = _resolve_base(root)
    changed: set[str] = set()
    for args in (
        ("diff", "--name-only", base),  # 工作区 vs base（未暂存）
        ("diff", "--name-only", "--cached", base),  # 暂存区 vs base
        ("diff", "--name-only", base, "HEAD"),  # 已提交 delta
    ):
        changed.update(_git(root, *args))
    untracked = set(_git(root, "ls-files", "--others", "--exclude-standard"))

    # 00 裁定 O2（2026-10-20）：禁区断言先于第四态 skip 判定——
    # 越界全 foreign 但含 scripts//alembic/ 时必须 fail 而非 skip。
    # 00 裁定（2026-10-20 · 跨波次碰撞修正 · #4）：硬 fail 面收窄至
    # _BANNED_PREFIXES；app/ 越界改由下方 violations 走波次分类。
    banned = sorted(p for p in changed | untracked if _banned(p))
    assert not banned, f"禁改面（scripts/ alembic/）出现改动: {banned}"

    violations = sorted(p for p in changed if not _allowed(p))
    if violations:
        # 00 裁定 O1 第四态（语义照抄 #2）：钉锚命中 ∧ 越出面全为后续波次
        # 产物 → 可审计 skip；含本波次窗内文件 → 仍 fail（回归牙保留）。
        internal = sorted(p for p in violations if _touched_in_wave(root, p))
        assert not internal, f"diff 越白名单且属 #3 波次窗内文件（回归牙）: {internal}"
        pytest.skip(
            "TC8 白名单闸使命于 #3 scenario-stage-rewire 合并时点完成："
            "基线后已有后续任务合入 · 实测越界文件清单（均后续波次产物）: "
            f"{violations}"
        )
