"""host-v1-episodic-memory-feedback · D4/D5 失败模式聚类 + 建议人工确认闸。

纯函数段（无 DB · 恒跑）：报告字段族齐全 · 频次阈值（<3 不成模式）·
sample_run_ids ≤5 · 确定性可重放（同输入同报告 · 乱序输入同输出）·
suggested_rule 人工确认语义 · env 非法回退。
DB 段（skipif 无 PG）：mine_patterns 端到端 + 报告 yaml 落盘 + 两次跑同字节
（可重放）+ **建议零生效 git 守护**（聚类跑完 redlines/manifest 零 diff）。
"""
from __future__ import annotations

import hashlib
import logging
import subprocess
import uuid
from datetime import datetime, timedelta
from pathlib import Path

import pytest
import yaml
from sqlalchemy import text

from app.db.models import OpsMemoryEpisode
from app.db.session import AsyncSessionLocal
from scripts.episode_pattern_mine import (
    DEFAULT_MIN_COUNT,
    MAX_SAMPLE_RUN_IDS,
    group_patterns,
    mine_patterns,
    pattern_min_count,
)
from tests.conftest import DB_AVAILABLE

_REPO_ROOT = Path(__file__).resolve().parents[1]
_TENANT = "epm-test-tenant"

#: D5 git 守护目标（建议未确认零生效断言面）
_GUARD_PATHS = [
    _REPO_ROOT / "evals/agent/redlines/capability_v1.yaml",
    *sorted((_REPO_ROOT / "app/ops/capability/manifests").glob("*.yaml")),
]


def _rows(
    *,
    failure_class: str | None,
    fingerprint: str,
    count: int,
    start: datetime | None = None,
    run_prefix: str = "run",
) -> list[tuple[str, str | None, str, datetime]]:
    base = start or datetime(2026, 9, 23, 12, 0, 0)
    return [
        (f"{run_prefix}-{i:02d}", failure_class, fingerprint, base + timedelta(minutes=i))
        for i in range(count)
    ]


# ================= 纯函数段（无 DB） =================


def test_group_patterns_report_field_family_complete():
    """报告字段族齐全：pattern_id/failure_class/fingerprint/count/
    sample_run_ids(≤5)/first_seen/last_seen/suggested_rule。"""
    rows = _rows(failure_class="capability_blocked", fingerprint="fp-a", count=3)
    patterns = group_patterns(rows, min_count=3)
    assert len(patterns) == 1
    p = patterns[0]
    assert set(p) == {
        "pattern_id",
        "failure_class",
        "fingerprint",
        "count",
        "sample_run_ids",
        "first_seen",
        "last_seen",
        "suggested_rule",
    }
    assert p["pattern_id"].startswith("pat_") and len(p["pattern_id"]) == 16
    assert p["failure_class"] == "capability_blocked"
    assert p["fingerprint"] == "fp-a"
    assert p["count"] == 3
    assert p["sample_run_ids"] == ["run-00", "run-01", "run-02"]  # 时间序
    assert p["first_seen"] < p["last_seen"]
    assert p["suggested_rule"]  # 非空建议段


def test_group_patterns_threshold_filters_below_min_count():
    """频次阈值：<3 不成模式（FP-2 第一保险）；=3 成模式。"""
    rows = (
        _rows(failure_class="capability_blocked", fingerprint="fp-a", count=2)
        + _rows(failure_class="upstream_error", fingerprint="fp-b", count=3)
    )
    patterns = group_patterns(rows, min_count=3)
    assert len(patterns) == 1
    assert patterns[0]["fingerprint"] == "fp-b"
    assert group_patterns(rows, min_count=4) == []


def test_group_patterns_sample_run_ids_capped_at_5():
    rows = _rows(failure_class="other", fingerprint="fp-c", count=8)
    (p,) = group_patterns(rows, min_count=3)
    assert len(p["sample_run_ids"]) == MAX_SAMPLE_RUN_IDS == 5
    assert p["sample_run_ids"] == [f"run-{i:02d}" for i in range(5)]
    assert p["count"] == 8  # count 是全量，sample 截断


def test_group_patterns_null_failure_class_grouped():
    """partial 无 failure_class（NULL）也可成组（报告 failure_class=null）。"""
    rows = _rows(failure_class=None, fingerprint="fp-null", count=3)
    (p,) = group_patterns(rows, min_count=3)
    assert p["failure_class"] is None
    assert "未分类" in p["suggested_rule"]


def test_group_patterns_deterministic_replay_shuffled_input():
    """确定性可重放：同输入（乱序）同报告（逐字节 dict 相等）。"""
    rows = (
        _rows(failure_class="capability_blocked", fingerprint="fp-a", count=4)
        + _rows(failure_class="upstream_error", fingerprint="fp-b", count=3)
        + _rows(failure_class="capability_blocked", fingerprint="fp-c", count=5)
    )
    shuffled = list(reversed(rows))
    a = group_patterns(rows, min_count=3)
    b = group_patterns(shuffled, min_count=3)
    assert a == b
    # pattern_id 由内容哈希决定：同 (class, fingerprint) 恒同 id
    ids = {p["fingerprint"]: p["pattern_id"] for p in a}
    expected = hashlib.sha256(b"capability_blocked|fp-a").hexdigest()[:12]
    assert ids["fp-a"] == f"pat_{expected}"
    # 排序确定性：count desc → failure_class asc → fingerprint asc
    assert [p["count"] for p in a] == sorted((p["count"] for p in a), reverse=True)


def test_suggested_rule_is_human_confirmation_only():
    """D5 人工确认闸：建议段明示「未经人工确认不得生效 · 零自动回写」。"""
    (p,) = group_patterns(
        _rows(failure_class="budget_exhausted", fingerprint="fp-x", count=3), min_count=3
    )
    rule = p["suggested_rule"]
    assert "建议" in rule
    assert "未经人工确认" in rule
    assert "零自动回写" in rule


def test_pattern_min_count_default_and_fallback(monkeypatch: pytest.MonkeyPatch, caplog):
    monkeypatch.delenv("EPISODE_PATTERN_MIN_COUNT", raising=False)
    assert pattern_min_count() == DEFAULT_MIN_COUNT == 3
    monkeypatch.setenv("EPISODE_PATTERN_MIN_COUNT", "abc")
    with caplog.at_level(logging.WARNING, logger="scripts.episode_pattern_mine"):
        assert pattern_min_count() == 3
    assert "EPISODE_PATTERN_MIN_COUNT" in caplog.text
    monkeypatch.setenv("EPISODE_PATTERN_MIN_COUNT", "0")
    assert pattern_min_count() == 3
    monkeypatch.setenv("EPISODE_PATTERN_MIN_COUNT", "5")
    assert pattern_min_count() == 5


# ================= DB 段（真 PostgreSQL · opsdesk_test） =================

_needs_pg = pytest.mark.skipif(
    not DB_AVAILABLE, reason="需要 PostgreSQL（conftest 会准备 opsdesk_test）"
)


async def _clear_test_rows() -> None:
    if not DB_AVAILABLE:
        return
    async with AsyncSessionLocal() as session, session.begin():
        await session.execute(
            text("DELETE FROM ops_memory_episodes WHERE tenant_id LIKE 'epm-test-%'")
        )


@pytest.fixture(autouse=True)
async def _clean():
    await _clear_test_rows()
    yield
    await _clear_test_rows()


async def _insert_episode(
    *,
    outcome: str,
    failure_class: str | None,
    fingerprint: str,
    created_at: datetime,
    run_id: str | None = None,
) -> None:
    async with AsyncSessionLocal() as session, session.begin():
        session.add(
            OpsMemoryEpisode(
                tenant_id=_TENANT,
                run_id=run_id or ("run-" + uuid.uuid4().hex[:8]),
                task_domain="ops_kb",
                context_fingerprint=fingerprint,
                plan_summary="聚类测试摘要",
                tool_sequence=["logs.read"],
                outcome=outcome,
                failure_class=failure_class,
                created_at=created_at,
            )
        )


async def _seed_patterns() -> None:
    base = datetime(2026, 9, 20, 8, 0, 0)
    # fp-a × capability_blocked × 4（成模式）
    for i in range(4):
        await _insert_episode(
            outcome="failure",
            failure_class="capability_blocked",
            fingerprint="fp-a",
            created_at=base + timedelta(minutes=i),
            run_id=f"epm-run-a{i}",
        )
    # fp-b × upstream_error × 2（不成模式）
    for i in range(2):
        await _insert_episode(
            outcome="failure",
            failure_class="upstream_error",
            fingerprint="fp-b",
            created_at=base + timedelta(hours=1, minutes=i),
        )
    # success 行不入聚类输入（outcome 谓词只收 failure/partial）
    await _insert_episode(
        outcome="success",
        failure_class=None,
        fingerprint="fp-a",
        created_at=base + timedelta(hours=2),
    )
    # partial 无 class × 3（成模式 · failure_class=null）
    for i in range(3):
        await _insert_episode(
            outcome="partial",
            failure_class=None,
            fingerprint="fp-p",
            created_at=base + timedelta(hours=3, minutes=i),
        )


@_needs_pg
async def test_mine_patterns_end_to_end_report_yaml(tmp_path: Path):
    await _seed_patterns()
    report = await mine_patterns(
        session_factory=AsyncSessionLocal,
        tenant_id=_TENANT,
        report_dir=tmp_path,
        report_date="2026-09-23",
    )
    assert report.status == "pass"
    assert report.scanned == 9  # 4+2 failure + 3 partial（success 不入）
    assert report.pattern_count == 2  # fp-a 成模式 · fp-b 阈值下 · fp-p 成模式
    by_fp = {p["fingerprint"]: p for p in report.patterns}
    assert by_fp["fp-a"]["count"] == 4
    assert by_fp["fp-a"]["failure_class"] == "capability_blocked"
    assert by_fp["fp-a"]["sample_run_ids"] == [f"epm-run-a{i}" for i in range(4)]
    assert by_fp["fp-p"]["failure_class"] is None
    assert "fp-b" not in by_fp  # 频次阈值：<3 不成模式

    # 报告 yaml 落盘且字段族齐全
    path = tmp_path / "2026-09-23.yaml"
    assert path.exists()
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert data["status"] == "pass"
    assert data["scanned"] == 9
    assert data["min_count"] == 3
    assert data["pattern_count"] == 2
    assert len(data["patterns"]) == 2
    for p in data["patterns"]:
        assert {
            "pattern_id",
            "failure_class",
            "fingerprint",
            "count",
            "sample_run_ids",
            "first_seen",
            "last_seen",
            "suggested_rule",
        } <= set(p)


@_needs_pg
async def test_mine_patterns_deterministic_replay_same_bytes(tmp_path: Path):
    """可重放：同一份表数据连跑两次 → 报告正文逐字节相同。"""
    await _seed_patterns()
    r1 = await mine_patterns(
        session_factory=AsyncSessionLocal,
        tenant_id=_TENANT,
        report_dir=tmp_path / "run1",
        report_date="2026-09-23",
    )
    r2 = await mine_patterns(
        session_factory=AsyncSessionLocal,
        tenant_id=_TENANT,
        report_dir=tmp_path / "run2",
        report_date="2026-09-23",
    )
    assert r1.as_dict() == r2.as_dict()
    b1 = (tmp_path / "run1/2026-09-23.yaml").read_bytes()
    b2 = (tmp_path / "run2/2026-09-23.yaml").read_bytes()
    assert b1 == b2  # 同输入同报告（逐字节）


@_needs_pg
async def test_mine_patterns_min_count_override(tmp_path: Path):
    await _seed_patterns()
    report = await mine_patterns(
        session_factory=AsyncSessionLocal,
        tenant_id=_TENANT,
        min_count=2,  # 阈值降到 2 → fp-b 也成模式
        report_dir=tmp_path,
        write_report=False,
    )
    assert report.min_count == 2
    assert report.pattern_count == 3


def _guard_hashes() -> dict[Path, str]:
    out: dict[Path, str] = {}
    for path in _GUARD_PATHS:
        assert path.exists(), f"守护目标不存在：{path}"
        out[path] = hashlib.sha256(path.read_bytes()).hexdigest()
    return out


def _git_porcelain(paths: list[Path]) -> str:
    result = subprocess.run(
        ["git", "status", "--porcelain", "--", *[str(p) for p in paths]],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


@_needs_pg
async def test_suggestion_zero_effect_redlines_manifest_zero_diff(tmp_path: Path):
    """D5 建议未确认零生效（git 守护断言）：聚类跑完后 redlines yaml 与
    capability manifests **零 diff**——suggested_rule 只落在报告里，本波代码
    零路径自动改 redlines/manifest。
    """
    before = _guard_hashes()
    assert _git_porcelain(list(before)) == ""  # 起跑即净（否则断言失真）

    await _seed_patterns()
    report = await mine_patterns(
        session_factory=AsyncSessionLocal,
        tenant_id=_TENANT,
        report_dir=tmp_path,  # 报告落 tmp，不污仓内 reports/
        report_date="2026-09-23",
    )
    assert report.pattern_count >= 1  # 确有建议产出（防空真）
    assert all(p["suggested_rule"] for p in report.patterns)

    assert _guard_hashes() == before  # 文件内容零变化
    assert _git_porcelain(list(before)) == ""  # git 面零 diff
