"""ops_lg_rag_run_events：lg-rag SSE 事件落盘（T4 replay）

Revision ID: 20260831_lg_rag_run_events
Revises: 20260831_lg_rag_threads
Create Date: 2026-08-31

独立于 ops_run_events / chat；按 run_id+seq 供 POST /lg-rag/replay。
"""
from typing import Sequence, Union

from alembic import op

revision: str = "20260831_lg_rag_run_events"
down_revision: Union[str, None] = "20260831_lg_rag_threads"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS ops_lg_rag_run_events (
            id          uuid         PRIMARY KEY,
            run_id      varchar(64)  NOT NULL,
            seq         integer      NOT NULL,
            user_id     uuid         NOT NULL REFERENCES ops_users(id) ON DELETE CASCADE,
            thread_id   varchar(255) NOT NULL,
            ts_ms       integer      NOT NULL,
            agent_role  varchar(64)  NOT NULL,
            event_type  varchar(64)  NOT NULL,
            payload     jsonb        NOT NULL DEFAULT '{}'::jsonb,
            created_at  timestamptz  NOT NULL DEFAULT now(),
            CONSTRAINT uq_ops_lg_rag_run_events_run_seq UNIQUE (run_id, seq)
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_ops_lg_rag_run_events_run_seq "
        "ON ops_lg_rag_run_events (run_id, seq)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_ops_lg_rag_run_events_user_run "
        "ON ops_lg_rag_run_events (user_id, run_id)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS ops_lg_rag_run_events")
