"""ops_knowledge_chunks：RAG 向量检索表（R-1）

Revision ID: 20260808_rag_chunks
Revises: 20260724_pr_first_review_at
Create Date: 2026-08-08

契约锚点：ops-desk-workspace/docs/contracts/rag-knowledge-contract-v1.md
- Q2 组合键 (repo, source_type, source_id, chunk_index)；metadata jsonb 管过滤与引用卡片
- Q3 bge-m3@1024 自部署 → vector(1024) + HNSW cosine（维度变更须重建表 + 全量重灌）
- 混合召回：fts_tokens tsvector + GIN（关键词路；RRF 融合在应用层）

与丢失初版的差异（人审点）：
- 补 metadata jsonb（初版缺失，契约 Q2 要求的 module_tag/updated_at/html_url 落此）
- source_type 不加 CHECK 硬枚举：为评论等扩展留余地
- fts_tokens 用 GENERATED 列替代触发器（少一个 function/trigger 活动部件）；
  配置用 'simple'：'english' 的词干化会把中文切成废 token，中文召回靠契约 Q6 的
  query 侧扩展先手，不靠 tsvector
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260808_rag_chunks"
down_revision: Union[str, None] = "20260724_pr_first_review_at"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute(
        """
        CREATE TABLE ops_knowledge_chunks (
            id           bigserial PRIMARY KEY,
            repo         text        NOT NULL,
            source_type  text        NOT NULL,
            source_id    text        NOT NULL,
            chunk_index  integer     NOT NULL,
            content      text        NOT NULL,
            metadata     jsonb       NOT NULL DEFAULT '{}'::jsonb,
            images       jsonb       NOT NULL DEFAULT '[]'::jsonb,
            content_hash text        NOT NULL,
            embedding    vector(1024) NOT NULL,
            embedded_at  timestamptz NOT NULL DEFAULT now(),
            fts_tokens   tsvector
                GENERATED ALWAYS AS (to_tsvector('simple'::regconfig, content)) STORED,
            CONSTRAINT uq_ops_knowledge_chunks_key
                UNIQUE (repo, source_type, source_id, chunk_index)
        )
        """
    )
    op.execute(
        "CREATE INDEX idx_ops_knowledge_chunks_source "
        "ON ops_knowledge_chunks (repo, source_type, source_id)"
    )
    op.execute(
        "CREATE INDEX idx_ops_knowledge_chunks_embedding_hnsw "
        "ON ops_knowledge_chunks USING hnsw (embedding vector_cosine_ops)"
    )
    op.execute(
        "CREATE INDEX idx_ops_knowledge_chunks_fts_gin "
        "ON ops_knowledge_chunks USING gin (fts_tokens)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS ops_knowledge_chunks")
