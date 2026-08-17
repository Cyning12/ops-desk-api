# Invoke：00 · siliconflow-rerank-api（统筹派发）

> **用途**：00 派发快照。00 **不实现**业务代码。30 验收机械通过后 **交维护者本地验收**，本波 **不 CLOSE**。

---

## 元信息表（必填）

| 字段 | 值 |
|------|-----|
| hat_id | 00 |
| task_slug | `siliconflow-rerank-api` |
| freeze_id | — |
| task_paths | `docs/tasks/active/task_siliconflow_rerank_api.md` |
| related_review_or_none | `docs/harness/reviews/task_siliconflow_rerank_api_audit_R1_20260817.md` |
| git_branch | `task/siliconflow-rerank-api` |
| worktree_root | `.` |
| created_utc_or_local | 2026-08-17 |
| notes | 维护者指示 00 统筹完成、子 agent 执行、人本地验收；00 不改 reranker 实现 |

---

## 可复制 Prompt 快照

````text
你是 ops-desk-api 仓的 00 统筹。Open Folder = 本仓根。分支 task/siliconflow-rerank-api。
task = docs/tasks/active/task_siliconflow_rerank_api.md

身份与禁止
- 只派发与闸扫描，不实现 app/ 业务代码。
- 不 CLOSE、不 git commit、不 push。
- 子 agent 验收通过后交给维护者本地验收。

派发顺序
1. 维护者「统筹完成」= 签 HG-TASK-DRAFT
2. 子 agent 20-task-audit → docs/harness/reviews/
3. 20 内容通过后再签 HG-AUDIT-R1
4. 子 agent 30（含 40）实现 + pytest mock
5. 00 机械核对 diff/测试后交人本地验收
````

---

## 派发计划

| 步 | 帽 | 执行者 | 产出 |
|---|---|---|---|
| 1 | 闸 | 00 | `HG-TASK-DRAFT=approved`（本会话维护者授权） |
| 2 | 20 | 子 agent | `docs/harness/reviews/task_siliconflow_rerank_api_audit_R1_20260817.md` |
| 3 | 闸 | 00 | 20 内容通过后 `HG-AUDIT-R1=approved` |
| 4 | 30+40 | 子 agent | 实现 + invoke + 自检结论；**不 commit** |
| 5 | 人 | 维护者 | 本地验收；通过后再 CLOSE/合入 |

---

## 交付摘要

## 交付摘要

- **验证命令**：00 复核 `.venv/bin/pytest tests/test_rag_reranker.py -q` → **17 passed**；`ruff check` → 0
- **变更路径**：见 30 invoke；workspace compose 透传落在 `chore/prod-env-hf-passthrough`（勿与 HF 文档混 commit 除非维护者同意）
- **下一棒**：维护者本地验收；通过后再 commit / PR / CLOSE


---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-08-17 | 00 派发：20 → 30+40 → 人本地验收 |
