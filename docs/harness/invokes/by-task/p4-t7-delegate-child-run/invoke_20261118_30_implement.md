# invoke · 30 实施 · p4-t7-delegate-child-run（2026-11-18）

## 闸扫描（30 前置 GATE_VERIFY · 真值在 task 人工闸表）

| gate | status | blocks_30 | 30 影响 |
|------|--------|-----------|--------|
| HG-TASK-DRAFT | approved | 30 | — |
| HG-AUDIT-R1 | approved | 30 | ✅ 可 30 |
| HG-GRAPH-MODULES | approved | — | ✅ |

npx --yes spec-wave@3.5.0 verify --target . --task docs/tasks/active/task_p4_t7_delegate_child_run.md → 见 invoke_40（三闸 approved · 30 放行）。

## 实施清单（契约 19 §8-§13 逐字对齐）

1. app/ops/lg_rag/run_store.py：新增 fetch_run_row(run_id)->dict|None（run_id/status/depth/parent_run_id/subtask_id/user_id/thread_id/tenant_id · 父轮询/depth 分流读面）+ count_child_runs(parent_run_id)->int（func.count where parent_run_id · §8.4 MAX_CHILDREN 校验读面）。
2. app/ops/lg_rag/event_store.py：新增 fetch_delegate_spec(run_id)（首帧 run.start payload["delegate_spec"] dict|None · resume 重跑规格重建）+ fetch_delegate_outcome(run_id)（末条 done/error 帧 {"terminal","payload"}|None · 父 join 收口读面）。
3. app/ops/lg_rag/multi/nodes.py：
   - env 三件套：ENV_RUN_TREE_ENABLED/ENV_RUN_TREE_MAX_CHILDREN/DEFAULT_RUN_TREE_MAX_CHILDREN=8/_RUN_TREE_POLL_SECONDS=1.0 · run_tree_enabled()（on→True · 非法 warning+False）· run_tree_max_children()（[1,64] 否则 8）。
   - route_next_subtask：run_tree_on and node=="tool_exec" → Send("delegate_exec")（payload 注 user_id/allowed_capability_ids/delegation_scope · 无 delegation_token）· elif delegation_on 原分支保留 · 闸 off 既有 Send(tool_exec) 逐字节零 diff。
   - 执行体提取 _run_tool_capability(state, *, subtask, result, call_args, budget_run_id="", emit_running=True)（闸链单真源 · W0 闸/running 帧/cap_ctx/capability_ainvoke/降级原样 · cap_ctx["run_id"]=budget_run_id or _run_id_of(state)）；tool_exec_node 薄壳（bump→执行体→hitl_required 直返无 bump→否则 _finish_worker）。
   - execute_delegate_subtask（exec_state 三键+delegation_scope · _delegation_active() 时 _issue_delegation_token 子侧自发签发 §3.9 · budget_run_id=parent emit_running=False · 返 kind/result/capability_id）。
   - acreate_delegate_hitl_request（pending 去重 · blocked_by=_BLOCKED_BY_CAPABILITY_WRITE · 自解锁 · payload{capability_id, write_intent?} · 单据 run_id=子 §9）。
   - delegate_exec_node（bump→parent_run_id 空拒→count_child_runs≥max warning 审计+error「委派子 run 总数超限」→claim_child_run None→error→fetch_run_row 取归属→emit_subtask_running(delegate_exec)→start_delegate_run_worker→轮询 budget_exhausted/TERMINAL/sleep(1.0)→fetch_delegate_outcome 收口：error 帧 delegate_result.error|message|reason|「子 run 失败」· done/resumed 有 output→output+degraded 透传 · else 含 payload.reason 透传「审批驳回」· _finish_worker）。asyncio/uuid/run_store/event_store 全函数内 lazy import。
4. app/ops/lg_rag/multi/graph.py：import delegate_exec_node · _DISPATCH_MAP+"delegate_exec" · _AGENT_NODES+add_node。
5. app/ops/lg_rag/sse_stream.py：_SUBTASK_NODES+"delegate_exec" · 新增 _iter_delegate_sse_core（emit 纪律复刻主 core · seq 自 last_seq 续防撞 uq · 帧序 run.start{mode:"delegate",parent_run_id,delegate_spec}/(hitl.waiting+done{waiting_approval})/answer(final)/done{status done|resumed · delegate_result}/error{stage:"lg_rag.delegate_failed"} · finally 未 settled 补 done{disconnected}）。
6. app/ops/lg_rag/run_worker.py：start_delegate_run_worker（共享 bus/_workers/单飞 · set domain/tenant/run_context · 不 create_run 不起 checkpointer · finally close+reset）+ settle_delegate_run_rejected（persist hitl.resumed{approved:[]}+done{status:"error",reason:"审批驳回"} seq 续 last_seq）。
7. app/ops/hitl/router.py：_is_delegate_child_run（fetch_run_row depth==1 · 查询失败 best-effort 非委派）· _execute_delegate_child_resume（approved→fetch_delegate_spec 缺 ResumeError("delegate_spec_missing")→start_delegate_run_worker(resumed=True) · rejected→settle_delegate_run_rejected · 返 sink:None）· _execute_decided_resume 在 _open_event_sink 前分流 · _preflight_decided_resume 分流（status!="waiting_approval"→ResumeError("not_interrupted") 重复 resume 防线 · approved 校验 spec）。
8. tests/test_lg_rag_delegate_run_tree.py：10 用例（env×4 · route×2 · DB MAX_CHILDREN/happy/HITL 三段/rejected×4 · 真 PG 五键 blank · write 罐头 fixture 承 test_write_approval_gate 范式 · _mk_delegate_state 带 args dict）。

## 偏差登记（最小改动 · 如实登记）

- GUIDE_env_inventory 不登记 env 三件套（承 p4-t2 OPS_DOMAIN 先例 · env 注记随图谱行备注落盘）。
- 实现修复两件（测试首跑红修复 · 教训入 task 档失败路径）：① _iter_delegate_sse_core resumed 重跑 seq 从 1 起撞 uq_ops_lg_rag_run_events_run_seq → 启动时 last_seq 续（承 ResumeEventSink start_seq 纪律）；② delegate_exec_node else 分支漏透传 done{status:error,reason:审批驳回} 的 reason → 加 or payload.get("reason")（19 §13）。

## 验证结果

- 目标测试：pytest tests/test_lg_rag_delegate_run_tree.py -q → **10 passed**（真 PG · 五键 blank 前缀）。
- 回归：pytest 目标 15 文件 -q → **210 passed**（T6 projection/ddl · write_approval_gate · hitl_resume×4 · hitl_pending_decide · sse/lg_rag_multi 等）。
- ruff check app tests → All checks passed。
- 全量 pytest tests（脏树期）：环境性红与 base 297363bd 同路径基线逐签对照（opsdesk_test 残留行 fix434-c4986a87 手动清理后复绿 · 既有脏数据非本波因果）· CI 终裁。
