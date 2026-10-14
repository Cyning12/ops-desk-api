# task_hitl_resume_async — POST /hitl/requests/{id}/resume 异步化（JC-F1 · B 方案 · 复用 RunWorker/auto_resume）

> **状态**：active（2026-10-14 · HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 全 **approved** · 00 依维护者 2026-10-14 会话授权代签 · R 轮真值 docs/harness/reviews/task_hitl_resume_async_audit_R2_20261014.md PASS · **30 可开工（红测先行）**）
> **类型**：性能/契约缺口收口（JC-F1 · web 00 跨仓移交 B 方案 · api 单边异步化）
> **依据**：web 00 移交令 `../ops-desk-web/docs/harness/invokes/by-task/hitl-resume-async-handoff/invoke_20261014_00_dispatch_api.md`（维护者裁定 B 方案）· JC-F1 40 机验实证（web 分支 `task/web-api-joint-check` @ a2b1b1f · 未并 web 主线）· 本仓锚点亲读核真（base `master` 56e4a9f）
> **分支**：`task/hitl-resume-async`（base `master` 56e4a9f）

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `hitl_resume_async` |
| **git_branch** | `task/hitl-resume-async` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 红测先行（阻塞闸门执行体钉「响应先于执行完成返回」· 修复前 RED=请求被卡死）+ 契约零回归对拍（ResumeError 映射表 / resume_mode 白名单 / 终帧逐键）+ 新增异步 resume 单测（幂等防重 / 崩溃兜底模拟）+ live 实证留 40（echo 场景 p95<1s · replay 在飞 409→沉降 200 · 菜谱复用 hitl-resume-replay-contract 40 invoke 的起服三坑 + echo 六 env 组） |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1`（`app/ops/hitl/router.py` resume 端点异步化 + auto_resume/run_worker 复用面 · 模块行为表述 · 30 按实判回写） |
| **graph_delta** | 预期 `docs/_tech_graph/l1/01_modules.md` hitl 行备注回写（resume 同步执行 → 异步派发行为表述 · 无模块增删预判） |
| **graph_delta_note** | 若 30 实证零图谱表述面变化，改填 `none` 并注理由（以 20 R1 核对为准） |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 无文档站/WikiTrack 变更（端点异步化 + 契约面零 diff 收口） |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,20,30,40` |
| **invoke_retention_profile** | `default`（10,30,40 留存 · 涉跨仓契约决策/响应面回执留 20 R1 审查文同档 · **required_invoke_hats 优先于 profile**（v2.12 · 20 留存不因 default 省略）） |
| **experience_capture** | `required`（异步化边界 + 红测先行 + 跨仓契约回执 · 落盘 `docs/experience/`） |
| **kpi_aggregator** | `n/a` |
| **orchestration** | 10 落稿（本文件）→ 20 R1 书面审查 → 00 代签三闸（维护者 2026-10-14 授权 · 见人工闸表）→ 30 红测先行 → 40 机验（echo live p95 + 响应面回执 web）→ PR + CI 绿 → CLOSE（commit 由 00 统提 · 10 棒不 commit） |
| **freeze_id** | `lg-rag-sse-v1`（不新 freeze · 不新 event_type · SSE 帧序列/终帧逐键零 diff · resume HTTP 响应键名/状态码不动 · `resume` 键值形态变「已受理」· 回写 05 按实判） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 20, 30 | 2026-10-14 00 代签（维护者会话授权「授权00签收后续所有文档」· invoke_10 留痕）· 初稿经 20 R1 FAIL 回填 → R2 PASS（reviews/task_hitl_resume_async_audit_R2_20261014.md） |
| HG-AUDIT-R1 | approved | 30 | 2026-10-14 00 代签（维护者会话授权同上）· R 轮真值 = reviews/task_hitl_resume_async_audit_R1_20261014.md（FAIL）→ r2.md（PASS · N1+n1–n4 全核销） |
| HG-GRAPH-MODULES | approved | 30 | 2026-10-14 00 代签（维护者会话授权同上）· 20 R1 核对 G-L1 预判与 docs/_tech_graph/l1/01_modules.md 现状相容 · **30 按实判回写义务存续** |

## 背景与目标

### 背景（JC-F1 · web 40 机验实证）

- 实证来源：`../ops-desk-web/docs/harness/invokes/by-task/web-api-joint-check/invoke_20261013_40_verify.md`（**在 web 分支 `task/web-api-joint-check` @ a2b1b1f · 未并 web 主线** · 读取须 `git -C ../ops-desk-web show a2b1b1f:<path>`）
- 服务端实测：decide(approved) → resume 请求被服务端**同步执行 130–310s**（JC-F1 结论行）；axios 全局 timeout 30_000（web `src/api/http.ts:50`）→ decide 200 后 30.1s resume 请求 `net::ERR_ABORTED`（jc_tc3v2_network.json）；前端 catch 把审批卡片退回「待审批」；**后端实际已跑完**（日志「HITL 恢复完成 replay=run:18」）
- 终帧实证：`done{status:"resumed", latency_ms:306187}`（run b3b2da40 · 18 帧 · jc_tc3v3_replay.sse）· `done{resumed, 124348}`（run 04417a5b）· jc_tc3v3_network.json 步骤 `server-resume-settled="replay 200 at 107.6s"`
- 危害：30 秒掐断 ≠ 服务端失败 —— 服务端跑完了、前端误判回「待审批」，审批卡片状态误导 + 用户重复点击风险

### 根因锚点（亲读核真 · base `master` 56e4a9f）

- 请求内同步执行：`app/ops/hitl/router.py:466-529` `resume_request`；**`router.py:494` `result = await _execute_decided_resume(row)`** 在请求内同步 await 整条恢复链 = 130–310s 来源
- 执行体：`app/ops/hitl/resume.py:288` `resume_hitl_run`（checkpointer fail-closed `ResumeError("checkpointer_not_configured")` :332-339 · 包装 `resume_failed` :353-355）
- 落盘链：`router.py:360-396` `_open_event_sink`（**`run_owner` 归属反查 :378 不可省** · 缺归属 → sink=None + error 日志 :372-388 · last_seq 基线 :390）+ `ResumeEventSink` 类 `resume.py:54-162`（close 终帧 :124-137 · `latency_ms=int(perf_counter)` :135）+ `_persist_resumed_turns` `router.py:399-415`（`persist_thread_turns` :413 补落 user/assistant turn）
- 现成复用机制（30 实现方向约束 · **复用、不另造轮子**）：
  - PR #250 `app/ops/lg_rag/run_worker.py` RunWorker：进程内 asyncio.Task 持 astream 循环、emit→event_store+fanout（模块 doc :1-6）· `RunEventBus` :25-61（`_BUS_END` 哨兵 :22）· `start_run_worker` run_id 单飞注册 :92-168（`_workers` dict :70 · 同 run_id 复用 bus :108-111 · `asyncio.create_task` :158）· SSE 断连只取消 subscriber 不 cancel worker · `scan_orphan_runs_for_compensation` :188-245（`list_open_runs` 候选 + 活跃 worker 跳过 + 已闭跳过 + 补 `done{status:"disconnected"}` → replay 不再永久 409 · `LG_RAG_ORPHAN_STALE_SECONDS` 默认 300 :172-185）
  - HITL 侧同源异步派发已存在：`app/ops/hitl/auto_resume.py` `schedule_auto_resume` :138-158（`asyncio.create_task` 派发不阻响应 · `_BACKGROUND_TASKS` 模块级句柄集 :65 · 台账 hitl_auto_resume_triggered/compensated）· `_claim_and_execute` :193-234（PG 行锁认领 `store.aclaim_approved_for_resume` FOR UPDATE SKIP LOCKED · `run_is_terminal` 守卫 :212 · `_interrupt_metadata_visible` 就绪校验 :218 不就绪 defer 等下轮）· 补偿扫描 `scan_approved_not_resumed_once` :237-274（approved ∧ 未过 TTL ∧ run 非终态 ∧ 同 run 无 pending 四条件）· **执行唯一走 `router._execute_decided_resume` :229-231（同源纪律 · 无状态恢复 · 禁第二条恢复实现 :11-14）**
- 30 方向约束（10 起草 · 非实现）：**请求内保留同步可判定的 fail-fast 守卫**（映射表不变 ⇒ `no_decision/stranded_checkpoint/checkpointer_not_configured` 等须仍在请求内判定）→ **派发立即返回 200 携 replay cursor** → 执行异步跑 · 事件照常落盘 · 前端 replay 追帧
- 接线面真相（30 裁定 · 非 10 预设）：`scan_orphan_runs_for_compensation` 全仓调用方仅 `tests/test_lg_rag_sse_run_worker.py`（生产侧周期接线未见于 app/）；`auto_resume` 补偿扫描器仅 `auto_resume_mode()==MODE_AUTO` 时 lifespan 挂（`app/main.py:52-54` · manual 零创建）→ manual 模式下「投递后崩溃」无周期兜底 → **30 必须裁定接线面**（resume 专属扫描 / 复用 lg_rag 扫描 / 其他），10 不越权

### 目标

1. resume **秒回 200 携 replay cursor**（p95 < 1s · echo 场景 live 实证）；执行异步跑完、事件照常落盘、前端 replay 追帧
2. 契约面零回归：钉死表（下节）逐项对拍零 diff；**web 侧零改动**（响应键名/状态码不动 · `resume` 键值形态变「已受理」）

## 范围

- **F1 · resume 请求异步化**：`router.py:466-529` `resume_request` 同步 await :494 改为「守卫 + 派发 + 秒回」；响应键集 `{ok,request,resume,replay,ts}`（:513-533）**键名全保留**，`resume` 键值变「已受理」形态（见契约决策点）
- **F2 · 异步执行单飞与幂等**：同 pending_id 在飞时重复 resume = 409/幂等（承映射表 `no_unlock`→409 语义区 · 具体形态 30 裁定）；进程内单飞句柄模式参照 `_BACKGROUND_TASKS`（auto_resume.py:65）/ RunWorker `_workers`（run_worker.py:70）
- **F3 · 崩溃兜底**：投递后进程崩溃 → 孤儿补偿扫描恢复路径（复用 `scan_orphan_runs_for_compensation` 形态 / `scan_approved_not_resumed_once` 四条件 · **接线面 30 裁定** · 勿让已判定单据永久悬 409 —— 孤儿 run 22b65ce2 永久 409 为反面实证）
- **F4 · 落盘链行为零 diff**：`ResumeEventSink` / `_persist_resumed_turns` / `run_owner` 反查不改「怎么落」，只改「何时被调」；终帧 `done{status:"resumed", latency_ms:int≥0, 无 model 键}` 逐键不变
- **F5 · 响应面回执**：40 机验完成后按启动令 §5 路径回执 web（落点 `../ops-desk-web/docs/harness/invokes/by-task/hitl-resume-async-handoff/`）

## 非范围

- decide 端点语义（`router.py:184-269` · `resume_mode` 求解/白名单/auto 触发挂点 `schedule_auto_resume` :246-254）零改动
- replay 409 契约（`app/ops/lg_rag/event_store.py:246` `refuse_in_flight` · replay 端点 `Retry-After: 2`）零触达
- web 侧复验（联调 TC3 链重跑属 web agent · 本 task 只按 §5 回执响应面）
- 落盘链重构（sink/turns/归属反查行为零 diff · 异步化只改「何时被调」不改「怎么落」）
- OA callback 签名面（不挂触发器 · 零 diff）
- SSE live 流 / RunWorker 订阅面（复用其机制形态 · 不改造 `run_worker.py` 本体）
- `OPS_HITL_AUTO_RESUME` 全局默认 manual fail-closed 面（`auto_resume_mode` 不动）
- 多副本部署 / DB 租约（承 RunWorker MVP 进程内边界 · 另立）
- **本 task 本棒（10 起草）app/ 与 tests/ 零改动 · 本 PR 纯 docs**；30 改码须 HG-AUDIT-R1 approved 后另棒

## 契约钉死（不可回归项 · 启动令 §4 逐项锚定）

| 钉死项 | 现值锚点（亲读核真 · base 56e4a9f） | 本 task 约束 |
|---|---|---|
| decide/resume 两步端点 | decide `router.py:184-269` · resume `router.py:466-529` | 两步不合并 · decide 语义零 diff |
| `resume_mode` 白名单 | 端点手工校验 `router.py:207-211`（未知值 400）· `_DecidePayload` docstring :116-120 · `RESUME_MODES=(inherit,immediate,manual)` `auto_resume.py:58-62` | 白名单不动；immediate 语义 = **立即调度**（非同步跑完）· 属契约钉死项 |
| 驳回可 resume | 状态守卫 `router.py:487-491`（approved/rejected 均可 · 否则 409）· docstring :478-480 | 驳回也必须能 resume 收工（等待态终帧），不变 |
| 终帧 done 键 | `resume.py:131-136`（close :124-137）：`status:"resumed"` · `latency_ms:int(perf_counter)` ≥0 · **无 `model` 键** | 逐键不变；status 枚举不变（resumed / waiting_approval） |
| replay 在飞 409 | `event_store.py:246` `refuse_in_flight` · `app/ops/lg_rag/router.py:417-421`（`headers={"Retry-After": "2"}` :420 设置点）· 实证 `Retry-After: 2` + body `{"detail":"Run is still in flight; retry after it settles."}`（hitl-resume-replay-contract TC5） | 不变；async resume 在飞期间 replay 立即打 = 409 属预期，沉降后 200 |
| ResumeError→HTTP 映射 | `router.py:495-509`：no_thread_id/no_decision/not_interrupted/stranded_checkpoint/no_unlock→409 · checkpointer_not_configured→503 · 其余→502 | 映射表不变；同步可判定错误仍请求内 fail-fast |

## 契约决策点（启动令 §5 · 待 30/00 裁定）

| # | 决策点 | 选项 | 推荐 | 裁定人 |
|---|---|---|---|---|
| D1 | resume 响应 `resume` 键值变「已受理」形态 | 键值内嵌 `{status:"accepted", ...}` 等受理表述 | A | 30 定稿 · 40 回执 web |
| D2 | 响应面零 diff 约束 | 状态码保持 200 · 键名不删不改（`{ok,request,resume,replay,ts}`）· web 零改动（`HitlResumeResponse.resume` 弱消费） | A | 钉死约束 · 非可选 |
| D3 | 若 30 发现必须动响应面（状态码/键名） | 先回执 web（落点 handoff 目录 · 写入本文件 failure_paths / 决策记录）再动 | A | 钉死纪律 · 非可选 |

## 失败路径

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|---|---|---|---|
| 异步执行失败（LLM 故障/checkpointer 执行期故障等） | 事件流/台账可见（ResumeEventSink 事件照常落盘 · 失败事件入事件流）· 不再以 HTTP 状态码表达（请求早已 200 返回） | 按事件流提示人工介入；单据仍在 approved/rejected 可再次 resume | 前端 replay 追帧可见失败事件；卡片不再误回「待审批」 |
| `run_owner` 归属反查失败 | sink=None + error 日志（router.py:372-388）· 事件不落盘 · 与同步现状同语义 | 修复归属后再次 resume | replay 无新增帧 · 日志可查 |
| 投递后进程崩溃 | 任务丢失 → 孤儿补偿扫描恢复（F3 · 复用 scan_orphan_runs_for_compensation 形态 / scan_approved_not_resumed_once 四条件 · **接线面 30 裁定** · 勿永久悬 409） | 扫描周期内自动恢复 | replay 先 409 在飞 → 补偿后沉降（done/disconnected 终帧） |
| 重复 resume（用户重试/双击） | 在飞期间二次 resume = 409/幂等（F2 · 承 no_unlock→409 语义区 · 30 裁定具体形态）；沉降后二次 resume 维持 409（TC5 回归） | 沉降后按单据状态判定 | 409 提示 |
| 响应面被改动（状态码/键名） | **禁止** · 违反钉死约束 D2；若必须动须先回执 web（D3） | n/a | web 侧须同步改（违背 web 零改动前提） |
| decide 时 `resume_mode=auto` 已触发自动恢复 | auto_resume 链路既有行为 · 手动 resume 走 `_execute_decided_resume` 守卫幂等（同源纪律 · 零 diff） | n/a | 409/已恢复（承现状） |
| checkpointer 未配置 | 请求内 fail-closed 503 `checkpointer_not_configured`（映射表不变 · 同步可判定守卫留请求内） | 配置后重试 | 503 detail |

## 验收标准

- [ ] **TC1 红测先行**：阻塞闸门执行体（测试替身 await 闸门）钉「resume 响应先于执行完成返回」；修复前 RED = 请求被卡死（测试超时/断言失败），修复后 GREEN
- [ ] **TC2 契约零回归对拍**：ResumeError 映射表逐条（no_decision/stranded_checkpoint/checkpointer_not_configured 等→409/503/502）· resume_mode 白名单未知值仍 400 · 状态守卫（非 approved/rejected→409）· 驳回 resume 收工链
- [ ] **TC2b 旧测 grep 影响面（行为变更适配 · 20 R1 N1 回填）**：消费 **resume 端点响应** outcome 键、异步化后必破的断言 4 处（基线已亲读核真 · 30 开工前 grep 复核）——`tests/test_hitl_resume.py:362`（`res.json()["resume"]["state"]["route"] == "replan"`）· `tests/test_hitl_pending_decide.py:501`（`resumed.json()["resume"]["state"]` → `hitl_unlocked_ids==[_T1]` / `react_observation.verdict=="replan"`）· `tests/test_hitl_pending_decide.py:528`（驳回链同形态 → `verdict=="settle"` · `hitl_unlocked_ids==[]`）· `tests/test_hitl_pending_decide.py:661`（`res2.json()["resume"]["state"]`）——**逐点裁定适配形态**（改断言为「已受理」形态 + replay 追帧取终帧断言 / 或经事件流取 outcome）；并断言 **decide 面 `resume` 块消费点零 diff 不受影响**（防误改 · decide 面属非范围钉死）：`tests/test_hitl_pending_decide.py:367-368`（`required`/`endpoint`）· `tests/test_hitl_auto_resume.py:308`（`resume` 块全字典 {required, method, endpoint}）/ `:417-418` / `:570` / `:909`（`auto_triggered`/`required`）
- [ ] **TC3 终帧逐键钉死**：replay 终帧 `done{status:"resumed", latency_ms:int≥0, 无 model 键}` 逐键断言 · status 枚举零 diff
- [ ] **TC4 落盘链零 diff**：异步执行后 user/assistant turn 照常补落（_persist_resumed_turns 路径）· 事件 seq 连续
- [ ] **TC5 幂等与防重**：在飞期间二次 resume = 409/幂等（按 F2 裁定形态断言）· 沉降后二次 resume 维持 409（承 hitl-resume-replay-contract TC5）
- [ ] **TC6 崩溃兜底**：模拟投递后执行未完成（任务丢失）→ 补偿扫描路径恢复（按 F3 裁定接线面断言 · 不永久悬 409）
- [ ] **TC7 pytest 全量对拍**：HITL/auto-resume 面 **10 件** —— `tests/test_hitl.py` · `test_hitl_approval_consumption.py` · `test_hitl_approved_replan_quality.py` · `test_hitl_auto_resume.py` · `test_hitl_pending_decide.py` · `test_hitl_resume.py` · `test_hitl_resume_events.py`（test_hitl*.py 7 件）+ `test_lg_rag_sse_hitl.py` · `test_lg_rag_sse_resume.py` · `test_lg_rag_sse_run_worker.py`（3 件）+ 新增异步 resume 单测 · 以同 base 基线对拍零新增红（红集对红集）
- [ ] **TC8 live 实证（40 棒 · echo 场景）**：resume p95 < 1s；秒回后 replay 立即打 = 409 在飞（Retry-After: 2）→ 沉降后 200 · 帧 seq 连续 · 终帧 `done{status:"resumed", latency_ms 实值}`；回归 T-W2 S3 链 + TC5 二次 resume 409（菜谱复用 `docs/harness/invokes/by-task/hitl-resume-replay-contract/invoke_20261013_40_verify.md` 起服三坑 + echo 六 env 组 + attachments/tc5_s3_step1.sh/step2.sh）

## 依赖

- 移交令原文：`../ops-desk-web/docs/harness/invokes/by-task/hitl-resume-async-handoff/invoke_20261014_00_dispatch_api.md`（§4 契约钉死 / §5 决策点 / §6 验收逐字）
- JC-F1 证据：web 分支 `task/web-api-joint-check` @ a2b1b1f（invoke_20261013_40_verify.md + jc_tc3v2_network.json / jc_tc3v3_network.json / jc_tc3v3_replay.sse · **未并 web 主线 · 工作树仅存 gitignored `*.log`** · 读取须 git show 该分支）
- 本仓锚点：见「根因锚点」节（base `master` 56e4a9f · 行号漂移按实校正）
- 菜谱复用：`docs/harness/invokes/by-task/hitl-resume-replay-contract/invoke_20261013_40_verify.md`（起服三坑：① OPS_CHAT_TRACER=off ② env -u 剥九个 proxy 变量（NO_PROXY 裸 ::1 炸 httpx）③ echo 能力组四 env · live env 六组 · uvicorn 127.0.0.1:8050）
- web 回执落点：`../ops-desk-web/docs/harness/invokes/by-task/hitl-resume-async-handoff/`
- 无代码面阻塞依赖（RunWorker / auto_resume 补偿机制已在 master · PR #250）

## 给执行帽的必读列表

1. 本 task 全部锚点行逐一亲读（`router.py:360-533` · `resume.py:54-162/:288-355` · `auto_resume.py` 全文 313 行 · `run_worker.py` 全文 245 行 · `event_store.py:128-170/:240-250` · `main.py:46-59` · **禁信转述 · 行号漂移按实校正**）
2. 移交令原文（web handoff invoke · §4/§5/§6 逐字）
3. `docs/standards/CODING_BACKEND_L2_v1_zh.md`
4. 菜谱：`docs/harness/invokes/by-task/hitl-resume-replay-contract/invoke_20261013_40_verify.md`（起服三坑 · echo env 组 · tc5 脚本）
5. `tests/test_hitl_auto_resume.py` + `tests/test_hitl_resume.py` + `tests/test_lg_rag_sse_run_worker.py`（同源派发 / 补偿扫描既有测试面）
6. `docs/tasks/active/task_lg_rag_sse_run_worker.md` / `docs/tasks/active/task_lg_rag_sse_disconnect_completion.md`（RunWorker 波次上下文 · 孤儿补偿周期接线归属另案 · 本 task 引用须注明裁定面）

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|---|---|---|---|---|
| R0 问题框定 | 完成 | false | | JC-F1 现象与根因锚点一致 · B 方案方向已裁定 |
| R1 证据收集 | 完成 | false | | web 证据在未并主线分支 a2b1b1f（已照登）· 复用面盘点完成 |
| R2 方案生成 | 完成 | false | | 请求内守卫+异步派发方向定稿 · 接线面留 30 裁定 |
| R3 反例与边界 | 完成 | false | | 7 条 failure_paths · manual 无扫描器缺口已显式化 |
| R4 验收与可测性 | 完成 | false | | TC1 红测先行防恒绿 · TC8 live p95<1s 门槛明确 |
| R5 收口 | 完成 | true | 范围/钉死/决策点/failure_paths/验收互洽 · 无新增疑问 | 接线面裁定（F3）与「已受理」键值形态由 30/00 落地时定稿 |

**actual_last_round**: R5

### R0 · 问题框定

- 问题：JC-F1 —— decide(approved) 后 resume 请求被服务端同步执行 130–310s，axios 30s 掐断 `net::ERR_ABORTED`，后端跑完但前端误回「待审批」
- 根因锚点亲读核真：`router.py:494` `await _execute_decided_resume(row)` 请求内同步执行（`router.py:466-529`）· 执行体 `resume.py:288 resume_hitl_run`
- 方案空间：A=web per-request timeout（维护者裁定不单独做）· **B=api 单边异步化（维护者裁定 B · 复用 PR #250 RunWorker / auto_resume 机制）**
- 闸面：三闸全 pending · 10 起草零签闸 · HG-AUDIT-R1 approved 前 30 拒改码
- 结论：问题定义闭合（同步执行 → 秒回+异步派发）· 进入证据收集

### R1 · 证据收集

- web 40 机验逐字核真（a2b1b1f）：axios 30_000（web src/api/http.ts:50）· 30.1s ERR_ABORTED · 终帧 done{resumed, latency_ms:306187/124348} · replay settled 200 at 107.6s
- 证据可得性真相：JC 证据在 web 分支 `task/web-api-joint-check` @ a2b1b1f · **未并 web 主线** · 工作树仅存 gitignored `*.log`（与启动令「证据只读 ../ops-desk-web/docs/harness/.../web-api-joint-check/」字面出入 · 照登并给出 git show 读取法）
- 复用面盘点：RunWorker 三件套（bus :25-61 / worker :92-168 / orphan scan :188-245）+ HITL 同源派发（auto_resume.schedule_auto_resume :138-158 · 行锁认领 · 补偿扫描 :237-274）
- 接线面真相：orphan scan 生产侧无调用方（仅 tests）；auto_resume 扫描器仅 MODE_AUTO lifespan 挂（main.py:52-54）→ **manual 模式无周期兜底**
- 结论：证据充分 · 复用机制现成 · 接线缺口显式化 → 进入方案生成

### R2 · 方案生成（10 方向约束 · 非实现）

- 形态：请求内同步可判定守卫保留（映射表不变 ⇒ no_decision/stranded_checkpoint/checkpointer_not_configured 等须请求内 fail-fast）→ 派发（asyncio.create_task · 复用 auto_resume 同源派发形态）→ 秒回 200 携 replay cursor
- 执行唯一走 `_execute_decided_resume`（router.py:418-463 · auto_resume 同源纪律 :11-14 禁第二条恢复实现）—— 异步化只是「调用点从请求内移到后台 task」
- `resume` 键值「已受理」形态 · 状态码保持 200 · 键名不删不改（web 零改动前提 · `HitlResumeResponse.resume` 弱消费）
- 崩溃兜底：复用补偿扫描机制形态（scan_approved_not_resumed_once 四条件 / scan_orphan_runs_for_compensation）· **接线面留 30 裁定**
- 结论：方向互洽于钉死表 → 进入反例

### R3 · 反例与边界（failure_paths）

- 7 条失败路径成表（见「失败路径」节）：异步失败可见形态 / run_owner 反查失败 / 崩溃孤儿 / 重复 resume 幂等 / 响应面零 diff 回执纪律 / auto_resume 同源零 diff / checkpointer fail-closed
- 关键张力：映射表不变 ⇒ 同步守卫必须留请求内（否则 409/503 变「先 200 后失败」，违反钉死项 6）；执行期失败只能走事件流/台账（FP-1）
- 结论：边界覆盖完备 · 每条验收可机断 → 进入 R4

### R4 · 验收与可测性

- TC1 红测先行（阻塞闸门执行体 · 修复前 RED=请求被卡死 · 防恒绿）
- TC2/TC3 契约对拍（映射表 / 白名单 / 终帧逐键 · replay 409 Retry-After: 2）
- TC4 落盘链零 diff（turns / 终帧 seq 连续）· TC5 幂等 · TC6 崩溃兜底 · TC2b 旧测 grep 影响面（4 处必破断言 + decide 面零 diff 区分）· TC7 全量对拍（10 件 HITL/auto-resume 测试文件面 + 新增单测 · 零新增红）· TC8 live echo p95<1s + replay 在飞 409→沉降 200 + T-W2 S3/TC5 复跑
- 结论：验收全部可机断 · 与钉死表一一对应 → 收口

### R5 · 收口

- early_stop：范围/非范围/钉死/决策点/失败路径/验收互洽 · 无新增疑问
- residual：接线面（F3）与「已受理」具体键值形态由 30 实现 / 00 回执时定稿；web 证据分支未并主线已照登依赖节
- 10 起草完成 · 移交 20 R1 书面审查

### 自检结论（执行者）

**10（2026-10-14）**：初稿落稿 · 锚点全亲读核真（base `master` 56e4a9f · 移交令/JC-F1 证据/router.py:360-533/resume.py:54-162,:288-355/auto_resume.py 全文/run_worker.py 全文/event_store.py/main.py:46-59）· lint PASS（E1–E8 零 error · 实证见 invoke_10 门禁节）· 三闸 pending 零签（维护者授权 00 代签留痕 · 签署动作归 00）· **20 R1 FAIL 退回已回填**（N1 旧测 grep 影响面 TC2b 四点亲读核真落验收 + n1–n4 · 复跑 lint PASS）· 30/40 执行者结论待签闸后回填。

## 修订记录

| 日期 | 版本 | 作者 | 变更 |
|---|---|---|---|
| 2026-10-14 | v0 初稿 | 10-task | 承接 web 00 移交令（B 方案）落稿 · 锚点亲读核真（base 56e4a9f）· 三闸 pending 零签 · 维护者授权 00 代签留痕（invoke_10） |
| 2026-10-14 | v0.1 · 吸收 20 R1 退回 | 10-task | N1 补验收 TC2b「旧测 grep 影响面」（4 处必破断言亲读核真：test_hitl_resume.py:362 · test_hitl_pending_decide.py:501/528/661 · decide 面零 diff 区分 test_hitl_pending_decide.py:367-368 · test_hitl_auto_resume.py:308/417-418/570/909）· n1 ResumeEventSink 锚 :54-162 · n2 TC7 实证 10 件列全名 · n3 钉死行5 补 lg_rag/router.py:417-421 Retry-After 设置点 · n4 retention 注明 required 优先 · 复跑 lint PASS |
