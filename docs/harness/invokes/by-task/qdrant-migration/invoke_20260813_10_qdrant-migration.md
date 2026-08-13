# Invoke · 10-task · qdrant-migration

| 字段 | 值 |
|------|-----|
| **hat** | 10-task（00 统筹起草） |
| **task_slug** | `qdrant-migration` |
| **日期** | 2026-08-13 |
| **分支** | `task/qdrant-migration` |
| **上游** | SPEC v1.1 · HG-SPEC-SIGNOFF=approved（维护者签收） |

## 摘要

- 落盘 `docs/tasks/active/task_qdrant_migration.md`
- 闸：`HG-TASK-DRAFT` / `HG-AUDIT-R1` = **pending**（不代签）
- 范围对齐 SPEC：fio → on_disk HNSW → hydrate → 影子写 → Flag；默认读仍 pgvector

## 下一棒

1. 维护者签 `HG-TASK-DRAFT`（或指示代签）  
2. **20-task-audit** → 人签 `HG-AUDIT-R1`  
3. 后方可 30（首步 fio）
