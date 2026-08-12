-- 影子库：灌库后再加 chinese 生成列 + GIN
-- 前置：schema_chunks_no_fts.sql + COPY 导入完成；init_chinese_fts.sql 已建 chinese 配置
-- 用法：psql "$SHADOW_DSN" -f add_fts_chinese.sql

ALTER TABLE ops_knowledge_chunks
  ADD COLUMN IF NOT EXISTS fts_tokens tsvector
  GENERATED ALWAYS AS (to_tsvector('chinese'::regconfig, content)) STORED;

CREATE INDEX IF NOT EXISTS idx_ops_knowledge_chunks_fts_gin
  ON ops_knowledge_chunks USING gin (fts_tokens);
