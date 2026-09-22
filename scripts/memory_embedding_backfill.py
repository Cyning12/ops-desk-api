#!/usr/bin/env python3
"""记忆存量行 embedding 回填批处理 CLI（task memory-embedding-backfill · SPEC §2 D1/D2）。

扫 ``embedding IS NULL AND status='active'``（id ASC keyset 分页）→
``_fact_embed_text`` 口径批量嵌入（同步 Embedder 经 ``asyncio.to_thread`` 卸载）→
逐行回写并再核 ``status='active'``（rowcount=0 记 skipped，竞态失效行不误嵌）。

幂等/续跑：正确性只依赖扫描谓词（已嵌行不再命中），checkpoint 文件仅作跳过加速，
损坏/缺失 → 从头重扫。回填层**零行级重试**（``ApiEmbedder`` 内置 3 次指数退避已足）；
连续 3 页全败 → 判下游不可用提前终止（status=failed，exit 1）。

用法：
    python scripts/memory_embedding_backfill.py --dry-run   # 只扫描计数 + 前置校验，零嵌入零写库
    python scripts/memory_embedding_backfill.py             # 实跑

退出码：0 = pass；1 = partial/failed（部分失败 / 中断 / 对账不等）；2 = 前置校验失败。
报告：``reports/memory_embedding_backfill/backfill_<UTC 时间戳>.yaml``（对齐 qdrant_migrate 形态；
只记 id/计数/模型名，**不存** fact 明文 value）。
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import signal
import sys
import time
import uuid as uuid_mod
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import yaml  # noqa: E402
from sqlalchemy import func, select, text, update  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker  # noqa: E402

from app.db.models import MEMORY_FACT_EMBEDDING_DIM, OpsMemoryFact  # noqa: E402
from app.db.session import AsyncSessionLocal  # noqa: E402
from app.ops.memory.service import STATUS_ACTIVE, _fact_embed_text  # noqa: E402
from app.ops.rag.embedder import Embedder, embed_model_name  # noqa: E402

logger = logging.getLogger(__name__)

DEFAULT_BATCH_SIZE = 32  # 对齐 Embedder 批形态（SentenceTransformerEmbedder.batch_size=32）
DEFAULT_SLEEP_MS = 200
#: 连续全败页数上限：达到即判下游不可用提前终止（不连打挣扎下游）
CONSECUTIVE_PAGE_FAILURE_LIMIT = 3
#: 报告 failed_ids 截断上限（防大行数报告膨胀）
MAX_FAILED_IDS_IN_REPORT = 1000
#: 前置校验试嵌探针文本（非 fact 明文；测试据此过滤试嵌调用）
PREFLIGHT_PROBE_TEXT = "memory-backfill-preflight-probe"
DEFAULT_REPORT_DIR = Path("reports/memory_embedding_backfill")

_MIN_UUID = uuid_mod.UUID(int=0)
_UNSET: object = object()

#: 会话工厂（CLI 用自建引擎，测试复用 app 全局 AsyncSessionLocal）
SessionFactory = async_sessionmaker[AsyncSession]


class BackfillPreflightError(RuntimeError):
    """前置校验失败（CLI 翻 exit 2，零写入，不嵌半库异构向量）。"""


@dataclass
class BackfillReport:
    """跑批报告（yaml 落盘；计数守恒 embedded+skipped+failed==scanned）。"""

    status: str = "pass"  # pass | partial | failed
    dry_run: bool = False
    scanned: int = 0
    embedded: int = 0
    skipped: int = 0
    failed: int = 0
    failed_ids: list[str] = field(default_factory=list)
    embedder_name: str = ""
    batch_size: int = DEFAULT_BATCH_SIZE
    sleep_ms: int = DEFAULT_SLEEP_MS
    remaining_null_active: int | None = None  # 实跑后重扫对账
    interrupted: bool = False
    elapsed_s: float = 0.0
    recorded_at: str = ""

    def as_dict(self) -> dict:
        return {
            "status": self.status,
            "dry_run": self.dry_run,
            "scanned": self.scanned,
            "embedded": self.embedded,
            "skipped": self.skipped,
            "failed": self.failed,
            "failed_ids": self.failed_ids[:MAX_FAILED_IDS_IN_REPORT],
            "failed_ids_truncated": len(self.failed_ids) > MAX_FAILED_IDS_IN_REPORT,
            "embedder_name": self.embedder_name,
            "batch_size": self.batch_size,
            "sleep_ms": self.sleep_ms,
            "remaining_null_active": self.remaining_null_active,
            "interrupted": self.interrupted,
            "elapsed_s": self.elapsed_s,
            "recorded_at": self.recorded_at,
        }


# ---------------- env（非法值回退默认 + warning，对齐 service.py:248-260 模式） ----------------


def _env_int(name: str, default: int, *, minimum: int) -> int:
    raw = (os.getenv(name) or "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        logger.warning("invalid %s=%r; fallback to %d", name, raw, default)
        return default
    if value < minimum:
        logger.warning("invalid %s=%r (< %d); fallback to %d", name, raw, minimum, default)
        return default
    return value


def backfill_batch_size() -> int:
    """MEMORY_BACKFILL_BATCH_SIZE：默认 32；非法/<1 回退默认 + warning。"""
    return _env_int("MEMORY_BACKFILL_BATCH_SIZE", DEFAULT_BATCH_SIZE, minimum=1)


def backfill_sleep_ms() -> int:
    """MEMORY_BACKFILL_SLEEP_MS：默认 200；非法/<0 回退默认 + warning。"""
    return _env_int("MEMORY_BACKFILL_SLEEP_MS", DEFAULT_SLEEP_MS, minimum=0)


def backfill_checkpoint_path() -> Path | None:
    """MEMORY_BACKFILL_CHECKPOINT：默认空 = 禁用；指向目录 = 非法回退禁用 + warning。"""
    raw = (os.getenv("MEMORY_BACKFILL_CHECKPOINT") or "").strip()
    if not raw:
        return None
    path = Path(raw)
    if path.is_dir():
        logger.warning(
            "invalid MEMORY_BACKFILL_CHECKPOINT=%r (is a directory); checkpoint disabled", raw
        )
        return None
    return path


# ---------------- checkpoint（仅加速；正确性由谓词幂等保证） ----------------


def _read_checkpoint(path: Path | None) -> uuid_mod.UUID | None:
    """读 last_id 水位；文件损坏/缺失 → None（从头重扫，正确性不受影响）。"""
    if path is None or not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return uuid_mod.UUID(str(data["last_id"]))
    except Exception:
        logger.warning("corrupt checkpoint file %s; rescan from scratch", path)
        return None


def _write_checkpoint(path: Path | None, last_id: uuid_mod.UUID) -> None:
    """页内零失败才推进水位（失败行阻塞水位，重跑必被重扫）。"""
    if path is None:
        return
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps({"last_id": str(last_id)}) + "\n", encoding="utf-8"
        )
    except OSError:
        logger.warning(
            "checkpoint write failed %s (acceleration only; correctness unaffected)",
            path,
            exc_info=True,
        )


# ---------------- DB 访问 ----------------


async def _probe_embedding_column(sf: SessionFactory) -> None:
    """前置探测 embedding 列：migration 未跑 → exit 2，不静默零回填。"""
    try:
        async with sf() as session:
            await session.execute(text("SELECT embedding FROM ops_memory_facts LIMIT 0"))
    except Exception as exc:
        raise BackfillPreflightError(
            "ops_memory_facts.embedding 列不存在（migration 未跑？）"
        ) from exc


async def _count_candidates(sf: SessionFactory) -> int:
    """存量缺口计数（embedding IS NULL AND status='active'）；兼作实跑后对账重扫。"""
    async with sf() as session:
        result = await session.execute(
            select(func.count())
            .select_from(OpsMemoryFact)
            .where(
                OpsMemoryFact.embedding.is_(None),
                OpsMemoryFact.status == STATUS_ACTIVE,
            )
        )
        return int(result.scalar() or 0)


async def _fetch_page(
    sf: SessionFactory, last_id: uuid_mod.UUID, batch_size: int
) -> list[tuple[uuid_mod.UUID, str, object]]:
    """keyset 分页扫描：谓词幂等的唯一正确性来源（稳定 id ASC 序）。"""
    stmt = (
        select(OpsMemoryFact.id, OpsMemoryFact.key, OpsMemoryFact.value)
        .where(OpsMemoryFact.embedding.is_(None))
        # 钉死：扫描谓词必带 status='active'（变异检验删此须真 fail）
        .where(OpsMemoryFact.status == STATUS_ACTIVE)
        .where(OpsMemoryFact.id > last_id)
        .order_by(OpsMemoryFact.id.asc())
        .limit(batch_size)
    )
    async with sf() as session:
        rows = (await session.execute(stmt)).all()
    return [(row.id, row.key, row.value) for row in rows]


async def _write_back(
    sf: SessionFactory, fact_id: uuid_mod.UUID, vector: list[float]
) -> str:
    """逐行回写再核 active：rowcount=1 → embedded，0 → skipped；单行失败不连坐同页。"""
    stmt = (
        update(OpsMemoryFact)
        .where(OpsMemoryFact.id == fact_id)
        # 再核：回填期间被 supersede/revoke/expire 的行不误嵌
        .where(OpsMemoryFact.status == STATUS_ACTIVE)
        .values(embedding=vector)
    )
    try:
        async with sf() as session, session.begin():
            result = await session.execute(stmt)
    except Exception:
        logger.warning("backfill write-back failed id=%s", fact_id, exc_info=True)
        return "failed"
    return "embedded" if result.rowcount == 1 else "skipped"


# ---------------- 前置校验（防混库：name fingerprint + 维度试嵌） ----------------


async def _preflight_embedder(
    embedder: Embedder, *, dry_run: bool, candidates: int
) -> None:
    """name 必须等于 RAG_EMBED_MODEL（embed_model_name()）；维度试嵌 == 1024。

    干跑 / 零候选时**零嵌入调用**（干跑纪律 + 幂等重跑零调用验收）：
    维度试嵌只在确有候选行的实跑前执行，且先于任何写库。
    """
    expected = embed_model_name()
    name = getattr(embedder, "name", None)
    if not name or name != expected:
        raise BackfillPreflightError(
            f"embedder name fingerprint 不符：{name!r} != RAG_EMBED_MODEL={expected!r}"
        )
    if dry_run or candidates == 0:
        return
    vectors = await asyncio.to_thread(embedder.embed, [PREFLIGHT_PROBE_TEXT])
    if not vectors or len(vectors[0]) != MEMORY_FACT_EMBEDDING_DIM:
        actual = len(vectors[0]) if vectors and vectors[0] else "empty"
        raise BackfillPreflightError(
            f"embedder 维度不符：期望 {MEMORY_FACT_EMBEDDING_DIM}，实际 {actual}"
        )


# ---------------- 主流程 ----------------


async def run_backfill(
    *,
    embedder: Embedder | None = None,
    batch_size: int | None = None,
    sleep_ms: int | None = None,
    checkpoint_path: Path | None | object = _UNSET,
    session_factory: SessionFactory | None = None,
    dry_run: bool = False,
    report_dir: Path = DEFAULT_REPORT_DIR,
    write_report: bool = True,
    should_stop: Callable[[], bool] = lambda: False,
) -> BackfillReport:
    """回填主流程；前置校验失败抛 BackfillPreflightError（CLI 翻 exit 2）。

    幂等：重跑时已嵌行不再命中扫描谓词，零重复嵌入。
    中断：should_stop 在页边界检查（SIGINT/SIGTERM 由 CLI 翻译为该旗标），
    当前页完成后落部分报告（status=partial）。
    """
    started = time.monotonic()
    batch_size = batch_size if batch_size is not None else backfill_batch_size()
    sleep_ms = sleep_ms if sleep_ms is not None else backfill_sleep_ms()
    if checkpoint_path is _UNSET:
        checkpoint_path = backfill_checkpoint_path()
    assert checkpoint_path is None or isinstance(checkpoint_path, Path)

    sf: SessionFactory = session_factory or AsyncSessionLocal
    if embedder is None:
        from app.ops.rag.embedder import get_query_embedder

        embedder = get_query_embedder()
    report = BackfillReport(
        dry_run=dry_run,
        batch_size=batch_size,
        sleep_ms=sleep_ms,
        embedder_name=getattr(embedder, "name", "") or "",
    )

    await _probe_embedding_column(sf)
    candidates = await _count_candidates(sf)
    await _preflight_embedder(embedder, dry_run=dry_run, candidates=candidates)

    if dry_run:
        # 干跑：只扫描计数，零嵌入零写库
        report.scanned = candidates
        report.status = "pass"
        return _finalize(report, started, report_dir, write_report)

    last_id = _read_checkpoint(checkpoint_path) or _MIN_UUID
    consecutive_failed_pages = 0
    while True:
        if should_stop():
            report.interrupted = True
            break
        try:
            page = await _fetch_page(sf, last_id, batch_size)
        except Exception:
            # 连接级故障：终止跑批 + 报告留档，不伪装成功
            logger.exception("backfill scan failed; abort run")
            report.status = "failed"
            break
        if not page:
            break
        report.scanned += len(page)
        last_id = page[-1][0]  # keyset 推进：失败页计入 failed_ids，重跑自愈
        texts = [_fact_embed_text(key, value) for _, key, value in page]
        try:
            vectors = await asyncio.to_thread(embedder.embed, texts)
            if len(vectors) != len(page):
                raise RuntimeError(
                    f"embedder returned {len(vectors)} vectors for {len(page)} texts"
                )
        except Exception:
            # 回填层零叠加重试：整页记 failed，继续下一页
            logger.warning(
                "backfill page embed failed (%d rows); page marked failed",
                len(page),
                exc_info=True,
            )
            report.failed += len(page)
            report.failed_ids.extend(str(fid) for fid, _, _ in page)
            consecutive_failed_pages += 1
            if consecutive_failed_pages >= CONSECUTIVE_PAGE_FAILURE_LIMIT:
                logger.error(
                    "连续 %d 页全败，判下游不可用，提前终止",
                    CONSECUTIVE_PAGE_FAILURE_LIMIT,
                )
                report.status = "failed"
                break
        else:
            consecutive_failed_pages = 0
            page_failed = False
            for (fid, _, _), vector in zip(page, vectors, strict=True):
                outcome = await _write_back(sf, fid, vector)
                if outcome == "embedded":
                    report.embedded += 1
                elif outcome == "skipped":
                    report.skipped += 1
                else:
                    report.failed += 1
                    report.failed_ids.append(str(fid))
                    page_failed = True
            if not page_failed:
                _write_checkpoint(checkpoint_path, last_id)
        if sleep_ms > 0:
            await asyncio.sleep(sleep_ms / 1000)

    # 对账：完整实跑后重扫 NULL-active 剩余必须 == failed（不等 = 不伪装成功）
    if not report.interrupted and report.status != "failed":
        try:
            report.remaining_null_active = await _count_candidates(sf)
        except Exception:
            logger.exception("backfill reconcile rescan failed")
            report.status = "failed"
        else:
            if report.remaining_null_active != report.failed:
                logger.error(
                    "backfill reconcile mismatch: remaining=%d != failed=%d",
                    report.remaining_null_active,
                    report.failed,
                )
                report.status = "failed"
    if report.status != "failed":
        if report.interrupted or report.failed > 0:
            report.status = "partial"
        else:
            report.status = "pass"
    return _finalize(report, started, report_dir, write_report)


def _finalize(
    report: BackfillReport, started: float, report_dir: Path, write_report: bool
) -> BackfillReport:
    report.elapsed_s = round(time.monotonic() - started, 3)
    report.recorded_at = datetime.now(UTC).isoformat()
    if write_report:
        path = _write_report(report_dir, report)
        logger.info("backfill report written: %s", path)
    return report


def _write_report(report_dir: Path, report: BackfillReport) -> Path:
    report_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    path = report_dir / f"backfill_{stamp}.yaml"
    path.write_text(
        yaml.safe_dump(report.as_dict(), allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return path


def main(argv: list[str] | None = None, *, embedder: Embedder | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="记忆存量行 embedding 回填批处理（幂等可断点续跑）"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="只扫描计数 + 前置校验，零嵌入零写库"
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=DEFAULT_REPORT_DIR,
        help="报告落盘目录（默认 reports/memory_embedding_backfill/）",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    resolved = embedder
    if resolved is None:
        try:
            from app.ops.rag.embedder import get_query_embedder

            resolved = get_query_embedder()
        except Exception as exc:
            # SILICONFLOW_API_KEY 缺失（ApiEmbedder 构造即抛）等 → exit 2，不静默退 local ST
            logger.error("embedder 初始化失败：%s", exc)
            return 2

    stop = {"flag": False}

    def _handle_signal(signum, _frame):
        if stop["flag"]:
            raise KeyboardInterrupt  # 二次信号 = 立即退
        stop["flag"] = True
        logger.warning("received signal %s; 将在当前页完成后停止（partial）", signum)

    try:
        signal.signal(signal.SIGINT, _handle_signal)
        signal.signal(signal.SIGTERM, _handle_signal)
    except ValueError:
        # 非主线程（如测试经 asyncio.to_thread 调用）：跳过信号安装
        pass

    # CLI 自建引擎（对齐 rag_ingest 独立引擎先例），不占用 app 全局连接池
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    from app.config import settings

    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def _run() -> BackfillReport:
        try:
            return await run_backfill(
                embedder=resolved,
                session_factory=session_factory,
                dry_run=args.dry_run,
                report_dir=args.report_dir,
                should_stop=lambda: stop["flag"],
            )
        finally:
            await engine.dispose()

    try:
        report = asyncio.run(_run())
    except BackfillPreflightError as exc:
        logger.error("前置校验失败：%s", exc)
        return 2
    except KeyboardInterrupt:
        logger.error("backfill force-interrupted")
        return 1

    print(
        f"报告: status={report.status} scanned={report.scanned} "
        f"embedded={report.embedded} skipped={report.skipped} failed={report.failed} "
        f"dry_run={report.dry_run} elapsed_s={report.elapsed_s}"
    )
    return 0 if report.status == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
