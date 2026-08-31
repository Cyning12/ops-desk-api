"""ops_lg_rag_threads + ops_lg_rag_turns：lg-rag session SoT（T3）

Revision ID: 20260831_lg_rag_threads
Revises: 20260828_github_ids_bigint
Create Date: 2026-08-31

独立于 ops_sessions_chat / ops_runs；thread_id 为产品 SoT。
"""
from typing import Sequence, Union

from alembic import op

revision: str = "20260831_lg_rag_threads"
down_revision: Union[str, None] = "20260828_github_ids_bigint"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS ops_lg_rag_threads (
            id          varchar(255) PRIMARY KEY,
            user_id     uuid         NOT NULL REFERENCES ops_users(id) ON DELETE CASCADE,
            created_at  timestamptz  NOT NULL DEFAULT now(),
            updated_at  timestamptz  NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_ops_lg_rag_threads_user "
        "ON ops_lg_rag_threads (user_id)"
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS ops_lg_rag_turns (
            id          uuid         PRIMARY KEY,
            thread_id   varchar(255) NOT NULL REFERENCES ops_lg_rag_threads(id) ON DELETE CASCADE,
            role        varchar(32)  NOT NULL,
            content     text         NOT NULL,
            created_at  timestamptz  NOT NULL DEFAULT now(),
            CONSTRAINT ck_ops_lg_rag_turns_role
                CHECK (role IN ('user', 'assistant', 'system'))
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_ops_lg_rag_turns_thread_created "
        "ON ops_lg_rag_turns (thread_id, created_at)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS ops_lg_rag_turns")
    op.execute("DROP TABLE IF EXISTS ops_lg_rag_threads")
