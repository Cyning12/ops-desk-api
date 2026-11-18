"""ops_lg_rag_runs Run 树三列 + 委派 claim 索引（P4-T6 · issue #23 夜间预授权）

Revision ID: 20261118_lg_rag_run_tree
Revises: 20261116_ops_fires_created_at
Create Date: 2026-11-18

19-p4-contracts.md §7.1/§7.2 逐字：`parent_run_id`（String(64) null · **不加 FK**——
承 run_events 顺序容错先例 models.py:285-288）、`subtask_id`（String(64) null · 父图内
子任务 id · claim 业务键一半）、`depth`（Integer NOT NULL DEFAULT 0 · 0=根 1=子 ·
深度硬上限 1 由 claim 层断言承载 · 契约 SQL 无 DB CHECK）。`uq_ops_lg_rag_runs_parent_subtask`
部分唯一索引 =「建行即认领」（19 §7.3）；`idx_ops_lg_rag_runs_parent` 投影反查索引。
可逆：downgrade 全量回退两索引三列。
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20261118_lg_rag_run_tree"
down_revision: str | None = "20261116_ops_fires_created_at"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE ops_lg_rag_runs
          ADD COLUMN IF NOT EXISTS parent_run_id VARCHAR(64) NULL,
          ADD COLUMN IF NOT EXISTS subtask_id    VARCHAR(64) NULL,
          ADD COLUMN IF NOT EXISTS depth         INTEGER NOT NULL DEFAULT 0
        """
    )
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_ops_lg_rag_runs_parent_subtask "
        "ON ops_lg_rag_runs (parent_run_id, subtask_id) "
        "WHERE parent_run_id IS NOT NULL"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_ops_lg_rag_runs_parent "
        "ON ops_lg_rag_runs (parent_run_id)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_ops_lg_rag_runs_parent")
    op.execute("DROP INDEX IF EXISTS uq_ops_lg_rag_runs_parent_subtask")
    op.execute(
        """
        ALTER TABLE ops_lg_rag_runs
          DROP COLUMN IF EXISTS depth,
          DROP COLUMN IF EXISTS subtask_id,
          DROP COLUMN IF EXISTS parent_run_id
        """
    )
