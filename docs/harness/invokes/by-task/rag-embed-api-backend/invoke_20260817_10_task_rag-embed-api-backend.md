# Invoke：10-task · rag-embed-api-backend

> **用途**：10-task 快照（自 workspace 总单复制入本仓）。不实现业务代码以外的关账。

---

## 元信息表（必填）

| 字段 | 值 |
|------|-----|
| hat_id | 10-task |
| task_slug | `rag-embed-api-backend` |
| freeze_id | — |
| task_paths | `docs/tasks/active/task_rag_embed_api_backend.md` |
| related_review_or_none | 无（10 时）；随后 20 → `docs/harness/reviews/task_rag_embed_api_backend_audit_R1_20260817.md` |
| git_branch | `task/rag-embed-api-backend` |
| worktree_root | `.` |
| created_utc_or_local | 2026-08-17 |
| notes | 查询 embed 默认 SiliconFlow ApiEmbedder；消本地 bge-m3 冷启动；禁改 graph.py |

---

## 可复制 Prompt 快照

````text
你是 ops-desk-api 仓的 10-task Agent。Open Folder = 本仓根。分支 task/rag-embed-api-backend。

身份与禁止
- 自 workspace 总单复制/对齐 active task：查询路径默认 ApiEmbedder。
- 不改 embedder 业务实现、不签发闸（由后续代签流程）。
- 不写绝对本机路径（跨仓用 ops-desk-workspace/ 相对表述）。

必须产出
- docs/tasks/active/task_rag_embed_api_backend.md
- 本 invoke

字段
- task_slug = rag-embed-api-backend
- required_invoke_hats = 10,30
- invoke_retention_profile = default
- graph_change_layer = G-L1
- wiki_delta = n/a + note
- 闸：HG-TASK-DRAFT / HG-AUDIT-R1 初为 pending；HG-GRAPH-MODULES = approved

范围
- get_query_embedder：RAG_EMBED_BACKEND 默认 siliconflow → ApiEmbedder
- 接线 retrieve.py + rag_nodes.py
- 模型 BAAI/bge-m3；禁隐式回落本地 ST
- .env.example + workspace 生产 compose 透传

非范围
- 不重灌、不改维、不改 graph.py、不改 ingest 默认远程
````

---

## 交付摘要

- **验证命令**：`npx @cyning/harness task lint --file docs/tasks/active/task_rag_embed_api_backend.md` → PASS（绝对路径亦可）
- **变更路径**：task 文件 + 本 invoke
- **下一棒**：20 audit → 代签闸 → verify → 30/40

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-08-17 | 10-task：workspace 复制入 api active |
