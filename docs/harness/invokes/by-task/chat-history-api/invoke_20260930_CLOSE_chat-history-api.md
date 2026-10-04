# Invoke：CLOSE · chat-history-api（B1 会话历史只读 API）

| 字段 | 值 |
|---|---|
| hat_id | CLOSE（00 统筹） |
| task_slug | `chat-history-api` |
| task_paths | `docs/tasks/done/task_chat_history_api.md`（已归档） |
| related_review_or_none | R1 `docs/harness/reviews/task_chat_history_api_audit_R1_20260930.md`（退回）· R2 `docs/harness/reviews/task_chat_history_api_audit_R2_20260930.md`（通过 0 阻塞） |
| git_branch | `task/chat-history-hitl-ux` → PR #204 MERGED（`eb22a66` · CI 四绿） |
| created_utc_or_local | 2026-09-30 |

---

## 链路留痕

10 拆解（裁定 A/B 上抛）→ 维护者令「安全推荐」落定 A1/B1 → 20 R1 退回（缺旧测 grep 影响面）→ 10 回填 5 项 → 20 R2 通过 → 维护者签 HG-TASK-DRAFT/HG-AUDIT-R1/HG-GRAPH-MODULES（2026-09-30）→ 30/40 交付 `9904f81` → 维护者令单 PR → PR #204 CI 四绿 MERGED → CLOSE。

## 交付摘要

| 项 | 内容 |
|---|---|
| **产出** | `app/ops/lg_rag/history.py` · `history_router.py` · `event_store.py` 只读扩展 · `run.start` 可选 `query` 键（A1）· `tests/test_chat_history_api.py` 25 用例 · G-L1 图谱备注 |
| **验收** | 14/14 机断全绿；pytest 1624 passed · lint-imports 12 kept 0 broken · graph-compile 0 · lint-wiki-delta PASS |
| **红线** | `app/ops/chat/**` 零 diff · SSE freeze 对拍锁死（零新 event_type）· 零新表/迁移/写路径 |
| **签闸链** | HG-TASK-DRAFT · HG-AUDIT-R1 · HG-GRAPH-MODULES 全 approved（维护者 2026-09-30 · 图谱闸签「在册」· 端点备注随 30 交付落盘已复核） |
| **KPI** | kpi_aggregator=CLOSE · 验收勾选 14/14 · PR #204 MERGED `eb22a66` |
| **遗留** | 本机 `ALTER ROLE ops CREATEDB` 环境修复留痕（非仓内 · B2 窗口所为）；存量 ruff 55 条在非本 task 文件（净 -1 · 零新增） |
