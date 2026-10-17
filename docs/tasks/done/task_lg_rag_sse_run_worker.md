# Task：lg-rag-sse-run-worker（E3 Wave B · RunWorker 与 SSE 订阅解耦 · 部分回复可见 · 失败后继续回复）

> **状态**：done（CLOSED 2026-10-17 · PR [#250](https://github.com/Cyning12/ops-desk-api/pull/250) MERGED（squash `56e4a9f` · 2026-10-14T07:56:02Z）· E3 Wave B RunWorker 与 SSE 订阅解耦落地 · B1–B6/B3/B5 PASS · 40 TC-B6 live PASS · 与旧 task `lg_rag_sse_disconnect_completion` co-CLOSE · 三闸 approved（00 代录）· CLOSE 归档 done/ · 细节见 CLOSE 文档 [`../close/close_lg_rag_sse_run_worker_co_disconnect_20261017.md`](../close/close_lg_rag_sse_run_worker_co_disconnect_20261017.md)）  

> **类型**：传输架构（进程内 RunWorker + StreamSubscriber · freeze `lg-rag-sse-v1` 行为收口）  
> **依据**：维护者选 **E3** + 产品口径（`docs/harness/invokes/by-task/lg-rag-sse-disconnect-completion/invoke_20261014_00_e3_wave_b_plan.md`）· 新 task 生成令（`…/invoke_20261014_00_e3_new_task_spawn.md`）· 旧 task TC5 live×3 FAIL / 停派 ASGI 钩史实  
> **分支**：`task/lg-rag-sse-run-worker`（base master `9ee928c` · 与旧分支工作树可并存；**勿**把无关 `uv.lock` 当本 task 范围）  
> **关联 co-CLOSE**：与 [`task_lg_rag_sse_disconnect_completion.md`](./task_lg_rag_sse_disconnect_completion.md)（旧 · Wave A 尝试 + TC5 停派史 · **正文不修订**）**一起关账**（Hub/PR 互链；旧 task TC5 known-gap 或随本 task B 语义重定义后同批 CLOSE）

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `lg_rag_sse_run_worker` |
| **git_branch** | `task/lg-rag-sse-run-worker` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 红测先行：断连后 worker 仍前进至 terminal；失败 `error{stage:lg_rag.worker_failed}`；`continue_from_run_id` 新 run；真在飞 409 零 diff；40 live 按 B 语义（断连→settle→replay 补后半段）重定义旧 TC5 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1`（**升判**：新增 `run_worker` / subscribe 拆分须写 `docs/_tech_graph/l1/01_modules.md` + `l1/10_flow_lg_rag.*` → **HG-GRAPH-MODULES 须再签**） |
| **graph_delta** | 预期 `docs/_tech_graph/l1/01_modules.md`（新模块行）+ `l1/10_flow_lg_rag.md` / `.graph.yaml` + `shared/graph.json`（compile） |
| **graph_delta_note** | 新一级/子模块入册后方可 30 改 `app/ops/lg_rag/run_worker.py` 等 |
| **wiki_delta** | `n/a`（可选 volatile 短注指针 · 30 实判） |
| **wiki_delta_note** | 契约真值优先回写 `docs/spec/agent-infra/05_lg_rag_transport_and_session_plan_v0.md` §10.3 / §4.2 |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,20,30,40` |
| **invoke_retention_profile** | `default` |
| **experience_capture** | `required` |
| **kpi_aggregator** | `n/a` |
| **orchestration** | 10 落稿 → **20 R1** → 维护者/00 代录签三闸（D1 已授权 A+B · 仍须闸表 approved）→ 30（B1→B2→薄 B4）→ 40 live → **与旧 disconnect task 同批 CLOSE**；**同步提示开 web task（D3）** |
| **freeze_id** | `lg-rag-sse-v1`（**不**新 freeze · **禁** silent 新 `event_type`；可扩 `error.stage` / 可选 `done.status` 字面量并回写 05） |
| **related_tasks** | [`task_lg_rag_sse_disconnect_completion.md`](./task_lg_rag_sse_disconnect_completion.md)（关联 co-CLOSE · 旧 task 正文零改） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | approved | 20, 30 | 维护者签 · 00 代录 2026-10-14 · 「确认并授权重新签 D1」+ 过程文档签收权 |
| HG-AUDIT-R1 | approved | 30 | 维护者签 · 00 代录 2026-10-14 · 20 R1 **PASS-WITH-NITS**（`task_lg_rag_sse_run_worker_audit_R1_20261014.md`） |
| HG-GRAPH-MODULES | approved | 30 | 维护者签 · 00 代录 2026-10-14 · G-L1 新 `run_worker` 在册授权；**30 须同步写 `01_modules.md`** |

### 维护者裁定口（**D1 已正式落表**）

| 裁定 ID | 选项 | 默认建议（10） | **已签（2026-10-14）** | 说明 |
|---------|------|----------------|------------------------|------|
| **D1 波次** | A-only · **A+B** · B-only · docs-spike | **A+B**（**B 为主**） | **A+B** | B=RunWorker 主交付；A=worker 死后补偿终帧；**不赌** ASGI disconnect |
| **D2 收尾帧形状** | `error{stage:…}` · `done{status:'disconnected'}` · 两者兼 | 成功 `done` · 失败 `error{stage:…}` | **成功普通 `done`；失败 `error{stage:lg_rag.worker_failed}`；补偿可 `done{status:'disconnected'}`** | 禁 silent 新 `event_type` |
| **D3 前端** | api-only · **同步开 web task** | **须开 web** | **须同步开 web task** | api 本棒机读终态；web CTA 另 task（报回路径） |

---

## 背景与目标

### 关联旧 task（史实 · 不修订其正文）

[`docs/tasks/active/task_lg_rag_sse_disconnect_completion.md`](./task_lg_rag_sse_disconnect_completion.md) 承载 Wave A（ASGI disconnect 钩 / `done{disconnected}`）尝试；**TC5 live×3 FAIL** 后 00 停派，维护者选 **E3**。旧 task **正文冻结**（保留 A 尝试与 FAIL 史）；本 task 承载 Wave B 真解。两 task **关联 co-CLOSE**。

### 问题

执行绑在 HTTP SSE 生成器上 → 客户端断连常导致后续帧（含 `done`）不落盘 → History 半截 + replay 409 / 假「续看」。ASGI 钩三次 live 未翻转，**不再加码赌 disconnect**。

### 产品口径（钉死）

1. **部分回复可见**：既有 `answer.delta` 落盘 + History 聚合；仍连着走现网 SSE；刷新/换机读 History（worker 仍跑则 `running` + 半截）。
2. **Worker 断连后继续**：HTTP 只取消 subscriber，不 cancel worker；成功 → 落盘普通 `done` → History 完整 · `POST /lg-rag/replay` 200 补后半段。
3. **Worker 失败** → 落盘 `error{stage:lg_rag.worker_failed}`（必要）→ `run_stream_closed=True` → 用户点「继续回复」= **同 `thread_id` 新 `/stream`（新 `run_id`）**，可选 body `continue_from_run_id` 注入 partial 草稿；**禁止** HITL `/resume`；**禁止** replay≡再调 LLM。
4. **协议**：不 silent 新 `event_type`；freeze 仍 `lg-rag-sse-v1`。
5. **D3**：须提示同步开 **web task**（CTA / 部分回复 /「继续回复」文案）。

### 目标

按 **D1=A+B（B 为主）** 交付：RunWorker 持有 astream 只写 event_store；StreamSubscriber 只读推 SSE；补偿 A 仅覆盖 worker 死掉/超时无终帧；验收 TC-B* + 文档/图谱；与旧 task 同批 CLOSE。

---

## 范围

### Wave B（主 · F5–F7）

- **F5**：设计并实现「run 执行生命周期」与「SSE 订阅连接」分离（MVP：进程内 `asyncio.Task` + `run_id` 单飞租约）。建议模块：`app/ops/lg_rag/run_worker.py`（新）、`sse_subscribe.py`（新或自 `sse_stream` 拆）；`router.py` `/stream`：鉴权 → 分配 `run_id` → **先** start worker → **再** `StreamingResponse(subscribe)`。
- **F6**：断连后 worker 继续 → 落盘至普通 `done` 或 `error{stage:lg_rag.worker_failed}`；新连接 `POST /lg-rag/replay`（或重订 live）可收到后半段 + 终帧；真在飞仍 **409+Retry-After**（零 diff）。
- **F7**：预算/取消策略显式化（产品默认「断连仍跑完」；超时谁杀 worker；env 开关若需要）；失败路径与观测（Langfuse `run_id` 连续）；可选薄补偿扫描（`list_open_runs` / 超时仍 `!run_stream_closed` → 补 `error`/`done{disconnected}`）。

### Wave A（降级补偿 · 同 D1=A+B）

- **F-A1**：worker 进程被杀 / 超时无终帧 → 补偿落盘终帧（优先 `error` 或 D2 的 `done{status:'disconnected'}`），使 `run_stream_closed` 真；**不**实现/依赖 ASGI `http.disconnect` 钩为主路径。
- **F-A2**：既有 HITL `waiting_approval` / completed / 真在飞 409 行为零回归。

### 产品衔接（api 面）

- **F-C1**：可选 `continue_from_run_id`（或 30 裁定等价）：新 run 读旧 run partial answer 拼进 history/system 草稿；HITL resume 路径零 diff。
- **F-C2**：History 透传 `error` / `disconnected` / `running` 机读终态，供 web CTA（本仓不强制改 web 码）。

### 文档 / 图谱 / 过程

- **F0**：本 task + 10/20 invoke；**闸 approved + D1 正式落表** 后才 30。
- **F-D1**：回写 `05` §10.3（应然：断连尽量跑完以 worker 为准 · 实然注 MVP 单进程）+ §4.2 `error.stage` / 可选 `done.status` 字面量。
- **F-D2**：`01_modules.md` + flow + `graph-compile` EXIT=0；experience 捕获。
- **F-D3**：**提示 00/维护者同步开 web task**（部分回复 +「继续回复」CTA · 与 api 同波或紧随）。

## 非范围

- **修改** [`task_lg_rag_sse_disconnect_completion.md`](./task_lg_rag_sse_disconnect_completion.md) 正文（旧 task 冻结）。
- **再赌 ASGI disconnect 钩**作主路径（三次 live 已否）。
- **HITL resume / auto_resume / decide** 状态机改语义；「继续回复」≠ resume。
- **replay 隐式再调 LLM**（禁）。
- **silent 新 `event_type`** / 新 freeze（除非维护者另批并回写 05）。
- **本仓强制实现 web UI**（D3=提示开 web task；api 只供机读终态与可选 `continue_from_run_id`）。
- **多副本 DB 租约完整方案**（对照 `task_multi_replica_verify`；MVP 进程内单飞即可；多副本可另立）。
- **chat legacy WS cancel**、iOS、租户无关面。
- **本起草阶段零 `app/` 改码**；无关 `uv.lock` 脏树勿卷入本 PR。

---

## 失败路径

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----------|----------|--------|----------|
| FP-1 worker 异常未 emit error | 补偿扫描/超时沉降打 `error` 或 `disconnected`；监控 | 是（补偿） | History 半截 + 可「继续回复」；续看不再永久 409 |
| FP-2 误伤 HITL `waiting_approval` | TC 钉：interrupt 路径仍 waiting+done{waiting_approval}；worker 不得把合法挂起当失败 | 是 | 审批卡消失=严重回归 |
| FP-3 多副本双 worker 同 `run_id` | MVP 进程内单飞；多副本须租约（对照 multi_replica）；30 钉单飞谓词 | 是 | 双份答案/双 seq |
| FP-4 断连后仍烧满 LLM（成本） | F7 策略/env 显式；默认跑完与「断连即停+补偿」可配 | 是 | 费用/延迟 |
| FP-5 前端仍把 replay 当「续跑」或未开「继续回复」 | D3 须开 web task；api History terminal 机读 | 是（web） | 假期望 / 按钮缺失 |
| FP-6 「继续回复」误调 HITL resume | 路由/客户端纪律：仅新 `/stream`；TC-B3 钉零 resume | 是 | 错误 4xx / 状态机乱 |
| FP-7 HG 未签或 D1 未正式落表即 30 | GATE_VERIFY 拒开工 | 是 | — |
| FP-8 旧 task 单独 CLOSE 而本 task 未关 | 关账纪律：两 task **同批 co-CLOSE** | 是 | 史实/缺口断裂 |

---

## 验收标准

- [x] **TC-B1（断连仍跑完）**：起 `/stream` → 中途关客户端 → worker 日志/观测仍前进 → DB 最终普通 `done`（无强制 `disconnected`）→ `POST /lg-rag/replay` 200 含断点后半段 `answer` + 终帧；红测先行可查。
- [x] **TC-B2（worker 失败）**：注入/模拟 worker 失败 → 落盘 `error` 且 `payload.stage==lg_rag.worker_failed` → `run_stream_closed==True` → replay 200 → History `terminal_status=error` + partial answer 仍在。
- [x] **TC-B3（继续回复=新 run）**：带可选 `continue_from_run_id`（或等价）同 `thread_id` 新 `/stream` 绿；**HITL `/resume` 零调用/零 diff**；replay **不**触发新 LLM 补算。（30 · `test_tc_b3_continue_from_new_stream_zero_resume`）
- [x] **TC-B4（真在飞 409）**：worker 仍写入中 → replay **409+Retry-After** 对 master/既有契约零回归。
- [x] **TC-B5（补偿 A）**：模拟 worker 死掉/超时无终帧 → 补偿终帧落盘 → `run_stream_closed` 真 → 不再永久 409（**不**依赖 ASGI disconnect 单测当 live 主证）。（30 · `list_open_runs` + `scan_orphan_runs_for_compensation` · `test_tc_b5_*`）
- [x] **TC-B6（旧 TC5 语义替换 · 40 live）**：真实 uvicorn + 中途断开 → 等 settle → DB terminal → replay 200 补后半段或明确 error；附件落盘；替代「同连接内 ASGI 钩必触发」旧验收。（40 · 2026-10-14 · PASS · `invoke_20261014_40_verify.md` · `attachments/tc_b6_*` · run `71d3cdfb…`）
- [x] **TC-B7 文档/图谱**：`05` §10.3/§4.2 与实现一致；`01_modules`+flow；`./scripts/graph-compile.sh` EXIT=0；experience 捕获。
- [x] **TC-B8 反回归**：触及路径 `pytest` / `ruff` 绿；HITL 挂起/completed/resume 保护区零新增红。
- [x] **TC-B9 D3 提示**：invoke/自检或 CLOSE 清单含「已提示同步开 web task（部分回复 + 继续回复 CTA）」可勾证据（web task 路径或 00 回执）。（见 `invoke_20261014_30_implement.md`）
- [ ] **TC-B10 co-CLOSE**：关闭本 task 时 **同时**关闭/归档 [`task_lg_rag_sse_disconnect_completion.md`](./task_lg_rag_sse_disconnect_completion.md)（或 CLOSE 文档显式双 slug）。

## 依赖

- 方案真值：
  - `docs/harness/invokes/by-task/lg-rag-sse-disconnect-completion/invoke_20261014_00_e3_wave_b_plan.md`
  - `docs/harness/invokes/by-task/lg-rag-sse-disconnect-completion/invoke_20261014_00_e3_new_task_spawn.md`
- 关联旧 task（co-CLOSE · 正文不改）：[`docs/tasks/active/task_lg_rag_sse_disconnect_completion.md`](./task_lg_rag_sse_disconnect_completion.md)
- base master `9ee928c`（含 F-OBS-2 409 语义）；Wave A 未合入码若在脏树，30 以本分支/PR 边界为准，勿误带无关 `uv.lock`。
- 锚点（10 亲读指向 · 行号 30 按实校正）：
  - `app/ops/lg_rag/sse_stream.py`（执行/订阅现状 · cancel anext）
  - `app/ops/lg_rag/router.py`（`/stream` · `/replay` · `refuse_in_flight`）
  - `app/ops/lg_rag/event_store.py`（`run_stream_closed` / `load_events_after`）
  - `docs/spec/agent-infra/05_lg_rag_transport_and_session_plan_v0.md` §10.3 · §4.2
  - `docs/tasks/active/task_hitl_resume_replay_contract.md`（409 / resume 语义 · 勿破坏）
  - `docs/tasks/done/task_multi_replica_verify.md`（多副本边界 · F7/FP-3）
  - 旧 task 40 附件：`docs/harness/invokes/by-task/lg-rag-sse-disconnect-completion/attachments/`（TC5 FAIL 证据）

## 给执行帽的必读列表

1. 本 task 全文（含 D1–D3 · 闸 pending 纪律 · co-CLOSE）。
2. `invoke_20261014_00_e3_wave_b_plan.md` + `invoke_20261014_00_e3_new_task_spawn.md`（方案/关联真值）。
3. 上列锚点文件相关段（禁信转述）。
4. [`task_lg_rag_sse_disconnect_completion.md`](./task_lg_rag_sse_disconnect_completion.md)（史实只读 · **勿改正文**）。
5. `docs/standards/CODING_BACKEND_L2_v1_zh.md`。
6. `docs/tasks/done/task_multi_replica_verify.md` 边界清单。
7. HITL：`docs/tasks/active/task_hitl_resume_replay_contract.md`（禁混 resume）。

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|---|---|---|---|---|
| R0 | 框定：ASGI 钩失败 → E3 解耦；产品=部分可见+断连跑完+失败新 run | false | — | 闸未签 |
| R1 | 证据：旧 TC5×3 FAIL · generator 绑执行 · 方案 invoke 已钉 A+B/B 主 | false | — | 行号漂移 |
| R2 | 方案：RunWorker+Subscriber；成功 done；失败 error.stage；补偿 A 薄做；freeze 不升 | false | — | continue_from 字段名 |
| R3 | 反例：HITL 误伤 · 真在飞 409 · 双 worker · replay≠LLM · 禁改旧 task | false | — | 多副本另立 |
| R4 | 验收：TC-B1–B10；红测+live B 语义；D3 web 提示；co-CLOSE | false | — | web 不同步 |
| R5 | 收口：闸 pending · D1 代录授权在案 · 交 20；禁 30 | true | 机理与产品口径已钉 · 再轮无新锚点 | HG/GRAPH 未签 |

**actual_last_round**：R5（early_stop）

### R0 · 问题框定

断连后对话无效的根因是执行与 HTTP 生命周期耦合；Wave A 赌 ASGI 钩已否证。产品要「半截可见 + 后台补完 + 失败则新 run 继续」，不是 resume/replay 续调 LLM。

### R1 · 证据收集

旧 task 40-R1/R2/R3：断连后无 settle、replay 409。方案 invoke：E3、D1=A+B（B 主）、D3 开 web、freeze 不升。

### R2 · 方案生成

进程内 Worker 写库、Subscriber 只读；失败钉 `lg_rag.worker_failed`；补偿只覆盖僵尸 run；`continue_from_run_id` 可选。

### R3 · 反例与边界

挂起合法收尾、真在飞 409、多副本单飞、成本开关、禁改旧 task 正文、co-CLOSE。

### R4 · 验收/可测性

TC-B1/B2 可单测+夹具；B3 钉新 run；B6 live 替换旧 TC5；B9/B10 过程验收。

### R5 · 收口

草稿交 20；三闸与 D1 正式落表前禁 30；同步提示 web task。

### 自检结论（执行者）

**10（2026-10-14）**：新 task `lg_rag_sse_run_worker` 落盘；**未改**旧 `task_lg_rag_sse_disconnect_completion` 正文；D1 裁定表写明 **00 代录已授权 A+B（B 主 · A=补偿）**；HG-\* **pending**（待 20+维护者/00 代录）；产品口径/F5–F7+补偿/FP/TC-B*/R0–R5/co-CLOSE/D3 web 提示齐；分支 `task/lg-rag-sse-run-worker`；invoke `docs/harness/invokes/by-task/lg-rag-sse-run-worker/invoke_20261014_10_task_draft.md`；`task lint` 见该 invoke；**禁 30**；**未 commit**。  
**20（2026-10-14）**：R1 **PASS-WITH-NITS**（`task_lg_rag_sse_run_worker_audit_R1_20261014.md` · 零内容阻塞 · NIT N1–N4 · 未代签闸）。  
**00（2026-10-14）**：三闸 **approved** · **D1=A+B** · **D2**=成功 `done` / 失败 `error{stage:lg_rag.worker_failed}` / 补偿可 `disconnected` · **D3**=须开 web · `invoke_20261014_00_gate_signoff.md` · **可派 30**（旧 task 正文未改 · co-CLOSE）。  
**30（2026-10-14）**：B1 完成（RunWorker+subscribe · TC-B1/B4 · 图谱/`05`）；B2 薄完成（`worker_failed` + `continue_from_run_id`）；A=TODO 扫描+cancel 补偿；触及 pytest 67 绿 · ruff 绿 · graph-compile EXIT=0；**未改**旧 disconnect task 正文 · **未 commit**；invoke `invoke_20261014_30_implement.md`；**建议派 40 live（TC-B6）** · D3 已提示开 web task。  
**40（2026-10-14）**：TC-B6 live **PASS**（uvicorn :8051 · 断连→worker settle→replay 200 后半段+普通 `done` · 409 抽检 PASS · continue_from 冒烟新 run）· pytest 92 · verify PASS · 证据 `attachments/tc_b6_*` · invoke `invoke_20261014_40_verify.md` · **未改 app/** · **未 commit**；仍 open：TC-B3/B5/B10 co-CLOSE · D3 web。  
**30-B3/B5（2026-10-14）**：TC-B3 HTTP 钉测（continue_from 新 run · resume 零调用 · replay 不调 LLM）· TC-B5 `list_open_runs`+`scan_orphan_runs_for_compensation` 补 `done{disconnected}`（活跃 worker 跳过）· pytest `test_lg_rag_sse_run_worker.py` 7 绿 · ruff 触及绿 · invoke `invoke_20261014_30_b3_b5.md` · **未改**旧 disconnect task · **未 commit**；仍 open：TC-B10 co-CLOSE。

---

### KPI（00）

（`kpi_aggregator: n/a` · CLOSE 时可选回填）

### 经验总结

ASGI disconnect 不可作唯一沉降路径（Wave A 三抡 live FAIL 实证）· Worker/Subscriber 拆分优先（E3 Wave B 成立）· 断连收尾靠 worker settle + replay 后半段补偿，不靠请求生命周期钩子。

## 修订记录（CLOSED 补行）

| 日期 | 说明 |
|------|------|
| 2026-10-17 | CLOSED：PR #250 MERGED（squash `56e4a9f` · 2026-10-14）· 与 `lg_rag_sse_disconnect_completion` co-CLOSE · 归档 done/ · CLOSE 档 `../close/close_lg_rag_sse_run_worker_co_disconnect_20261017.md` · 批量关账 PR 待开（close/active-batch-20261017）· 分支 `task/lg-rag-sse-run-worker` 移交 00 统一清理 |
