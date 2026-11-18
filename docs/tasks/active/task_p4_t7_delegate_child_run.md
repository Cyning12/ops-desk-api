---
title: task · P4-T7 · 委派子 run 执行（Run 树线核心）
---

# task · P4-T7 · 委派子 run 执行（Run 树线核心）

> **状态**：`active`（2026-11-18 落卡 · 夜间自动执行波）
> **来源**：workspace 18-p4-generalization-design.md §3/§7 + 19-p4-contracts.md §8-§13（commit e453a36）· 授权 issue Cyning12/ops-desk-workspace#23（m03796 夜间预授权 · 委派书 p4-t7-delegate-child-run）

## Harness 元信息

| 键 | 值 |
|----|----|
| **task_slug** | p4-t7-delegate-child-run |
| base | 297363bd |
| 关联 issue | issue Cyning12/ops-desk-workspace#23（授权真源）· workspace 18 文 §3/§7 + 19 文 §8-§13（需求真源） |
| 关联 PR | feat 本 PR · close chore PR（收口登记） |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 本仓未启用 WikiTrack；本波为委派子 run 执行面（总闸 + delegate worker + HITL 恢复 + 父 join）+ 图谱登记 |
| graph_change_layer | G-L1（01_modules.md lg_rag 行 p4-t7 备注 + HG-GRAPH-MODULES 签收行） |
| review_hat | 20（R1 审查文已落盘 · GO） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | approved | 30 | approved 2026-11-18 · 授权 issue Cyning12/ops-desk-workspace#23 m03796（夜间预授权）+ 委派书 p4-t7-delegate-child-run 为唯一范围真源 |
| HG-AUDIT-R1 | approved | 30 | approved 2026-11-18 · 同上授权 + R1 审查文 docs/harness/reviews/task_p4_t7_delegate_child_run_audit_R1_20261118.md（GO） |
| HG-GRAPH-MODULES | approved | 30 | approved 2026-11-18 · 同上授权（lg_rag 行 p4-t7 备注属图谱登记义务 · 随 30 交付回填） |

## 背景

P4 泛化设计（18 文 §3）裁定：supervisor 的 type=tool 子任务在总闸开时**委派提升为独立子 run**（与 start_run_worker 同级共享 RunEventBus/_workers/单飞/孤儿补偿），数据面前提（runs 三列 + claim 部分唯一索引 + REST 投影）已由 T6 落地（wave_tip 142723ee）。本波 T7 交付执行面：

- 19 §8.1：闸 on 时 `route_next_subtask` 对 inflight 的 type=tool 子任务不发 `Send(tool_exec)`，改走 claim → `start_delegate_run_worker` → 图内 `delegate_exec` 节点轮询子终态 join；rag/extract 留图内；plan-JSON 零新 type。
- 19 §8.2/§8.3：子 run 继承父 tenant/user/thread（T6 claim 已从父行取值）；父轮询 SELECT status 间隔 1s，超时/失败预算复用既有子任务闸（is_supervisor_budget_exhausted），子终态后从其事件表读 answer/done payload 进 subtask_join 既有通路。
- 19 §8.4 三层预算：深度 1 硬上限（结构性无环 · 子 run 执行体内无 route_next_subtask 通路）+ `OPS_RUN_TREE_MAX_CHILDREN` 默认 8（claim 前 COUNT(parent_run_id) 校验 · 超限=子任务按失败进既有收口 + logger.warning 审计）+ MAX_SUBTASKS=4 不动；cap_ctx 配额记桶键=父（根）run_id 防 9× 分裂。
- 19 §9 令牌五行表：事件/状态行 run_id=子 run_id；token binding run_id/subtask_id=子 run_id/子任务 id（claim 先于签发 · 子侧每次执行尝试自发签发 TTL 自尝试起算 · 父令牌仅授权凭证不复用）；cap_ctx 预算键=父根 run_id；HITL 单据 run_id=子 run_id；`_approval_consumed` 匹配键=(子 run_id, subtask_id, capability_id)。
- 19 §10 HITL 三段：①子执行体遇写能力且审批未消费 → 落 hitl.waiting 帧 + status=waiting_approval 后退出 worker（不占 _workers 槽）②用户经既有 decide/resume 端点批准 → resume 按 run 行 depth 分流：depth=1 → 重启 start_delegate_run_worker 重跑该子任务执行体 ③重跑至同一能力调用点 `_approval_consumed` 命中放行（fail-closed · 副作用闸在 capability_ainvoke 前）。
- 19 §11 帧面零新增：run.start payload 加可选 parent_run_id（+delegate_spec 加性键 · 见关键决策）；流边界 per-run；cursor 不动。
- 19 §12 总闸：`OPS_RUN_TREE_ENABLED` 词表 off(默认)/on · 非法值回退 off + logger.warning；off 态 route_next_subtask 走既有 Send 路径逐字节不变；`OPS_RUN_TREE_MAX_CHILDREN`=8 缺省。

## 范围

1. **总闸三件套**（nodes.py）：`ENV_RUN_TREE_ENABLED="OPS_RUN_TREE_ENABLED"` + `run_tree_enabled()`（on→True · 空/off→False · 非法值 logger.warning + False fail-closed 承 OPS_DOMAIN 先例）· `ENV_RUN_TREE_MAX_CHILDREN="OPS_RUN_TREE_MAX_CHILDREN"` + `run_tree_max_children()`（默认 8 · 域 [1,64] 否则默认 8 + warning 承 auto_resume scan_interval env_int 先例）· 轮询间隔 `_RUN_TREE_POLL_SECONDS=1.0` 常量（19 §8.3 钉 1s 不做 env）。
2. **委派执行提升**（nodes.py + graph.py）：
   - `route_next_subtask`：`run_tree_on and node=="tool_exec"` → `Send("delegate_exec")`（payload 注 user_id/allowed_capability_ids/delegation_scope · 不注 delegation_token）· elif 既有 delegation_on 分支原样保留；闸 off 走既有 Send(tool_exec) 逐字节零 diff（19 §12）。
   - tool_exec 执行体提取 `_run_tool_capability(state, *, subtask, result, call_args, budget_run_id="", emit_running=True) -> dict`（闸链单真源：W0 写执行审批闸 / emit_subtask_running / cap_ctx / capability_ainvoke / 降级标记原样 · cap_ctx["run_id"]=budget_run_id or _run_id_of(state) 配额键=父根 run_id）；`tool_exec_node` 薄壳（bump → 执行体 → hitl_required 直返 {"subtask_results":[result]} 无 bump · 否则 _finish_worker）。
   - `execute_delegate_subtask(*, subtask, child_run_id, parent_run_id, user_id, allowed_capability_ids=None, delegation_scope=None)`：exec_state={run_id:child, user_id, allowed_capability_ids}(+delegation_scope)；`_delegation_active()` 时 `_issue_delegation_token(exec_state, subtask)` 子侧每次尝试自发签发（19 §9/§3.9 · TTL 自尝试起算 · 消解批准后 REJECT_EXPIRED）；调 `_run_tool_capability(budget_run_id=parent_run_id, emit_running=False)`；返 {"kind": hitl|error|ok, "result", "capability_id"}。
   - `delegate_exec_node(state)`（graph.py 注册 + _DISPATCH_MAP + _AGENT_NODES）：bump → parent_run_id 空拒（error result）→ `count_child_runs` ≥ `run_tree_max_children()` → logger.warning 审计 + error result「委派子 run 总数超限」（19 §8.4）→ `claim_child_run`（None → error result · 撞 uq 取回复用零重复建行 19 §7.4）→ `fetch_run_row` 取子行 thread/user/tenant → emit_subtask_running(agent_role="delegate_exec") → `start_delegate_run_worker` → 轮询（is_supervisor_budget_exhausted → error 收口 · fetch_run_row status ∈ TERMINAL_STATUSES → break · asyncio.sleep(1.0)）→ `fetch_delegate_outcome` 收口：error 帧 → result["error"]=delegate_result.error|payload.message|payload.reason|「子 run 失败」；done/resumed 有 output → result["output"]（degraded 透传）；否则 result["error"]（含 done{status:error,reason:审批驳回} 的 reason 透传 · 19 §13）；`_finish_worker` 收尾。
3. **委派 worker + SSE core**（run_worker.py + sse_stream.py）：
   - `start_delegate_run_worker(*, child_run_id, parent_run_id, thread_id, user_id, tenant_id, subtask, allowed_capability_ids=None, delegation_scope=None, resumed=False, approved=None, decided_by="") -> RunEventBus`（18 §3.4：与 start_run_worker 同级共享 bus/_workers/单飞/孤儿补偿；set_current_domain+set_current_tenant+set_run_context 同纪律；**不 create_run**（claim 已建行）· **不起 checkpointer**（重跑=重启 worker · 18 §3.4）；finally bus.close()+reset）。
   - `_iter_delegate_sse_core(...)`（sse_stream.py）：emit 纪律复刻主 core（seq 单调/format_sse_event/cursor/后台 persist_tasks 闭包钉字段/finally drain）；resumed 重跑 seq 自 `last_seq(child_run_id)` 续（承 ResumeEventSink start_seq 纪律 · 防撞 uq_ops_lg_rag_run_events_run_seq）；帧序：非 resumed → run.start{run_id, thread_id, mode:"delegate", query, parent_run_id, delegate_spec:{subtask, user_id, allowed_capability_ids, delegation_scope}}；resumed → hitl.resumed{run_id, thread_id, approved, decided_by}；kind=hitl → `acreate_delegate_hitl_request` 建单 + hitl.waiting{reason:"hitl_waiting", unpersisted:False, requests:[{id, subtask_id, unlock_subtask_id, blocked_by, reason}]} + done{status:"waiting_approval"} 退出；kind=ok → answer{content, final:true}（非 str → json.dumps ensure_ascii=False）+ done{status:"resumed" if resumed else "done", latency_ms, delegate_result:{output, degraded?}}；kind=error/异常 → error{stage:"lg_rag.delegate_failed", message}；finally 未 settled → done{status:"disconnected"} 补偿（承主 core 纪律）。帧型零新增（19 §11 · _SUBTASK_NODES 加 "delegate_exec" 走既有 subtask.progress 映射）。
   - `settle_delegate_run_rejected(*, run_id, thread_id, user_id, decided_by)`：persist hitl.resumed{approved:[], decided_by} + done{status:"error", reason:"审批驳回"}（seq 自 last_seq 续 · 19 §13 拒绝路径收口）。
4. **委派 HITL 建单**（nodes.py）：`acreate_delegate_hitl_request(*, run_id, thread_id, tenant_id, subtask_id, capability_id, write_intent, reason)`——pending 去重（同 run_id+subtask_id 复用）；blocked_by=`_BLOCKED_BY_CAPABILITY_WRITE`；unlock_subtask_id=subtask_id（自解锁承 _SELF_UNLOCK_BLOCKED_BY 先例）；payload{capability_id, write_intent?}；单据 run_id=子 run_id（19 §9）。
5. **HITL 三段恢复分流**（hitl/router.py）：`_is_delegate_child_run(row)`（lazy import fetch_run_row · depth==1 → 行 · 查询失败按非委派 best-effort）；`_execute_decided_resume` 在 _open_event_sink 前分流 depth==1 → `_execute_delegate_child_resume`：approved → `fetch_delegate_spec`（缺 → ResumeError("delegate_spec_missing")）→ start_delegate_run_worker(resumed=True, approved, decided_by)；rejected → settle_delegate_run_rejected；返 {req_status, thread_id, sink:None, outcome}（sink=None 安全 · 返回值仅内部消费）；`_preflight_decided_resume` 同分流：status!="waiting_approval" → ResumeError("not_interrupted")（重复 resume 防线 · 子终态后拒）；approved 校验 spec 存在。19 §10②「resume 按 run 行 depth 分流」逐字对齐。
6. **测试**（真 PG postgresql+asyncpg://ops:ops_password@localhost:5432/opsdesk_test · 五键 blank 前缀 OPS_HITL_PERSISTENCE= OPS_CAPABILITY_ALLOW_WRITE= OPS_CAPABILITY_ALLOW_WRITE_TAGS= OPS_CAPABILITY_PERSISTENCE= OPS_CAPABILITY_EXTRA_MANIFESTS=）tests/test_lg_rag_delegate_run_tree.py：
   - env 三件套解析 ×4（off 默认/on/非法 banana→off+warning/max_children 默认 8·"3"→3·"0"/"abc"→8）；
   - route 闸 off → Send(tool_exec) 零 diff · 闸 on → Send(delegate_exec)（payload 含 user_id/allowed_capability_ids · 无 delegation_token · plan type 仍 tool）；
   - DB：MAX_CHILDREN=2 超限 → error「委派子 run 总数超限」不再建行；
   - DB happy path（read 罐头）：子 run 继承归属 + 帧序 run.start(parent_run_id+delegate_spec)/answer(final)/done(status done · delegate_result.output) + 父接回 output + adapter 恰好 1 次；
   - DB HITL 三段（write 罐头 + InMemoryHitlStore）：建单（run_id=子/blocked_by/unlock_subtask_id=sid/tenant）→ waiting_approval 退出（帧序 run.start/hitl.waiting/done{waiting_approval} · 父仍轮询）→ adecide approved → `_execute_decided_resume` 分流 delegate_restarted → 重跑放行 done（帧序续 hitl.resumed/answer/done{resumed} · 能力执行全链恰好 1 次 · 子 status resumed）· 重复 decide → None · 重复 resume → `_preflight_decided_resume` 抛 ResumeError code=not_interrupted（19 §10 T7 实证两条：approve 后重跑放行至 done · 重复 decide/重复 resume 不重复执行能力）；
   - DB rejected → settle → 帧尾 hitl.resumed/done{status:error, reason:审批驳回} · 父 result error 含「审批驳回」零执行；
   - 回归：目标 15 测试文件 210 passed（T6 projection/ddl · write_approval_gate · hitl_resume ×4 · hitl_pending_decide · sse/lg_rag_multi 等）· ruff check app tests 绿 · 全量 pytest 绿（环境性红与 base 297363bd 同路径基线逐签对照 · CI 终裁）。
7. **图谱**：docs/_tech_graph/l1/01_modules.md lg_rag 行（:35）补 P4-T7 备注 + HG-GRAPH-MODULES 签收行（承 :49 先例 · hitl 行不动登记于 lg_rag 行叙事）。
8. **落盘**：registry entry（status=active → close 波 closed 钉 wave_tip · banned_prefixes=[alembic/, scripts/] 本波不触 alembic）· invokes by-task/p4-t7-delegate-child-run/{10,30,40,50} · R1 审查文 · task 档 active→done。

## 非范围

- 不动 DDL/claim 本体（T6 已合 · 本波仅消费 claim_child_run/fetch_run_row/count_child_runs 读面）。
- 不做 web 树形面板（T8）· 不做验收冒烟（T9）。
- 不做 RunWorker DB 租约/多深度/root_run_id 冗余列/树形合并流/children 端点（19 §14 非范围钉死）。
- 不动 SSE 帧型词表/cursor/流边界（19 §11 帧面零新增 · 复用 run.start/hitl.waiting/hitl.resumed/answer/done/error 既有帧型）。
- 不动签发审批面（delegation_issue_hitl_required 仍在父侧 dispatch 前完成 · nodes.py:1456-1470 既有通路零改）。
- 不引新依赖 · 不碰 scripts//alembic/ · 不动 .importlinter（无新跨模块 import 边 · nodes↔run_store/event_store/run_worker 均 lg_rag 行内 · hitl/router→run_store 延迟 import 属 hitl→lg_rag 既有边）。
- 不做 env 台账文档登记（GUIDE_env_inventory 不动 · 承 p4-t2 OPS_DOMAIN 先例 · env 注记入图谱行备注）。

## 失败路径

- 闸 off 零 diff 失守：route_next_subtask 分支顺序必须先 run_tree_on 后 delegation_on · off 态走既有 Send(tool_exec) 逐字节不变——由 route 闸 off/on 对拍用例守（19 §11.5/§12）。
- MAX_CHILDREN 绕过：超限判定必须在 claim 前 COUNT(parent_run_id)（19 §8.4 · 先 COUNT 后 claim 次序不可反 · 超限行零建行）——由超限用例守。
- 父崩重入重复建行：claim 撞 uq SELECT 取回复用（19 §7.4/§13）· delegate_exec_node 重入不重复 spawn 已终态子 run 的副作用能力（闸链幂等键在 capability 层）——T6 并发 claim 用例已守数据面 · 本波 happy path 用例守 adapter 恰好 1 次。
- HITL 重跑重复执行：重跑幂等成立的前提是副作用闸在 capability_ainvoke 前（_approval_consumed fail-closed）+ 建单 pending 去重——由 HITL 三段用例「echo_calls==1 全链恰好一次」守（19 §10 实证钉死）。
- resumed 重跑撞事件 uq：重跑 seq 必须从 last_seq 续（承 ResumeEventSink start_seq 纪律）——首版实现 seq 从 1 起撞 uq_ops_lg_rag_run_events_run_seq（asyncpg UniqueViolationError）已修复 · 由重跑帧序断言守。
- rejected 收口丢失：settle 落 done{status:error, reason:审批驳回} 是 done 帧（terminal≠error）· 父 else 分支必须透传 payload.reason——由 rejected 用例守（19 §13）。
- 子 run waiting_approval 被父误判终态：TERMINAL_STATUSES 不含 waiting_approval（run_store.py:24）· 父轮询继续等 decide——由 HITL 用例「父仍轮询」断言守。
- 孤儿子 run：claim 建行但 worker 未起/父崩 → 既有 orphan 扫描（list_stale_running_runs + done{disconnected} 两段式）天然生效（18 §3.5 断线矩阵）· start_delegate_run_worker 登记同一 _workers/bus 面。
- 并行 agent 撞 registry.yaml/01_modules.md 同区冲突 → rebase origin/master 保留双方 entry 手动解 · 冲突块如实登记。
- 脏树期 wave_gate_registry 红为结构性常态（closed entry banned 面咬在途文件 · 提交后复绿 · CI 终裁 · 委派书钉明）。
- PR CONFLICTING → CI 不触发 → rebase origin/master 解冲突重推（委派书并行铁律）。

## 验收标准

- [x] env 三件套：off 默认 · on 生效 · 非法回退 off+warning · MAX_CHILDREN 默认 8 域 [1,64]（4 用例）
- [x] route 闸 off → Send(tool_exec) 逐字节零 diff · 闸 on → Send(delegate_exec)（payload 三键 · plan type 仍 tool）
- [x] MAX_CHILDREN 超限 → error「委派子 run 总数超限」不再建行（19 §8.4）
- [x] happy path：子 run 继承归属 · 帧序 run.start/answer/done · delegate_result.output 父接回 · 能力恰好 1 次
- [x] HITL 三段：建单 run_id=子 · waiting_approval 退出不占槽 · approve 重跑放行至 done · 重复 decide/resume 不重复执行（19 §10 实证两条）
- [x] rejected：settle done{status:error, reason:审批驳回} · 父透传 reason · 零执行（19 §13）
- [x] 回归：目标 15 文件 210 passed · ruff 绿 · 全量 pytest 绿（CI 终裁）
- [x] 01_modules.md lg_rag 行 P4-T7 备注 + HG-GRAPH-MODULES 签收行
- [x] 过闸四件：task lint PASS · registry entry · invokes {10,30,40,50} · R1 审查文 GO

### 自检结论

- 实现：7 个 app 文件（run_store fetch_run_row/count_child_runs · event_store fetch_delegate_spec/fetch_delegate_outcome · nodes 三件套/route 分支/执行体提取/execute_delegate_subtask/acreate_delegate_hitl_request/delegate_exec_node · graph 注册 · sse_stream _iter_delegate_sse_core · run_worker start_delegate_run_worker/settle_delegate_run_rejected · hitl/router depth 分流）py_compile + ruff 全绿。
- 测试：tests/test_lg_rag_delegate_run_tree.py 10 用例全 pass（真 PG 五键 blank）；修复两处首跑红（resumed seq 续 last_seq · rejected reason 透传）。
- 回归：目标 15 文件 210 passed 全绿；ruff All checks passed；全量脏树期红与 base 297363bd 同路径基线逐签对照（环境性/并发 flaky/结构性脏树期三分 · CI 终裁）。
- 图谱：01_modules.md lg_rag 行 P4-T7 备注 + HG-GRAPH-MODULES 签收行 · graph-compile.sh 绿。
- 过闸件：R1 审查文 GO/PASS · invoke_10/30 已落 · task lint 见 invoke_40 · registry entry active（CLOSE 后钉 wave_tip）。

## 必读列表

- workspace docs/01-scope/03-general-agent/18-p4-generalization-design.md §3/§7（设计真源 · commit e453a36）
- workspace docs/01-scope/03-general-agent/19-p4-contracts.md §7-§13（契约真源 · 同上 commit）
- app/ops/lg_rag/run_store.py（claim_child_run :110-162 · fetch_run_row/count_child_runs 本波新增 · TERMINAL_STATUSES :24）
- app/ops/lg_rag/run_worker.py（start_run_worker :98-187 纪律模板 · scan_orphan_runs_for_compensation :207）
- app/ops/lg_rag/sse_stream.py（_iter_lg_rag_sse_core :291 emit 纪律模板）
- app/ops/lg_rag/multi/nodes.py（route_next_subtask :1837- · tool_exec_node/_run_tool_capability · _approval_consumed :497-538 · _issue_delegation_token :677-702）
- app/ops/hitl/router.py（_execute_decided_resume :493 · _preflight_decided_resume · ResumeError code 词表）
- app/ops/hitl/resume.py（ResumeEventSink start_seq 纪律）· app/ops/hitl/auto_resume.py（env 三件套先例）
- tests/test_write_approval_gate.py（write 罐头/InMemoryHitlStore fixture 范式）· tests/test_lg_rag_run_tree_projection.py（真 PG 体例）
- docs/tasks/done/task_p4_t6_run_tree_ddl.md（T6 数据面前提 + 过闸体例先例）

## 思考轮控制

| 轮 | 结论 | early_stop |
|----|------|-----------|
| R0 | 范围七面对账 18/19 文锚 · T6/T8/T9 排除 | 否 |
| R1 | 失败路径十一条 · HITL 重跑幂等链定稿 | 否 |
| R2 | 非范围边界钉死（帧型词表/§14 被否项/签发面） | 否 |
| R3 | 关键决策八条（执行体提取 · seq 续 last_seq · depth 分流位 · delegate_spec 加性 · 轮询 1s 常量 · 建单去重 · banned 双前缀 · env 文档不登记） | 否 |
| R4 | 体例对账 T6 · 仓规条款一遵守 | 否 |
| R5 | 验收 9 条锚定 · 回退面明确 | 否 |

**actual_last_round**：R5 · **early_stop**：no · **residual_risks**：闸 off 默认 ⇒ 生产路径默认不消费本波代码（闸 on 由 T9 验收冒烟承接）

## 思考轮（actual_last_round=R5）

### R0 · 范围对账

委派书七条与 18/19 文锚逐条对齐：总闸三件套（§12）· 委派执行提升（§8.1 · 执行体提取 18 §3.4）· 令牌身份映射（§9 五行表 · 子侧自发签发 §3.9）· HITL 三段恢复（§10）· 父 join（§8.3）· 测试真 PG（§10 实证两条 + §13 失败路径表）· 图谱+落盘。T6（DDL/claim 本体）· T8（web）· T9（验收冒烟）全部排除。

### R1 · 失败路径推演

见「失败路径」节。核心链：HITL 重跑幂等 = 副作用闸在 capability_ainvoke 前（_approval_consumed fail-closed · 匹配键=(子 run_id, subtask_id, capability_id) §9）+ 建单 pending 去重 + 重复 resume 由 preflight status 闸拒（子终态后 not_interrupted）；重跑 seq 续 last_seq 防撞事件 uq（首版实现实测撞 uq 已修复 · 教训入档）。

### R2 · 非范围边界

帧型词表零新增（§11 · run.start/hitl.waiting/hitl.resumed/answer/done/error 全既有）；§14 被否项（DB 租约/多深度/root_run_id/合并流/children 端点）不碰；签发审批面（delegation_issue_hitl_required 父侧 dispatch 前 · nodes.py:1456-1470）零改；GUIDE_env_inventory 不登记（承 p4-t2 OPS_DOMAIN 先例 · env 注记入图谱行备注）。

### R3 · 关键决策记录

- **执行体提取 `_run_tool_capability` 闸链单真源**：18 §3.4 钉「从 tool_exec 提取的委派执行函数（闸链单真源：idempotency/circuit/budget/HITL/delegation 验签原样）」——提取为独立协函数，tool_exec_node 与 execute_delegate_subtask 双调用面共享同一函数体，禁两份闸链漂移；budget_run_id/emit_running 两参承载委派差异（配额键=父根 run_id §9 · 子 run 不发父流 running 帧）。
- **resumed 重跑 seq 续 last_seq**：ResumeEventSink start_seq 纪律（hitl/resume.py）同构——重跑与首跑共享 (run_id, seq) 唯一键，从 1 起必撞 uq_ops_lg_rag_run_events_run_seq（实测 asyncpg UniqueViolationError 修复入档）。
- **depth 分流位在 hitl/router._execute_decided_resume/_preflight_decided_resume**：19 §10②「resume 按 run 行 depth 分流」逐字——分流在 _open_event_sink 前（depth==1 无 checkpoint · ResumeEventSink 不适用）；depth 查询失败按非委派 best-effort 不阻断主链路。
- **run.start payload 加 delegate_spec 加性键**：19 §11 钉 run.start 加可选 parent_run_id；resume 重跑需重建 subtask/user/scope 规格，规格随首帧落盘（fetch_delegate_spec 读回）——加性 payload 键与 §11.5「消费方须容忍未知键」同口径豁免，不引 env 闸。
- **轮询间隔 1.0s 常量不做 env**：19 §8.3 钉 1s · env 面最小化（三件套之外不加键）。
- **建单 pending 去重（同 run_id+subtask_id 复用）**：重跑/重入防双单 · 承 hitl store alist(status="pending") 活读先例。
- **registry banned_prefixes=[alembic/, scripts/]**：本波不触 alembic（T6 已合 DDL）· 双前缀承 p4-t2 先例。
- **env 台账文档不登记**：GUIDE_env_inventory 不动（承 p4-t2 OPS_DOMAIN 未登记先例 · 图谱行备注承载 env 注记）。

### R4 · 体例对账

照 docs/tasks/done/task_p4_t6_run_tree_ddl.md：task 档结构/人工闸表/registry entry（base=297363bd · allowed_app_files 七件 · banned_prefixes=[alembic/, scripts/]）/invokes by-task 四件 {10,30,40,50}/R1 审查文 GO 机读词/spec-wave@3.5.0 task lint PASS 为闸；图谱签收承 :49 先例。仓规条款一遵守（走 20-R1 审查文非 --allow-no-review）。

### R5 · 收尾复核

验收 9 条逐条锚：env 解析 · route 对拍 · MAX_CHILDREN · happy path · HITL 三段（含 19 §10 实证两条）· rejected 收口 · 回归+全量+ruff · 图谱两件 · 过闸四件。回退 = revert 7 个 app 文件 + 测试 + 图谱/过闸件（闸 off 默认 ⇒ 生产面天然回退态 · 零迁移零数据面改动）。

## 实现备忘

### 偏差登记

1. **env 台账文档不登记**：委派书未列 GUIDE_env_inventory；承 p4-t2 OPS_DOMAIN 先例（同夜间波 · 未登记 GUIDE）——env 注记入 01_modules.md lg_rag 行备注 · 最小改动如实登记。
2. 其余无偏差：范围/非范围/铁律（帧型词表/cursor/§14 被否项）全部按契约执行。

### 限制登记

1. 闸 off 默认 ⇒ 生产路径默认不消费本波代码（route 走既有 Send(tool_exec) 逐字节零 diff）；闸 on 行为由 T9 验收冒烟承接（18 §7 S2/S3 样例）。
2. 子 run 无 checkpointer（重跑=重启 worker 全量重跑执行体 · 18 §3.4 裁定）；深度硬上限 1 为结构性（子执行体内无 route_next_subtask 通路 · 18 §3.3）。
3. 全量 pytest 环境性红若存在，与 base 297363bd 同路径基线逐签对照登记 · CI 终裁。

## 测试策略

pytest tests（CI 终裁 · 真 PG postgresql+asyncpg://ops:ops_password@localhost:5432/opsdesk_test · 五键 blank 前缀 OPS_HITL_PERSISTENCE= OPS_CAPABILITY_ALLOW_WRITE= OPS_CAPABILITY_ALLOW_WRITE_TAGS= OPS_CAPABILITY_PERSISTENCE= OPS_CAPABILITY_EXTRA_MANIFESTS=）；新增 tests/test_lg_rag_delegate_run_tree.py（env 解析 ×4 · route 对拍 ×2 · DB MAX_CHILDREN/happy/HITL 三段/rejected ×4）；目标回归 tests/test_lg_rag_run_tree_projection.py / test_lg_rag_run_tree_ddl.py / test_write_approval_gate.py / test_hitl_resume*.py / test_hitl_pending_decide.py / sse/lg_rag_multi 等 15 文件全绿；全量回归环境性红与 base 297363bd 同路径基线逐签对照；ruff check app tests 绿；allowed_app_files=[app/ops/hitl/router.py, app/ops/lg_rag/event_store.py, app/ops/lg_rag/multi/graph.py, app/ops/lg_rag/multi/nodes.py, app/ops/lg_rag/run_store.py, app/ops/lg_rag/run_worker.py, app/ops/lg_rag/sse_stream.py] 机判。

## 修订记录

| 日期 | 修订 |
|------|------|
| 2026-11-18 | 落卡（夜间自动执行波 · 授权 issue Cyning12/ops-desk-workspace#23 m03796 · 来源 workspace 18 文 §3/§7 + 19 文 §8-§13） |
