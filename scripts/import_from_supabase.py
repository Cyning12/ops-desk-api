"""Import historical data from Supabase into the local PostgreSQL database.

Usage:
    export SUPABASE_DATABASE_URL="postgresql://postgres.<ref>:<pwd>@aws-0-<region>.pooler.supabase.com:5432/postgres"
    python scripts/import_from_supabase.py [--dry-run] [--only ops_repos,ops_issues] [--batch-size 500]

See docs/ops/supabase-import-guide.md for how to obtain the source DSN.

Idempotency rules:
- ops_repos: upsert by full_name; a pre-existing repo keeps its local id and
  child-table foreign keys are remapped to it.
- ops_issues / ops_pull_requests: upsert by (repo_id, number).
- ops_sync_runs / ops_scan_snapshots / ops_graph_snapshots: skip rows whose
  source id already exists locally.

Exit codes: 0 ok · 1 source unreachable · 2 missing SUPABASE_DATABASE_URL ·
3 one or more tables failed.
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
import uuid
from datetime import datetime
from typing import Any

import asyncpg
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    OpsGraphSnapshot,
    OpsIssue,
    OpsPullRequest,
    OpsRepo,
    OpsScanSnapshot,
    OpsSyncRun,
)
from app.db.session import AsyncSessionLocal
from app.ops.admin.service import _to_naive_utc

GUIDE_HINT = "见配置指引: docs/ops/supabase-import-guide.md"

# Import order satisfies foreign keys.
IMPORT_ORDER = [
    "ops_repos",
    "ops_sync_runs",
    "ops_issues",
    "ops_pull_requests",
    "ops_scan_snapshots",
    "ops_graph_snapshots",
]

_MODELS = {
    "ops_repos": OpsRepo,
    "ops_sync_runs": OpsSyncRun,
    "ops_issues": OpsIssue,
    "ops_pull_requests": OpsPullRequest,
    "ops_scan_snapshots": OpsScanSnapshot,
    "ops_graph_snapshots": OpsGraphSnapshot,
}

# Local columns that must never be copied from the source row directly.
_FK_COLUMNS = {"repo_id", "scan_run_id", "graph_run_id"}

# Columns allowed to be NULL locally but better defaulted when source is NULL.
_JSONB_DEFAULTS: dict[str, dict[str, Any]] = {
    "ops_scan_snapshots": {"parsed_summary": dict},
    "ops_graph_snapshots": {"payload": dict},
}


def normalize_row(table: str, row: dict, local_columns: set[str]) -> dict:
    """Map a source row onto local columns: intersection copy + type cleanup."""
    out: dict[str, Any] = {}
    for key, value in row.items():
        if key not in local_columns or key in _FK_COLUMNS:
            continue
        if isinstance(value, datetime):
            value = _to_naive_utc(value)
        out[key] = value

    for key, default_factory in _JSONB_DEFAULTS.get(table, {}).items():
        if key in local_columns and out.get(key) is None:
            out[key] = default_factory()
    return out


async def fetch_table(
    conn: asyncpg.Connection, table: str, batch_size: int
) -> tuple[list[str], list[dict]]:
    """Fetch all rows of a table in batches; returns (columns, rows)."""
    rows: list[dict] = []
    columns: list[str] = []
    offset = 0
    while True:
        batch = await conn.fetch(
            f"SELECT * FROM {table} ORDER BY 1 LIMIT $1 OFFSET $2",  # noqa: S608
            batch_size,
            offset,
        )
        if batch and not columns:
            columns = list(batch[0].keys())
        rows.extend(dict(r) for r in batch)
        if len(batch) < batch_size:
            break
        offset += batch_size
    return columns, rows


async def table_exists(conn: asyncpg.Connection, table: str) -> bool:
    """Check whether the source has the given table in the public schema."""
    return bool(
        await conn.fetchval(
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_name = $1)",
            table,
        )
    )


async def source_columns(conn: asyncpg.Connection, table: str) -> set[str]:
    """Column names of a source table (public schema)."""
    rows = await conn.fetch(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema = 'public' AND table_name = $1",
        table,
    )
    return {r["column_name"] for r in rows}


class ImportStats:
    """Per-table counters."""

    def __init__(self) -> None:
        self.inserted = 0
        self.updated = 0
        self.skipped = 0

    def line(self) -> str:
        return f"inserted={self.inserted} updated={self.updated} skipped={self.skipped}"


async def import_repos(
    db: AsyncSession, rows: list[dict], local_columns: set[str], dry_run: bool
) -> tuple[dict[str, str], ImportStats]:
    """Upsert repos by full_name; returns (source_id -> local_id remap, stats)."""
    stats = ImportStats()
    id_map: dict[str, str] = {}
    for row in rows:
        data = normalize_row("ops_repos", row, local_columns)
        existing = await db.scalar(
            select(OpsRepo).where(OpsRepo.full_name == data.get("full_name"))
        )
        if existing is not None:
            stats.updated += 1
            id_map[str(row["id"])] = str(existing.id)
            if not dry_run:
                source_id = data.pop("id", None)
                for key, value in data.items():
                    setattr(existing, key, value)
                _ = source_id  # local id wins; source id recorded in id_map
        else:
            stats.inserted += 1
            if not dry_run:
                repo = OpsRepo(**data)
                db.add(repo)
                await db.flush()
                id_map[str(row["id"])] = str(repo.id)
            else:
                id_map[str(row["id"])] = str(row["id"])
    return id_map, stats


async def import_sync_runs(
    db: AsyncSession,
    rows: list[dict],
    local_columns: set[str],
    id_map: dict[str, str],
    dry_run: bool,
) -> ImportStats:
    """Insert sync runs not already present (by source id)."""
    stats = ImportStats()
    for row in rows:
        data = normalize_row("ops_sync_runs", row, local_columns)
        data["repo_id"] = id_map.get(str(row.get("repo_id")), row.get("repo_id"))
        existing = await db.scalar(select(OpsSyncRun).where(OpsSyncRun.id == data["id"]))
        if existing is not None:
            stats.skipped += 1
            continue
        stats.inserted += 1
        if not dry_run:
            db.add(OpsSyncRun(**data))
    return stats


async def _import_numbered(
    db: AsyncSession,
    table: str,
    rows: list[dict],
    local_columns: set[str],
    id_map: dict[str, str],
    dry_run: bool,
) -> ImportStats:
    """Upsert issues/PRs by (repo_id, number)."""
    model = _MODELS[table]
    stats = ImportStats()
    for row in rows:
        data = normalize_row(table, row, local_columns)
        data["repo_id"] = id_map.get(str(row.get("repo_id")), row.get("repo_id"))
        existing = await db.scalar(
            select(model).where(
                model.repo_id == data["repo_id"],
                model.number == data["number"],
            )
        )
        if existing is not None:
            stats.updated += 1
            if not dry_run:
                data.pop("id", None)
                for key, value in data.items():
                    setattr(existing, key, value)
            continue
        stats.inserted += 1
        if not dry_run:
            id_taken = await db.scalar(select(model).where(model.id == data["id"]))
            if id_taken is not None:
                data["id"] = str(uuid.uuid4())
            db.add(model(**data))
    return stats


async def import_snapshots(
    db: AsyncSession,
    table: str,
    rows: list[dict],
    local_columns: set[str],
    id_map: dict[str, str],
    dry_run: bool,
) -> ImportStats:
    """Insert scan/graph snapshots not already present (by source id)."""
    model = _MODELS[table]
    stats = ImportStats()
    for row in rows:
        data = normalize_row(table, row, local_columns)
        data["repo_id"] = id_map.get(str(row.get("repo_id")), row.get("repo_id"))
        existing = await db.scalar(select(model).where(model.id == data["id"]))
        if existing is not None:
            stats.skipped += 1
            continue
        stats.inserted += 1
        if not dry_run:
            db.add(model(**data))
    return stats


async def run_import(
    src_dsn: str,
    only: list[str] | None,
    batch_size: int,
    dry_run: bool,
) -> int:
    """Run the import; returns process exit code."""
    tables = [t for t in IMPORT_ORDER if only is None or t in only]
    unknown = set(only or []) - set(IMPORT_ORDER)
    if unknown:
        print(f"未知表名: {sorted(unknown)} · 可选: {IMPORT_ORDER}", file=sys.stderr)
        return 2

    try:
        src = await asyncpg.connect(src_dsn)
    except (OSError, asyncpg.PostgresError) as exc:
        print(f"源库连接失败: {exc}\n{GUIDE_HINT}", file=sys.stderr)
        return 1

    failed: list[str] = []
    try:
        async with AsyncSessionLocal() as db:
            id_map: dict[str, str] = {}
            for table in tables:
                if not await table_exists(src, table):
                    print(f"[warn] 源库缺表 {table}，跳过", file=sys.stderr)
                    continue
                src_cols = await source_columns(src, table)
                local_columns = {
                    c.name for c in _MODELS[table].__table__.columns
                }
                missing_locally = src_cols - local_columns
                if missing_locally:
                    print(
                        f"[warn] {table} 源列在本地不存在，将被忽略: "
                        f"{sorted(missing_locally)}",
                        file=sys.stderr,
                    )

                try:
                    _, rows = await fetch_table(src, table, batch_size)
                    if table == "ops_repos":
                        id_map, stats = await import_repos(
                            db, rows, local_columns, dry_run
                        )
                    elif table == "ops_sync_runs":
                        stats = await import_sync_runs(
                            db, rows, local_columns, id_map, dry_run
                        )
                    elif table in ("ops_issues", "ops_pull_requests"):
                        stats = await _import_numbered(
                            db, table, rows, local_columns, id_map, dry_run
                        )
                    else:
                        stats = await import_snapshots(
                            db, table, rows, local_columns, id_map, dry_run
                        )
                    print(f"{table}: {stats.line()} (source_rows={len(rows)})")
                    if not dry_run:
                        # Commit per table so a later table's rollback does not
                        # undo earlier successes.
                        await db.commit()
                except Exception:
                    failed.append(table)
                    await db.rollback()
                    print(f"[error] {table} 导入失败", file=sys.stderr)
                    import traceback

                    traceback.print_exc()
                    continue

            if dry_run:
                await db.rollback()
                print("dry-run：未写入任何数据")
    finally:
        await src.close()

    if failed:
        print(f"失败表: {failed}", file=sys.stderr)
        return 3
    return 0


def main() -> int:
    """CLI entry."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="只统计不写入")
    parser.add_argument("--only", type=str, default=None, help="逗号分隔的表名子集")
    parser.add_argument("--batch-size", type=int, default=500)
    args = parser.parse_args()

    src_dsn = os.environ.get("SUPABASE_DATABASE_URL")
    if not src_dsn:
        print(f"缺少 SUPABASE_DATABASE_URL 环境变量\n{GUIDE_HINT}", file=sys.stderr)
        return 2

    only = [t.strip() for t in args.only.split(",")] if args.only else None
    return asyncio.run(run_import(src_dsn, only, args.batch_size, args.dry_run))


if __name__ == "__main__":
    sys.exit(main())
