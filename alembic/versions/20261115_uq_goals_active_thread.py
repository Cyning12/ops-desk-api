"""uq_ops_goals_active_thread 部分唯一索引（P1-T4 · issue #396）

07-p1-goal-design §3 platform 修正③：1 thread : 1 非终态 goal 的 DB 执行面。
部分唯一索引 (tenant_id, thread_id) WHERE status IN ('active','paused')——
终态行（done/abandoned）不占位，同 thread 换目标=人工废弃+懒创建新行（O-3）。
懒创建竞态由 store.resolve_goal_for_thread 的 IntegrityError 重读消化（T1）。

回退=关闸 + 回撤迁移互不影响（07 §5 T4 红线）。

Revision ID: 20261115_uq_goals_active_thread
Revises: 20261114_drop_legacy_chat_tables
Create Date: 2026-11-15
"""

from alembic import op

revision = "20261115_uq_goals_active_thread"
down_revision = "20261114_drop_legacy_chat_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "uq_ops_goals_active_thread",
        "ops_goals",
        ["tenant_id", "thread_id"],
        unique=True,
        postgresql_where="status IN ('active','paused')",
    )


def downgrade() -> None:
    op.drop_index("uq_ops_goals_active_thread", table_name="ops_goals")
