# Invoke：10-task · siliconflow-rerank-api

> **用途**：轻量 10-task 快照。不实现代码、不签发 `HG-AUDIT-R1`。

---

## 元信息表（必填）

| 字段 | 值 |
|------|-----|
| hat_id | 10-task |
| task_slug | `siliconflow-rerank-api` |
| freeze_id | — |
| task_paths | `docs/tasks/active/task_siliconflow_rerank_api.md` |
| related_review_or_none | 无 |
| git_branch | `task/siliconflow-rerank-api` |
| worktree_root | `.` |
| created_utc_or_local | 2026-08-17 |
| notes | 生产 2C4G 本地 CE 不可用；精排改 SiliconFlow HTTP；闸 pending |

---

## 可复制 Prompt 快照

````text
你是 ops-desk-api 仓的 10-task Agent。Open Folder = 本仓根。分支 task/siliconflow-rerank-api。

身份与禁止
- 把「SiliconFlow API 精排替换本地 CrossEncoder」写成可验收轻量 task。
- 不改 reranker.py 实现、不签发 HG-AUDIT-R1。
- 不写绝对本机路径。

必须产出
- docs/tasks/active/task_siliconflow_rerank_api.md
- 本 invoke

字段
- task_slug = siliconflow-rerank-api
- required_invoke_hats = 10,30
- invoke_retention_profile = minimal
- graph_change_layer = none
- wiki_delta = n/a + note
- 闸：HG-TASK-DRAFT / HG-AUDIT-R1 = pending；HG-GRAPH-MODULES = approved

范围
- reranker 打分默认 POST SiliconFlow /v1/rerank
- 模型 RAG_RERANK_MODEL 默认 BAAI/bge-reranker-v2-m3
- 过滤策略保持 SPEC 方案 B；失败回退粗排 top-5
- RAG_RERANK_BACKEND=siliconflow|local

非范围
- 不升配、不强制全量金样、不改 graph.py、不改前端 120s
````

---

## 交付摘要

- **验证命令**：`npx @cyning/harness task lint --file docs/tasks/active/task_siliconflow_rerank_api.md`
- **变更路径**：task 文件 + 本 invoke
- **下一棒**：维护者签 `HG-TASK-DRAFT` → 20 或直接签 `HG-AUDIT-R1` → 30

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-08-17 | 10-task 起草 |
