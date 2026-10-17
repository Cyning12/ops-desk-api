# E0 · 证据命令全文台账（40 实证棒 · 2026-10-17 · 全只读）

> 工作目录：worktree t-local-data-audit（branch task/local-vector-data-state-audit）
> 代理污染规避：Qdrant 访问统一 `env -u http_proxy -u https_proxy -u all_proxy NO_PROXY=` 剥离（承 123538Z 降级先例教训）
> 全程零写动作：SQL 仅 SELECT/pg_stat/pg_class 只读函数；Qdrant 仅 GET collection + POST points/scroll；docker 仅 inspect/ps/exec ls

| # | 证据文件 | 命令（全文） |
|---|----------|--------------|
| E1 | e01_docker_inspect_containers.json | `docker inspect ops-desk-api-db-1 ops-desk-api-qdrant-1`（解析 Created/State/Mounts） |
| E1b | e01b_volumes.txt · e01b_volume_inspect.json | `docker volume ls | grep ops-desk-api` · `docker volume inspect ops-desk-api_pgdata ops-desk-api_qdrant_data` |
| E2 | e02_pg_queries.txt | `docker exec -i ops-desk-api-db-1 psql -U ops -d opsdesk -x`：SELECT count(*) FROM ops_knowledge_chunks；SELECT * FROM alembic_version；SELECT count(*) FROM ops_qdrant_dlq；SELECT stats_reset,xact_commit,xact_rollback,tup_inserted,tup_updated,tup_deleted FROM pg_stat_database WHERE datname='opsdesk'；SELECT relname,n_tup_ins,n_tup_upd,n_tup_del,n_live_tup,n_dead_tup,last_vacuum,last_autovacuum,last_analyze,seq_scan,idx_scan FROM pg_stat_user_tables WHERE relname IN ('ops_knowledge_chunks','ops_qdrant_dlq','alembic_version')；SELECT relname,n_live_tup,n_tup_ins,n_tup_del FROM pg_stat_user_tables ORDER BY relname；SELECT pg_postmaster_start_time()；SELECT (pg_stat_file('PG_VERSION')).modification |
| E2b | e02b_pg_table_files.txt | 同上 psql：SELECT relname,oid,relfilenode,reltuples,relpages,relallvisible FROM pg_class WHERE relname IN (...)；SELECT relname,pg_relation_filepath(oid)；SELECT relname,(pg_stat_file(pg_relation_filepath(oid))).modification,pg_relation_size(oid),pg_total_relation_size(oid)；SELECT pg_relation_size('ops_knowledge_chunks_pkey')；SELECT count(*) FROM pg_indexes WHERE tablename='ops_knowledge_chunks' |
| E3 | e03_qdrant_collection_info.json | `curl -sS http://127.0.0.1:6333/collections/ops_knowledge` |
| E3b | e03b_qdrant_storage_files.txt | `docker exec ops-desk-api-qdrant-1 sh -c 'ls -la /qdrant/storage/ /qdrant/storage/collections/ /qdrant/storage/collections/ops_knowledge/0/ /qdrant/snapshots/'` |
| E3c | e03c_qdrant_wal_segments.txt | `docker exec ops-desk-api-qdrant-1 sh -c 'ls -la /qdrant/storage/collections/ops_knowledge/0/wal/ 及每个 segments/*/'` |
| E4 | e04_scroll_ids_raw.json · e04_sample_payloads_raw.json · e04_scroll_stats.txt | 一次性只读脚本（python3 stdlib urllib · ProxyHandler({}) 剥离代理 · 脚本走 stdin 不落码文件）：①POST /collections/ops_knowledge/points/scroll 循环 {"limit":1000,"with_payload":false,"with_vector":false} 至 next_page_offset=null 收集全量 id（9 页）；②排序后取头 50（1..50）/中 50（4263..4312）/尾 50（8525..8593）共 150 id；③POST points/scroll {"limit":200,"with_payload":true,"with_vector":false,"filter":{"must":[{"has_id":[...150 id]}]}} 取样本 payload；④统计键集/source_type/repo/tenant_id/chunk_index 分布 |
