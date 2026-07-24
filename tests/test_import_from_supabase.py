"""Tests for scripts/import_from_supabase.py.

Integration tests build a scratch ``opsdesk_src`` database on the local
PostgreSQL instance with Supabase-shaped tables, run the import, and verify
idempotency; they are skipped when PostgreSQL is unavailable.
"""
from __future__ import annotations

from datetime import UTC, datetime

import asyncpg
import pytest
from sqlalchemy import delete, select

from app.db.models import OpsIssue, OpsRepo, OpsScanSnapshot, OpsSyncRun
from app.db.session import AsyncSessionLocal
from scripts.import_from_supabase import normalize_row, run_import
from tests.conftest import DB_AVAILABLE

ADMIN_DSN = "postgresql://ops:ops_password@localhost:5432/postgres"
SRC_DB = "opsdesk_src"
SRC_DSN = f"postgresql://ops:ops_password@localhost:5432/{SRC_DB}"

REPO_ID = "11111111-1111-1111-1111-111111111111"
RUN_ID = "22222222-2222-2222-2222-222222222222"
ISSUE_ID = "33333333-3333-3333-3333-333333333333"
SCAN_ID = "44444444-4444-4444-4444-444444444444"
FULL_NAME = "acme/import-src"


# ---------------------------------------------------------------------------
# Unit: normalize_row
# ---------------------------------------------------------------------------


def test_normalize_row_converts_aware_datetime_to_naive_utc() -> None:
    row = {
        "id": REPO_ID,
        "full_name": FULL_NAME,
        "created_at": datetime(2026, 7, 1, 12, 0, tzinfo=UTC),
    }
    local_columns = {"id", "full_name", "created_at"}
    out = normalize_row("ops_repos", row, local_columns)
    assert out["created_at"] == datetime(2026, 7, 1, 12, 0)
    assert out["created_at"].tzinfo is None


def test_normalize_row_drops_unknown_and_fk_columns() -> None:
    row = {
        "id": ISSUE_ID,
        "repo_id": REPO_ID,
        "number": 1,
        "legacy_field": "x",
    }
    local_columns = {"id", "repo_id", "number"}
    out = normalize_row("ops_issues", row, local_columns)
    assert "legacy_field" not in out
    assert "repo_id" not in out  # FK columns are remapped by the importer
    assert out["number"] == 1


def test_normalize_row_defaults_null_jsonb() -> None:
    row = {"id": SCAN_ID, "parsed_summary": None}
    local_columns = {"id", "parsed_summary"}
    out = normalize_row("ops_scan_snapshots", row, local_columns)
    assert out["parsed_summary"] == {}


# ---------------------------------------------------------------------------
# Integration: scratch source database
# ---------------------------------------------------------------------------

_SOURCE_DDL = """
CREATE TABLE ops_repos (
    id uuid PRIMARY KEY,
    owner text NOT NULL,
    name text NOT NULL,
    full_name text NOT NULL,
    default_branch text,
    description text,
    github_repo_id int,
    created_at timestamptz,
    updated_at timestamptz,
    legacy_field text
);
CREATE TABLE ops_sync_runs (
    id uuid PRIMARY KEY,
    repo_id uuid NOT NULL,
    sync_type text NOT NULL,
    status text,
    started_at timestamptz,
    finished_at timestamptz,
    summary jsonb,
    error_message text
);
CREATE TABLE ops_issues (
    id uuid PRIMARY KEY,
    repo_id uuid NOT NULL,
    number int NOT NULL,
    title text NOT NULL,
    body text,
    state text,
    labels text[],
    module_tag text,
    author text,
    assignees text[],
    html_url text,
    created_at timestamptz,
    updated_at timestamptz,
    closed_at timestamptz,
    raw_payload jsonb
);
CREATE TABLE ops_scan_snapshots (
    id uuid PRIMARY KEY,
    repo_id uuid NOT NULL,
    scan_run_id uuid,
    parsed_summary jsonb,
    raw_markdown text,
    created_at timestamptz
);
"""

_SOURCE_ROWS = f"""
INSERT INTO ops_repos VALUES (
    '{REPO_ID}', 'acme', 'import-src', '{FULL_NAME}', 'main', 'demo', 777,
    '2026-07-01T12:00:00+08:00', '2026-07-01T12:00:00+08:00', 'ignore-me'
);
INSERT INTO ops_sync_runs VALUES (
    '{RUN_ID}', '{REPO_ID}', 'full', 'completed',
    '2026-07-01T12:00:00Z', '2026-07-01T12:05:00Z', '{{"issues": 1}}', NULL
);
INSERT INTO ops_issues VALUES (
    '{ISSUE_ID}', '{REPO_ID}', 1, '导入测试 issue', 'body', 'open',
    ARRAY['bug'], 'auth', 'dev-a', ARRAY[]::text[],
    'https://example.com/1',
    '2026-07-01T12:00:00Z', '2026-07-01T12:00:00Z', NULL, NULL
);
INSERT INTO ops_scan_snapshots VALUES (
    '{SCAN_ID}', '{REPO_ID}', '{RUN_ID}', NULL, '# scan', '2026-07-01T12:10:00Z'
);
"""


@pytest.fixture
async def scratch_source():
    """Create a scratch Supabase-shaped source database; drop it afterwards."""
    if not DB_AVAILABLE:
        pytest.skip("PostgreSQL not available")

    admin = await asyncpg.connect(ADMIN_DSN)
    try:
        await admin.execute(f"DROP DATABASE IF EXISTS {SRC_DB}")
        await admin.execute(f"CREATE DATABASE {SRC_DB}")
    finally:
        await admin.close()

    src = await asyncpg.connect(SRC_DSN)
    try:
        await src.execute(_SOURCE_DDL)
        await src.execute(_SOURCE_ROWS)
    finally:
        await src.close()

    yield SRC_DSN

    admin = await asyncpg.connect(ADMIN_DSN)
    try:
        await admin.execute(f"DROP DATABASE IF EXISTS {SRC_DB}")
    finally:
        await admin.close()

    async with AsyncSessionLocal() as db:
        await db.execute(delete(OpsRepo).where(OpsRepo.full_name == FULL_NAME))
        await db.commit()


@pytest.mark.skipif(not DB_AVAILABLE, reason="PostgreSQL not available")
async def test_import_roundtrip_and_idempotency(scratch_source) -> None:
    """Import inserts rows preserving source ids; second run updates/skips."""
    rc = await run_import(scratch_source, None, 500, dry_run=False)
    assert rc == 0

    async with AsyncSessionLocal() as db:
        repo = await db.scalar(select(OpsRepo).where(OpsRepo.full_name == FULL_NAME))
        assert repo is not None
        assert str(repo.id) == REPO_ID
        # 2026-07-01T12:00:00+08:00 -> 04:00 UTC（ops_repos.created_at 为 timestamptz）
        assert repo.created_at == datetime(2026, 7, 1, 4, 0, tzinfo=UTC)

        issue = await db.scalar(
            select(OpsIssue).where(
                OpsIssue.repo_id == repo.id, OpsIssue.number == 1
            )
        )
        assert issue is not None
        assert issue.title == "导入测试 issue"
        assert issue.labels == ["bug"]

        run = await db.scalar(select(OpsSyncRun).where(OpsSyncRun.id == RUN_ID))
        assert run is not None

        scan = await db.scalar(
            select(OpsScanSnapshot).where(OpsScanSnapshot.id == SCAN_ID)
        )
        assert scan is not None
        assert scan.parsed_summary == {}  # NULL jsonb defaulted

    # Second run: no duplicates.
    rc = await run_import(scratch_source, None, 500, dry_run=False)
    assert rc == 0
    async with AsyncSessionLocal() as db:
        repos = (await db.scalars(select(OpsRepo).where(OpsRepo.full_name == FULL_NAME))).all()
        issues = (await db.scalars(select(OpsIssue).where(OpsIssue.repo_id == repo.id))).all()
        runs = (await db.scalars(select(OpsSyncRun).where(OpsSyncRun.id == RUN_ID))).all()
    assert len(repos) == 1
    assert len(issues) == 1
    assert len(runs) == 1


@pytest.mark.skipif(not DB_AVAILABLE, reason="PostgreSQL not available")
async def test_import_repo_conflict_remaps_children(scratch_source) -> None:
    """A pre-existing repo with a different id keeps its id; children remap."""
    local_repo_id = None
    async with AsyncSessionLocal() as db:
        repo = OpsRepo(owner="acme", name="import-src", full_name=FULL_NAME)
        db.add(repo)
        await db.commit()
        local_repo_id = str(repo.id)
    assert local_repo_id != REPO_ID

    rc = await run_import(scratch_source, None, 500, dry_run=False)
    assert rc == 0

    async with AsyncSessionLocal() as db:
        repo = await db.scalar(select(OpsRepo).where(OpsRepo.full_name == FULL_NAME))
        assert str(repo.id) == local_repo_id  # local id preserved
        issue = await db.scalar(
            select(OpsIssue).where(OpsIssue.repo_id == repo.id, OpsIssue.number == 1)
        )
        assert issue is not None  # child FK remapped to local repo id
        # Source-id repo must NOT have been inserted as a duplicate.
        assert await db.scalar(select(OpsRepo).where(OpsRepo.id == REPO_ID)) is None


@pytest.mark.skipif(not DB_AVAILABLE, reason="PostgreSQL not available")
async def test_dry_run_writes_nothing(scratch_source) -> None:
    """--dry-run counts but never writes."""
    rc = await run_import(scratch_source, None, 500, dry_run=True)
    assert rc == 0
    async with AsyncSessionLocal() as db:
        assert await db.scalar(select(OpsRepo).where(OpsRepo.full_name == FULL_NAME)) is None
