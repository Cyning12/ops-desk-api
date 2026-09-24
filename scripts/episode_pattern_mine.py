#!/usr/bin/env python3
"""失败模式聚类离线批处理 CLI（host-v1-episodic-memory-feedback D4/D5 · Q2 指纹规则）。

读 ops_memory_episodes（outcome ∈ {failure, partial}，id ASC 确定性全扫）→
**指纹规则聚类**：按 (failure_class × context_fingerprint) 分组计数 →
频次阈值 EPISODE_PATTERN_MIN_COUNT（默认 3，<阈值不成模式 · SPEC FP-2 双保险
之一）→ 模式库报告 reports/episode_patterns/<date>.yaml（承 backfill 报告先例）。

- **确定性可重放**：同输入同报告——扫描序、分组序、sample_run_ids、
  first_seen/last_seen、suggested_rule 全部由数据决定，报告正文不含
  时间戳/耗时等非确定字段（日期只在文件名）。
- **人工确认闸（D5）**：建议只落在报告 suggested_rule 字段（文本建议非自动
  改动）；本脚本**零路径**写 redlines/manifest——聚类跑完后
  evals/agent/redlines/capability_v1.yaml 与 app/ops/capability/manifests/
  零 diff（git 守护断言钉死）。建议未经人工确认零生效。
- 审计记动作不记内容：报告只含 run_id/指纹/分类/计数，不含 plan 摘要正文。

用法：
    python scripts/episode_pattern_mine.py                 # 实跑（默认阈值 3）
    python scripts/episode_pattern_mine.py --min-count 5   # 自定义阈值
    python scripts/episode_pattern_mine.py --tenant t-1    # 只扫某 tenant

退出码：0 = pass；2 = 前置失败（表不存在 / DB 不可达，不静默产出空报告）。
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import logging
import os
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import yaml  # noqa: E402
from sqlalchemy import select  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker  # noqa: E402

from app.db.models import OpsMemoryEpisode  # noqa: E402
from app.db.session import AsyncSessionLocal  # noqa: E402

logger = logging.getLogger(__name__)

DEFAULT_MIN_COUNT = 3
#: sample_run_ids 截断上限（SPEC 报告字段族钉死 ≤5）
MAX_SAMPLE_RUN_IDS = 5
DEFAULT_REPORT_DIR = Path("reports/episode_patterns")

#: 会话工厂（CLI 用自建引擎，测试复用 app 全局 AsyncSessionLocal）
SessionFactory = async_sessionmaker[AsyncSession]


class PatternMinePreflightError(RuntimeError):
    """前置失败（表不存在 / DB 不可达）：CLI 翻 exit 2，不产出空报告伪装成功。"""


@dataclass
class PatternReport:
    """聚类报告（yaml 落盘；**全字段确定性**：同输入同字节，可重放断言钉死）。"""

    status: str = "pass"  # pass
    scanned: int = 0
    min_count: int = DEFAULT_MIN_COUNT
    pattern_count: int = 0
    patterns: list[dict] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "status": self.status,
            "scanned": self.scanned,
            "min_count": self.min_count,
            "pattern_count": self.pattern_count,
            "patterns": self.patterns,
        }


# ---------------- env（非法值回退默认 + warning，对齐 backfill 模式） ----------------


def pattern_min_count() -> int:
    """EPISODE_PATTERN_MIN_COUNT：默认 3；非法/<1 回退默认 + warning。"""
    raw = (os.getenv("EPISODE_PATTERN_MIN_COUNT") or "").strip()
    if not raw:
        return DEFAULT_MIN_COUNT
    try:
        value = int(raw)
    except ValueError:
        logger.warning(
            "invalid EPISODE_PATTERN_MIN_COUNT=%r; fallback to %d",
            raw,
            DEFAULT_MIN_COUNT,
        )
        return DEFAULT_MIN_COUNT
    if value < 1:
        logger.warning(
            "invalid EPISODE_PATTERN_MIN_COUNT=%r (< 1); fallback to %d",
            raw,
            DEFAULT_MIN_COUNT,
        )
        return DEFAULT_MIN_COUNT
    return value


# ---------------- 纯函数聚类（零 IO · 可重放断言直接打在这里） ----------------


def _suggested_rule(failure_class: str | None, fingerprint: str, count: int) -> str:
    """建议段（**文本建议非自动改动** · D5 人工确认闸：未经人工确认零生效）。"""
    cls = failure_class or "（未分类）"
    return (
        f"高频失败模式：failure_class={cls} · fingerprint={fingerprint} · "
        f"累计 {count} 次。建议人工复盘 sample_run_ids 后评估是否向 "
        f"redlines/manifest 增加对应防护规则；**未经人工确认不得生效**"
        f"（本报告仅建议，零自动回写）。"
    )


def group_patterns(
    rows: list[tuple[str, str | None, str, datetime]],
    *,
    min_count: int,
) -> list[dict]:
    """(failure_class × fingerprint) 分组计数 → 达阈值模式列表（确定性）。

    rows 每项为 (run_id, failure_class, context_fingerprint, created_at)
    （调用方已按 outcome ∈ {failure, partial} 过滤）。输出按 (count desc,
    failure_class asc, fingerprint asc) 排序；pattern_id =
    sha256(failure_class|fingerprint) 前 12 hex（同输入同 id）；
    sample_run_ids 取组内 (created_at asc, run_id asc) 前 5。
    """
    groups: dict[tuple[str, str], list[tuple[str, datetime]]] = {}
    for run_id, failure_class, fingerprint, created_at in rows:
        key = ((failure_class or "").strip(), (fingerprint or "").strip())
        groups.setdefault(key, []).append((run_id, created_at))
    patterns: list[dict] = []
    for (failure_class, fingerprint), members in groups.items():
        count = len(members)
        if count < min_count:
            continue  # 频次阈值：<min_count 不成模式（FP-2 第一保险）
        ordered = sorted(members, key=lambda m: (m[1], m[0]))
        digest = hashlib.sha256(f"{failure_class}|{fingerprint}".encode()).hexdigest()
        patterns.append(
            {
                "pattern_id": f"pat_{digest[:12]}",
                "failure_class": failure_class or None,
                "fingerprint": fingerprint,
                "count": count,
                "sample_run_ids": [rid for rid, _ in ordered[:MAX_SAMPLE_RUN_IDS]],
                "first_seen": ordered[0][1].isoformat(),
                "last_seen": ordered[-1][1].isoformat(),
                "suggested_rule": _suggested_rule(failure_class or None, fingerprint, count),
            }
        )
    patterns.sort(
        key=lambda p: (-int(p["count"]), str(p["failure_class"] or ""), str(p["fingerprint"]))
    )
    return patterns


# ---------------- DB 访问 ----------------


async def _fetch_failure_rows(
    sf: SessionFactory, *, tenant_id: str | None = None
) -> list[tuple[str, str | None, str, datetime]]:
    """failure/partial 全扫（id ASC 稳定序 · 确定性可重放的输入侧保证）。"""
    stmt = (
        select(
            OpsMemoryEpisode.run_id,
            OpsMemoryEpisode.failure_class,
            OpsMemoryEpisode.context_fingerprint,
            OpsMemoryEpisode.created_at,
        )
        .where(OpsMemoryEpisode.outcome.in_(["failure", "partial"]))
        .order_by(OpsMemoryEpisode.id.asc())
    )
    if tenant_id:
        stmt = stmt.where(OpsMemoryEpisode.tenant_id == tenant_id)
    try:
        async with sf() as session:
            rows = (await session.execute(stmt)).all()
    except Exception as exc:
        text = f"{type(exc).__name__}: {exc}"
        if "ops_memory_episodes" in text and (
            "does not exist" in text or "UndefinedTable" in text
        ):
            raise PatternMinePreflightError(
                "ops_memory_episodes 表不存在（migration 未跑？）"
            ) from exc
        raise PatternMinePreflightError(f"episode 扫描失败：{exc}") from exc
    return [(str(r[0]), r[1], str(r[2]), r[3]) for r in rows]


# ---------------- 主流程 ----------------


async def mine_patterns(
    *,
    session_factory: SessionFactory | None = None,
    min_count: int | None = None,
    tenant_id: str | None = None,
    report_dir: Path = DEFAULT_REPORT_DIR,
    report_date: str | None = None,
    write_report: bool = True,
) -> PatternReport:
    """聚类主流程；前置失败抛 PatternMinePreflightError（CLI 翻 exit 2）。

    确定性可重放：同一份表数据 + 同 min_count → 同报告正文（patterns 全字段
    由数据决定；日期只进文件名不进正文）。
    """
    threshold = min_count if min_count is not None else pattern_min_count()
    sf: SessionFactory = session_factory or AsyncSessionLocal
    rows = await _fetch_failure_rows(sf, tenant_id=tenant_id)
    report = PatternReport(scanned=len(rows), min_count=threshold)
    report.patterns = group_patterns(rows, min_count=threshold)
    report.pattern_count = len(report.patterns)
    # 审计记动作不记内容
    logger.info(
        "episode pattern mine scanned=%d min_count=%d patterns=%d",
        report.scanned,
        threshold,
        report.pattern_count,
    )
    if write_report:
        path = _write_report(report_dir, report, report_date=report_date)
        logger.info("episode pattern report written: %s", path)
    return report


def _write_report(
    report_dir: Path, report: PatternReport, *, report_date: str | None = None
) -> Path:
    report_dir.mkdir(parents=True, exist_ok=True)
    stamp = report_date or datetime.now(UTC).strftime("%Y-%m-%d")
    path = report_dir / f"{stamp}.yaml"
    path.write_text(
        yaml.safe_dump(report.as_dict(), allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="失败模式指纹规则聚类（离线 · 建议人工确认才生效）"
    )
    parser.add_argument("--min-count", type=int, default=None, help="频次阈值（默认 env/3）")
    parser.add_argument("--tenant", type=str, default=None, help="只扫某 tenant")
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=DEFAULT_REPORT_DIR,
        help="报告落盘目录（默认 reports/episode_patterns/）",
    )
    parser.add_argument("--date", type=str, default=None, help="报告文件名日期（默认今日 UTC）")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    # CLI 自建引擎（对齐 backfill 先例），不占用 app 全局连接池
    from sqlalchemy.ext.asyncio import create_async_engine

    from app.config import settings

    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def _run() -> PatternReport:
        try:
            return await mine_patterns(
                session_factory=session_factory,
                min_count=args.min_count,
                tenant_id=args.tenant,
                report_dir=args.report_dir,
                report_date=args.date,
            )
        finally:
            await engine.dispose()

    try:
        report = asyncio.run(_run())
    except PatternMinePreflightError as exc:
        logger.error("前置失败：%s", exc)
        return 2

    print(
        f"报告: status={report.status} scanned={report.scanned} "
        f"min_count={report.min_count} patterns={report.pattern_count}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
