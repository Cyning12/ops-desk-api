"""阶段 T Fixture：session / issue / PR 增加 tenant_id（回填试点 A）。

不改 (repo_id, number) 唯一约束：本波负样本用不同 number；同号跨租户后置。
生产 B 种子不在本迁移内。

Revision ID: 20260918_tenant_readonly
Revises: 20260831_lg_rag_run_events
"""

from typing import Sequence, Union

from alembic import op

revision: str = "20260918_tenant_readonly"
down_revision: Union[str, None] = "20260831_lg_rag_run_events"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_DEFAULT = "ops-desk-pilot"


def upgrade() -> None:
    for table in ("ops_sessions", "ops_issues", "ops_pull_requests"):
        op.execute(
            f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS tenant_id text "
            f"NOT NULL DEFAULT '{_DEFAULT}'"
        )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_ops_issues_tenant_number "
        "ON ops_issues (tenant_id, number)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_ops_pull_requests_tenant_number "
        "ON ops_pull_requests (tenant_id, number)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_ops_issues_tenant_number")
    op.execute("DROP INDEX IF EXISTS idx_ops_pull_requests_tenant_number")
    for table in ("ops_sessions", "ops_issues", "ops_pull_requests"):
        op.execute(f"ALTER TABLE {table} DROP COLUMN IF EXISTS tenant_id")
