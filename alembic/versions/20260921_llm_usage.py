"""ops_llm_usage：LLM usage 按 run_id 聚合账本（llm-layer-hardening D4）

Revision ID: 20260921_llm_usage
Revises: 20260921_memory_facts_embedding
Create Date: 2026-09-21

**为什么不挂 FK**：run_id 双口径并存（chat=ops_runs.id UUID /
lg_rag=uuid4().hex），无共同父表可挂 → text + surface 区分。
**为什么不存金额**：成本公式钉死在查询/导出侧（usage × price_table_v1.yaml
占位价 · E5），表内只存 token 计数与模型名，不存 prompt/answer 正文。
**为什么不写 0 假账**：provider 未回 usage 末帧 = 无行；有行即真实末帧。
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260921_llm_usage"
down_revision: str | None = "20260921_memory_facts_embedding"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS ops_llm_usage (
            id                   uuid        PRIMARY KEY,
            run_id               text,
            surface              text        NOT NULL DEFAULT 'background',
            task_type            text,
            provider             text        NOT NULL DEFAULT '',
            model                text        NOT NULL DEFAULT '',
            prompt_tokens        integer     NOT NULL,
            completion_tokens    integer     NOT NULL,
            cached_input_tokens  integer     NOT NULL DEFAULT 0,
            attempts             integer     NOT NULL DEFAULT 1,
            created_at           timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    # 按 run 聚合（这个 run 的 answer+grader+extract 合计）
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_ops_llm_usage_run_id "
        "ON ops_llm_usage (run_id)"
    )
    # 按入口面 + 时间扫描（成本盘点）
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_ops_llm_usage_surface_created "
        "ON ops_llm_usage (surface, created_at)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_ops_llm_usage_surface_created")
    op.execute("DROP INDEX IF EXISTS idx_ops_llm_usage_run_id")
    op.execute("DROP TABLE IF EXISTS ops_llm_usage")
