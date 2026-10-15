# invoke_20261014_30_implement — hitl-resume-async · 30 实现帽

## 结论

HITL resume 端点异步化实现落地：**pytest HITL 10 件面全绿（红集对红集零新增红）· ruff 绿 · 图谱编译绿 · 响应面钉死约束 D2 全守（状态码 200 · 顶层键 {ok,request,resume,replay,ts} 不删不改）**。TC8 live 实证归 40 棒，不在本帽。

## GATE_VERIFY（30 开工闸扫描）

| 闸 | 状态 | 真值 |
|---|---|---|
| HG-AUDIT-R1 | approved | task_hitl_resume_async.md 人工闸表（00 依维护者授权代签 · m00026） |
| HG-GRAPH-MODULES | approved | 同上 · 20 R1 核对 G-L1 预判相容 |
| HG-PILOT-OPSDESK-GLAYER | approved | 同上 |
| 分支 | task/hitl-resume-async（base master 56e4a9f） | 非 master 直改 |
| pre-30 invoke | 齐 | 本目录 invoke_20261014_10_task_draft.md / invoke_20261014_20_task_audit.md（R2 PASS） |

## 实现面（diff 六件 · 未 commit）

| 文件 | 改动 |
|---|---|
| app/ops/hitl/resume.py | `_resume_with`/`resume_hitl_run` 增 `preflight_only: bool = False` 尾参透传（:223/:312）；preflight 短路在两道快照检查（not_interrupted / stranded_checkpoint）**之后**、astream **之前**（:254），返 `{thread_id,approved,rejected,decided_by,preflight:True,state:{},answer:"",query:""}` 不驱动图；PG 路径 `apostgres_saver(setup=not preflight_only)`（:363 · preflight 不 setup） |
| app/ops/hitl/router.py | 抽 `_collect_decisions_or_raise`（:419 · _execute_decided_resume 改用 · 零 diff）；新增 `_preflight_decided_resume`（:483）· `_RESUME_IN_FLIGHT: dict[str, asyncio.Task[None]\|None]`（:480）· `_run_resume_in_background`（:502 · try 执行 / except logger.exception / finally pop）· `_best_effort_replay_cursor`（:516 · last_seq+make_cursor · 异常 warning 降级空串）；`resume_request`（:531）改写：404/状态守卫不变 → 在飞 409（:562-565）→ 占位 None（:567 · 防 TOCTOU）→ preflight（映射表逐字不变 · 异常 pop :573/:589）→ `asyncio.create_task`（:592 · name=hitl-resume-<id>）→ 响应已受理形（:609） |
| tests/test_hitl_resume_async.py | **新建 6 测**（红测先行 · 详见 TC1） |
| tests/test_hitl_resume.py | TC2b 适配 1 处 + `_drain` helper 落位（供三件测试文件导入） |
| tests/test_hitl_pending_decide.py | TC2b 适配 3 处 + `_resume_via(saver, outcomes)` 捕获形态 + async `_adrain` |
| tests/test_hitl_resume_events.py | 单点适配 2 处（语义迁移 · 见裁定记录） |
| tests/test_hitl_auto_resume.py | 单路径钉 ==1→==2（裁定 · 见下） |

## 30 裁定记录（决策点定稿 · 含 web 回执要点）

1. **D1 响应「已受理」形态**：`resume = {status:"accepted", thread_id, approved, rejected, decided_by}`；`replay = {run_id, cursor:best-effort, events_persisted:0, events_failed:0, persisted:bool(run_id), re_interrupted:False}`；**状态码 200 · 顶层键 {ok,request,resume,replay,ts} 不删不改（D2 全守）** → web 零改动预判成立（`HitlResumeResponse.resume` 为 unknown 弱消费）。
2. **F2 在飞重复 resume**：409 + detail「该申请的恢复正在执行中，待沉降后再试」（承 no_unlock→409 语义区 · 占位防 TOCTOU：先占位再 preflight · 失败 pop）。
3. **F3 崩溃兜底（不新造扫描器）**：进程内单飞字典随进程消失无残留；重调 resume 幂等重投递（preflight not_interrupted 防重跑已完成者）；auto 模式既有 `scan_approved_not_resumed_once` 周期兜底；replay 永久悬 409 的孤儿补偿周期接线归 task_lg_rag_sse_disconnect_completion 另案。
4. **语义迁移（web 回执）**：`run_owner` 归属反查失败的「明说」从响应面（旧 `replay.persisted=false`）迁移到后台执行——受理响应无法预知解析结果，信号改由 error 日志 + 事件流缺席承担（opener 被调 · persist_run_event 零调用）。web 侧对该键为弱消费，预判零改动；若 web 有依赖 `replay.persisted==false` 做提示的逻辑须复查。
5. **单路径钉 ==1→==2**：test_hitl_auto_resume.py:761 钉 `await resume_hitl_run(` 调用点唯一 → preflight 探针与后台执行体调**同一驱动器**，非第二恢复实现；钉语义（禁第三实现）保留，计数改 ==2 并改写注释。

## TC 验收逐项

- **TC1 红测先行 ✓**：test_hitl_resume_async.py::test_resume_returns_before_execution_completes（闸门 fake · preflight 秒回 / 执行路径 await threading.Event · Timer 2s 防死锁）。**RED 实证**（修复前 6 测全红，失败原因钉死）：「resume 端点仍同步等执行（2.01s）」· KeyError 'status' · 在飞第二发 200≠409 · RuntimeError 同步传播 · TypeError: resume_hitl_run() got an unexpected keyword argument 'preflight_only'（×2）→ 修复后 **6 passed**。
- **TC2 契约零回归对拍 ✓**：test_hitl_resume.py 映射表测（no_thread_id/no_decision/not_interrupted/stranded_checkpoint/no_unlock→409 · checkpointer_not_configured→503 · resume_failed→502）全绿——preflight 路由经过 router.resume_hitl_run 引用，映射表逐字未动；resume_mode 白名单未知值 400 / 状态守卫 409 / 驳回 resume 收工链（test_hitl_pending_decide.py::test_decide_rejected_then_resume_settles verdict==settle · hitl_unlocked_ids==[]）全绿。
- **TC2b 旧测影响面 ✓**：4 处必破断言逐点适配（形态：fake 捕获 outcome 到列表 · 响应断 `resume.status=="accepted"` · `_drain`/`_adrain` 沉降后断 outcome）——test_hitl_resume.py::test_resume_endpoint_drives_the_graph · test_hitl_pending_decide.py::test_decide_approved_then_resume_drives_the_graph / test_decide_rejected_then_resume_settles / test_db_decide_survives_store_rebuild_then_resume（真 PG checkpointer 全链 · outcomes+_adrain）。**decide 面 5 处零 diff 实证绿**：test_hitl_pending_decide.py:367-368 · test_hitl_auto_resume.py:308/:417-418/:570/:909（未触碰）。
- **TC3 终帧逐键钉死 ✓**：ResumeEventSink.close() 终帧 done{status:'resumed', latency_ms:int≥0, 无 model 键} 由 test_hitl_resume_events.py sink 面既有断言覆盖（零 diff · 全绿）；live 逐键归 TC8（40 棒）。
- **TC4 落盘链零 diff ✓**：test_resume_endpoint_returns_replay_cursor——沉降后 sink.persisted==3（open/aggregator/done seq 连续 4/5/6）· sink.cursor=='r1:6' · turns.assert_awaited_once_with(thread,user,原始问题,批准后的答案)（_persist_resumed_turns 路径）。
- **TC5 幂等与防重 ✓**：在飞二次 resume=409（test_resume_in_flight_duplicate_is_409 · detail 含「执行中」）；沉降后二次 resume=409（preflight not_interrupted 双钉：test_preflight_refuses_finished_thread 驱动器层 + 映射表测端点层 :485）。
- **TC6 崩溃兜底 ✓**：test_resume_after_background_failure_redispatches——后台执行抛异常 → 在飞登记 finally pop → 重调 resume 幂等重投递成功（F3 裁定接线面断言 · 不永久悬 409）。
- **TC7 pytest 全量对拍 ✓**：HITL/auto-resume 10 件面 152 绿（test_hitl.py 一件红见下）；新增异步单测 6 绿。**全量 pytest：7 failed / 1815 passed —— 红集与 master 56e4a9f 基线完全同集（git worktree 对拍 · 同 .env 同 DB）**：test_capability_lookups.py×3（.env 依赖 · 无 .env 时 master 绿/有 .env 时 master 同红）· test_lg_rag_multi.py::test_unknown_tool_at_invoke_recorded_and_continues（同 .env 因）· test_hitl.py::test_db_store_alist_really_executes_on_asyncpg（环境因 · master 同红）· test_multi_replica_dualproc.py×2（双进程环境因 · master 同红）。**零新增红**。
- **TC8 live 实证**：归 40 棒（echo p95<1s · replay 409→200 · T-W2 S3 链 + TC5 回归）· 菜谱 docs/harness/invokes/by-task/hitl-resume-replay-contract/invoke_20261013_40_verify.md。

## 环境留痕（排障记录 · 40 棒可参考）

- 本机 ops_hitl_requests 残留 63 行（10-10~10-14 测试累积）曾致 pending 列表 LIMIT 50 挤爆假象「B 看不到 A 的申请」——已清；dualproc 两测红为环境因（master 基线同红）。
- TestClient portal loop 纪律：异步化后沉降等待（_drain）必须在 `with TestClient` 块**内**做，否则 RuntimeError: Event loop is closed。
- `last_seq` 真库调用会把 asyncpg 连接绑到 portal loop——端点测需 patch `app.ops.lg_rag.event_store.last_seq`（resume_events 两测已顶）。

## 图谱回写

- docs/_tech_graph/l1/01_modules.md hitl 行尾追加 hitl-resume-async 备注（异步化形态/preflight/单飞/F3 裁定 · 零新表/迁移/SSE 事件 · 不新增一级模块 · 零新跨模块边 · 不增 implementedBy）· `./scripts/graph-compile.sh` 绿。与 task graph_delta 预判一致（备注回写 · 无模块增删）。

## 禁区自查

- 未 commit / 未 push（git add 仅本人六件 + 新测 + 图谱行 · 见 00 收口指示）· 未动 decide 语义 / resume_mode 白名单 / replay 409 契约 / ResumeError 映射表 · 未动别线文件（app/main.py 等）· 未新造扫描器/模块/表/事件类型 · 映射表测试面零破（preflight 复用 router.resume_hitl_run 引用）。

## 交接 40 棒

- live 机验按 task TC8 菜谱：起服三坑 + echo 六 env 组；resume p95<1s 门槛；秒回后 replay 立即打=409 在飞（Retry-After: 2）→ 沉降后 200 · 帧 seq 连续 · 终帧 done{resumed, latency_ms 实值}；T-W2 S3 链 + TC5 二次 resume 409 回归。
- web 回执已落：../ops-desk-web/docs/harness/invokes/by-task/hitl-resume-async-handoff/invoke_20261014_30_api_receipt.md（响应面终态 + 语义迁移一点）。
