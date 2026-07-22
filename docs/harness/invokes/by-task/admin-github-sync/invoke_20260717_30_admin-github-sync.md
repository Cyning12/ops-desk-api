# Invoke：30 执行编码 · admin-github-sync（补录）

> **补录说明**：本文件为 2026-07-20 流程补录。执行时未按纪律落盘 invoke，现按 `TEMPLATE_invoke.md` 补齐，交付摘要为当时实际结果。

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 30（含 40 自检闭环） |
| task_slug | `admin-github-sync` |
| freeze_id | — |
| task_paths | `docs/tasks/done/task_admin_github_sync_2026-07-17.md` |
| related_review_or_none | 无 |
| git_branch | `task/admin-github-sync` |
| worktree_root | — |
| created_utc_or_local | 2026-07-17（执行日） |
| notes | PR 待合并 |

---

## 可复制 Prompt 快照

```text
## 30 开工（签闸后 · 须 GATE_VERIFY）

@docs/tasks/active/task_admin_github_sync.md
@docs/harness/prompts/30-execute-code.md
@docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md
@docs/_tech_graph/01_struct.md

【开工前】
1. 首输出 FRAGMENT_30_gate_verify 闸扫描表（读 task 人工闸表，比对用户声称）
2. 仅当 HG-AUDIT-R1=approved（task 表）→ 可改码

【实现】
- 分支：task/admin-github-sync（基于 task/auth-session-db-cookie）· 仅 task 所列路径
- 范围：SyncPayload schema、process_sync_payload upsert、POST /admin/sync、
  GET /issues|pulls|graph 只读接口、测试、graph 文档
- test_strategy: required → 先红后绿

【Verify】
- pytest tests · ruff check app tests · ./scripts/graph-compile.sh
```

---

## 交付摘要（本帽结束时填）

- **验证命令**：`pytest tests`（66 passed）· `ruff check app tests`（绿）· `./scripts/graph-compile.sh`（绿）· iOS smoke（login → sync → issues/pulls/graph → chat #1 上下文命中 `tool_result`，通过）
- **变更路径**：`app/ops/admin/{schema,service,sync}.py`、`app/ops/{issues,pulls,graph}.py`、`tests/test_admin_sync.py`、`tests/test_{issues,pulls,graph}.py`、`tests/conftest.py`、`docs/_tech_graph/11_flow_sync_to_chat.*`
- **下一棒**：CLOSE（task 归档 `docs/tasks/done/task_admin_github_sync_2026-07-17.md`）

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-07-20 | 流程补录：执行时未落盘 invoke，按模板补齐 |
