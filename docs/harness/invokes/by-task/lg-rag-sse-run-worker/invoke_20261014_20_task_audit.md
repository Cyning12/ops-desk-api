# invoke · 20-task-audit R1 · lg-rag-sse-run-worker

> **task**：`docs/tasks/active/task_lg_rag_sse_run_worker.md`（task_slug: `lg_rag_sse_run_worker`）  
> **hat**：20-task-audit（书面审查 · 零 `app/` 改动 · 零 task 实质改动 · **未改**旧 disconnect task · 流程闸交维护者）  
> **日期**：2026-10-14 · **仓态**：分支 `task/lg-rag-sse-run-worker` @ `9ee928c`（≡ master base）  
> **本 invoke 落盘依据**：task `required_invoke_hats=10,20,30,40` 含 20 → 20 帽 invoke 快照强制

## 真读清单（逐一亲读 · 禁信转述）

- `docs/tasks/active/task_lg_rag_sse_run_worker.md` 全文
- `docs/harness/invokes/by-task/lg-rag-sse-run-worker/invoke_20261014_10_task_draft.md`
- `docs/harness/invokes/by-task/lg-rag-sse-disconnect-completion/invoke_20261014_00_e3_wave_b_plan.md`
- `docs/harness/invokes/by-task/lg-rag-sse-disconnect-completion/invoke_20261014_00_e3_new_task_spawn.md`
- `docs/tasks/active/task_lg_rag_sse_disconnect_completion.md`（只读 · **未改正文**）
- `app/ops/lg_rag/sse_stream.py` 文件头 Wave A/B 边界 · cancel anext · `_settle_disconnected`
- `app/ops/lg_rag/event_store.py` `run_is_terminal` / `run_stream_closed` / `load_events_after(refuse_in_flight=…)`
- `app/ops/lg_rag/router.py` `/stream` · `/replay` 409 路径
- `app/ops/lg_rag/history.py:161-171` `run_terminal_status`
- `docs/spec/agent-infra/05_lg_rag_transport_and_session_plan_v0.md` §10.3
- `tests/test_lg_rag_sse_resume.py` / `test_chat_history_api.py`（旧测影响面代查）
- 审查文样例：`docs/harness/reviews/task_lg_rag_sse_disconnect_completion_audit_R1_20261013.md`

## 裁定

1. **结论 PASS-WITH-NITS · 内容零阻塞**：范围 F5–F7+补偿可测；D1=A+B / D2 / D3 与方案一致；TC-B1–B10 覆盖产品口径；G-L1 + HG-GRAPH-MODULES 升判正确。
2. **核对项全过**：旧 task co-CLOSE · D1=A+B（B 主 · A 补偿）· 继续回复≠HITL resume · 帧类型不升级 · 多副本 MVP 单飞 · web D3。
3. **须交 10 重写的项：无**。NIT：K7 旧测文件名未单列 · F7 策略软验收 · `continue_from` 字段名开放 · Wave A 脏树边界——均不升否决。
4. **D1 建议确认 A+B**；**D2** 确认 10 默认（成功普通 `done` · 失败 `lg_rag.worker_failed` · 补偿可 `disconnected`）；**D3** 须开 web。
5. **流程闸交维护者**：三闸 + D1 正式落表仍 pending；**未附 30 Prompt**；**未 commit**。

## 门禁实证

```text
npx --yes spec-wave@3.3.0 task lint --file docs/tasks/active/task_lg_rag_sse_run_worker.md
→ LINT: PASS · task_lg_rag_sse_run_worker.md
```

- 未跑 `verify`：三闸 pending 为已知正确语义（预期 BLOCKED）· 本帽不改变闸态
- 未改 `app/` · 未热修 task 草稿 · **未改** `task_lg_rag_sse_disconnect_completion.md`

## 交付物

- 审查文：`docs/harness/reviews/task_lg_rag_sse_run_worker_audit_R1_20261014.md`
- 本 invoke：`docs/harness/invokes/by-task/lg-rag-sse-run-worker/invoke_20261014_20_task_audit.md`
