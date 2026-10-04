# Invoke：10-task · hitl-browser-decide（B2 HITL 浏览器决策面）

| 字段 | 值 |
|---|---|
| hat_id | 10-task |
| task_slug | `hitl-browser-decide` |
| task_paths | `docs/tasks/active/task_hitl_browser_decide.md` |
| related_review_or_none | `docs/harness/reviews/spec_chat_history_hitl_ux_audit_R1_20260930.md` · task R1 `docs/harness/reviews/task_hitl_browser_decide_audit_R1_20260930.md`（通过 0 阻塞 · 4 nit 转 30） |
| git_branch | `task/chat-history-hitl-ux` |
| created_utc_or_local | 2026-09-30 |
| notes | 本 invoke 自批量拆解 invoke 派生：`docs/harness/invokes/by-task/chat-history-hitl-ux/invoke_20260930_10_chat-history-hitl-ux.md`（同一 10 帽产出 · 按 task_slug 归档以满足 pre-30 invoke 闸）；10-task 不实现代码、不签 human_gate |

---

## 可复制 Prompt 快照

hat_id：10-task
task_slug：hitl-browser-decide
本帽禁区：不实现代码、不改 CI、不签发 HG-AUDIT-R1、不动 `app/`/`tests/`

必读：SPEC `docs/spec/chat-history-hitl-ux/SPEC-chat-history-hitl-ux_v0.md`（signed · §2 B2 · §4 Q2/Q5 · §5 FP-3/FP-6 · §6 B2）· 本仓 `AGENTS.md` 人工闸 · 码面真值 `app/ops/hitl/router.py`（签名面/callback/resume）· `app/ops/hitl/store.py`（`adecide` 守卫）· `app/ops/deps.py`（`require_maintainer`/`require_admin_sync`）· `app/ops/lg_rag/event_store.py:50-69`（`run_owner`）

只做什么：
1. 预填 `## Harness 元信息` + `wiki_delta` 行
2. `npx spec-wave task lint --file` PASS
3. 上抛裁定 D（新端点鉴权依赖口径）/ 裁定 E（pending 归属过滤口径）
4. 携带 SPEC 审查 N2 回填（`OPS_HITL_PERSISTENCE=db` 持久化路径入 test_strategy）

禁止扩 scope。禁止改 `app/` / `tests/` / `alembic/`。

## 签收栏

10 帽产出 · 2026-09-30 · 裁定 D1/E1 经维护者令落定；20 R1 通过（0 阻塞 · 4 nit 转 30）；维护者签 HG-TASK-DRAFT/HG-AUDIT-R1/HG-GRAPH-MODULES = approved（2026-09-30 · 图谱闸签「在册」· 备注随 30 交付落盘）

---

## 交付摘要

| 项 | 内容 |
|---|---|
| **产出** | `docs/tasks/active/task_hitl_browser_decide.md`（ready · 三闸 approved） |
| **验证** | `task lint` PASS · `lint-wiki-delta` PASS · `verify` 三闸 approved（pre-30 invoke 本件补齐后放行） |
| **已定夺** | D1（新端点 `MaintainerUser`）· E1（pending 仅本人 owner） |
| **未改** | `app/` · `tests/` · `alembic/` · CI · 图谱 YAML |
| **下一棒** | 30 实现（00 派发 · 与 B1 串行 · B1 先） |
