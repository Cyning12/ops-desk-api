"""ops_goals：Goal 落表（P0' T5 · issue #23 裁定 A2 · 仅 DDL 零功能）

Revision ID: 20261114_ops_goals
Revises: 20261114_lg_rag_runs
Create Date: 2026-11-14

A2：图零改动，落图为外状态——本迁移只建表；goal 摘要注入 query 前缀与
status 规则流转（不让 LLM 自判）属 P1 另卡。tenant_id 必填（freeze F1-F6），
承 notes/runs 先例默认 ''；thread_id 不加 FK（承 run_events 顺序容错先例）。
表无读写方，off 态 drop 安全。
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20261114_ops_goals"
down_revision: str | None = "20261114_lg_rag_runs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS ops_goals (
            goal_id     uuid          PRIMARY KEY,
            tenant_id   varchar(64)   NOT NULL DEFAULT '',
            thread_id   varchar(255)  NOT NULL DEFAULT '',
            objective   text          NOT NULL,
            status      varchar(32)   NOT NULL DEFAULT 'active',
            created_at  timestamptz   NOT NULL DEFAULT now(),
            updated_at  timestamptz   NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_ops_goals_tenant_status "
        "ON ops_goals (tenant_id, status)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_ops_goals_thread ON ops_goals (thread_id)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS ops_goals")
