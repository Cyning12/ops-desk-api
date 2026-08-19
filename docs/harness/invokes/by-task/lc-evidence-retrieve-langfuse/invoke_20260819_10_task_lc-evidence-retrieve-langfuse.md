# Invoke：10-task · lc-evidence-retrieve-langfuse

> **用途**：轻量 10-task 快照。不实现代码、不签发 `HG-AUDIT-R1`。

---

## 元信息表（必填）

| 字段 | 值 |
|------|-----|
| hat_id | 10-task |
| task_slug | `lc-evidence-retrieve-langfuse` |
| freeze_id | — |
| task_paths | `docs/tasks/active/task_lc_evidence_retrieve_langfuse.md` |
| related_review_or_none | 无 |
| git_branch | `task/lc-evidence-retrieve-langfuse` |
| worktree_root | `.` |
| created_utc_or_local | 2026-08-19 |
| notes | retrieve 内 embed/rerank 缺 generation；对齐 answer/grader；闸 pending |

---

## 可复制 Prompt 快照

````text
你是 ops-desk-api 仓的 10-task Agent。Open Folder = 本仓根。
建议分支 task/lc-evidence-retrieve-langfuse（实现时再切；本帽只写 task）。

身份与禁止
- 把「lc_evidence retrieve 内 embed/rerank 补 Langfuse generation」写成可验收轻量 task。
- 不改 retrieve.py 实现、不签发 HG-AUDIT-R1。
- 不写绝对本机路径。

必须产出
- docs/tasks/active/task_lc_evidence_retrieve_langfuse.md
- 本 invoke

字段
- task_slug = lc-evidence-retrieve-langfuse
- required_invoke_hats = 10,30
- invoke_retention_profile = default
- graph_change_layer = none
- wiki_delta = n/a + note
- 闸：HG-TASK-DRAFT / HG-AUDIT-R1 = pending；HG-GRAPH-MODULES = approved

范围
- retrieve.py：embed 与（可选）rerank 用 trace_span(run_type=llm, model=...)
- 复用 app.ops.tracing；不新造开关
- pytest mock；本机 UI 为人工项

非范围
- 默认不改 Chat rag_nodes（除非闸明示）
- 不升 Langfuse SDK v4、不改 hybrid_recall / graph.py
````

---

## 交付摘要

- **验证命令**：`npx @cyning/harness task lint --file docs/tasks/active/task_lc_evidence_retrieve_langfuse.md`
- **变更路径**：task 文件 + 本 invoke
- **下一棒**：维护者签 `HG-TASK-DRAFT`（确认是否同步 Chat）→ 20 或签 `HG-AUDIT-R1` → 切 `task/lc-evidence-retrieve-langfuse` 做 30

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-08-19 | 10-task 起草 |
