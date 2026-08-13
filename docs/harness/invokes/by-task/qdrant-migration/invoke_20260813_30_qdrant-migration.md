# Invoke · 30-execute · qdrant-migration

| 字段 | 值 |
|------|-----|
| **hat** | 30 |
| **task_slug** | `qdrant-migration` |
| **日期** | 2026-08-13 |
| **分支** | `task/qdrant-migration` |
| **SPEC** | `docs/spec/SPEC-qdrant-migration_v1.md`（v1.1） |

## 人工闸扫描（GATE_VERIFY · 首输出）

| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---------------|--------------|-----------------|--------|-----------|------------|
| HG-TASK-DRAFT | approved | approved（00 代签） | Y | N | Y |
| HG-AUDIT-R1 | approved | approved（00 代签 · C1–C3） | Y | Y | Y |
| HG-GRAPH-MODULES | approved（`l1/01_modules.md`） | — | Y | Y | Y |

reviews：`docs/harness/reviews/task_qdrant_migration_audit_R1_20260813.md` 存在且 R1 conditional_pass + 00 代签接受 C1–C3？ **是**

pre-30 invoke：`required ∩ {10,20,00}` 齐全？ **是**（00/10/20 已落盘）

结论：**可进入读码/改码**

## 交付摘要（P0）

- docker-compose：Qdrant **v1.13.6** + mem_limit 说明；默认 `RAG_VECTOR_BACKEND=pgvector`
- `scripts/qdrant_migrate/`：fio / create_collection / export / bulk_upsert / payload indexes / reconcile / check_dlq / bench 骨架
- 应用：`backend.py` Flag+即时降级；`retrievers/` + hydrate；`retrieve` 接线；`ingest` 影子写（commit 后 enqueue upsert/delete）+ `ops_qdrant_dlq` alembic
- 单测：`tests/test_rag_qdrant_backend.py`
- 图谱：`docs/_tech_graph/l1/01_modules.md` 增 `rag` 模块

## P1 / 未在本机完成

- 真实 fio 摸盘、80 万灌库、金样 vs `reports/r4-2.yaml`：脚本具备；本机可能无生产盘 → 实测记录可写「未在本机跑通原因」（`bench_hnsw.py --skip-live`）
- DLQ cron replayer：表已建；重放 worker 可后续波次

## 验证

- `ruff check`（本波改动文件）：PASS
- `pytest tests/test_rag_qdrant_backend.py`：9 passed
- `pytest tests/test_rag_*.py`：51 passed
- `npx @cyning/harness verify --task docs/tasks/active/task_qdrant_migration.md`：**VERIFY: PASS**（HG-AUDIT-R1=approved）
- 说明：`tests/test_chat_router.py::test_stream_success` 现网失败（error 事件，与本波 RAG 无关）

## 下一棒

压测/对账过门禁后再议切流；关账归 00。
