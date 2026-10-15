# Task：lg-rag-sse-disconnect-completion（SSE 断连后 run 残缺 · 收尾帧 / 执行解耦 · 消解孤儿 in-flight）

> **状态**：**BLOCKED · TC5 live×3 FAIL · 00 停派升级维护者**（E1–E4 见 `invoke_20261014_00_escalate_tc5.md`）· 闸仍 approved · D1=A-only  
> **类型**：传输可靠性缺口（契约意图 vs 实现张力 · freeze `lg-rag-sse-v1` 行为收口）  
> **依据**：本仓对话实勘（2026-10-13）· T4 联调遗留（web `task_web_lg_rag_sse_t4` invoke_40：客户端断开即取消 generator · done 不落盘）· F-OBS-2 孤儿 run 409 活样本（`task_hitl_resume_replay_contract` 40 · run `22b65ce2`）· web 联调 TC4 活样本（`web-api-joint-check` · `jc_tc4_network.json` reload 后 `POST /lg-rag/replay`→409 · `jc_tc4_inflight_409.png`）· §10.3「断连尽量跑完」条文  
> **分支**：`task/lg-rag-sse-disconnect-completion`（base master `9ee928c`）

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `lg_rag_sse_disconnect_completion` |
| **git_branch** | `task/lg-rag-sse-disconnect-completion` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 断连/取消路径契约测（收尾帧存在性 · `run_stream_closed` 真）+ replay 孤儿面不再永久 409；若裁入 Wave B 另加 worker 解耦测与 live 断连后仍至 done。红测先行（断连后无终帧 → RED 签名） |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1`（预判：`lg_rag` 行备注回写断连/收尾语义；若 Wave B 新增 worker/队列模块则升判并补 `01_modules.md` · 30 按实回写） |
| **graph_delta** | 预期 `docs/_tech_graph/l1/01_modules.md` + `l1/10_flow_lg_rag.*` 备注；Wave B 若新模块另列 |
| **graph_delta_note** | 无模块增删时仅备注；Wave B 新一级模块须 HG-GRAPH-MODULES 再签 |
| **wiki_delta** | `n/a`（可选 volatile 短注指针 · 30 实判） |
| **wiki_delta_note** | 以 05 transport §10.3 回写为契约真值优先 |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,20,30,40` |
| **invoke_retention_profile** | `default` |
| **experience_capture** | `required` |
| **kpi_aggregator** | `n/a` |
| **orchestration** | 10 落稿 → **20 R1 复检（含波次裁剪裁定建议）** → 维护者签三闸 + **D1 波次裁定** → 30（红测先行）→ 40 live 断连对照 → PR+CI 绿 → CLOSE |
| **freeze_id** | `lg-rag-sse-v1`（**不**新 freeze；收尾语义优先复用既有 `error` / `done`+status 扩展键 · **禁** silent 新 `event_type` 除非 D2 裁定并回写 05） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | approved | 20, 30 | 维护者签 · 00 代录 2026-10-14 · 授权原话「统筹此任务，授权签收后续过程文档」· `invoke_20261014_00_gate_signoff.md` |
| HG-AUDIT-R1 | approved | 30 | 维护者签 · 00 代录 2026-10-14 · 20 R1 **PASS-WITH-NITS**（`task_lg_rag_sse_disconnect_completion_audit_R1_20261013.md`） |
| HG-GRAPH-MODULES | approved | 30 | 维护者签 · 00 代录 2026-10-14 · G-L1 备注在册；Wave B 若另立新模块须该 task 再签 |

### 维护者裁定口（20 复检后签 · **D1 阻塞 30**）

| 裁定 ID | 选项 | 默认建议（10） | **已签（2026-10-14）** | 说明 |
|---------|------|----------------|------------------------|------|
| **D1 波次** | **A-only** · **A+B** · **B-only** · **docs-spike 后另立** | **A-only** | **A-only** | Wave B 另立；本 task 只做收尾帧+解除孤儿永久 409 |
| **D2 收尾帧形状** | `error{stage:…}` · `done{status:'cancelled'\|'disconnected'}` · 两者兼 | 待 20/30 | **`done{status:'disconnected'}`** | 禁 silent 新 `event_type`；须回写 05 §10.3 + History `terminal_status` 变体测 |
| **D3 前端** | api-only · 同步开 web task 提示「须重问」 | api-only + FP-1 报回 web | **api-only** | 假续看文案另 web task（联调 TC4 已实证 409+「续看」） |

---

## 背景与目标

### 问题（F-OBS-DISCONNECT）

契约（`05_lg_rag_transport_and_session_plan_v0.md` §10.3 / `sse_stream.py` 文件头）写明：**断连后服务端尽量跑完图、无 cancel；客户端不保证收齐，靠落盘 + `POST /lg-rag/replay` 补帧**。

**实现张力（已实证）**：

1. Live 图执行绑在 `StreamingResponse` 异步生成器上；客户端断开 → generator `close` → `sse_stream.py` 循环 `finally` **cancel 挂起的 `__anext__`**（防泄漏）→ **后续帧（含 `done`）不再产生/落盘**。
2. T4 web 联调遗留原文：「客户端断开即取消 SSE generator，已 yield 帧落盘但后续帧（含 done）不再产生——断连期间跑完 replay 至 done **仅在服务端先于断开跑完时成立**」。
3. 无 `done`/`error` 收尾时，`run_stream_closed==False` → replay `refuse_in_flight=True` → **409**；孤儿在飞 run（客户端掐断、永不沉降）在 `hitl_resume_replay_contract` 40 已留活样本（run `22b65ce2`）。
4. 产品后果：用户刷新/换机 → History 见半截回答 → 点「续看」**补不出后半段、也可能永久 409** → **该次对话实质无效**；HITL `resume` **不能**充当通用「从 seq N 接着跑完」（resume 仅 interrupt 挂起路径）。

### 目标

按 **D1** 裁波交付：

- **Wave A（建议本 task 默认）**：断连/取消路径**必落盘明确收尾帧**，使 run 流关闭、`run_stream_closed` 真、replay 不再永久 409；History `terminal_status` 可区分「未完成/已取消」；**不**承诺补算 LLM 后半段（用户须重问或另开 Wave B）。
- **Wave B（可选 / 建议另立）**：run 执行与 HTTP SSE 连接**解耦**（后台 worker/任务持有 astream）；`/stream` 仅订阅已落盘或队列事件；断连后图仍跑完并落 `done`；之后 replay 可补到终态（兑现 §10.3 原意图）。

**非目标（本草稿钉死）**：把「前端调 replay」改成「隐式 resume 同 run_id 再调 LLM」——与 HITL resume 语义冲突，禁混。

---

## 范围

### Wave A（D1=A-only 或 A+B 时必做）

- **F1**：识别「客户端断开 / generator close / 请求 cancel」路径（亲读 `sse_stream.py` 主循环 `finally` · FastAPI/Starlette 断连信号）；在仍可落盘时 **emit + persist 收尾帧**（形状按 D2）。
- **F2**：保证收尾后 `event_store.run_stream_closed(run_id)==True`；孤儿 run 再 `POST /lg-rag/replay` **不再**因无收尾永久 409（可 200 重放已有帧至收尾，或空尾 + 已含收尾）。
- **F3**：契约测试红测先行：模拟断连/close → 断言存在收尾帧 + `run_stream_closed`；既有 HITL `done{waiting_approval}` / completed / error 零 diff。
- **F4**：回写 `05` §10.3（实然：断连=收尾取消帧 · **不**等同跑完）；`01_modules.md` / flow 备注；experience 捕获；40 live：中途杀客户端 → 库有收尾 → replay 200。

### Wave B（仅 D1 含 B 时）

- **F5**：设计并实现「run 执行生命周期」与「SSE 订阅连接」分离（进程内 task / 队列 · 多副本语义须对照 `task_multi_replica_verify` 边界）。
- **F6**：断连后 worker 继续 → 落盘至 `done`/`error`；新连接 replay（或重订 live）可收到后半段 + 终帧。
- **F7**：预算/取消策略显式化（是否保留「产品无 cancel」；超时谁杀 worker）；失败路径与观测（Langfuse run_id 连续）。

### 公共

- **F0**：10/20 invoke + 本 task 体；**D1/D2/D3 维护者签后**才 30。

## 非范围

- **HITL resume / auto_resume / decide 状态机**（既有路径零 diff；本缺口不是 HITL）。
- **前端强制改码**（D3=api-only 时）；web「假续看」文案另 task（FP-1 报回）。
- **新 freeze / 新 event_type**（除非 D2 显式批准并回写 05）。
- **通用「任意 seq 点 resume 同 run 再调 LLM」**（禁；与 checkpoint interrupt 模型不同）。
- **chat legacy WS cancel**、iOS、租户无关面。
- **本起草阶段零 `app/` 改码**（仅 docs）；`uv.lock` 脏树勿卷入本 PR。

---

## 失败路径

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----------|----------|--------|----------|
| FP-1 断连瞬间 DB 不可写，收尾帧落盘失败 | 打 error 日志；尽力；run 可能仍孤儿 → 补偿扫描/定时收尾（30 裁定是否本 task 薄做） | 是（补偿） | 续看仍可能 409（须监控） |
| FP-2 收尾帧误伤 HITL `waiting_approval`（把挂起当断连） | TC 钉：interrupt 路径仍只发 waiting+done{waiting_approval}；断连探测不得在挂起合法收流后误标 cancelled | 是 | 审批卡消失=严重回归 |
| FP-3 Wave B 多副本双 worker 同 run | 须租约/单飞（对照 capability idempotency / hitl claim）；30 钉单飞谓词 | 是 | 双份答案/双 seq |
| FP-4 Wave B 成本：用户已走，LLM 仍烧完 | D1/预算策略显式；可 env 开关「断连即停+收尾」vs「断连仍跑完」 | 是 | 费用/延迟 |
| FP-5 前端仍展示「续看」暗示能补完答案 | api-only 时 History terminal 须可机读；web 另 task 改文案 | 是 | 假期望 |
| FP-6 HG 未签即 30 | GATE_VERIFY 拒开工 | 是 | — |

---

## 验收标准

- [x] **TC1（Wave A）断连收尾**：构造 mid-stream 断开/close → 事件表存在 D2 裁定的收尾帧 → `run_stream_closed==True`；修复前 RED（无收尾）→ 修复后 GREEN；时序 git 可查。
- [x] **TC2（Wave A）孤儿 replay**：无收尾历史形态（或测试夹具）在修复后可沉降或补写收尾；`POST /lg-rag/replay` **不再**对已死连接 run 永久 409（200 含收尾，或 30 裁定的明确终态语义）。
- [x] **TC3 零 diff 保护区**：HITL 挂起 replay 200、completed replay 帧序、在飞真写入中 409+Retry-After（F-OBS-2）行为对 master 零回归。
- [x] **TC4 文档**：§10.3 实然回写与实现一致；图谱备注落盘；`graph-compile` EXIT=0。
- [ ] **TC5（Wave A）live 40**：真实 uvicorn + 客户端中途断开 → DB 收尾 → replay 200；照登附件。**40 FAIL（R1）** → **30-R2 peek 假绿** → **40-R2 仍 FAIL** → **30-R3 blocking receive** → **40-R3 仍 FAIL**（`invoke_20261014_40_r3_verify.md` · **停派升级维护者**）
- [ ] **TC6（仅 Wave B）**：断开后等待 worker → 库出现后半段 + `done` → replay `after_seq` 前端断点可补到 done；多副本单飞测（若适用）。（D1=A-only · **不适用**）
- [x] **TC7 反回归全量**：`pytest` 对拍 master 零新增红；`ruff` 触及路径绿。（相关面 73 passed · 触及 ruff 绿；全量跑环境中断一次，见 30 invoke）

## 依赖

- base master `9ee928c`（含 F-OBS-2 409 语义）。
- 锚点（10 亲读 · 行号 30 按实校正）：
  - `app/ops/lg_rag/sse_stream.py` 文件头断连语义 · 主循环 `:396-425` cancel anext · `:509-525` Exception→error
  - `app/ops/lg_rag/router.py` `:336-395` replay + `refuse_in_flight`
  - `app/ops/lg_rag/event_store.py` `run_stream_closed` / `run_is_terminal` / `load_events_after`
  - `docs/spec/agent-infra/05_lg_rag_transport_and_session_plan_v0.md` §10.3
  - web T4 遗留：`ops-desk-web/docs/tasks/done/task_web_lg_rag_sse_t4.md`（断开即取消 generator）
  - 孤儿 409：`docs/harness/invokes/by-task/hitl-resume-replay-contract/invoke_20261013_40_verify.md`
  - web 联调 TC4（参照）：`ops-desk-web/docs/harness/invokes/by-task/web-api-joint-check/attachments/jc_tc4_network.json`（reload → `POST /lg-rag/replay` **409**）· `jc_tc4_inflight_409.png`（UI「Run is still in flight」+「续看」）
- **不**依赖 web 改码开工（D3）；Wave B 依赖维护者接受成本/取消策略。

## 给执行帽的必读列表

1. 本 task 全文（含 D1–D3 裁定表 · 未签不得 30）。
2. 上列锚点文件全文相关段（禁信转述）。
3. `docs/tasks/done/task_lg_rag_sse_resume.md`（T4 意图）+ web T4 done task 遗留段。
4. `docs/tasks/active/task_hitl_resume_replay_contract.md`（409 语义 · 勿破坏）。
5. `docs/standards/CODING_BACKEND_L2_v1_zh.md`。
6. 若 D1 含 B：`docs/tasks/done/task_multi_replica_verify.md` 边界清单。

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|---|---|---|---|---|
| R0 | 框定：契约「断连跑完」vs 实现「generator close 停跑」张力 → 半截回答 + 孤儿 409 | false | — | Wave 裁剪未签 |
| R1 | 证据：T4 遗留句 · sse_stream cancel anext · run_stream_closed · 孤儿 22b65ce2 · HITL resume 非通用续跑 | false | — | 断连信号在 Starlette 层确切钩点留 30 |
| R2 | 方案：Wave A 收尾帧（小）/ Wave B 解耦（大）；默认建议 A-only；禁 replay≡resume | false | — | D2 帧形状 vs History 聚合 |
| R3 | 反例：误伤 waiting_approval · 真在飞 409 须保留 · Wave B 双 worker | false | — | 补偿扫描是否本 task |
| R4 | 验收：TC1–TC5（A）+ TC6（B）+ TC7；红测先行 | false | — | live 断连稳定复现 |
| R5 | 收口：闸 pending · D1 阻塞 30 · 交 20 复检 | true | 机理单一 · 波次显式开放 · 再轮无新锚点 | D1/D2 未签 |

**actual_last_round**：R5（early_stop）

### R0 · 问题框定

用户路径「前端断 → 再开 → History/续看」在无 done 时失败：replay 只能重放已落盘段，且常因无收尾被 409 挡死；LLM 不会因 replay 继续。根因是执行绑死在 SSE 生成器生命周期，与 §10.3 条文冲突。

### R1 · 证据收集

代码：`sse_stream` 断连 cancel anext；异常路径才有 `error` 帧，纯断开通常无收尾。产品：T4/F-OBS-2 孤儿样本。语义：HITL resume ≠ 断流续跑。

### R2 · 方案生成

先 A（诚实收尾 + 解除假续看）再 B（真跑完）。合并或拆分由 D1 裁定，避免一个 PR 吞下多副本 worker。

### R3 · 反例与边界

挂起合法收尾、真在飞 409、多副本单飞、断连后仍烧 LLM 的成本，均须显式策略。

### R4 · 验收/可测性

断连收尾可单测；孤儿 409 可 DB 夹具；Wave B 必须 live。

### R5 · 收口

草稿交 20；三闸与 D1 未签前禁 30。

### 自检结论（执行者）

**10（2026-10-13）**：F-OBS-DISCONNECT 框定成立（契约尽量跑完 vs generator close 停跑 · T4/孤儿 409 有案）；Wave A/B + D1–D3 显式开放；默认建议 D1=A-only；TC1–TC7 与 FP1–FP6 齐；闸全 pending · **禁 30**。  
**20（2026-10-13）**：R1 **PASS-WITH-NITS**（审查文 `docs/harness/reviews/task_lg_rag_sse_disconnect_completion_audit_R1_20261013.md` · 内容零阻塞 · 不退回 10 · 不代签闸）；NIT：E5 自检结论占位（本段补）· Exception 行号校正 `:509-525` · K7 旧测面代查不退回；D1/D2 建议见审查文（A-only · `done{status:'disconnected'|'cancelled'}`）。**维护者签三闸 + D1 后方可 30。**  
**00（2026-10-14）**：维护者令「统筹此任务，授权签收后续过程文档」→ 三闸 **approved** · **D1=A-only** · **D2=`done{status:'disconnected'}`** · **D3=api-only** · 联调 TC4 409 附件挂依赖；**可派 30**（delegate-only · 本窗未改 `app/`）。  
**30（2026-10-14）**：Wave A 交付——`GeneratorExit`/`CancelledError` → 落盘 `done{status:'disconnected'}`（不 yield）· `run_stream_closed` 真；TC1 红→绿（`tests/test_lg_rag_sse_disconnect_completion.py`）· TC2 DB 沉降 replay 放行 · TC3 保护区（resume 409/挂起 · hitl · History `disconnected`）绿 · TC4 §10.3+图谱+`graph-compile` EXIT=0 · TC7 相关面 73 passed / ruff 触及绿；**FP-1 补偿扫描未薄做**；**TC5 待 40 live**；Wave B 未做；invoke `docs/harness/invokes/by-task/lg-rag-sse-disconnect-completion/invoke_20261014_30_implement.md`；**未 git commit**。  
**40（2026-10-14）**：**TC5 FAIL / BLOCKED→00**——uvicorn `:8051` supervisor 中途 kill 客户端（run `5c5b4cf0187b4184a9c4be7307a4eab5`）→ DB 仅 `run.start` · `run_stream_closed=false` · replay **120s+ 仍 409**（无 `done{status:'disconnected'}`）；**TC3 保护区 live 抽检 PASS**（同 run 断连前 409+Retry-After:2）；pytest 子集 27/26 绿 · `spec-wave verify` PASS；假设：Starlette 1.3 ASGI≥2.4 无并行 disconnect 监听 · live 未触达 `agen.aclose()`/`_settle_disconnected`（单测 aclose 仍绿）；附件 `docs/harness/invokes/by-task/lg-rag-sse-disconnect-completion/attachments/` · invoke `invoke_20261014_40_verify.md`；**未改业务码 · 未 commit**。建议 00 裁定是否派 30 补 ASGI 断连钩（仍 Wave A · 禁静默 Wave B）。  
**00（2026-10-14 R2）**：**派 30 补修** ASGI 断连钩（仍 **D1=A-only** · 禁 Wave B）· 修后交 40 复跑 TC5 · 留痕 `invoke_20261014_00_r2_dispatch_30.md`。  
**40-R2（2026-10-14）**：TC5 **仍 FAIL**（`f6a9cdd5…` · `is_disconnected` live 未翻转 · 无 settle 日志 · `invoke_20261014_40_r2_verify.md`）。  
**00（2026-10-14 R3）**：判定 peek 轮询假绿 → **再派 30** 改 **blocking receive** disconnect watch（禁只加深 peek · 禁 Wave B）· 留痕 `invoke_20261014_00_r3_dispatch_30.md`；若再 FAIL 停派升级维护者。  
**30-R2（2026-10-14）**：亲读 Starlette ASGI≥2.4 无并行 `listen_for_disconnect` 成立 → 主循环旁轮询 `is_disconnected`（路由挂 `request.is_disconnected` · `_DISCONNECT_POLL_S=1s`）→ cancel anext + `_settle_disconnected`；新增 `test_asgi_disconnect_probe_settles_without_aclose`（无 aclose 仍沉降）绿；TC1/TC2/keepalive/HITL+resume/history 绿；§10.3+图谱备注补探针；invoke `invoke_20261014_30_r2_asgi_disconnect.md`；**未 commit** · **交 00 再派 40 复跑 TC5**。  
**40-R2（2026-10-14）**：**TC5 仍 FAIL / BLOCKED→00**——干净 uvicorn `:8051` · supervisor mid-stream（httpx break run `f6a9cdd567ae41cc91c8ce3938712083` + curl `--max-time 8` run `b16d704c9895435db7c69e88a9bdc380`）→ 断连后 20–30s+ replay **仍 409** · DB 无 `done{disconnected}` · uvicorn **无** `ASGI disconnect probe settled`；码面探针在册、单元 mock 绿；假设：live `Request.is_disconnected` 读不到 uvicorn `http.disconnect`。**TC3 live 409+Retry-After PASS**（`tc5_r2_inflight_409.*`）。pytest 子集 52 passed · verify PASS；附件 `tc5_r2_*`；invoke `invoke_20261014_40_r2_verify.md`；**未改业务码 · 未 commit**。  
**30-R3（2026-10-14）**：亲读 **starlette 0.52.1** / **uvicorn 0.44.0**：`is_disconnected` CancelScope peek 成立 → 摘 peek/`_DISCONNECT_POLL_S`；路由挂 `request.receive`；独立 Task **阻塞**等 `http.disconnect` 与主循环竞速 → settle；新测 `test_blocking_receive_disconnect_settles_when_peek_would_miss`（peek 对照永 False）绿；TC1/TC2/keepalive/HITL+history 绿；§10.3+图谱 R3；invoke `invoke_20261014_30_r3_blocking_disconnect.md`；**未 commit** · **交 00 再派 40-R3 复跑 TC5**。  
**40-R3（2026-10-14）**：**TC5 仍 FAIL / BLOCKED→00 · 停派升级维护者**——干净 uvicorn `:8051`（PID 91210）· supervisor mid-stream（httpx break run `426b0a70e37d452aaeb649c2e091e79d` + curl `--max-time 8` run `eea35bd94a274067a4e66e3712ff254a`）→ 断连后 20–48s+ replay **仍 409** · DB 无 `done{disconnected}`（止于 seq6 `subtask.progress running`）· uvicorn **无** `ASGI disconnect watch settled`；码面 blocking watch 在册、单元 mock 绿。**TC3 live 409+Retry-After PASS**（`tc5_r3_inflight_409.*`）。pytest 子集 52 passed · verify PASS；附件 `tc5_r3_*`；invoke `invoke_20261014_40_r3_verify.md`；**未改业务码 · 未 commit**。按 00 R3 纪律：**禁止再派 30** · 升级维护者裁定。  
**00（2026-10-14 升级）**：**停派** · 请维护者选 **E1–E4**（`invoke_20261014_00_escalate_tc5.md`）· 本窗未改实现码 · 待派：无。

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-14 | v0.8 · 40-R3：TC5 live 仍 FAIL（blocking receive 未 live 沉降）· 409 保护区 PASS · **停派升级** · invoke_40_r3 |
| 2026-10-14 | v0.7 · 30-R3：blocking `request.receive` 等 disconnect（弃 peek）· 新测绿 · 待 40-R3 · invoke_30_r3 |
| 2026-10-14 | v0.6 · 40-R2：TC5 live 仍 FAIL（探针码面绿·live 未沉降）· 409 保护区 PASS · BLOCKED→00 · invoke_40_r2 |
| 2026-10-14 | v0.5 · 30-R2：ASGI `is_disconnected` 轮询沉降 · 探针单测绿 · 待 40 复跑 TC5 · invoke_30_r2 |
| 2026-10-14 | v0.4 · 40 TC5 live FAIL：uvicorn 中途断连未沉降 · 409 保护区 PASS · BLOCKED→00 · invoke_40 |
| 2026-10-14 | v0.3 · 30 Wave A：断连收尾帧 + 红绿测 + 文档图谱 · TC1–4/7 勾选 · TC5 待 40 |
| 2026-10-14 | v0.2 · 00 代录三闸 approved + D1/D2/D3 已签 · 挂 web 联调 TC4 409 参照 · 状态可 30 |
| 2026-10-13 | v0.1 · 吸收 20 R1 NIT：补 `### 自检结论` · Exception 锚点行号 `:509-525` · 修订记录本行 |
| 2026-10-13 | v0 · 10 落稿：F-OBS-DISCONNECT（断连停跑 · 无 done · 孤儿 409 · 假续看）· Wave A/B + D1–D3 裁定口 · TC1–TC7 · R0–R5 early_stop · 闸全 pending · 分支 `task/lg-rag-sse-disconnect-completion` · base `9ee928c` · 来源：本仓 SSE 实勘对话 + T4/F-OBS-2 遗留 |
