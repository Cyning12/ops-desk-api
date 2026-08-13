#!/usr/bin/env bash
# 从主库 COPY 导出 ops_knowledge_chunks（排除 fts_tokens）→ 影子库导入。
#
# 环境变量（可选）：
#   PRIMARY_DSN  主库（默认 postgresql://ops:ops_password@localhost:5432/opsdesk）
#   SHADOW_DSN   影子库（默认 postgresql://ops:ops_password@localhost:5433/opsdesk）
#   CHUNKS_CSV   中间 CSV 路径（默认 /tmp/ops_knowledge_chunks_shadow.csv）
#
# 前置：影子库已执行 init_chinese_fts.sql + schema_chunks_no_fts.sql
# 后置：再执行 add_fts_chinese.sql
#
# 注意：本脚本只读主库（SELECT/COPY TO），不对 5432 做写操作。

set -euo pipefail

PRIMARY_DSN="${PRIMARY_DSN:-postgresql://ops:ops_password@localhost:5432/opsdesk}"
SHADOW_DSN="${SHADOW_DSN:-postgresql://ops:ops_password@localhost:5433/opsdesk}"
CHUNKS_CSV="${CHUNKS_CSV:-/tmp/ops_knowledge_chunks_shadow.csv}"

CHUNK_COLS="id, repo, source_type, source_id, chunk_index, content, metadata, images, content_hash, embedding, embedded_at"

echo "[shadow_copy] export from PRIMARY → ${CHUNKS_CSV}"
psql "$PRIMARY_DSN" -v ON_ERROR_STOP=1 -c "\\COPY (
  SELECT ${CHUNK_COLS}
  FROM ops_knowledge_chunks
) TO '${CHUNKS_CSV}' WITH CSV HEADER"

echo "[shadow_copy] import into SHADOW from ${CHUNKS_CSV}"
psql "$SHADOW_DSN" -v ON_ERROR_STOP=1 -c "\\COPY ops_knowledge_chunks (
  ${CHUNK_COLS}
) FROM '${CHUNKS_CSV}' WITH CSV HEADER"

COUNT="$(psql "$SHADOW_DSN" -tAc "SELECT count(*) FROM ops_knowledge_chunks")"
echo "[shadow_copy] done · shadow rows=${COUNT}"
