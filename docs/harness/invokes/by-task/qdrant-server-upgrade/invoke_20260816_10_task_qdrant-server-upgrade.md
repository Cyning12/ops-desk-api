# Invoke：10-task · qdrant-server-upgrade

> **用途**：轻量 10-task 快照。不实现代码、不签发 `HG-AUDIT-R1`。

---

## 元信息表（必填）

| 字段 | 值 |
|------|-----|
| hat_id | 10-task |
| task_slug | `qdrant-server-upgrade` |
| freeze_id | — |
| task_paths | `docs/tasks/active/task_qdrant_server_upgrade.md` |
| related_review_or_none | 无 |
| git_branch | `task/qdrant-server-upgrade` |
| worktree_root | `.` |
| created_utc_or_local | 2026-08-16 |
| notes | 升 server 1.19.x 对齐 client；本机先于生产；闸 pending |

---

## 可复制 Prompt 快照

````text
你是 ops-desk-api 仓的 10-task Agent。Open Folder = 本仓根。分支 task/qdrant-server-upgrade。

身份与禁止
- 把「本机+生产升 Qdrant server」写成可验收轻量 task。
- 不改 compose、不部署、不签发 HG-AUDIT-R1。
- 不写绝对本机路径。

必须产出
- docs/tasks/active/task_qdrant_server_upgrade.md
- 本 invoke

字段
- task_slug = qdrant-server-upgrade
- required_invoke_hats = 10,30
- invoke_retention_profile = minimal
- graph_change_layer = none
- wiki_delta = n/a + note
- 闸：HG-TASK-DRAFT / HG-AUDIT-R1 = pending；HG-GRAPH-MODULES = approved

范围
- docker-compose.yml 与 workspace deploy/docker-compose.prod.yml 镜像 v1.13.6 → v1.19.x
- SPEC / cutover 版本句
- 本机先升；volume 不兼容则按 cutover 从 PG 重建
- 生产可切 pgvector 保底

非范围
- 不改 qdrant-client、不改 graph、不改默认 RAG_VECTOR_BACKEND
````

---

## 交付摘要

- **验证命令**：`npx @cyning/harness task lint --file docs/tasks/active/task_qdrant_server_upgrade.md`
- **变更路径**：task 文件 + 本 invoke
- **下一棒**：维护者签 `HG-TASK-DRAFT` → 20 或直接签 `HG-AUDIT-R1` → 30

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-08-16 | 10-task 起草 |
