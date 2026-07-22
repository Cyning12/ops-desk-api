# Invoke：30 执行编码 · auth-session-db-cookie（补录）

> **补录说明**：本文件为 2026-07-20 流程补录。执行时未按纪律落盘 invoke，现按 `TEMPLATE_invoke.md` 补齐，交付摘要为当时实际结果。

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 30（含 40 自检闭环） |
| task_slug | `auth-session-db-cookie` |
| freeze_id | — |
| task_paths | `docs/tasks/done/task_auth_session_db_cookie.md` |
| related_review_or_none | 无 |
| git_branch | `task/auth-session-db-cookie` |
| worktree_root | — |
| created_utc_or_local | 2026-07-17（执行日） |
| notes | PR 待合并 |

---

## 可复制 Prompt 快照

```text
## 30 开工（签闸后 · 须 GATE_VERIFY）

@docs/tasks/active/task_auth_session_db_cookie.md
@docs/harness/prompts/30-execute-code.md
@docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md
@docs/_tech_graph/01_struct.md

【开工前】
1. 首输出 FRAGMENT_30_gate_verify 闸扫描表（读 task 人工闸表，比对用户声称）
2. 仅当 HG-AUDIT-R1=approved（task 表）→ 可改码

【实现】
- 分支：task/auth-session-db-cookie · 仅 task 所列路径
- 范围：scripts/create_initial_user.py、POST /api/ops/auth/login|logout、
  GET /api/ops/auth/me、get_current_user / require_maintainer、
  GET /api/ops/chat/sessions/latest、iOS 接口文档、测试
- test_strategy: required → 先红后绿

【Verify】
- pytest tests · ruff check app tests · ./scripts/graph-compile.sh
```

---

## 交付摘要（本帽结束时填）

- **验证命令**：`pytest tests`（绿）· `ruff check app tests`（绿）· `./scripts/graph-compile.sh`（绿）· iOS smoke（login → latest session → SSE stream，通过）
- **变更路径**：`app/ops/auth.py`、`app/ops/deps.py`、`app/ops/security.py`、`app/config.py`、`app/ops/chat/router.py`、`app/ops/chat/schema.py`、`scripts/create_initial_user.py`、`tests/test_auth.py`、`docs/ios/api-auth-chat.md`、`docs/_tech_graph/10_flow_auth.*`
- **下一棒**：CLOSE（task 归档 `docs/tasks/done/task_auth_session_db_cookie.md`）

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-07-20 | 流程补录：执行时未落盘 invoke，按模板补齐 |
