"""add first_review_at to ops_pull_requests

Revision ID: 20260724_pr_first_review_at
Revises: 20260715_init
Create Date: 2026-07-24 00:00:00.000000

Supabase source already has this column; backfill via
scripts/import_from_supabase.py (idempotent upsert).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260724_pr_first_review_at"
down_revision: Union[str, None] = "20260715_init"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "ops_pull_requests",
        sa.Column("first_review_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("ops_pull_requests", "first_review_at")
