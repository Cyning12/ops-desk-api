"""ops_schedule_fires.created_at：抢占时刻列（P3-T3 · issue #23 · R10 启动补链超时判据）

Revision ID: 20261116_ops_fires_created_at
Revises: 20261116_ops_schedules
Create Date: 2026-11-16

启动补链（14 §1.5 · R10）须区分「崩溃孤儿」与「补跑刚抢占」：判据 =
status=claimed AND run_id IS NULL AND created_at ≤ now - CLAIM_STALE_SECONDS。
用 planned_fire_at 会把 fire_once 补跑（计划时刻本就在过去）误判为超时 →
双火窗口。T2 建表未含抢占时刻列，本迁移补齐（最小加列 · 如实登记偏差 D5）。
存量行回填 now() 语义安全：T3 worker 上线前无 claimed 台账行。
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20261116_ops_fires_created_at"
down_revision: str | None = "20261116_ops_schedules"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE ops_schedule_fires
        ADD COLUMN IF NOT EXISTS created_at timestamptz NOT NULL DEFAULT now()
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE ops_schedule_fires DROP COLUMN IF EXISTS created_at")
