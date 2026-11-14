"""drop legacy chat tables (ops_run_events / ops_runs / ops_sessions_chat)

P0' T2b（issue Cyning12/ops-desk-workspace#23 · T2a 偏差登记衍生卡）：
旧 chat 概念表三表归档 drop。web 仓已摘除唯一消费方（W1 · PR #103），
端点已 410 墓碑化；prod（cynaya.cn）数据导出为运营前置动作
（pg_dump --table=ops_sessions_chat --table=ops_runs --table=ops_run_events），
不在本迁移内执行。

downgrade 按 20260715_init_ops_desk 建表史逐字重建，独立可回退。

Revision ID: 20261114_drop_legacy_chat_tables
Revises: 20261114_v_audit_unified
Create Date: 2026-11-14
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20261114_drop_legacy_chat_tables"
down_revision = "20261114_v_audit_unified"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table("ops_run_events")
    op.drop_table("ops_runs")
    op.drop_table("ops_sessions_chat")


def downgrade() -> None:
    op.create_table(
        "ops_sessions_chat",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ops_users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("idx_ops_sessions_chat_user_updated", "ops_sessions_chat", ["user_id", "updated_at"])

    op.create_table(
        "ops_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ops_sessions_chat.id", ondelete="CASCADE"), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("intent", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="running"),
        sa.Column("model", sa.String(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("answer", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("idx_ops_runs_session_created", "ops_runs", ["session_id", "created_at"])

    op.create_table(
        "ops_run_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ops_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("seq", sa.Integer(), nullable=False),
        sa.Column("ts_ms", sa.Integer(), nullable=False),
        sa.Column("agent_role", sa.String(), nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.UniqueConstraint("run_id", "seq", name="uq_ops_run_events_run_seq"),
    )
    op.create_index("idx_ops_run_events_run_seq", "ops_run_events", ["run_id", "seq"])
    op.create_index("idx_ops_run_events_run_type", "ops_run_events", ["run_id", "event_type"])
