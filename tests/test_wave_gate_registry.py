"""波次审计闸自注册（N3 · 2026-11-07 立 · task env-red-n3-governance）。

真值面 = docs/harness/audit_gates/registry.yaml（数据即闸）。

未来波次要在守卫面（scripts/ alembic/ 其余 app/）工作：只在 registry 登记
entry（status=active · base/wave_tip/allowed 三集合 · 限定语 note），本闸自动生效；
不写新测试代码（承 2026-10-20 三闸先例的逐波复制痛点 · N3 口径=「未来波次
committed 面审计须自注册新闸」· 20-R1 非阻塞登记）。

语义对齐 tests/test_lg_rag_write_replay_guard.py::test_tc8_diff_whitelist（00 签认形态②）：
- committed 面 = base..wave_tip 闭窗（不随 master 合入增长）；
- 在途面 = 工作区/暂存 vs HEAD + untracked（closed entry 同样咬 · O2 语义）；
- banned 前置于全部 skip 出口；
- N2 规格：wave_tip 未钉/不可解析 → 带审计输出跳过 committed 面，绝不退化为
  vs HEAD 增长窗（浅克隆环境锚点漂移的结构性常态红即此成因）；
- fail-closed 立档见 docs/harness/audit_gates/adr-001（脏树+tip 不可解析保守保牙）。
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import yaml

_ROOT = Path(__file__).resolve().parents[1]
_REGISTRY = _ROOT / "docs" / "harness" / "audit_gates" / "registry.yaml"


def _load_registry() -> list[dict[str, Any]]:
    assert _REGISTRY.is_file(), f"审计闸自注册簿缺失: {_REGISTRY}（N3 程序见同目录 README）"
    data = yaml.safe_load(_REGISTRY.read_text(encoding="utf-8")) or {}
    waves = data.get("waves") or []
    assert waves, "registry.yaml waves 为空——守卫面波次须先登记（自注册程序见 README）"
    return waves


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


def _in_flight(root: Path) -> set[str]:
    """在途面 = 工作区/暂存 vs HEAD + untracked（TC8 _changed_faces 未提交面口径）。"""
    changed: set[str] = set()
    changed.update(_git(root, "diff", "--name-only", "HEAD"))
    changed.update(_git(root, "diff", "--name-only", "--cached", "HEAD"))
    changed.update(_git(root, "ls-files", "--others", "--exclude-standard"))
    return changed


def _is_banned(entry: dict[str, Any], path: str) -> bool:
    banned_prefixes = tuple(entry.get("banned_prefixes") or ("scripts/", "alembic/"))
    if path.startswith(banned_prefixes):
        return True
    if not path.startswith("app/"):
        return False
    allowed_app = frozenset(entry.get("allowed_app_files") or ())
    return path not in allowed_app


def _is_allowed(entry: dict[str, Any], path: str) -> bool:
    return (
        path in frozenset(entry.get("allowed_app_files") or ())
        or path in frozenset(entry.get("allowed_tree_files") or ())
        or path.startswith(tuple(entry.get("allowed_tree_prefixes") or ()))
    )


def test_wave_gate_registry() -> None:
    """自注册簿全 entry 审计：banned 在途前置 · active committed 闭窗 ⊆ allowed。"""
    root = _ROOT
    waves = _load_registry()
    inflight = _in_flight(root)
    failures: list[str] = []
    for entry in waves:
        slug = str(entry.get("task_slug") or "?")
        # ① banned 前置（全部 entry 含 closed：在途守卫是档案形态下仍咬的牙）
        banned = sorted(p for p in inflight if _is_banned(entry, p))
        assert not banned, f"[{slug}] 禁改面在途触碰: {banned}"
        # ② active entry：committed 面闭窗审计
        if str(entry.get("status") or "") != "active":
            continue
        base = str(entry.get("base") or "")
        tip = entry.get("wave_tip")
        if not tip:
            print(f"[{slug}] committed 面跳过：wave_tip 未钉（N2 规格）")
            continue
        tip = str(tip)
        ok, _ = _git_ok(root, "rev-parse", "--verify", f"{tip}^{{commit}}")
        if not ok:
            print(f"[{slug}] committed 面跳过：wave_tip {tip} 不可解析（浅克隆? · N2 规格）")
            continue
        ok, base_res = _git_ok(root, "rev-parse", "--verify", f"{base}^{{commit}}")
        if not ok:
            failures.append(f"[{slug}] base {base} 不可解析（active entry 钉锚必须可解析）")
            continue
        committed = set(_git(root, "diff", "--name-only", base, tip))
        offenders = sorted(p for p in committed if not _is_allowed(entry, p))
        if offenders:
            failures.append(f"[{slug}] committed 闭窗越白名单: {offenders}")
    assert not failures, "；".join(failures)


def test_registry_seed_entry_matches_tc8_whitelist() -> None:
    """回归牙：种子 entry（diff-whitelist-anchor-drift）allowed 集合与原 TC8 声明白名单一致。

    闸的本体真值在 registry；此用例钉住「迁移不缩水」——允许集合只能经签认
    （00 裁定式登记限定语）演进，不得在本簿静默漂移。
    """
    waves = {w.get("task_slug"): w for w in _load_registry()}
    entry = waves.get("diff-whitelist-anchor-drift")
    assert entry, "种子 entry 缺失"
    assert frozenset(entry.get("allowed_app_files") or ()) == frozenset(
        {"app/ops/capability/delegation.py", "app/ops/lg_rag/multi/nodes.py"}
    )
    assert frozenset(entry.get("allowed_tree_files") or ()) == frozenset(
        {
            "tests/test_capability_delegation.py",
            "tests/test_capability_testing_write.py",
            "tests/test_lg_rag_write_replay_guard.py",
            "tests/test_hitl_approved_replan_quality.py",
            "tests/test_strategy_scenario.py",
            "docs/_tech_graph/l1/01_modules.md",
            "docs/guides/GUIDE_env_inventory_v1.md",
            "docs/tasks/active/task_delegation_naming_boundary.md",
            "docs/tasks/done/task_delegation_naming_boundary.md",
            "docs/harness/reviews/task_delegation_naming_boundary_review40_20261020.md",
            "backups/local_qdrant_orphan_cleanup_20261018T005320Z/ops_knowledge-7885642805251913-2026-10-18-00-53-20.snapshot",
            "docs/harness/reviews/task_query_coref_rewrite_review40_20261019.md",
        }
    )
    assert tuple(entry.get("allowed_tree_prefixes") or ()) == (
        "docs/harness/invokes/by-task/delegation-naming-boundary/",
    )
    assert tuple(entry.get("banned_prefixes") or ()) == ("scripts/", "alembic/")
