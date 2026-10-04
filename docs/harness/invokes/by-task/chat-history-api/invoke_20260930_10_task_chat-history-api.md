# Invoke：10-task · chat-history-api（B1 会话历史只读 API）

| 字段 | 值 |
|---|---|
| hat_id | 10-task |
| task_slug | `chat-history-api` |
| task_paths | `docs/tasks/active/task_chat_history_api.md` |
| related_review_or_none | `docs/harness/reviews/spec_chat_history_hitl_ux_audit_R1_20260930.md` · task R1 `docs/harness/reviews/task_chat_history_api_audit_R1_20260930.md`（退回）· R2 `docs/harness/reviews/task_chat_history_api_audit_R2_20260930.md`（通过 0 阻塞） |
| git_branch | `task/chat-history-hitl-ux` |
| created_utc_or_local | 2026-09-30 |
| notes | 本 invoke 自批量拆解 invoke 派生：`docs/harness/invokes/by-task/chat-history-hitl-ux/invoke_20260930_10_chat-history-hitl-ux.md`（同一 10 帽产出 · 按 task_slug 归档以满足 pre-30 invoke 闸）；10-task 不实现代码、不签 human_gate |

---

## 可复制 Prompt 快照

hat_id：10-task
task_slug：chat-history-api
本帽禁区：不实现代码、不改 CI、不签发 HG-AUDIT-R1、不动 `app/`/`tests/`

必读：SPEC `docs/spec/chat-history-hitl-ux/SPEC-chat-history-hitl-ux_v0.md`（signed · §2 B1 · §4 Q1/Q6 · §5 FP-1/2/4 · §6 B1）· 本仓 `AGENTS.md` 人工闸 · `.importlinter` 契约 · 码面真值 `app/ops/lg_rag/event_store.py` · `app/ops/lg_rag/sse_stream.py:343-347/458-473` · `app/db/models.py:290-344`

只做什么：
1. 预填 `## Harness 元信息` + `wiki_delta` 行
2. `npx spec-wave task lint --file` PASS
3. 上抛 SPEC 内部冲突（裁定 A · query 真源 / 裁定 B · 端点归属模块）
4. 携带 SPEC 审查 N3 阈值回填（截断 32000 / 超时 10s）

禁止扩 scope。禁止改 `app/` / `tests/` / `alembic/`。

## 签收栏

10 帽产出 · 2026-09-30 · 裁定 A1/B1 经维护者令落定；20 R1 退回 → 回填 5 项 → 20 R2 通过（0 阻塞）；维护者签 HG-TASK-DRAFT/HG-AUDIT-R1/HG-GRAPH-MODULES = approved（2026-09-30 · 图谱闸签「在册」· 备注随 30 交付落盘）

---

## 交付摘要

| 项 | 内容 |
|---|---|
| **产出** | `docs/tasks/active/task_chat_history_api.md`（ready · 三闸 approved） |
| **验证** | `task lint` PASS · `lint-wiki-delta` PASS · `verify` 三闸 approved（pre-30 invoke 本件补齐后放行） |
| **已定夺** | A1（`run.start` 增可选 `query` 键 · errata 落盘）· B1（路由落 `lg_rag/history_router.py` · import 间接取纪律） |
| **未改** | `app/` · `tests/` · `alembic/` · CI · 图谱 YAML |
| **下一棒** | 30 实现（00 派发） |
