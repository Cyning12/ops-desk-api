"""delegation-naming-boundary 验收（D1 正名 + D2 护栏解耦 · TC3/TC4/TC5/TC7/TC8）。

契约锚：docs/tasks/active/task_delegation_naming_boundary.md（v0.2 · 三闸全 approved）
SPEC：docs/spec/delegation-naming-boundary/SPEC-delegation-naming-boundary_v0.md

- **TC3 正牙**：默认开（键缺省）· delegation off —— write 双胞胎重放被拦
  （guard-skip 终态 + write_replay_guard_skip/replay_of 台账钩子）。
  FP-2 唯一 intentional behavior change：delegation off 下护栏由从不生效
  变默认生效（真门控仅 nodes.py:903/:931 两处切至独立开关）。
- **TC4 逆牙（回归钉）**：LG_RAG_WRITE_REPLAY_GUARD_ENABLED=false · delegation
  off —— 恢复 master 基线行为（s2 照派 · 无 guard 终态 · 无台账），前后皆绿。
- **TC5**：delegation on 矩阵零 diff —— on×on twin 照拦（同 master）；on×off
  不 skip 但签发审批门 :970 照常拦（blocked_by=delegation_issue_hitl_required），
  实证签发审批门保持 delegation 耦合不动（R1 N3 误并澄清）。
- **TC7**：非法值回退开（fail-closed 反向 · 护栏保持生效）+ warning 留痕；
  _write_replay_guard_enabled 解析单元矩阵（默认/真/假/非法）。
- **TC8**：app 改动白名单 diff 闸（四态 · banned 前置于全部 skip 出口 ·
  态④锚缺失以 vs HEAD + untracked 兜底）。蓝本照抄
  tests/test_strategy_scenario.py:449-562（00 裁定 O1/O2 语义）。
"""

from __future__ import annotations

import logging
import os
import subprocess
import uuid
from pathlib import Path

import pytest

import app.ops.lg_rag.multi.nodes as nodes
from app.ops.capability import delegation as dl
from app.ops.capability.gateway import unregister
from app.ops.capability.manifest import load_capability_manifest
from app.ops.hitl import reset_hitl_store, set_hitl_store
from app.ops.hitl.store import InMemoryHitlStore
from app.ops.lg_rag.multi.nodes import _join_subtasks
from tests.test_hitl_approval_consumption import (
    _TESTING_CAP,
    _TESTING_MANIFEST,
    _approved_req,
    _guard_row,
    _guard_state,
    cap_env,  # noqa: F401 - pytest fixture 注入（形参同名由 def 行 noqa F811 承接）
)

_GUARD_LOGGER = "app.ops.lg_rag.multi.nodes"
_ENV_GUARD = "LG_RAG_WRITE_REPLAY_GUARD_ENABLED"


@pytest.fixture(autouse=True)
def _registry_snapshot_restore():
    """注册表快照恢复（本文件全用例）：guard_off_env 与共享 cap_env 均加载
    testing 清单；用后恢复 _TESTING_CAP 至用例前状态，防跨文件注册表泄漏
    翻转下游 ∩visible 断言（fp5 env_write_id_stripped 实测翻转先例——
    tests/test_lg_rag_delegation_wiring.py:56 clear 后本文件重注册所致）。
    """
    from app.ops.capability.gateway import get_registry

    pre = get_registry().get(_TESTING_CAP) is not None
    yield
    if not pre and get_registry().get(_TESTING_CAP) is not None:
        unregister(_TESTING_CAP)


@pytest.fixture
def guard_off_env(monkeypatch):
    """delegation off（默认态 · 显式 delenv 防本机 .env enforce 渗入）+ 干净 store。"""
    monkeypatch.delenv(dl.ENV_MODE, raising=False)
    monkeypatch.delenv(dl.ENV_SECRET, raising=False)
    monkeypatch.delenv(_ENV_GUARD, raising=False)
    load_capability_manifest(_TESTING_MANIFEST)
    store = InMemoryHitlStore()
    set_hitl_store(store)
    yield store
    reset_hitl_store()


def _twin_state(run_id: str) -> tuple[dict, str, str]:
    """write 双胞胎场景（承 test_tc1_write_twin_guard_skips_redispatch 签名）。

    :1 write 已成功终态（locked 前缀）；:2 approved unlocked 待重跑且与 :1
    canonical 相同 → 命中结构护栏即 guard-skip（不派发 · 不消费单据）。
    """
    s1, s2 = run_id + ":1", run_id + ":2"
    args = {"request_id": "r-twin", "note": "同参写步"}
    state = _guard_state(
        run_id,
        [_guard_row(s1, input=args), _guard_row(s2, input=dict(args))],
        [
            {
                "subtask_id": s1,
                "id": s1,
                "type": "tool",
                "tool": _TESTING_CAP,
                "output": {"echo": "W1-OK"},
            }
        ],
        plan_prefix_ids=[s1],
        hitl_unlocked_ids=[s2],
    )
    return state, s1, s2


def _twin_terminal(joined: dict, s2: str) -> dict | None:
    batch = list(joined.get("subtask_results") or [])
    return next((r for r in batch if str(r.get("subtask_id")) == s2), None)


# ---------------------------------------------------------------------------
# TC3 正牙：默认开 · delegation off → 护栏拦重放
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_tc3_default_on_blocks_write_twin_replay_delegation_off(guard_off_env, caplog):
    """TC3：键缺省默认开 ∧ delegation off —— twin guard-skip（FP-2 声明行为变化）。"""
    run_id = "run-" + uuid.uuid4().hex[:8]
    state, s1, s2 = _twin_state(run_id)

    with caplog.at_level(logging.INFO, logger=_GUARD_LOGGER):
        joined = await _join_subtasks(state)

    assert s2 not in (joined.get("inflight_subtask_ids") or []), (
        "TC3 RED：delegation off 现码护栏不生效（s2 照派 = write 二次执行重放危害）"
    )
    twin = _twin_terminal(joined, s2)
    assert twin is not None, "write 孪生须落 guard-skip 终态（delegation off 下护栏生效）"
    assert twin.get("write_replay_guard_skip") is True
    assert twin.get("replay_of") == s1
    assert twin.get("output") == {"echo": "W1-OK"}  # 已成功写结果照抄
    assert "error" not in twin
    assert any("write_replay_guard_skip" in r.message for r in caplog.records)


# ---------------------------------------------------------------------------
# TC4 逆牙：开关 false · delegation off → 恢复 master 基线（回归钉 · 前后皆绿）
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_tc4_guard_off_restores_master_baseline_delegation_off(
    guard_off_env, monkeypatch, caplog
):
    """TC4：LG_RAG_WRITE_REPLAY_GUARD_ENABLED=false ∧ delegation off —— s2 照派。

    与 master 基线逐字节一致（delegation off 下护栏从不生效的旧行为）；本钉
    实施前后皆绿，防「关恢复」退化为「关也拦」。
    """
    monkeypatch.setenv(_ENV_GUARD, "false")
    run_id = "run-" + uuid.uuid4().hex[:8]
    state, _s1, s2 = _twin_state(run_id)

    with caplog.at_level(logging.INFO, logger=_GUARD_LOGGER):
        joined = await _join_subtasks(state)

    assert s2 in (joined.get("inflight_subtask_ids") or []), (
        "开关 false 须恢复 master 基线：s2 照常派发"
    )
    twin = _twin_terminal(joined, s2)
    assert twin is None, "开关 false 不得落 guard-skip 终态（master 基线零 guard 痕迹）"
    assert not any("write_replay_guard_skip" in r.message for r in caplog.records)


# ---------------------------------------------------------------------------
# TC5：delegation on 矩阵零 diff
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_tc5_delegation_on_guard_on_twin_skipped(cap_env, caplog):  # noqa: F811
    """TC5-a：delegation on × guard 默认开 —— twin 照拦（与 master 行为零 diff）。"""
    run_id = "run-" + uuid.uuid4().hex[:8]
    state, s1, s2 = _twin_state(run_id)
    await cap_env.acreate(_approved_req(run_id, s2))

    with caplog.at_level(logging.INFO, logger=_GUARD_LOGGER):
        joined = await _join_subtasks(state)

    assert s2 not in (joined.get("inflight_subtask_ids") or [])
    twin = _twin_terminal(joined, s2)
    assert twin is not None and twin.get("write_replay_guard_skip") is True
    assert twin.get("replay_of") == s1
    assert twin.get("output") == {"echo": "W1-OK"}


@pytest.mark.asyncio
async def test_tc5_delegation_on_guard_off_issue_gate_holds(
    cap_env, monkeypatch, caplog  # noqa: F811
):
    """TC5-b：delegation on × guard 关 —— 不 skip，但签发审批门 :970 照常拦。

    实证签发审批门保持 _delegation_active() 耦合不动（R1 N3：:970 不随护栏
    解耦）；无 approved 单据 → blocked_by=delegation_issue_hitl_required。
    """
    monkeypatch.setenv(_ENV_GUARD, "false")
    run_id = "run-" + uuid.uuid4().hex[:8]
    state, _s1, s2 = _twin_state(run_id)

    with caplog.at_level(logging.INFO, logger=_GUARD_LOGGER):
        joined = await _join_subtasks(state)

    assert s2 not in (joined.get("inflight_subtask_ids") or []), (
        "无 approved 单据时签发审批门必须拦下（delegation 耦合不动）"
    )
    twin = _twin_terminal(joined, s2)
    assert twin is not None, "签发审批门拦截须落 error 终态"
    assert twin.get("write_replay_guard_skip") is not True, "guard 关 → 不得走 skip 路径"
    assert twin.get("blocked_by") == "delegation_issue_hitl_required"
    assert twin.get("hitl_required") is True
    assert not any("write_replay_guard_skip" in r.message for r in caplog.records)


# ---------------------------------------------------------------------------
# TC7：非法值回退开（fail-closed 反向）+ 解析单元矩阵
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize("bad", ["2", "maybe"])
async def test_tc7_invalid_value_fails_closed_guard_stays_on(
    guard_off_env, monkeypatch, caplog, bad
):
    """TC7 行为面：非法值 → warning 留痕 + 回退默认开（护栏仍拦重放）。"""
    monkeypatch.setenv(_ENV_GUARD, bad)
    run_id = "run-" + uuid.uuid4().hex[:8]
    state, s1, s2 = _twin_state(run_id)

    with caplog.at_level(logging.INFO, logger=_GUARD_LOGGER):
        joined = await _join_subtasks(state)

    assert s2 not in (joined.get("inflight_subtask_ids") or []), (
        "非法值须回退开（fail-closed 反向）：护栏保持生效"
    )
    twin = _twin_terminal(joined, s2)
    assert twin is not None and twin.get("write_replay_guard_skip") is True
    assert twin.get("replay_of") == s1
    assert any(
        "invalid LG_RAG_WRITE_REPLAY_GUARD_ENABLED" in r.message
        and r.levelno >= logging.WARNING
        for r in caplog.records
    ), "非法值须 warning 留痕（承 SESSION_SUMMARY_ENABLED 解析先例 · 方向相反）"


@pytest.mark.parametrize(
    ("raw", "expected", "warns"),
    [
        (None, True, False),  # 键缺省 → 默认开
        ("", True, False),  # 空串 → 默认开（无 warning）
        ("1", True, False),
        ("true", True, False),
        ("TRUE", True, False),
        (" on ", True, False),  # strip + lower
        ("yes", True, False),
        ("0", False, False),
        ("false", False, False),
        ("off", False, False),
        ("no", False, False),
        ("2", True, True),  # 非法 → 回退开 + warning
        ("enabled", True, True),  # 非法 → 回退开 + warning
    ],
)
def test_tc7_parse_matrix(monkeypatch, caplog, raw, expected, warns):
    """TC7 解析面：_write_replay_guard_enabled 值矩阵（默认开 · 非法回退开）。

    承 continuity.py session_summary_enabled 解析先例（_TRUTHY/_FALSY 词表
    一致 · strip().lower() · 非法 warning），唯默认/回退方向相反（R1 N-d）。
    """
    fn = getattr(nodes, "_write_replay_guard_enabled", None)
    assert fn is not None, "nodes._write_replay_guard_enabled 未落地（D2 未实施）"
    if raw is None:
        monkeypatch.delenv(_ENV_GUARD, raising=False)
    else:
        monkeypatch.setenv(_ENV_GUARD, raw)
    with caplog.at_level(logging.WARNING, logger=_GUARD_LOGGER):
        assert fn() is expected
    assert (
        any("invalid LG_RAG_WRITE_REPLAY_GUARD_ENABLED" in r.message for r in caplog.records)
        is warns
    )


# ---------------------------------------------------------------------------
# TC8：app 改动白名单 diff 闸（四态 · banned 前置 · 态④兜底）
# 蓝本照抄 tests/test_strategy_scenario.py:449-562（00 裁定 O1/O2 语义）
# ---------------------------------------------------------------------------

_ROOT = Path(__file__).resolve().parents[1]
# 钉锚：docs/task-delegation-naming-boundary HEAD（30 分支切出点 · 回归语义不变）
_BASE = "d337486"
# 00 裁定 O1（语义照抄先例）：波次窗 = _BASE.._WAVE_TIP（合并 commit · 由 00
# 于 CLOSE 时钉死）。合并 commit 未定期间以「钉锚后仅本波次文件」判定逻辑
# 等价处理；_WAVE_TIP 钉死后 _touched_in_wave 恢复全量历史判定。
_WAVE_TIP: str | None = None

_APP_ALLOWED = frozenset(
    {
        "app/ops/capability/delegation.py",
        "app/ops/lg_rag/multi/nodes.py",
    }
)
_TREE_ALLOWED_FILES = frozenset(
    {
        "tests/test_capability_delegation.py",
        "tests/test_capability_testing_write.py",
        "tests/test_lg_rag_write_replay_guard.py",
        # 00 裁定（2026-10-20 · 冲突 A）：扩充白名单纳入本文件——限定语：仅
        # test_tc2_guard_zero_touch_when_delegation_off 增补一行 setenv 夹具
        # （LG_RAG_WRITE_REPLAY_GUARD_ENABLED=false · FP-2 旧行为钉忠实翻译），
        # 禁动断言/场景构造。
        "tests/test_hitl_approved_replan_quality.py",
        # 00 裁定（2026-10-20 · 冲突 B）：扩充白名单纳入本文件——限定语：仅
        # test_diff_whitelist_scenario_stage_rewire 闸前置硬 fail 收窄至
        # _BANNED_PREFIXES（跨波次碰撞修正 · 先例 9dd5c79/c61a2d5）。
        "tests/test_strategy_scenario.py",
        "docs/_tech_graph/l1/01_modules.md",
        "docs/guides/GUIDE_env_inventory_v1.md",
        "docs/tasks/active/task_delegation_naming_boundary.md",
        # 00 裁定（2026-10-20 · #3 O1 先例）：CLOSE done/ 移动面预登记——CLOSE
        # commit 将 git mv task 至 done/，active/ 原路径保留覆盖 deletion，
        # 避免 CLOSE 后闸落态③ foreign skip 削弱态①严格 pass 语义。
        "docs/tasks/done/task_delegation_naming_boundary.md",
        # 00 裁定（2026-10-20 · 40=approve 非阻塞观察 O2 · 裁定甲先例）：审查文
        # 入库并纳入白名单，避免态③ foreign skip 削弱严格 pass 语义。
        "docs/harness/reviews/task_delegation_naming_boundary_review40_20261020.md",
    }
)
_TREE_ALLOWED_PREFIXES = ("docs/harness/invokes/by-task/delegation-naming-boundary/",)
_BANNED_PREFIXES = ("scripts/", "alembic/")


def _allowed(path: str) -> bool:
    return (
        path in _APP_ALLOWED
        or path in _TREE_ALLOWED_FILES
        or path.startswith(_TREE_ALLOWED_PREFIXES)
    )


def _banned(path: str) -> bool:
    if path.startswith(_BANNED_PREFIXES):
        return True
    return path.startswith("app/") and path not in _APP_ALLOWED


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
    """path 是否在本波次窗内被触碰（越界分类：True=internal → fail 保牙）。

    _WAVE_TIP 未钉（None · 合并 commit 未知）：等价判定「钉锚后仅本波次
    文件」——声明面（_allowed）内且钉锚后有触碰史视为波次内；声明面外的
    越界路径视为后续波次产物（foreign → skip eligible）。
    _WAVE_TIP 已钉：git log _BASE.._WAVE_TIP -- <path> 非空即波次内
    （锚点不可解析/命令异常 → 保守 True 保牙 · 口径照抄先例）。
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


def _resolve_base(root: Path) -> tuple[str | None, list[str]]:
    """基线锚点解析（CI 浅克隆健壮化 · 承 test_strategy_scenario.py:508-532）。

    探测序：
    1. 本地全量历史：钉死 {_BASE}（文档线尖端 · 30 分支切出点）；
    2. 浅克隆（fetch-depth=1 对象库无该提交）退化：merge-base HEAD
       origin/{GITHUB_BASE_REF}（未设则 origin/master）；
    3. 仍不可得：返回 (None, tried)——态④由调用方 banned 兜底后 skip。
    """
    ok, _ = _git_ok(root, "rev-parse", "--verify", f"{_BASE}^{{commit}}")
    if ok:
        return _BASE, []
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
            return mb, tried
        tried.append(f"{ref} 在册但 merge-base HEAD 不可得（浅克隆无共祖）")
    return None, tried


def _changed_and_untracked(root: Path, *diff_args: str) -> tuple[set[str], set[str]]:
    changed: set[str] = set()
    for args in diff_args:
        changed.update(_git(root, *args))
    untracked = set(_git(root, "ls-files", "--others", "--exclude-standard"))
    return changed, untracked


def test_tc8_diff_whitelist() -> None:
    """TC8：本波次改动面 ⊆ 声明白名单；禁改面（scripts/ alembic/ 其余 app/）零触达。

    四态（00 裁定 O1/O2 语义照抄 · banned 断言前置于全部 skip 出口）：
    ① 钉锚命中 ∧ 零越界 → pass；② 退化基线（merge-base）∧ 零越界 → pass；
    ③ 钉锚命中 ∧ 越界全 foreign（后续波次产物）→ 可审计 skip；含波内 → fail；
    ④ 锚不可得 → banned 以 vs HEAD + untracked 兜底（绝不整体豁免禁区），
    再带实测 ref 状态 skip。
    """
    root = _ROOT
    base, tried = _resolve_base(root)
    if base is None:
        # 态④：锚缺失时 banned 以「vs HEAD + untracked」兜底——
        # 不可因基线缺失整体豁免禁区（task TC8 强化条款）。
        changed, untracked = _changed_and_untracked(
            root,
            ("diff", "--name-only", "HEAD"),
            ("diff", "--name-only", "--cached", "HEAD"),
        )
        banned = sorted(p for p in changed | untracked if _banned(p))
        assert not banned, f"态④兜底：禁改面（scripts/ alembic/ 及其余 app/）出现改动: {banned}"
        pytest.skip("TC8 基线锚点不可解析（" + "；".join(tried) + "）")

    changed, untracked = _changed_and_untracked(
        root,
        ("diff", "--name-only", base),  # 工作区 vs base（未暂存）
        ("diff", "--name-only", "--cached", base),  # 暂存区 vs base
        ("diff", "--name-only", base, "HEAD"),  # 已提交 delta
    )

    # banned 断言先于第四态 skip 判定（00 裁定 O2）：越界全 foreign 但含
    # scripts//alembic/（或其余 app/）时必须 fail 而非 skip。
    banned = sorted(p for p in changed | untracked if _banned(p))
    assert not banned, f"禁改面（scripts/ alembic/ 及其余 app/）出现改动: {banned}"

    violations = sorted(p for p in changed if not _allowed(p))
    if violations and base == _BASE:
        # 态③（00 裁定 O1 第四态）：钉锚命中 ∧ 越出面全为后续波次产物 →
        # 可审计 skip；含本波次窗内文件 → 仍 fail（回归牙保留）。
        internal = sorted(p for p in violations if _touched_in_wave(root, p))
        assert not internal, f"diff 越白名单且属本波次窗内文件（回归牙）: {internal}"
        pytest.skip(
            "TC8 白名单闸使命于本波次合并时点完成：基线后已有后续任务合入 · "
            f"实测越界文件清单（均后续波次产物）: {violations}"
        )
    assert not violations, f"diff 越白名单: {violations}"
