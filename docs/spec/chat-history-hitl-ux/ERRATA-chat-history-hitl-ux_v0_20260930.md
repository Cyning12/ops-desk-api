# ERRATA：chat-history-hitl-ux v0 · `run.start` payload 增可选 `query` 键（裁定 A1）

> **性质**：对 signed SPEC `docs/spec/chat-history-hitl-ux/SPEC-chat-history-hitl-ux_v0.md` §1 纪律 #1「SSE 契约零改动」的**有界豁免**记录（非新 event_type）。
> **依据**：维护者令 2026-09-30「冲突部分安全推荐方案进行」；20-task-audit R1 nit N4（`docs/harness/reviews/task_chat_history_api_audit_R1_20260930.md`）要求 errata 有可追溯落点。
> **关联 task**：`docs/tasks/active/task_chat_history_api.md`（B1 · slug `chat-history-api`）

## 豁免内容

| 项 | 内容 |
|---|---|
| 触及帧 | `run.start`（`app/ops/lg_rag/sse_stream.py:343-347`） |
| 变更 | payload 增**可选** `query` 键（存量旧 run 无键） |
| 边界 | **不新增 event_type** · 不改 `hitl.waiting`/`done{status}`/`answer`/`subtask.progress` 帧语义 · 既有断言 subset-安全 |
| 原因 | SPEC §2 B1 要求历史按 run 重建 query，而 `run.start` 现状 payload 无 query；挂起路径不落 `ops_lg_rag_turns`，无替代真源 |
| 影响面 | `tests/test_lg_rag_sse_stream.py:101-102` · `tests/test_lg_rag_session_continuity.py:166-167` · `tests/test_multi_replica_dualproc.py:420-424` · `tests/test_lg_rag_sse_token_stream.py:183/254` · `tests/test_chat_ws.py:226/275` |

## 后续

SPEC 下次升版时把本节并轨进 §1/§3 措辞（「SSE 零新事件类型 · 既有帧可选字段增键须 errata」）。本便签不修改 signed SPEC 正文。

## 修订记录

| 日期 | 说明 |
|---|---|
| 2026-09-30 | 立便签：裁定 A1 豁免落盘（10-task 回填 20 R1 nit N4） |
