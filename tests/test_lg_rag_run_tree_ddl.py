"""P4-T6 · Run 树 DDL（ops_lg_rag_runs 三列 + 委派 claim 两索引 · 19-p4-contracts §7）。

- scratch 库迁移 upgrade/downgrade 实证（承 tests/test_import_from_supabase.py:158-188
  asyncpg ADMIN_DSN 先例 · 子进程传 DATABASE_URL 跑 alembic）；
- 部分唯一谓词功能实证（同键二次 INSERT → UniqueViolationError · NULL parent 不触谓词）；
- models.py __table_args__ 对齐迁移（消 autogenerate 漂移 · 承 models.py:302-308 纪律）。
"""

from __future__ import annotations

import asyncio
import os
import sys
import uuid
from pathlib import Path

import pytest

from tests.conftest import DB_AVAILABLE

_DB_REQUIRED = pytest.mark.skipif(
    not DB_AVAILABLE, reason="需要本地 PG 真跑迁移 scratch 库与约束"
)

_ROOT = Path(__file__).resolve().parents[1]
_ADMIN_DSN = "postgresql://ops:ops_password@localhost:5432/postgres"
_SCRATCH_DB = f"opsdesk_p4t6_{uuid.uuid4().hex[:8]}"
_SCRATCH_DSN = f"postgresql://ops:ops_password@localhost:5432/{_SCRATCH_DB}"
_SCRATCH_URL = f"postgresql+asyncpg://ops:ops_password@localhost:5432/{_SCRATCH_DB}"
_DOWN_REV = "20261116_ops_fires_created_at"

# 迁移前置表形（20261114_lg_rag_runs 原始 7 列 + ops_users FK 宿主 · scratch 最小重演）
_PARENT_DDL = """
CREATE TABLE ops_users (id uuid PRIMARY KEY);
CREATE TABLE ops_lg_rag_runs (
    run_id       varchar(64)   PRIMARY KEY,
    tenant_id    varchar(64)   NOT NULL DEFAULT '',
    user_id      uuid          NOT NULL REFERENCES ops_users(id) ON DELETE CASCADE,
    thread_id    varchar(255)  NOT NULL DEFAULT '',
    status       varchar(32)   NOT NULL DEFAULT 'running',
    created_at   timestamptz   NOT NULL DEFAULT now(),
    finished_at  timestamptz
);
"""


async def _alembic(*args: str) -> tuple[int, str]:
    """子进程跑 alembic（cwd=仓根找 alembic.ini · DATABASE_URL 指向 scratch 库）。"""
    env = {**os.environ, "DATABASE_URL": _SCRATCH_URL}
    proc = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "alembic",
        *args,
        cwd=str(_ROOT),
        env=env,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    out, _ = await proc.communicate()
    return proc.returncode or 0, out.decode()


@pytest.fixture
async def scratch_dsn():
    """建 scratch 库 + 迁移前置表形；测后 DROP。DSN 供 asyncpg 直连断言。"""
    if not DB_AVAILABLE:
        pytest.skip("PostgreSQL not available")
    import asyncpg

    admin = await asyncpg.connect(_ADMIN_DSN)
    try:
        await admin.execute(f"DROP DATABASE IF EXISTS {_SCRATCH_DB}")
        await admin.execute(f"CREATE DATABASE {_SCRATCH_DB}")
    finally:
        await admin.close()
    conn = await asyncpg.connect(_SCRATCH_DSN)
    try:
        await conn.execute(_PARENT_DDL)
    finally:
        await conn.close()
    yield _SCRATCH_DSN
    admin = await asyncpg.connect(_ADMIN_DSN)
    try:
        await admin.execute(f"DROP DATABASE IF EXISTS {_SCRATCH_DB}")
    finally:
        await admin.close()


@_DB_REQUIRED
@pytest.mark.asyncio
async def test_migration_upgrade_downgrade_and_claim_uq(scratch_dsn: str) -> None:
    """19 §7.2 迁移可逆 + §7.3 委派 claim 键功能实证（scratch 库 · 不影响 opsdesk_test）。"""
    import asyncpg

    rc, out = await _alembic("stamp", _DOWN_REV)
    assert rc == 0, out
    rc, out = await _alembic("upgrade", "head")
    assert rc == 0, out

    conn = await asyncpg.connect(scratch_dsn)
    try:
        cols = {
            r["column_name"]: r
            for r in await conn.fetch(
                "SELECT column_name, is_nullable, column_default"
                " FROM information_schema.columns"
                " WHERE table_name = 'ops_lg_rag_runs'"
            )
        }
        # §7.1 三列形态逐字
        assert cols["parent_run_id"]["is_nullable"] == "YES"
        assert cols["subtask_id"]["is_nullable"] == "YES"
        assert cols["depth"]["is_nullable"] == "NO"
        assert cols["depth"]["column_default"] == "0"

        idx = {
            r["indexname"]: r["indexdef"]
            for r in await conn.fetch(
                "SELECT indexname, indexdef FROM pg_indexes"
                " WHERE tablename = 'ops_lg_rag_runs'"
            )
        }
        assert "uq_ops_lg_rag_runs_parent_subtask" in idx
        uq_def = idx["uq_ops_lg_rag_runs_parent_subtask"]
        assert "UNIQUE" in uq_def and "parent_run_id, subtask_id" in uq_def
        assert "WHERE (parent_run_id IS NOT NULL)" in uq_def
        assert "idx_ops_lg_rag_runs_parent" in idx

        # §7.3 claim 键功能实证：同 (parent, subtask) 二次 INSERT → UniqueViolationError
        uid = await conn.fetchval(
            "INSERT INTO ops_users (id) VALUES (gen_random_uuid()) RETURNING id"
        )
        await conn.execute(
            "INSERT INTO ops_lg_rag_runs (run_id, user_id) VALUES ('p1', $1)", uid
        )
        await conn.execute(
            "INSERT INTO ops_lg_rag_runs"
            " (run_id, user_id, parent_run_id, subtask_id, depth)"
            " VALUES ('c1', $1, 'p1', 'st1', 1)",
            uid,
        )
        with pytest.raises(asyncpg.UniqueViolationError):
            await conn.execute(
                "INSERT INTO ops_lg_rag_runs"
                " (run_id, user_id, parent_run_id, subtask_id, depth)"
                " VALUES ('c2', $1, 'p1', 'st1', 1)",
                uid,
            )
        # 部分谓词：parent_run_id IS NULL 的根 run 不触 uq（同 subtask_id 合法两行）
        await conn.execute(
            "INSERT INTO ops_lg_rag_runs (run_id, user_id, subtask_id)"
            " VALUES ('r1', $1, 'st1'), ('r2', $1, 'st1')",
            uid,
        )
    finally:
        await conn.close()

    rc, out = await _alembic("downgrade", _DOWN_REV)
    assert rc == 0, out
    conn = await asyncpg.connect(scratch_dsn)
    try:
        cols_after = {
            r["column_name"]
            for r in await conn.fetch(
                "SELECT column_name FROM information_schema.columns"
                " WHERE table_name = 'ops_lg_rag_runs'"
            )
        }
        assert "parent_run_id" not in cols_after
        assert "subtask_id" not in cols_after
        assert "depth" not in cols_after
        idx_after = {
            r["indexname"]
            for r in await conn.fetch(
                "SELECT indexname FROM pg_indexes WHERE tablename = 'ops_lg_rag_runs'"
            )
        }
        assert "uq_ops_lg_rag_runs_parent_subtask" not in idx_after
        assert "idx_ops_lg_rag_runs_parent" not in idx_after
    finally:
        await conn.close()


def test_models_table_args_alignment() -> None:
    """models.py __table_args__ 对齐迁移（消 autogenerate 漂移 · 免 DB 纯元数据断言）。"""
    from app.db.models import OpsLgRagRun

    indexes = {i.name: i for i in OpsLgRagRun.__table__.indexes}
    uq = indexes["uq_ops_lg_rag_runs_parent_subtask"]
    assert uq.unique is True
    assert [c.name for c in uq.columns] == ["parent_run_id", "subtask_id"]
    where = uq.dialect_options["postgresql"]["where"]
    assert where is not None and "parent_run_id IS NOT NULL" in str(where)
    parent_idx = indexes["idx_ops_lg_rag_runs_parent"]
    assert parent_idx.unique is False
    assert [c.name for c in parent_idx.columns] == ["parent_run_id"]
    cols = OpsLgRagRun.__table__.c
    assert cols["parent_run_id"].nullable is True
    assert cols["subtask_id"].nullable is True
    assert cols["depth"].nullable is False
    # 契约：parent_run_id 刻意无 FK（承 run_events 顺序容错先例）
    assert not cols["parent_run_id"].foreign_keys
