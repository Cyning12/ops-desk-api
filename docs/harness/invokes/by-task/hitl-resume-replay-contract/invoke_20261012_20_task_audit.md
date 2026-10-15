# invoke · 20-task-audit R1 · hitl-resume-replay-contract

> **task**：`docs/tasks/active/task_hitl_resume_replay_contract.md`（task_slug: `hitl_resume_replay_contract`）
> **hat**：20-task-audit（书面审查 · 零 app/ 改动 · 零 task 实质改动 · 未代签）
> **日期**：2026-10-12 · **仓态**：master `cff3660`（pull 后 · 工作树净）
> **开窗授权**：用户令「pull 之后来进行审核」（承接 #246 阅读会话 · 本会话先读 PR #246 全文）
> **本 invoke 落盘依据**：task `required_invoke_hats=10,20,30,40` 含 20 → 20 帽 invoke 快照强制

## 真读清单（逐一亲读 · 禁信转述）

- `docs/tasks/active/task_hitl_resume_replay_contract.md` 全文（pull 后本地 · 与 PR #246 合入版一致）
- `app/ops/hitl/resume.py:1-159`（含 :85 `_started` 计时面 · :124-134 close 终帧四键）
- `app/ops/lg_rag/router.py:330-373`（:344-348 422 · :350-356 单捕 RunNotFound）
- `app/ops/lg_rag/event_store.py:128-169`（assert_run_owned · load_events_after）
- `app/ops/lg_rag/sse_stream.py:455-494`（双 done 对照面 · latency_ms 口径）
- `app/ops/chat/streaming.py:278-302`（done 含 latency_ms+model）
- `app/ops/hitl/router.py:418-430/:515-521`（_execute_decided_resume 同源体首尾）
- `app/ops/hitl/auto_resume.py:193-237`（_claim_and_execute · :229-231 同源调用）
- `tests/` grep：replay 状态码断言面 + resume 终帧键断言面（旧测影响面代查）
- `docs/harness/reviews/task_testing_write_capability_audit_R1_20261009.md`（审查文格式先例）
- `docs/tasks/done/task_lg_rag_sse_subtask_message.md` / `task_lg_rag_sse_resume.md`（freeze 先例存在性确认）

## 裁定

1. **结论 PASS · 内容零阻塞**：锚点 9 行全实证一致；范围/非范围互斥闭合；TC1–TC5 可机断；failure_paths 覆盖四类主险；思考轮 R0–R5 闭合、early_stop at R5 理由具体。
2. **旧测影响面代查实证为空 → 不退回 10-task 补列**：无任何旧测断言在飞 replay 500；resume 旧测断言 `events_persisted` 既有键不受增键影响；TC4 全量对拍 + FP-5 CI 拦实质兜底（强于 grep 枚举）。
3. **流程闸不代签**：HG-AUDIT-R1 / HG-GRAPH-MODULES 维持 pending，审查文附维护者签闸清单，**未附 30 Prompt**（闸 pending 纪律）。
4. **非阻塞观察项 O1–O3** 照登审查文（_started 计时面可复用 · 在飞判定面建议复用 run_is_terminal · TC5 环境依赖承前例）。

## 门禁实证

- `npx spec-wave@3.3.0 task lint --file docs/tasks/active/task_hitl_resume_replay_contract.md` → **EXIT=0 · LINT: PASS**（2026-10-12 本帽复跑）
- 未跑 `verify`：两闸 pending 为已知正确语义（EXIT=2 BLOCKED 预期 · PR #246 已实证），本帽不改变闸态。

## 交付物

- 审查文：`docs/harness/reviews/task_hitl_resume_replay_contract_audit_R1_20261012.md`
- 本 invoke：`docs/harness/invokes/by-task/hitl-resume-replay-contract/invoke_20261012_20_task_audit.md`
