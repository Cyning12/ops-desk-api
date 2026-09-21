"""ops_hitl_requests：人工审批申请（HITL）落库

Revision ID: 20260920_hitl_requests
Revises: 20260919_capability_receipts
Create Date: 2026-09-20

**为什么必须落库，不能只打在状态里**：

``prefix_touch_required`` 的含义是"要满足这一步，得重跑一个**已执行**的步骤"。
按 Q8 §2.2，已执行步骤的 ``(tool, args)`` 决定幂等键 —— 改它就是一次**新的写**。
所以这不是"要不要做"的技术选择，是"谁批准一次新的写"的授权问题。
授权决策必须**跨实例、跨重启可查**：

- 进程内的字典重启即丢 ⇒ 申请静默消失，没人知道有人在等；
- 而"申请丢了"和"没人申请过"在观测上长得一模一样。

表里**刻意记下恢复现场所需的最小集合**：``thread_id`` / ``checkpoint_id`` /
``run_id`` / ``unlock_subtask_id``。审批通过 = 授权把 ``unlock_subtask_id``
那一步从不可变前缀里**解锁**，于是可恢复点回退到它，从那里重跑。
"""

from typing import Sequence, Union

from alembic import op

revision: str = "20260920_hitl_requests"
down_revision: Union[str, None] = "20260919_capability_receipts"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS ops_hitl_requests (
            id                 varchar(64)   PRIMARY KEY,
            run_id             varchar(64)   NOT NULL,
            thread_id          varchar(255)  NOT NULL,
            checkpoint_id      varchar(255),
            tenant_id          varchar(64)   NOT NULL DEFAULT '',
            subtask_id         varchar(128)  NOT NULL DEFAULT '',
            blocked_by         varchar(64)   NOT NULL DEFAULT '',
            unlock_subtask_id  varchar(128)  NOT NULL DEFAULT '',
            reason             text          NOT NULL DEFAULT '',
            detail             text          NOT NULL DEFAULT '',
            payload            jsonb         NOT NULL DEFAULT '{}'::jsonb,
            status             varchar(16)   NOT NULL DEFAULT 'pending',
            decision_by        varchar(128),
            decision_note      text,
            decided_at         timestamptz,
            created_at         timestamptz   NOT NULL DEFAULT now(),
            updated_at         timestamptz   NOT NULL DEFAULT now(),
            CONSTRAINT ck_ops_hitl_status CHECK (
                status IN ('pending', 'approved', 'rejected', 'expired')
            )
        )
        """
    )
    # 「有哪些在等审批」是运维最常问的一句 —— 单独给索引，别让它走全表扫
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_ops_hitl_status_created "
        "ON ops_hitl_requests (status, created_at)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_ops_hitl_run "
        "ON ops_hitl_requests (run_id)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_ops_hitl_run")
    op.execute("DROP INDEX IF EXISTS idx_ops_hitl_status_created")
    op.execute("DROP TABLE IF EXISTS ops_hitl_requests")
