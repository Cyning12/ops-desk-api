"""ops_memory_episodes：情景记忆库（host-v1-episodic-memory-feedback D1 · Q1 run 级）

Revision ID: 20260923_memory_episodes
Revises: 20260922_session_summaries
Create Date: 2026-09-23

**为什么独立表（U4 铁律）**：经验≠事实——事实是主体绑定的可验证标量
（ops_memory_facts），经验是 run 级模式归纳（plan 摘要+工具序列+成败
标签）；判据、存储、召回路径全部分立，**零互写**断言化守护。
**为什么 run 级**（SPEC Q1 裁定）：归因载体天然（V1-A 主体绑定 / run_events
均以 run 为轴）· 写入频次低（每 run 至多 1 条）· 聚类噪声小；subtask 级
写入放大且单 subtask 上下文不足以构成「经验」，弃选。
**零数据迁移**：纯新表，存量无数据义务。
**回滚安全**：MEMORY_EPISODES_WRITE_ENABLED / MEMORY_EPISODES_ENABLED
双开关默认关 · off 态不读不写本表 → downgrade = drop table 即安全
（回退 = 关开关，零代码零迁移；承 session_summaries 先例）。
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260923_memory_episodes"
down_revision: str | None = "20260922_session_summaries"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS ops_memory_episodes (
            id                  uuid         PRIMARY KEY,
            tenant_id           text         NOT NULL,
            run_id              text         NOT NULL,
            task_domain         text         NOT NULL,
            context_fingerprint varchar(64)  NOT NULL,
            plan_summary        text         NOT NULL,
            tool_sequence       jsonb        NOT NULL,
            outcome             text         NOT NULL,
            failure_class       text,
            status              text         NOT NULL DEFAULT 'active',
            created_at          timestamptz  NOT NULL DEFAULT now(),
            CONSTRAINT ck_ops_memory_episodes_outcome CHECK (
                outcome IN ('success', 'failure', 'partial')
            ),
            CONSTRAINT ck_ops_memory_episodes_status CHECK (
                status IN ('active', 'revoked')
            )
        )
        """
    )
    # 召回主谓词：(tenant, outcome, status) —— 装配面相似成功经验召回
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_ops_memory_episodes_recall "
        "ON ops_memory_episodes (tenant_id, outcome, status)"
    )
    # 聚类键 + 召回指纹匹配（D3/D4）
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_ops_memory_episodes_fingerprint "
        "ON ops_memory_episodes (context_fingerprint)"
    )
    # revoke_by_run 一键纠错溯源
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_ops_memory_episodes_run "
        "ON ops_memory_episodes (run_id)"
    )


def downgrade() -> None:
    # 回滚安全：双开关默认关 · off 态不读不写 → drop 安全；
    # 回退 = 关开关（零代码零迁移），承 session_summaries 先例。
    op.execute("DROP INDEX IF EXISTS idx_ops_memory_episodes_run")
    op.execute("DROP INDEX IF EXISTS idx_ops_memory_episodes_fingerprint")
    op.execute("DROP INDEX IF EXISTS idx_ops_memory_episodes_recall")
    op.execute("DROP TABLE IF EXISTS ops_memory_episodes")
