# E0 · 证据命令全文台账（40 处置棒 · 2026-10-18 · 含 F3 唯一写动作）

> 工作目录：worktree t-orphan-cleanup（branch task/local-qdrant-orphan-points-cleanup · base origin/master 423ba71）
> 代理污染规避：Qdrant/PG 访问统一 `env -u http_proxy -u https_proxy -u all_proxy -u NO_PROXY -u no_proxy` 剥离
> 写动作面：仅 F3 `POST /collections/ops_knowledge/points/delete?wait=true`（显式 id 白名单 9 批）；其余全只读（GET/scroll/inspect/shasum/tar -tf/pytest/lint）

| # | 证据文件 | 命令（全文/形态） |
|---|----------|------------------|
| E1 | e01_docker_inspect_containers.json | `docker inspect ops-desk-api-qdrant-1 ops-desk-api-db-1` |
| E2 | e02_snapshot_create.json | `curl -sS -X POST http://127.0.0.1:6333/collections/ops_knowledge/snapshots`（代理剥离） |
| E3 | e03_snapshot_list.json | `curl -sS http://127.0.0.1:6333/collections/ops_knowledge/snapshots`（代理剥离） |
| E4/E5 | e04_backup_tar_listing.txt · e05_backup_ledger.txt | `curl -sS -o backups/local_qdrant_orphan_cleanup_20261018T005320Z/<snapshot> http://127.0.0.1:6333/collections/ops_knowledge/snapshots/<snapshot>` → `stat -f%z` · `shasum -a 256` · `tar -tf <备份>\|head -15` |
| E6/E7 | e06_dryrun_scroll_ids_raw.json · e07_dryrun_verify.txt | python3 stdlib urllib（ProxyHandler({}) 剥离）stdin 一次性脚本：POST /collections/ops_knowledge/points/scroll 循环 {"limit":1000,"with_payload":false,"with_vector":false} 至 next_page_offset=null（9 页）→ 与 e04 基准逐集 diff |
| E8/E9/E10 | e08_collections_before.json · e09_delete_batches_log.json · e10_collections_after.json | ①GET /collections（删除前基线）②**写**：POST /collections/ops_knowledge/points/delete?wait=true body {"points":[<批次显式 id>]} ×9 批（≤1000/批 · 逐批台账）③GET /collections（删除后对照） |
| E11 | e11_collection_after_delete.json | `curl -sS http://127.0.0.1:6333/collections/ops_knowledge`（删后 points_count=0 实证） |
| — | reports/vector_waterline_local_20261018T005534Z.yaml | `DATABASE_URL='postgresql+asyncpg://ops:ops_password@localhost:5432/opsdesk' uv run --extra dev python scripts/check_vector_waterline.py --env local`（代理剥离 · 脚本 :211 asyncpg→psycopg 自转） |
| — | reports/vector_waterline_local_20261018T005444Z.yaml | 同上首跑未注入 DATABASE_URL → degraded（PG 面无实证）如实留档 |

**备份二进制**：`backups/local_qdrant_orphan_cleanup_20261018T005320Z/ops_knowledge-7885642805251913-2026-10-18-00-53-20.snapshot`（82,857,984 B · sha256 270b02bd419d1e4a1a94664bc576844467639b65f3bc4838934d567838692e7f）—— **untracked 留本机，不入 git**。
