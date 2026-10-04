# Invoke：10-task · chat-history-hitl-ux（批量拆解 B1/B2）

| 字段 | 值 |
|---|---|
| hat_id | 10-task |
| task_slug | `chat-history-api` · `hitl-browser-decide` |
| task_paths | `docs/tasks/active/task_chat_history_api.md` · `docs/tasks/active/task_hitl_browser_decide.md` |
| related_review_or_none | `docs/harness/reviews/spec_chat_history_hitl_ux_audit_R1_20260930.md`（SPEC R1 PASS-WITH-NITS · 携带 N2/N3） |
| git_branch | `task/chat-history-hitl-ux` |
| created_utc_or_local | 2026-09-30 |
| notes | 依据 signed SPEC `docs/spec/chat-history-hitl-ux/SPEC-chat-history-hitl-ux_v0.md` §2 B1/B2 批量拆两个 active task；10-task 不实现代码、不签 HG-AUDIT-R1 |

---

## 可复制 Prompt 快照

hat_id：10-task  
task_slug：chat-history-hitl-ux（B1 `chat-history-api` / B2 `hitl-browser-decide`）  
本帽禁区：不实现代码、不改 CI、不签发 HG-AUDIT-R1、不动 `app/`/`tests/`

必读：`docs/harness/prompts/10-task-requirements.md` · SPEC `chat-history-hitl-ux_v0.md`（signed）· SPEC 审查 R1 · 本仓 `AGENTS.md` 人工闸 · `.importlinter` 契约 · 码面真值 `app/ops/lg_rag/event_store.py` · `app/ops/lg_rag/sse_stream.py` · `app/ops/hitl/router.py` · `app/ops/hitl/store.py` · `app/ops/deps.py`

只做什么：
1. 每个 task 预填 `## Harness 元信息` + `wiki_delta` 行（bulk-split 义务）
2. 每 task 落 `npx spec-wave task lint --file` PASS
3. 显式上抛 SPEC 内部冲突/口径待裁（B1 裁定 A/B · B2 裁定 D/E）
4. 携带 SPEC 审查 N1–N3 回填（B1：N3 阈值 · N4 亡端点；B2：N2 持久化路径）
5. 回填本 invoke 交付摘要；下一棒 20-task-audit

禁止扩 scope。禁止改 `app/` / `tests/` / `alembic/`。

## 签收栏

10 帽产出（未经人签）· 2026-09-30

---

## 交付摘要

| 项 | 内容 |
|---|---|
| **产出** | B1 `task_chat_history_api.md` · B2 `task_hitl_browser_decide.md`（active/） |
| **验证** | `npx spec-wave task lint --file` 两文件 · `task lint-wiki-delta --target . --scope active` |
| **已定夺** | 维护者令「冲突部分安全推荐方案进行」→ A1（`run.start` 增可选 `query` 键）· B1（路由落 `lg_rag/history_router.py`）· D1（新端点 `MaintainerUser`）· E1（pending 仅本人 owner） |
| **未改** | `app/` · `tests/` · `alembic/` · CI · 图谱 YAML · 未签任何 human_gate |
| **内容可交 20** | 是（结构齐全；裁定 A1/B1/D1/E1 已由维护者令落定，无悬置阻塞） |
| **下一棒** | 20-task-audit R1（两 task）→ HG-AUDIT-R1 人签 |
