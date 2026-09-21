"""ops_session_summaries：会话历史真摘要缓存表（session-summary-fallback D2 · C1 独立表）

Revision ID: 20260922_session_summaries
Revises: 20260922_memory_kind_preference
Create Date: 2026-09-22

**为什么独立表**：摘要与原文 SoT（ops_lg_rag_turns / ops_runs）物理分表——
写回 turns 表会污染原文（摘要的摘要失真复利），C2 方案弃选。
**为什么 key 含内容哈希**：只用 (thread_id, 序号) 会在窗口滑动后命中旧
摘要 = 缓存污染静默错；chunk_hash = sha256(prompt_version + model + chunk
turns canonical JSON)，内容变 → hash 变 → 自然 miss，**无主动失效逻辑**。
唯一约束 (thread_id, chunk_hash)：并发同 key 双生成先写赢，后者冲突容忍。
**零数据迁移**：纯新表，存量无数据义务。
**回滚安全**：SESSION_SUMMARY_ENABLED 默认关 · off 态不读不写本表 →
downgrade = drop table 即安全（回退 = 关开关，零代码零迁移；缓存表留库
无害）。
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260922_session_summaries"
down_revision: str | None = "20260922_memory_kind_preference"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS ops_session_summaries (
            id              uuid         PRIMARY KEY,
            thread_id       varchar(255) NOT NULL
                            REFERENCES ops_lg_rag_threads(id) ON DELETE CASCADE,
            chunk_hash      varchar(64)  NOT NULL,
            summary         text         NOT NULL,
            prompt_version  varchar(32)  NOT NULL,
            model           varchar(255) NOT NULL DEFAULT '',
            turn_count      integer      NOT NULL,
            source          varchar(16)  NOT NULL DEFAULT 'llm',
            created_at      timestamptz  NOT NULL DEFAULT now(),
            CONSTRAINT uq_ops_session_summaries_thread_chunk
                UNIQUE (thread_id, chunk_hash)
        )
        """
    )


def downgrade() -> None:
    # 回滚安全：SESSION_SUMMARY_ENABLED 默认关 · off 态不读不写 → drop 安全；
    # 回退 = 关开关（零代码零迁移），缓存表留库无害。
    op.execute("DROP TABLE IF EXISTS ops_session_summaries")

