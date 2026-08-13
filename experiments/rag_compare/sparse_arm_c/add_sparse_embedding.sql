-- C 臂影子列：bge-m3 lexical weights → sparsevec
-- 仅在本地 / 影子库执行；**不要**对生产库跑本脚本。
-- 维度 250002 = bge-m3 vocab；索引用内积（<#>/sparsevec_ip_ops）。
-- 幂等：列已存在则跳过 ADD；索引用 IF NOT EXISTS。

CREATE EXTENSION IF NOT EXISTS vector;

ALTER TABLE ops_knowledge_chunks
  ADD COLUMN IF NOT EXISTS sparse_embedding sparsevec(250002);

-- HNSW 内积：ORDER BY sparse_embedding <#> query ASC
CREATE INDEX IF NOT EXISTS idx_ops_knowledge_chunks_sparse_hnsw
  ON ops_knowledge_chunks
  USING hnsw (sparse_embedding sparsevec_ip_ops);

-- 自检（加列后应多为 NULL，重嵌后再跑）
-- SELECT count(*) AS total,
--        count(sparse_embedding) AS filled,
--        count(*) FILTER (WHERE sparse_embedding IS NULL) AS nulls
-- FROM ops_knowledge_chunks;
