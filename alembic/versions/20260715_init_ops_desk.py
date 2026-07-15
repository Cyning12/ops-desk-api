"""init ops desk

Revision ID: 20260715_init
Revises:
Create Date: 2026-07-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260715_init"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgvector"')

    # ops_users
    op.create_table(
        "ops_users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("username", sa.String(), nullable=False, unique=True),
        sa.Column("role", sa.String(), nullable=False, server_default="viewer"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )

    # ops_invite_tokens
    op.create_table(
        "ops_invite_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("token", sa.String(), nullable=False, unique=True),
        sa.Column("role", sa.String(), nullable=False, server_default="viewer"),
        sa.Column("used_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ops_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("idx_ops_invite_tokens_token", "ops_invite_tokens", ["token"])

    # ops_sessions
    op.create_table(
        "ops_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ops_users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("idx_ops_sessions_user_id", "ops_sessions", ["user_id"])
    op.create_index("idx_ops_sessions_token_hash", "ops_sessions", ["token_hash"])

    # ops_repos
    op.create_table(
        "ops_repos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("owner", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("full_name", sa.String(), nullable=False, unique=True),
        sa.Column("default_branch", sa.String(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("github_repo_id", sa.BigInteger(), nullable=True, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )

    # ops_issues
    op.create_table(
        "ops_issues",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("repo_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ops_repos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("github_issue_id", sa.BigInteger(), nullable=True),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("state", sa.String(), nullable=False, server_default="open"),
        sa.Column("labels", postgresql.ARRAY(sa.String()), server_default="{}", nullable=False),
        sa.Column("scan_status", sa.String(), nullable=True),
        sa.Column("module_tag", sa.String(), nullable=True),
        sa.Column("author", sa.String(), nullable=True),
        sa.Column("assignees", postgresql.ARRAY(sa.String()), server_default="{}", nullable=False),
        sa.Column("html_url", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("raw_payload", postgresql.JSONB(), nullable=True),
        sa.UniqueConstraint("repo_id", "number", name="uq_ops_issues_repo_number"),
    )
    op.create_index("idx_ops_issues_repo_state_updated", "ops_issues", ["repo_id", "state", "updated_at"])
    op.create_index("idx_ops_issues_labels", "ops_issues", ["labels"], postgresql_using="gin")
    op.create_index("idx_ops_issues_module_tag", "ops_issues", ["module_tag"])

    # ops_pull_requests
    op.create_table(
        "ops_pull_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("repo_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ops_repos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("github_pr_id", sa.BigInteger(), nullable=True),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("state", sa.String(), nullable=False, server_default="open"),
        sa.Column("draft", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("ci_status", sa.String(), nullable=True),
        sa.Column("author", sa.String(), nullable=True),
        sa.Column("reviewers", postgresql.ARRAY(sa.String()), server_default="{}", nullable=False),
        sa.Column("html_url", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("merged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("raw_payload", postgresql.JSONB(), nullable=True),
        sa.UniqueConstraint("repo_id", "number", name="uq_ops_pull_requests_repo_number"),
    )
    op.create_index("idx_ops_pull_requests_repo_state_updated", "ops_pull_requests", ["repo_id", "state", "updated_at"])

    # ops_sync_runs
    op.create_table(
        "ops_sync_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("repo_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ops_repos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sync_type", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="running"),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("summary", postgresql.JSONB(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
    )
    op.create_index("idx_ops_sync_runs_repo_started", "ops_sync_runs", ["repo_id", "started_at"])

    # ops_scan_snapshots
    op.create_table(
        "ops_scan_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("repo_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ops_repos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("scan_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ops_sync_runs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("parsed_summary", postgresql.JSONB(), nullable=False),
        sa.Column("raw_markdown", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("idx_ops_scan_snapshots_repo_created", "ops_scan_snapshots", ["repo_id", "created_at"])

    # ops_graph_snapshots
    op.create_table(
        "ops_graph_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("repo_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ops_repos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("graph_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ops_sync_runs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("module_matrix", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("idx_ops_graph_snapshots_repo_created", "ops_graph_snapshots", ["repo_id", "created_at"])

    # ops_sessions_chat
    op.create_table(
        "ops_sessions_chat",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ops_users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("idx_ops_sessions_chat_user_updated", "ops_sessions_chat", ["user_id", "updated_at"])

    # ops_runs
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

    # ops_run_events
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


def downgrade() -> None:
    tables = [
        "ops_run_events",
        "ops_runs",
        "ops_sessions_chat",
        "ops_graph_snapshots",
        "ops_scan_snapshots",
        "ops_sync_runs",
        "ops_pull_requests",
        "ops_issues",
        "ops_repos",
        "ops_sessions",
        "ops_invite_tokens",
        "ops_users",
    ]
    for table in tables:
        op.drop_table(table)

    op.execute('DROP EXTENSION IF EXISTS "pgvector"')
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')
