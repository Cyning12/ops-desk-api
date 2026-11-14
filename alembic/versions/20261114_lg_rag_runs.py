"""ops_lg_rag_runs：lg-rag run 一等实体表（P0' T4 · issue #23 裁定 A1）

Revision ID: 20261114_lg_rag_runs
Revises: 20261105_capability_notes
Create Date: 2026-11-14

run 此前只是 `ops_lg_rag_run_events.run_id` 字符串标签，orphan 补偿须全扫事件表。
A1：新建实体表（run_id String(64) PK 与事件表同型零迁移 · tenant_id 必填 ·
user_id FK · thread_id · status · created_at/finished_at）；`run_events.run_id`
**不加 FK**——orphan 补偿「先扫事件后补 run 行」顺序容错；`uq(run_id,seq)` 不动。
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20261114_lg_rag_runs"
down_revision: str | None = "20261105_capability_notes"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS ops_lg_rag_runs (
            run_id       varchar(64)   PRIMARY KEY,
            tenant_id    varchar(64)   NOT NULL DEFAULT '',
            user_id      uuid          NOT NULL REFERENCES ops_users(id) ON DELETE CASCADE,
            thread_id    varchar(255)  NOT NULL DEFAULT '',
            status       varchar(32)   NOT NULL DEFAULT 'running',
            created_at   timestamptz   NOT NULL DEFAULT now(),
            finished_at  timestamptz
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_ops_lg_rag_runs_status_created "
        "ON ops_lg_rag_runs (status, created_at)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_ops_lg_rag_runs_thread "
        "ON ops_lg_rag_runs (thread_id)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS ops_lg_rag_runs")
