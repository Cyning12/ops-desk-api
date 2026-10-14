# invoke · 20-task-audit R1 · lg-rag-sse-disconnect-completion

> **task**：`docs/tasks/active/task_lg_rag_sse_disconnect_completion.md`（task_slug: `lg_rag_sse_disconnect_completion`）  
> **hat**：20-task-audit（书面审查 · 零 `app/` 改动 · 零 task 实质改动 · 未代签）  
> **日期**：2026-10-13 · **仓态**：分支 `task/lg-rag-sse-disconnect-completion` @ `9ee928c`（≡ master base）  
> **本 invoke 落盘依据**：task `required_invoke_hats=10,20,30,40` 含 20 → 20 帽 invoke 快照强制

## 真读清单（逐一亲读 · 禁信转述）

- `docs/tasks/active/task_lg_rag_sse_disconnect_completion.md` 全文
- `docs/harness/invokes/by-task/lg-rag-sse-disconnect-completion/invoke_20261013_10_task_draft.md`
- `app/ops/lg_rag/sse_stream.py` 文件头断连语义 · `:396-425` cancel anext · `:509-525` Exception→error · `:526-531` finally（无收尾帧）
- `app/ops/lg_rag/event_store.py` `run_is_terminal` / `run_stream_closed` / `load_events_after(refuse_in_flight=…)`
- `app/ops/lg_rag/router.py:336-395` replay 409 路径
- `app/ops/lg_rag/history.py:161-171` `run_terminal_status`（D2 对照）
- `docs/spec/agent-infra/05_lg_rag_transport_and_session_plan_v0.md` §10.3
- web T4 done：`ops-desk-web/docs/tasks/done/task_web_lg_rag_sse_t4.md` 断连遗留句
- `docs/harness/invokes/by-task/hitl-resume-replay-contract/invoke_20261013_40_verify.md`（孤儿 `22b65ce2`）
- `tests/test_lg_rag_sse_resume.py` / `test_lg_rag_sse_hitl.py` / `test_chat_history_api.py`（旧测影响面代查）
- 审查文样例：`docs/harness/reviews/task_hitl_resume_replay_contract_audit_R1_20261012.md`

## 裁定

1. **结论 PASS-WITH-NITS · 内容零阻塞**：问题框定（契约 vs generator close）与码面一致；Wave 默认 A-only 可接受；TC1–TC7 可机断；HITL / 真在飞 409 保护区充分；freeze 纪律正确。
2. **须退回 10 的阻塞项：无**。NIT：E5 缺自检结论（lint FAIL）· Exception 行号略宽 · K7 旧测文件名未单列 · Wave A 钩点留 30——均不升 BLOCKED。
3. **D1 建议 A-only**（同意 10）；若签 A+B → 建议拆 task（条件范围过大）。
4. **D2 建议** `done{status:'disconnected'}`（或钉死 `'cancelled'` 一字面量）；慎用泛化 `error`；禁 silent 新 `event_type`。
5. **流程闸不代签**：HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 维持 pending；D1/D2 待维护者签；**未附 30 Prompt**。

## 门禁实证

- `npx spec-wave@3.3.0 task lint --file docs/tasks/active/task_lg_rag_sse_disconnect_completion.md` → **LINT: FAIL** · `[E5] 缺 ### 自检结论 节`（照登审查文 N1）
- 未跑 `verify`：三闸 pending 为已知正确语义（预期 BLOCKED）· 本帽不改变闸态
- 未改 `app/` · 未热修 task 草稿（修订意见列审查文「建议 10 修订」）

## 交付物

- 审查文：`docs/harness/reviews/task_lg_rag_sse_disconnect_completion_audit_R1_20261013.md`
- 本 invoke：`docs/harness/invokes/by-task/lg-rag-sse-disconnect-completion/invoke_20261013_20_task_audit.md`
