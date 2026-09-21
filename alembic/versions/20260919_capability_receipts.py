"""ops_capability_receipts / ops_capability_idempotency：副作用回执 + 幂等防重（W5）

Revision ID: 20260919_capability_receipts
Revises: 20260918_tenant_readonly
Create Date: 2026-09-19

两张表配套，缺一不可：

- ``ops_capability_receipts``：副作用以收据为真。写能力无论成败都落一行——
  一次"失败"的写可能已经在下游生效（超时 / 半成功），不留就无从对账。
- ``ops_capability_idempotency``：同一个幂等键不在本层发出两次请求。
  ``status='in_flight'`` 由 ``lease_expires_at`` 兜底——**没有租约，进程崩一次
  就会把该键永久卡死，而且是静默的**。

只落表结构；DB 版 store / sink 的实现是下一步（见工作区《能力注册表落地设计》）。
"""

from typing import Sequence, Union

from alembic import op

revision: str = "20260919_capability_receipts"
down_revision: Union[str, None] = "20260918_tenant_readonly"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS ops_capability_receipts (
            id               uuid          PRIMARY KEY,
            receipt_id       varchar(32)   NOT NULL,
            capability_id    varchar(128)  NOT NULL,
            side_effect      varchar(16)   NOT NULL,
            ok               boolean       NOT NULL,
            write_confirmed  boolean       NOT NULL DEFAULT false,
            user_id          varchar(64)   NOT NULL DEFAULT '',
            tenant_id        varchar(64)   NOT NULL DEFAULT '',
            subtask_id       varchar(64)   NOT NULL DEFAULT '',
            idempotency_key  varchar(512),
            captured         jsonb         NOT NULL DEFAULT '{}'::jsonb,
            error            text,
            created_at       timestamptz   NOT NULL DEFAULT now(),
            CONSTRAINT uq_ops_capability_receipts_receipt_id UNIQUE (receipt_id)
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_ops_capability_receipts_key "
        "ON ops_capability_receipts (tenant_id, idempotency_key)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_ops_capability_receipts_cap_created "
        "ON ops_capability_receipts (capability_id, created_at)"
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS ops_capability_idempotency (
            id                uuid          PRIMARY KEY,
            tenant_id         varchar(64)   NOT NULL,
            idempotency_key   varchar(512)  NOT NULL,
            capability_id     varchar(128)  NOT NULL DEFAULT '',
            status            varchar(16)   NOT NULL,
            lease_expires_at  timestamptz,
            attempts          integer       NOT NULL DEFAULT 1,
            receipt_id        varchar(32),
            created_at        timestamptz   NOT NULL DEFAULT now(),
            updated_at        timestamptz   NOT NULL DEFAULT now(),
            CONSTRAINT uq_ops_capability_idem_tenant_key
                UNIQUE (tenant_id, idempotency_key)
        )
        """
    )
    # 扫描"卡住的 in_flight"（运维对账 / 租约巡检）走这个索引
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_ops_capability_idem_inflight "
        "ON ops_capability_idempotency (status, lease_expires_at)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS ops_capability_idempotency")
    op.execute("DROP TABLE IF EXISTS ops_capability_receipts")
