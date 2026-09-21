"""ops_memory_facts：事实型记忆 P0（写入闸 + 状态机 + 确定性召回）

Revision ID: 20260921_memory_facts
Revises: 20260920_hitl_requests
Create Date: 2026-09-21

**为什么不物理删**：「记错了怎么纠正 / 怎么遗忘」两问靠状态机承接——
superseded（同 key 新值取代）、revoked（按 source_run_id 批量纠错）、
expired（TTL 到点）。旧行全部留表，审计对账能回答"当时为什么这样答"。

**过期不可见是双保险**：召回 SQL 自带 ``expires_at`` 过滤，不依赖
sweep 任务存活；sweep 只是把过期行显式置 ``expired`` 便于盘点。

P0 刻意**不含 embedding 列**：向量召回是 P1，届时加列并复用
``RAG_VECTOR_BACKEND`` 双后端。
"""

from typing import Sequence, Union

from alembic import op

revision: str = "20260921_memory_facts"
down_revision: Union[str, None] = "20260920_hitl_requests"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS ops_memory_facts (
            id             uuid         PRIMARY KEY,
            tenant_id      text         NOT NULL,
            user_id        text         NOT NULL,
            key            text         NOT NULL,
            value          jsonb        NOT NULL,
            kind           text         NOT NULL DEFAULT 'fact',
            source_run_id  text,
            source_turn    integer,
            supersedes     uuid         REFERENCES ops_memory_facts(id) ON DELETE SET NULL,
            status         text         NOT NULL DEFAULT 'active',
            expires_at     timestamptz,
            created_at     timestamptz  NOT NULL DEFAULT now(),
            updated_at     timestamptz  NOT NULL DEFAULT now(),
            CONSTRAINT ck_ops_memory_facts_status CHECK (
                status IN ('active', 'superseded', 'revoked', 'expired')
            ),
            CONSTRAINT ck_ops_memory_facts_kind CHECK (kind = 'fact')
        )
        """
    )
    # 召回主谓词：(tenant, user, key, status) —— 每次装配都走它
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_ops_memory_facts_recall "
        "ON ops_memory_facts (tenant_id, user_id, key, status)"
    )
    # revoke_by_source 按源头批量纠错
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_ops_memory_facts_source_run "
        "ON ops_memory_facts (source_run_id)"
    )
    # sweep 只扫活跃行：部分索引（仓内 migration 为裸 SQL 风格，直接落 WHERE）
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_ops_memory_facts_expires_active "
        "ON ops_memory_facts (expires_at) WHERE status = 'active'"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_ops_memory_facts_expires_active")
    op.execute("DROP INDEX IF EXISTS idx_ops_memory_facts_source_run")
    op.execute("DROP INDEX IF EXISTS idx_ops_memory_facts_recall")
    op.execute("DROP TABLE IF EXISTS ops_memory_facts")
