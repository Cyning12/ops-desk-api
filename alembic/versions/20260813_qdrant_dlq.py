"""ops_qdrant_dlq：Qdrant 影子写死信表

Revision ID: 20260813_qdrant_dlq
Revises: 20260808_rag_chunks
Create Date: 2026-08-13

影子写失败入队；cron 重放（幂等 upsert/delete）。
"""
from typing import Sequence, Union

from alembic import op

revision: str = "20260813_qdrant_dlq"
down_revision: Union[str, None] = "20260808_rag_chunks"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS ops_qdrant_dlq (
            id          bigserial PRIMARY KEY,
            op          text        NOT NULL,
            point_ids   jsonb       NOT NULL,
            payload     jsonb,
            error       text        NOT NULL DEFAULT '',
            attempts    integer     NOT NULL DEFAULT 0,
            created_at  timestamptz NOT NULL DEFAULT now(),
            updated_at  timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT ck_ops_qdrant_dlq_op CHECK (op IN ('upsert', 'delete'))
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_ops_qdrant_dlq_created "
        "ON ops_qdrant_dlq (created_at)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS ops_qdrant_dlq")
