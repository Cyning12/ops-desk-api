"""ops_schedules + ops_schedule_fires：Schedule 双表（P3-T2 · issue #23 · 契约真源 15 §1.2/§4.1）

Revision ID: 20261116_ops_schedules
Revises: 20261115_uq_goals_active_thread
Create Date: 2026-11-16

P3-T2 只建表 + REST 面；worker 点火循环在 T3。tenant_id 必填（freeze F1-F6 ·
R7 租户谓词）。ops_schedules.thread_id 不加 FK（fire 时不存在则 worker 自建 ·
15 §1.2）；ops_schedule_fires.schedule_id 不加 FK（schedule 删除不级联 ·
台账保留 · 15 §4.1）。uq_ops_schedule_fires_planned(schedule_id,
planned_fire_at) 为幂等键，支撑 T3 INSERT ... ON CONFLICT DO NOTHING（§4.2）。
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20261116_ops_schedules"
down_revision: str | None = "20261115_uq_goals_active_thread"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS ops_schedules (
            schedule_id      uuid          PRIMARY KEY,
            tenant_id        varchar(64)   NOT NULL,
            user_id          uuid          NOT NULL REFERENCES ops_users(id) ON DELETE CASCADE,
            thread_id        varchar(255)  NOT NULL,
            name             varchar(120)  NOT NULL,
            instruction      text          NOT NULL,
            schedule_kind    varchar(16)   NOT NULL,
            run_at           timestamptz   NULL,
            interval_seconds integer       NULL,
            time_of_day      varchar(5)    NULL,
            timezone         varchar(64)   NOT NULL DEFAULT 'Asia/Shanghai',
            next_fire_at     timestamptz   NOT NULL,
            catchup_policy   varchar(16)   NOT NULL DEFAULT 'fire_once',
            status           varchar(16)   NOT NULL DEFAULT 'active',
            fire_count       integer       NOT NULL DEFAULT 0,
            max_fires        integer       NULL,
            last_fired_at    timestamptz   NULL,
            created_at       timestamptz   NOT NULL DEFAULT now(),
            updated_at       timestamptz   NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_ops_schedules_next_fire "
        "ON ops_schedules (status, next_fire_at)"
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS ops_schedule_fires (
            id               uuid          PRIMARY KEY DEFAULT gen_random_uuid(),
            schedule_id      uuid          NOT NULL,
            tenant_id        varchar(64)   NOT NULL,
            planned_fire_at  timestamptz   NOT NULL,
            run_id           varchar(64)   NULL,
            status           varchar(16)   NOT NULL DEFAULT 'claimed',
            fired_at         timestamptz   NULL
        )
        """
    )
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_ops_schedule_fires_planned "
        "ON ops_schedule_fires (schedule_id, planned_fire_at)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_ops_schedule_fires_run_id "
        "ON ops_schedule_fires (run_id)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS ops_schedule_fires")
    op.execute("DROP TABLE IF EXISTS ops_schedules")
