"""ops_memory_facts 加 embedding 列：事实型记忆 P1（向量语义召回）

Revision ID: 20260921_memory_facts_embedding
Revises: 20260921_memory_facts
Create Date: 2026-09-21

**nullable 不回填**：既有行 embedding = NULL → 只走确定性通路即正确
（SPEC-P1 §2 D1）；回填批处理另开 task。向量通路任何失败都回退
确定性召回（memory_vector_degraded），不拖垮请求。
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260921_memory_facts_embedding"
down_revision: str | None = "20260921_memory_facts"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # bge-m3@1024（与 ops_knowledge_chunks.embedding / rag ingest EMBEDDING_DIM 同源）；
    # vector 扩展由 20260715_init_ops_desk 建库时保证
    op.execute(
        "ALTER TABLE ops_memory_facts "
        "ADD COLUMN IF NOT EXISTS embedding vector(1024)"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE ops_memory_facts DROP COLUMN IF EXISTS embedding")
