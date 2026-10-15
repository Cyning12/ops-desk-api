# task_lg_rag_sse_run_worker 审查（R1 · 20-task-audit）

> **审查对象**：`docs/tasks/active/task_lg_rag_sse_run_worker.md`（E3 Wave B · RunWorker 与 SSE 订阅解耦 · 部分回复可见 · 失败后继续回复）  
> **审查帽**：20-task-audit（书面审查 · 未改 task 实质内容 · 流程闸交维护者 · 未执行 30 · 零 `app/` 改动 · **未改**旧 disconnect task）  
> **日期**：2026-10-14 · **审查时仓态**：分支 `task/lg-rag-sse-run-worker` @ `9ee928c`（≡ master base · 工作树可含旧 Wave A 脏码 / 两 active task 未提交 docs · 与非范围「勿卷入无关 `uv.lock`」一致）  
> **对照样例**：`docs/harness/reviews/task_lg_rag_sse_disconnect_completion_audit_R1_20261013.md`（结构对齐 · 结论节机读口径）  
> **方案真值**：`docs/harness/invokes/by-task/lg-rag-sse-disconnect-completion/invoke_20261014_00_e3_wave_b_plan.md`  
> **10 invoke**：`docs/harness/invokes/by-task/lg-rag-sse-run-worker/invoke_20261014_10_task_draft.md`  
> **旧 task（只读）**：`docs/tasks/active/task_lg_rag_sse_disconnect_completion.md`

---

## 结论与签收

**结论：PASS-WITH-NITS · 零阻塞**（内容面审查通过 · 四条 NIT 登记在案 · 属挂载面/软验收/字段名/脏树边界级）。

本棒对新 task 草稿完成书面审查：与 E3 Wave B 方案 / 10 落稿一致；D1=A+B（B 为主 · A=补偿）口径正确；「继续回复」≠ HITL resume、帧类型不升级、多副本 MVP 单飞、D3 须开 web、与旧 task co-CLOSE 均已钉死可机断；锚点亲读核真。流程闸与 D1 正式落表仍 pending，交维护者/00 代录。

| 维度 | 结论 |
|------|------|
| task **内容**可执行 | ✅ **PASS-WITH-NITS · 零阻塞**——同上 |
| **流程闸**（审查当时） | HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES = **pending** → 交维护者签；D1 00 代录授权在案、正式落表仍待 |
| lint 复跑 | `task lint` → **LINT: PASS** · `task_lg_rag_sse_run_worker.md` |
| draft 洁净度 | ✓ 起草阶段零 `app/`（本棒确认未改）；旧 disconnect task **本棒未触** |

---

## 审查要点逐项核对

### 1. 锚点实证（task 依赖节 · 本帽逐行亲读 · HEAD `9ee928c` + 工作树实然）✅

| 锚点 | 实证结果 |
|------|----------|
| `sse_stream.py` 文件头 | ✓ 现网 Wave A 实然：断连→执行随 generator 停 + `done{disconnected}`；**明文**「Wave B 解耦另立，本模块不做」——与新 task 问题框定 / 非范围「不赌 ASGI 钩为主路径」同向 |
| `sse_stream.py` 主循环 cancel anext | ✓ `:484+` `ensure_future(_anext_or_end)` · `:541` `next_task.cancel()`；`:635+` `GeneratorExit` / cancel → `_settle_disconnected()`——**今日执行仍绑 HTTP**；Wave B 须拆出 worker 后断连只取消 subscriber |
| `event_store.run_stream_closed` | ✓ `:132-152`：`done` **或** `error` → True（含 `waiting_approval`）——失败 `error{stage:lg_rag.worker_failed}` / 补偿终帧即可解除 409 |
| `event_store.run_is_terminal` | ✓ `:97-129`：`error` 或 `done` 且 `status != waiting_approval`；与 History 互注 |
| `event_store.load_events_after` + `refuse_in_flight` | ✓ `:166-182`：在飞且 refuse → `LgRagRunInFlightError`——TC-B4 零 diff 面 |
| `router.py` `/stream` | ✓ `:302-337`：鉴权后直接 `iter_lg_rag_sse` 进 `StreamingResponse`——**尚无**「先 start worker → 再 subscribe」；与 F5 目标差一刀 |
| `router.py` replay 409 | ✓ `:340-382`：`refuse_in_flight=True` · 409 + `Retry-After: 2` |
| `history.run_terminal_status` | ✓ `:161-171`：末条 `done.status`（缺省 `completed`）/ `error`→`"error"` / 否则 `running`——失败 CTA=`error`；补偿 `disconnected` 已可透传（既有测含变体） |
| `05` §10.3 | ✓ 现写 Wave A 实然（断连≠跑完 · ASGI receive 沉降）；F-D1 要求回写「应然以 worker 为准 · 实然 MVP 单进程」——与方案 §6 一致 |
| 旧 task 只读 | ✓ 正文冻结史实（A 尝试 / TC5×3 FAIL）；新 task 背景/依赖/TC-B10/FP-8/非范围均链 co-CLOSE · **本帽未改正文** |

### 2. 与方案 / 旧 task / 产品口径对齐 ✅

| 核对项 | 结果 |
|--------|------|
| **D1=A+B**（B 为主 · A=补偿 · 不赌 ASGI） | ✅ 裁定表 + 范围 F5–F7 / F-A1–A2 与 `e3_wave_b_plan` / spawn 一致；00 代录授权在案 · 正式落表待闸后 |
| **继续回复 ≠ HITL resume** | ✅ 产品口径 #3 · 非范围 · FP-6 · TC-B3（新 `/stream` + 可选 `continue_from_run_id` · resume 零 diff · replay≠LLM） |
| **帧类型不升级** | ✅ `freeze_id=lg-rag-sse-v1` · 禁 silent 新 `event_type` · 仅扩 `error.stage` / 可选 `done.status`——与方案「帧类型要不要升级」表一致 |
| **多副本单飞** | ✅ 非范围「完整 DB 租约」· F5 MVP 进程内 `run_id` 单飞 · FP-3 · 必读 `task_multi_replica_verify` |
| **D3 web** | ✅ 裁定须开 web · F-D3 · TC-B9（提示证据可勾）· 本仓不强制改 web 码 |
| **co-CLOSE** | ✅ `related_tasks` / 背景 / FP-8 / TC-B10；旧 task D1 史实可保持 A-only（spawn：D1 重签仅落新 task） |
| **graph G-L1** | ✅ 新 `run_worker` → `01_modules` + flow · HG-GRAPH-MODULES 须再签——正确升判 |

### 3. 旧测 grep 影响面（行为变更类 · K7）✅ 代查 · 不退回补列

本 task 改执行生命周期 / 断连后仍跑完 / 失败 stage / 可选 continue_from，属行为变更；验收未单列「旧测影响面」专项（→ **N1**）。本帽代查：

| 代查项 | 实证结果 |
|--------|----------|
| 真在飞 409 | `tests/test_lg_rag_sse_resume.py` `test_replay_in_flight_run_409_with_retry_after` · `test_load_events_refuses_in_flight_run`——**须零 diff**（TC-B4） |
| HITL 挂起 replay | 同文件 `test_load_events_waiting_approval_replays_normally` + `tests/test_lg_rag_sse_hitl.py`——**须零 diff**（FP-2 / TC-B8） |
| History `terminal_status` | `tests/test_chat_history_api.py` `test_run_terminal_status_variants` 已含 `completed` / `waiting_approval` / `disconnected` / `error` / `running`——失败 `error` 面已覆盖；`worker_failed` stage 须新红测（TC-B2） |
| 断连仍跑完 | **零旧测钉死**「断连必停」为产品契约——Wave B 新建 TC-B1/B6；既有 Wave A 断连测若在脏树，30 按 PR 边界收敛，勿与 B 主路径冲突 |

裁定：与 disconnect R1 同口径——**不退回 10 强制补列**；TC-B4/B8 + 代查面实质兜底。

### 4. 范围 / 非范围 / Wave 裁剪 ✅

- **Wave B（主）**：F5–F7 RunWorker + Subscriber + 断连后落盘 + 预算显式——与方案骨架一致。  
- **Wave A（降级）**：F-A1 仅 worker 死/超时补偿；F-A2 HITL/409 零回归——正确降级，非再赌 ASGI。  
- **产品衔接**：F-C1 `continue_from_run_id` 可选；F-C2 History 机读——api 面闭合。  
- **非范围**：禁改旧 task · 禁 ASGI 主路径 · 禁 resume/replay≡LLM · 禁 silent 新 event_type · 禁本仓强改 web · 禁多副本完整租约 · 起草零 `app/`——互斥闭合。  
- **切片**：orchestration「30（B1→B2→薄 B4）」与方案 B1/B2/B4 对齐；web B3 外置——可接受单 task 文档承载、实现分切片。

### 5. 验收可机断性 ✅

| # | 验收 | 可机断性核验 |
|---|------|--------------|
| TC-B1 | 断连仍跑完 → done → replay 后半段 | ✓ DB 终帧 + replay 200 + 观测/日志 |
| TC-B2 | worker 失败 `stage==lg_rag.worker_failed` | ✓ payload 字面量 + `run_stream_closed` + History error |
| TC-B3 | 继续回复=新 run · resume 零 diff | ✓ 新 run_id + 无 resume 调用 |
| TC-B4 | 真在飞 409 | ✓ 对 master 同输入 |
| TC-B5 | 补偿 A | ✓ 无终帧→补终帧→closed 真；**不**以 ASGI 单测当 live 主证 |
| TC-B6 | 旧 TC5 语义替换 live | ✓ settle→replay；附件照登 |
| TC-B7 | 05 + 图谱 + compile | ✓ diff + EXIT=0 |
| TC-B8 | 反回归 | ✓ pytest/ruff |
| TC-B9 | D3 提示证据 | ✓ CLOSE/invoke 勾 |
| TC-B10 | co-CLOSE | ✓ 双 slug |

缺口提醒（NIT）：F7 策略/env 无独立 TC 字面机断（→ **N2**）；`continue_from` 字段名开放（→ **N3**）。

### 6. failure_paths 覆盖 ✅

FP-1 无 error 补偿 · FP-2 HITL 误伤 · FP-3 双 worker · FP-4 成本 · FP-5 前端假期望 · FP-6 resume 误用 · FP-7 闸未签 · FP-8 单关旧 task——主险覆盖充分。

### 7. freeze / event_type 纪律 ✅

不新 freeze · 禁 silent 新 `event_type` · 成功普通 `done` · 失败 `error.stage` · 补偿可 `done{disconnected}`——与方案及 `run_stream_closed`/`run_terminal_status` 兼容。

### 8. 思考轮审查 ✅

控制表 R0–R5 五列齐 · early_stop at R5 理由具体（机理与产品口径已钉 · 再轮无新锚点）· residual（闸未签 · continue_from 名 · 多副本另立 · web 不同步）诚实 · 正文与表互洽。

---

## D1 / D2 / D3 审查建议（供维护者裁定 · 流程闸交维护者）

### D1 波次

| 选项 | 本帽建议 |
|------|----------|
| **A+B（同意 10 / 方案 / 00 代录授权）** | **推荐签此**。本 task **即** E3 另立的 Wave B 真解；A 已降为补偿，**不是**旧 disconnect task 内硬并 A+B。 |
| A-only | 不适用本 slug（旧 task 史实已承载 A 尝试）。 |
| B-only | 可接受但丢僵尸 run 补偿；方案已选 A+B 薄补偿——不推荐改口。 |

### D2 收尾帧形状

| 形状 | 建议 |
|------|------|
| 成功终态普通 `done` | ✅ **钉死**（断连跑完成功路径 **无**强制 `disconnected`） |
| 失败 `error{stage:lg_rag.worker_failed}` | ✅ **钉死**（驱动 History `error` +「继续回复」） |
| 补偿 `done{status:'disconnected'}` 或等价 error | ✅ 仅 F-A1 僵尸/超时；与旧 D2 字面量可并存 |

**本帽建议（流程交维护者）**：确认 10 默认栏即可正式落表；禁 silent 新 `event_type`。

### D3 前端

**须同步开 web task**（部分回复 +「继续回复」CTA）——同意 10 / 方案；api 本 task 供机读终态 + 可选 `continue_from_run_id`。

---

## 非阻塞观察项 / NIT（不升内容否决）

- **N1（K7）**：建议在 TC-B4/B8 或必读旁注旧测文件名：`test_lg_rag_sse_resume.py` · `test_lg_rag_sse_hitl.py` · `test_chat_history_api.py`。本帽代查已覆盖，**不退回强制改稿**。  
- **N2（F7 软验收）**：预算/超时/env 开关无独立 TC；建议 30 钉开关名或文档勾选项，或 10 可选补一行「F7 策略写入 05/README 可机读」。  
- **N3（字段名）**：`continue_from_run_id` 标可选/等价——R2 residual 诚实；30 裁定一字面量并回写 05 即可。  
- **N4（脏树边界）**：工作树可含 Wave A ASGI 沉降实现；本 task 主路径是 worker 解耦。30 以本分支/PR 边界为准，**勿**把 ASGI 钩 live 当 TC-B6 主证；无关 `uv.lock` 勿卷入。

## 建议 10 修订清单（可选 · 非阻塞）

1. （可选）TC-B4/B8 旁注旧测文件名（N1）。  
2. （可选）F7/TC 补一行策略/env 机断（N2）。  
3. （可选）产品口径钉死 `continue_from_run_id` 一字面量（N3）。

本帽**未**直接改 task 草稿（优先列意见）。

## 观察清单（非否决）

**内容面：零阻塞。**  
**须交 10 重写的项：无**（NIT 可选修补）。

**流程闸（审查当时 pending · 交维护者/00 代录）**：

- HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES → 待 `approved`
- **D1**=A+B（00 代录授权在案 · 正式落表待写）· **D2**=成功普通 `done` + 失败 `lg_rag.worker_failed` + 补偿可 `disconnected` · **D3**=须开 web task

---

## 维护者签闸（20 后 · 30 前）

- [x] 已读 R1 审查结论（**PASS-WITH-NITS**）
- [x] 裁定 **D1**=**A+B** 正式落表（00 代录 2026-10-14）
- [x] 裁定 **D2** / **D3** 正式落表（00 代录 2026-10-14）
- [x] 三闸 **approved**（00 代录 2026-10-14 · `invoke_20261014_00_gate_signoff.md`；30 须写 `01_modules.md`）
- [ ] commit task 文档（交维护者 / 30 同批 docs）
- [x] 再下发 Harness 30 Prompt（00 派 B1）
- [ ] （过程）同步开 web task（D3 · TC-B9 · 00/维护者另开）

30 Agent 将以 task 表为准；任一 blocks 30 的闸或 D1 未正式落表时必须拒开工（见 `TEMPLATE_30_gate_stop.md`）。

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-14 | R1 · 20-task-audit：结论 **PASS-WITH-NITS**（零阻塞）· 锚点亲读 · 方案/D1=A+B/co-CLOSE/继续回复≠resume/帧不升级/多副本单飞/D3 web 全核对 · K7 代查 · NIT N1–N4 · 三闸+D1 交维护者 · lint PASS 照登 · 零 `app/` · 未改旧 task · 未附 30 Prompt · 未 commit |
