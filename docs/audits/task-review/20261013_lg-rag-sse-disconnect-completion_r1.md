# task_lg_rag_sse_disconnect_completion 审查（R1 · 20-task-audit）

> **审查对象**：`docs/tasks/active/task_lg_rag_sse_disconnect_completion.md`（SSE 断连后 run 残缺 · 收尾帧 / 执行解耦 · 消解孤儿 in-flight）  
> **审查帽**：20-task-audit（书面审查 · 未改 task 实质内容 · 流程闸交维护者 · 未执行 30 · 零 `app/` 改动）  
> **日期**：2026-10-13 · **审查时仓态**：分支 `task/lg-rag-sse-disconnect-completion` @ `9ee928c`（≡ master base · 工作树含本 task/10 invoke 未提交 docs + `uv.lock` 脏 · 与非范围「勿卷入」一致）  
> **对照样例**：`docs/harness/reviews/task_hitl_resume_replay_contract_audit_R1_20261012.md`（结构对齐 · 结论可不同）  
> **10 invoke**：`docs/harness/invokes/by-task/lg-rag-sse-disconnect-completion/invoke_20261013_10_task_draft.md`

---

## 结论与签收

**结论：PASS-WITH-NITS · 零阻塞**（内容面审查通过 · 四条 NIT 登记在案 · 属措辞/行号/挂载面级）。

本棒对该 task 草稿完成书面审查与复核：契约「断连尽量跑完」vs 实现「generator close → cancel anext → 无 done」张力与码面实然一致；Wave 默认 A-only 裁剪得当；HITL / 真在飞 409 保护区（TC3 · FP-2）闭合；freeze 禁 silent 新 `event_type` 纪律正确；验收可机断；锚点亲读核真。流程闸与 D1/D2 于审查当时 pending，交维护者签；**2026-10-14 起 task 表三闸 + D1/D2/D3 已 approved**（00 代录 · `invoke_20261014_00_gate_signoff.md`）。

| 维度 | 结论 |
|------|------|
| task **内容**可执行 | ✅ **PASS-WITH-NITS · 零阻塞**——同上 |
| **流程闸**（审查当时） | 三闸 pending → 维护者签后 approved（见 task 表 2026-10-14） |
| lint 复跑（审查当时） | `task lint` E5 缺自检结论 → **N1**；task v0.1 已补占位 |
| draft 洁净度 | ✓ 起草阶段零 `app/`；`uv.lock` 脏树未入本 task 产物 |

---

## 审查要点逐项核对

### 1. 锚点实证（task 依赖节 · 本帽逐行亲读 · HEAD `9ee928c`）✅

| 锚点 | 实证结果 |
|------|----------|
| `sse_stream.py` 文件头 L3 | ✓ 「断连语义（T2/T4）：服务端尽量跑完图；不保证客户端收齐；无 cancel。」——与 §10.3 / task 契约句一致 |
| `sse_stream.py` 主循环 finally cancel anext | ✓ `:396-425`：`while True` + `ensure_future(_anext_or_end)`；`:422-425` 注释「生成器被 close（断连）或异常时取消挂起的 anext，防 task 泄漏」+ `next_task.cancel()`——**断连实然停跑**核真 |
| `sse_stream.py` Exception→error | ✓ `:509-525` `except Exception` → emit `error` + `_drain_persist`；**:526-531 `finally` 仅 reset sink / drain / flush_traces，不发收尾帧**。task 写作 `:509-531` 略宽（→ **N2**） |
| 纯断开无收尾机理 | ✓ `GeneratorExit` ∉ `Exception` → 客户端 close 生成器**不会**走 error 帧；外层 finally 亦不补 `done`/`error`——与 task「纯断开通常无收尾」一致 |
| `event_store.run_stream_closed` | ✓ `:132-152`：存在 `done` **或** `error` 即 True；**刻意**含 `done{waiting_approval}`（挂起也算收尾） |
| `event_store.run_is_terminal` | ✓ `:97-129`：`error` 或 `done` 且 `status != waiting_approval` → 终态；与 History 口径互注 |
| `event_store.load_events_after` + `refuse_in_flight` | ✓ `:166-182`：`refuse_in_flight and not run_stream_closed` → `LgRagRunInFlightError` |
| `router.py` replay 409 | ✓ `:336-395`：`refuse_in_flight=True` · 捕 `LgRagRunInFlightError` → **409** + `Retry-After: 2`（F-OBS-2） |
| `05` §10.3 | ✓ 表行「断连服务端仍『尽量跑完』图（**无** cancel）」——与文件头契约同向；实现张力成立 |
| web T4 遗留 | ✓ `ops-desk-web/.../task_web_lg_rag_sse_t4.md`：「客户端断开即取消 SSE generator…后续帧（含 done）不再产生」——与 task 引文一致 |
| 孤儿 409 活样本 | ✓ `invoke_20261013_40_verify.md`：run `22b65ce2…` 掐断后复打仍 409——F-OBS-DISCONNECT 产品后果有案 |

### 2. 旧测 grep 影响面（行为变更类 · K7）✅ 代查 · 不退回补列

本 task 改断连收尾 / 解除孤儿永久 409，属行为变更；验收未单列「旧测影响面」专项（→ **N3**）。本帽代查：

| 代查项 | 实证结果 |
|--------|----------|
| 真在飞 409 钉死面 | `tests/test_lg_rag_sse_resume.py:220+` `test_replay_in_flight_run_409_with_retry_after` · `:264+` `test_load_events_refuses_in_flight_run`——**须零 diff**（TC3 已钉） |
| HITL 挂起 replay | 同文件 `:289+` `test_load_events_waiting_approval_replays_normally` + `tests/test_lg_rag_sse_hitl.py` waiting+done{waiting_approval}——**须零 diff**（FP-2 / TC3） |
| History `terminal_status` | `tests/test_chat_history_api.py:250+` 仅钉 `completed` / `waiting_approval` / `error` / `running`——D2 若选 `done{status:cancelled\|disconnected}`，30 须**扩展**该变体测（非破坏既有断言） |
| 断连无收尾旧断言 | **零命中**——无旧测钉死「断连后永久无 done」；Wave A 增收尾帧对旧测破坏面空；红测须新建（TC1 已要求） |

裁定：与 hitl R1 同口径——**不退回 10 强制补列**；TC3 + TC7 全量对拍实质兜底；N3 建议 10/30 在必读或 TC 旁注挂载面文件名即可。

### 3. 范围 / 非范围 / Wave 裁剪 ✅

- **Wave A**（F1–F4）：收尾帧 + `run_stream_closed` + 红测 + §10.3 实然回写——与问题最小解一致，**默认本 task 可接受**。  
- **Wave B**（F5–F7）：执行与 SSE 解耦——面大（worker / 多副本单飞 / 预算）；task 已标「建议另立」且 **D1 阻塞 30**。  
- **非范围**：禁 replay≡resume、禁 silent 新 `event_type`、HITL 状态机零 diff、起草零 `app/`——互斥闭合。  
- **A+B 并入**：文档列出 B 本身**不**构成范围否决（D1 默认 A-only + 显式裁定口）。**若维护者签 D1=A+B**，本帽建议视为范围过大 → **拆 task 或另立 Wave B**（见「D1/D2 建议」），勿单 PR 吞多副本 worker。

### 4. 验收可机断性 ✅

| # | 验收 | 可机断性核验 |
|---|------|--------------|
| TC1 | 断连收尾红→绿 | ✓ 收尾帧存在 + `run_stream_closed==True`；时序 git 可查 |
| TC2 | 孤儿 replay 不再永久 409 | ✓ 夹具/历史形态 → 200 含收尾或明确终态语义 |
| TC3 | HITL / completed / 真在飞 409 零 diff | ✓ 对 master 同输入；与既有 `test_lg_rag_sse_resume` 钉死面同向 |
| TC4 | §10.3 + 图谱 + graph-compile | ✓ 文档 diff + EXIT=0 |
| TC5 | live 40 中途杀客户端 | ✓ 照登附件；依赖 live 已作 residual |
| TC6 | 仅 Wave B | ✓ 条件启用；与 D1 互锁 |
| TC7 | 全量对拍 + ruff | ✓ 命令可查 |

缺口提醒（NIT 级）：TC 未显式写「旧测挂载面文件名」；机断性仍成立。

### 5. failure_paths 覆盖 ✅

FP-1 落盘失败/补偿 · FP-2 误伤 waiting_approval · FP-3 Wave B 双 worker · FP-4 断连仍烧 LLM · FP-5 假续看文案 · FP-6 闸未签——主险覆盖；与 HITL/409/成本边界互锁充分。

### 6. freeze / event_type 纪律 ✅

`freeze_id=lg-rag-sse-v1` · **不**新 freeze · 禁 silent 新 `event_type` · 收尾优先复用 `error` / `done`+status 扩展键（对齐既有 `waiting_approval` 先例）——正确。D2 若选新 status 字面量须回写 05 + History 测。

### 7. 思考轮审查 ✅

控制表 R0–R5 五列齐 · early_stop at R5 理由具体（机理单一 · 波次开放 · 再轮无新锚点）· residual_risks 诚实（Starlette 钩点留 30 · D2 vs History · 补偿是否本 task）。R0–R5 正文与表互洽。

---

## D1 / D2 审查建议（供维护者裁定 · **非代签**）

### D1 波次

| 选项 | 本帽建议 |
|------|----------|
| **A-only（同意 10 默认）** | **推荐签此**。先诚实收尾 + 解除孤儿永久 409 + 产品「须重问」可机读；兑现成本低、误伤面可控、与 T4 遗留/F-OBS-2 活样本直接对齐。 |
| A+B | **不推荐本 task 内合并**。B 触及执行生命周期 / 多副本单飞 / 预算，应另立 task（或 docs-spike 后另立）；若强行 A+B → 视为范围过大，建议退回 10 拆分后再审。 |
| B-only | 不解决「当前孤儿永久 409」最短路径；且 B 未交付前假续看仍在——不推荐作本缺口首刀。 |
| docs-spike 后另立 | 仅当对 Starlette 钩点/落盘时机仍无把握时；本帽锚点已够 Wave A 开工，**不必**先 spike。 |

### D2 收尾帧形状

对照 `history.run_terminal_status`（`:161-171`：取末条 `done.status` 或缺省 `completed`；`error`→`"error"`）与 `run_stream_closed` / `run_is_terminal`：

| 形状 | `run_stream_closed` | `run_is_terminal` | History `terminal_status` | 建议 |
|------|---------------------|-------------------|---------------------------|------|
| `error{stage:…}` | ✅ | ✅ | `"error"` | 可用但易与真失败混淆；若用须 **stage 钉死可机读**（如 `lg_rag.client_disconnect`）且 05 回写 |
| `done{status:'cancelled'}` | ✅ | ✅（≠ waiting_approval） | `"cancelled"` | 与 chat legacy cancel 语感近；可接受 |
| `done{status:'disconnected'}` | ✅ | ✅ | `"disconnected"` | **更贴产品实然**（客户端走了 · 非用户主动 cancel） |
| 两者兼 | ✅ | ✅ | 末帧胜 | **不推荐**——双帧噪声 · 无增益 |

**本帽建议（非代签）**：优先 **`done{status:'disconnected'}`**（或团队更熟的 `'cancelled'` 二选一钉死一字面量）；**不要** silent 新 `event_type`；**不要**默认走泛化 `error` 除非 stage 契约先钉。须同步扩展 `test_run_terminal_status_variants` + §10.3 实然句（断连=收尾取消/断连帧 · **不**等同跑完）。

---

## 非阻塞观察项 / NIT（不退回升 BLOCKED）

- **N1（E5）**：缺 `### 自检结论` 节 → `task lint` FAIL。建议 10 补「10 起草者」占位（对齐历 task）；**不**阻内容通过。  
- **N2（行号）**：Exception→error 精确 `:509-525`（非 `:509-531`）；30 按实校正即可。  
- **N3（K7）**：建议在 TC3/必读旁注旧测挂载面：`test_lg_rag_sse_resume.py`（409/挂起）· `test_lg_rag_sse_hitl.py` · `test_chat_history_api.py`（terminal_status）。本帽代查已覆盖，**不退回强制改稿**。  
- **N4（观察）**：Wave A 实现钩点（`GeneratorExit` / request cancel / `finally` 仍可 `emit+persist` 的时序）留 30 实证；R1 residual 已诚实。注意：收尾必须在 sink reset / 连接彻底拆掉**之前**落盘（对照 FP-1）。

## 建议 10 修订清单（可选 · 非阻塞）

1. 增补 `### 自检结论（10 起草者）` 以满足 E5。  
2. 依赖节 Exception 锚点改为 `:509-525`。  
3. （可选）TC3 或必读增一行旧测文件名枚举。  
4. （可选）D2 默认建议栏补一句「倾向 done+status 扩展键 · 对照 history.run_terminal_status」。

本帽**未**直接改 task 草稿（优先列意见；无「明显笔误」级单字符错误须热修）。

## 观察清单（非否决）

**内容面：零阻塞。**  
**须交 10 重写的项：无**（NIT 可选修补）。

**条件范围过大（仅当维护者签 D1=A+B 且坚持单 task 交付）**：应拆 Wave B 另立后再开 30。

**流程闸（审查当时 pending · 2026-10-14 已签）**：

- HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES → **approved**（00 代录）
- **D1**=A-only · **D2**=`done{status:'disconnected'}` · **D3**=api-only

---

## 维护者签闸（20 后 · 30 前）

- [x] 已读 R1 审查结论（**PASS-WITH-NITS**）
- [x] 裁定 **D1**=**A-only**（已写入 task 裁定表 · 2026-10-14）
- [x] 裁定 **D2**=**`done{status:'disconnected'}`**（已写入 task 裁定表 · 2026-10-14）
- [x] （可选）E5 自检结论已由 10 修订补齐（task v0.1）
- [x] 人工闸表三闸 **approved**（维护者 · 00 代录 2026-10-14 · `invoke_20261014_00_gate_signoff.md`）
- [ ] commit task 文档（交维护者 / 30 同批 docs 提交亦可）
- [x] 再下发 Harness 30 Prompt（红测先行 · Wave A · 00 派子 Agent）

30 Agent 将以 task 表为准；任一 blocks 30 的闸或 D1 pending 时必须拒开工。

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-14 | 00 软修结论节机读口径（「内容阻塞/不代签/退回」→「零阻塞/交维护者/拆 task」）· 同步签闸后态 · 内容结论未变 |
| 2026-10-13 | R1 · 20-task-audit：结论 **PASS-WITH-NITS**（零阻塞）· 锚点全实证（HEAD `9ee928c`）· 旧测影响面代查（K7 可选旁注）· D1 建议 A-only · D2 建议 `done{status:disconnected\|cancelled}` · NIT N1–N4 · 三闸+D1/D2 交维护者 · lint E5 FAIL 照登 · 零 `app/` 改动 |
