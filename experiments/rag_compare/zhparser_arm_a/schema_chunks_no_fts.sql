-- 影子库建表：ops_knowledge_chunks（不含 fts_tokens 生成列）
-- 对齐 alembic 20260808_rag_chunks 业务列；先不建 fts GIN（由 add_fts_chinese.sql 补）
-- 前置：init_chinese_fts.sql（vector 扩展）
-- 用法：psql "$SHADOW_DSN" -f schema_chunks_no_fts.sql

CREATE TABLE IF NOT EXISTS ops_knowledge_chunks (
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
    CONSTRAINT uq_ops_knowledge_chunks_key
        UNIQUE (repo, source_type, source_id, chunk_index)
);

CREATE INDEX IF NOT EXISTS idx_ops_knowledge_chunks_source
    ON ops_knowledge_chunks (repo, source_type, source_id);

CREATE INDEX IF NOT EXISTS idx_ops_knowledge_chunks_embedding_hnsw
    ON ops_knowledge_chunks USING hnsw (embedding vector_cosine_ops);
