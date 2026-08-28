"""github_*_id 对齐 GitHub node id（bigint）

Revision ID: 20260828_github_ids_bigint
Revises: 20260813_qdrant_dlq
Create Date: 2026-08-28

ORM 曾用 Integer，asyncpg 按 int32 绑定；kimi-code issue id 已超过 2^31-1。
init 迁移已是 BigInteger；若表由 create_all / 旧模型建成 Integer，本迁移 ALTER。
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260828_github_ids_bigint"
down_revision: Union[str, None] = "20260813_qdrant_dlq"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "ops_repos",
        "github_repo_id",
        existing_type=sa.Integer(),
        type_=sa.BigInteger(),
        existing_nullable=True,
    )
    op.alter_column(
        "ops_issues",
        "github_issue_id",
        existing_type=sa.Integer(),
        type_=sa.BigInteger(),
        existing_nullable=True,
    )
    op.alter_column(
        "ops_pull_requests",
        "github_pr_id",
        existing_type=sa.Integer(),
        type_=sa.BigInteger(),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "ops_pull_requests",
        "github_pr_id",
        existing_type=sa.BigInteger(),
        type_=sa.Integer(),
        existing_nullable=True,
    )
    op.alter_column(
        "ops_issues",
        "github_issue_id",
        existing_type=sa.BigInteger(),
        type_=sa.Integer(),
        existing_nullable=True,
    )
    op.alter_column(
        "ops_repos",
        "github_repo_id",
        existing_type=sa.BigInteger(),
        type_=sa.Integer(),
        existing_nullable=True,
    )
