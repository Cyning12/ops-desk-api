"""ops_capability_notes：受控写便签（stage-w-write-expand · Q1=S1 仓内落笔型写）

Revision ID: 20261105_capability_notes
Revises: 20260923_memory_episodes
Create Date: 2026-11-05

第二条真实窄写能力 ``ops.write.run_note`` 的落笔目标面（Q3 实扫结论：既有表无
适配面 → 新表 + 本迁移；义务随 task 修订表回填留痕）。

- ``(tenant_id, idempotency_key)`` 唯一约束：FP-4「重放不双写」的 DB 级兜底
  （幂等 store 进程丢失/跨实例漂移时仍然成立 · ON CONFLICT DO NOTHING 语义）；
- 行上带 ``approval_id``：A4 审计串链（审批决策 ↔ 执行结果可串链查询）。
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20261105_capability_notes"
down_revision: str | None = "20260923_memory_episodes"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS ops_capability_notes (
            id               uuid          PRIMARY KEY,
            capability_id    varchar(128)  NOT NULL,
            tenant_id        varchar(64)   NOT NULL,
            run_id           varchar(64)   NOT NULL,
            subtask_id       varchar(64)   NOT NULL DEFAULT '',
            approval_id      varchar(64)   NOT NULL DEFAULT '',
            note             text          NOT NULL,
            created_by       varchar(128)  NOT NULL DEFAULT '',
            idempotency_key  varchar(512)  NOT NULL,
            created_at       timestamptz   NOT NULL DEFAULT now(),
            CONSTRAINT uq_ops_capability_notes_tenant_key
                UNIQUE (tenant_id, idempotency_key)
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_ops_capability_notes_run "
        "ON ops_capability_notes (run_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_ops_capability_notes_approval "
        "ON ops_capability_notes (approval_id)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS ops_capability_notes")
