# ROADMAP：lg-rag 传输主线 · Session / SSE（L0）

> **层级**：L0 规划（跨 `lg_rag` / session / tracing / 传输契约）  
> **状态**：`active`（2026-08-30 **T0 签收** · HG-SPEC-SIGNOFF approved；**不**直接授权 30；实现须另开 task）  
> **上游**：[`00_architecture_and_boundaries.md`](./00_architecture_and_boundaries.md) · H3 [`session/ROADMAP_chat_continuity_v0.md`](./session/ROADMAP_chat_continuity_v0.md)（思想继承）· [`04_eval_and_observability_plan_v0.md`](./04_eval_and_observability_plan_v0.md)  
> **域夹**：[`session/`](./session/)（主）· 观测穿插回指 [`eval/`](./eval/)  
> **本波文档 task**：[`task_lg_rag_sse_t0_t1_spec`](../../tasks/done/task_lg_rag_sse_t0_t1_spec.md)（**CLOSE** · Spec 签收完成 · 无改码）

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **plan_slug** | `lg-rag-transport-session` |
| **invoke_slug** | `lg-rag-sse-t0-t1-spec` |
| **test_strategy** | 本文件为规划；实现波次另开 task 时再填 |
| **graph_change_layer（建议）** | 实现波多为 `G-L1`（transport / session）；本 Spec 波 `none` |
| **默认分支** | `task/lg-rag-sse-t0-t1-spec`（本签收波） |

### 人工闸（SPEC / T0）

| human_gate_id | status | 说明 |
|---|---|---|
| **HG-SPEC-SIGNOFF** | **approved** | 2026-08-30 · **00 代签 · 维护者令「签收」** · §3 优先级表 + §4 T0/T1 |

---

## 1. 背景与主线决策（已钉死 · 2026-08-30）

| 决策 | 内容 |
|---|---|
| 传输主线 | **`lg_rag` SSE**；LangGraph Agent（supervisor 图）为未来产品主路径 |
| Chat | **弃用方向**；后续 Spec / 实现 **不保证**兼容 `chat/graph` · `/chat/stream` 契约 |
| Session | **继承 H3 思想**（消息持久化 · 窗口压缩 · seq/cursor · 断线 replay），**不以 chat 兼容为目标** |
| 颗粒度 | **系列 Spec / 多 task**；单 task 无法覆盖全节点过程流 + 终答 SSE + 断联重启 |
| Obs 内容 I/O | 纳入本轨优先级表；**不**单独开 Obs-I/O task（见 §3） |

### 一句话目标

把「旁路 `POST /lg-rag/invoke`」演进为 **可流式、可续会话、可断线恢复** 的产品传输面，观测上可看清节点过程与 LLM 正文 I/O；Chat 仅作过渡期并存，不进入新契约兼容矩阵。

---

## 2. 波次总表（系列 · 示意 ID）

| 序 | ID | 摘要 | 本波是否交付条文 |
|---|---|---|---|
| **T0** | `product-boundary` | 主线签收：lg-rag SSE · chat 弃用时间表 · 非兼容声明 | **是**（§4.1） |
| **T1** | `event-contract` | 节点进度 + 终答帧字段表（`run_id`/`seq`/`event_type`/…） | **是**（§4.2 草案级） |
| **Obs-I/O** | `langfuse-generation-io` | Generation 截断 Input/Output；与 SSE 解耦 | **优先级表**（§3）；**不**单开 task |
| **T2** | `stream-updates` | `POST /lg-rag/stream` · `astream(updates)` · 无 token 流 | 否 · 签收后另 task |
| **T3** | `session-continuity` | thread/session · 历史注入 · 窗口策略迁到 lg-rag | 否 · 见 session ROADMAP |
| **T4** | `disconnect-resume` | cursor / replay 或 run-resume；可先契约后实现 | 否 |
| **T5** | `token-stream` | aggregator（等）token 级 SSE | 否（实现已合；契约见 §4.2 / §10.4） |
| **T5.1** | `delta-realtime` | 终答 delta **投递时效**（pacing / anti-buffer）；不改 event_type | **是**（§10.4.1 · 2026-09-01） |
| **T6** | `deprecate-chat` | 文档/前端切流 · chat 下线窗口 | 否 |

**顺序建议**：T0/T1 签收 →（实现可穿插 Obs-I/O）→ T2 → T3/T4 → T5 → T6。  
**T5.1**：T5 合入后的契约增量（与 T6 **正交**）；本文件钉应然，缺口修复另实现 task。  
**禁止**：未签 T0/T1 就改现网默认路由到 supervisor，或强行兼容 chat 事件全集。

详规（Session）：[`session/ROADMAP_lg_rag_session_continuity_v0.md`](./session/ROADMAP_lg_rag_session_continuity_v0.md)。

---

## 3. 优先级表（本波真值 · T0 + T1 + Obs-I/O）

> **用途**：维护者签收与后续拆 task 的排序依据。  
> **Obs-I/O 定夺**：影响面小、与 SSE 解耦 → **优先级高**；但 **不单独出 task**——并入首个实现波（建议随 **T2** 最小 diff，或 T2 前的同 PR 薄提交），由 00 在开 T2 task 时写入验收条，而非再开 `task_langfuse_io_*`。

| 优先级 | ID | 交付物 | 影响范围 | 依赖 | 建议落地形态 |
|:---:|---|---|---|---|---|
| **P0** | **T0** | 产品边界：主线 / 弃用 / 非兼容 | 文档 · freeze 声明 | — | 本文件签收即生效 |
| **P0** | **T1** | SSE 事件契约草案（节点 updates + 终答） | 文档 · 未来 HTTP freeze | T0 | 本文件 §4.2；实现随 T2 |
| **P1** | **Obs-I/O** | Langfuse Generation 正文 Input/Output（截断 + 脱敏策略） | `tracing` / LLM complete 边界；**不**依赖 SSE | T0 思想对齐即可 | **不单开 task**；挂 T2（或紧随）验收 |
| P2 | T2 | `/lg-rag/stream` + updates 映射 | `lg_rag` router · 新 SSE | T0+T1 | 另 task |
| P3 | T3 | lg-rag Session 连续性 | session · checkpointer · DB | T1（字段）· 可与 T2 尾穿插 | 另 task |
| P3 | T4 | 断联 replay / resume | 传输 + 事件存储 | T1+T2（有流才有 cursor） | 另 task；可先契约 |
| P4 | T5 | token 流 | provider stream + 终答帧 | T2 稳 | 另 task |
| P5 | T6 | 弃用 chat | 多仓文档 / 前端 | T2+ 产品可用 | 另 task |

### 3.1 Obs-I/O 设计钉死（避免后续 SSE 大改）

| 钉死项 | 内容 |
|---|---|
| 写入边界 | 单次 LLM `complete`（或等价）结束时 `update` generation；**不是** SSE payload 当唯一 I/O 源 |
| 与 SSE | SSE 只推业务事件；Langfuse I/O 独立；token 流时在流结束再 flush 全文即可 |
| 安全 | 截断长度 · PII/密钥脱敏 · 与 E5 usage 键并存 |
| 非本波 | 不改 score 字典；不强制全路径补齐（可列缺口清单随 T2） |

### 3.2 与 Eval 轨关系

- E0–E5：测评 / 费用账本 **正交**；Obs-I/O 补的是 **内容可观测**，不替代 Dataset/Score。  
- 不在本轨重开 Eval task；字典若需新 metadata 键，走 `eval/ROADMAP` 修订记录，随实现波最小 diff。

---

## 4. T0 / T1 条文（签收范围）

### 4.1 T0 · 产品边界

**范围内**

- 声明：产品问答传输主线 = `lg_rag` supervisor（及后续同图演进）+ SSE。  
- 声明：`/api/ops/chat/stream`（及 chat 图）进入 **弃用通道**；新功能 **不**要求 chat 兼容。  
- 声明：Session/断点能力以 **lg-rag thread/session** 为 SoT，H3 Chat 实现仅作参考实现。

**非范围（T0）**

- 不定具体下线日（留给 T6）。  
- 不删 chat 代码。  
- 不定前端改版排期。

**验收（文档）**

- [x] 本条与维护者口头决策一致，写入修订记录日期。  
- [x] session 域 README 指向新 ROADMAP，并标注 H3 chat ROADMAP 为「归档参考」。

### 4.2 T1 · 事件契约草案

**设计原则**

- 继承 Chat SSE **外形思想**：`run_id` · `seq` · `ts_ms` · `agent_role` · `event_type` · `payload`（见既有 iOS/chat 文档），**字段语义按 lg-rag 节点重映射**，不承诺与 chat `thinking`/`answer` 行为 1:1。  
- 第一版（T2）以 **节点完成 updates** 为主；token 碎片留给 T5。  
- 终答：至少一帧明确「最终答案」（整段或后续改为 delta），再 `done`。

**建议 `event_type` 子集（草案 · 实现可微调但须回写本表）**

| event_type | 典型 agent_role | 含义 |
|---|---|---|
| `run.start` | `system` | 开跑；带 `run_id` / `thread_id` |
| `node.progress` | `intent` / `strategy_builder` / `supervisor` / … | 节点完成摘要（非全文 dump） |
| `subtask.progress` | `rag_subtask` / `info_extract` / `tool_exec` | 子任务进度 / 结果摘要 |
| `answer` | `aggregator` / `direct_answer` | 最终答案（**T5 已实现**：token delta 多帧 `{"delta": "<chunk>"}` 按 `seq` 有序拼接 + 终帧 `{"content": "<full>", "final": true}`；T2 兼容——旧客户端仅看 `content` 行为不变；流式降级时仅终帧整段）。**T5.1**：`delta` 须在生成过程中持续 SSE 刷出，**不得**等 aggregator / direct_answer 节点整段结束后再批量 flush（应然；见 §10.4.1） |
| `done` | `system` | 正常结束；可选 `payload.status`：`waiting_approval`（HITL）· `disconnected`（仅补偿/worker 死无终帧）· 缺省≡completed |
| `error` | `system` | 失败；`retryable` 布尔；**Wave B** `payload.stage` 钉 `lg_rag.worker_failed`（worker 异常；禁 silent 新 event_type）；**supervisor-first（2026-10-19）** `payload.stage` 增 `supervisor_plan`（supervisor 首次规划失败 fail-closed 停图 · 灾备 env `LG_RAG_SUPERVISOR_PLAN_ON_FAIL=error(默认)|single_rag`，single_rag 降级续跑终帧 `done.degraded=true`） |
| `cursor`（可选 · T4） | `system` | 供 replay 的游标提示（**可选** `event_type`；本波 SoT 见下行顶层字段） |

**T4 顶层 `cursor` 字段（freeze `lg-rag-sse-v1` 扩展 · 2026-08-31）**

- 每帧 SSE `data` JSON **可选顶层** `cursor = "{run_id}:{seq}"`（与 `run_id`/`seq` 并列）。  
- **不强制**每帧另发 `event_type=cursor`；表内 `cursor` 行仍为可选提示。  
- 客户端续看：`POST /api/ops/lg-rag/replay`，body `{run_id, after_seq}` 或 `{cursor}`（解析后重放 `seq > after_seq`）。  
- 事件落盘表：`ops_lg_rag_run_events`（独立于 chat `ops_run_events`）。

**非范围（T1）**

- 不定 WS 双通道（可后置）。

**T2 冻结（2026-08-30）**

- HTTP 路径：`POST /api/ops/lg-rag/stream`  
- freeze_id：`lg-rag-sse-v1`  
- 默认 `mode=supervisor`；`stream_mode=updates`；断连=服务端尽量跑完、无 replay

**T4 冻结补充（2026-08-31）**

- 同 freeze_id：`lg-rag-sse-v1`（顶层可选 `cursor` + `POST /lg-rag/replay`；不 silent 扩必选 `event_type`）  
- 断连仍「尽量跑完」、无 cancel；replay 仅已落盘帧（**Wave B 真源**=RunWorker；HTTP 订阅可断）

**T5 冻结补充（2026-08-31）**

- 同 freeze_id：`lg-rag-sse-v1`（`answer` 扩多帧 delta + 终帧 `final` 标记；**不**新增 `event_type`）  
- 客户端规则：见 `delta` 追加、见 `content` **全量替换**、`done` 后停止追加；禁止把 `content` 帧 append 到 delta 结果（§10.4 常见坑）  
- token 归属**仅** aggregator / direct_answer 的终答 LLM（`complete_stream` + contextvar token sink）；流式不可用/异常 → 降级整段（T2 行为）+ 日志；终帧沿用 32_000 截断

**T5.1 冻结补充（2026-09-01 · 投递时效 · 不新 freeze）**

- 仍 **`lg-rag-sse-v1`**：不新 freeze、不新 `event_type`、不改 `delta` / `content` / `final` 键语义  
- 跨端打字机 SoT = **SSE 上 delta 的到达时间线**（非前端定时器缓冲）；细则 §10.4.1

**验收（文档）**

- [x] 上表可作为 T2 mock 流测的断言骨架。  
- [x] 明确「不兼容 chat 事件全集」。

### 4.3 failure_paths（规划级）

| 触发 | 期望 | 波次 |
|---|---|---|
| 客户端断连 | 服务端可取消或继续跑完（T2 定一种）；T4 起支持按 cursor replay | T2/T4 |
| 非法 `thread_id` | 4xx；不泄露内部栈 | T2+ |
| 节点异常 | `error` 帧 + trace 保留；策略对齐现 lg_rag「宁退化不拖垮」处继续沿用 | T2 |
| Generation I/O 上报失败 | **不**阻断主答；打日志 | Obs-I/O |

---

## 5. 非目标（本 L0 全轨）

- 动态 StateGraph compile  
- 以兼容 chat 为验收条件  
- 完整长期记忆产品  
- 用 SSE 替代 Langfuse 做唯一观测  
- 本签收波改 `app/`（**禁止**）

---

## 6. 思考轮控制（10-spec 摘要）

| 轮 | 结论 |
|---|---|
| R0 | 维护者：lg-rag SSE 主线 · 弃用 chat · 系列 Spec · I/O 进优先级表不单开 task |
| R1 | 范围 = T0+T1 条文 + 全波优先级；非范围 = 实现码 / T2+ 细则冻结 |
| R2 | 方案 A 旁路 lg-rag 流（选）vs B 先改 chat 兼容（弃 · 与主线冲突） |
| R3 | 断连与 I/O 失败不得拖垮主答；PII 截断 |
| R4 | 本波验收 = 文档签收表；实现可测性留给 T2 task |
| R5 | 交维护者 `HG-SPEC-SIGNOFF`；通过后 00 方可拆 T2（含 Obs-I/O 验收条） |

| 项 | 值 |
|---|---|
| early_stop | no |
| residual_risks | T1 事件名在 T2 仍可能微调；chat 弃用窗口未定导致双栈并存成本 |

---

## 7. 00 入口

- **已签收**：可拆实现 task（建议首棒 **T2**，验收含 **Obs-I/O**）——须维护者令「开工」  
- Session 详规：[`session/ROADMAP_lg_rag_session_continuity_v0.md`](./session/ROADMAP_lg_rag_session_continuity_v0.md)  
- G-L2 义务：见 **§9**（系列硬约束）  
- **本文件不授权 30 改码**（实现波另开 task）

---

## 8. 修订记录

| 日期 | 说明 |
|---|---|
| 2026-08-30 | 初版：主线钉死；T0–T6 波次；§3 T0+T1+Obs-I/O 优先级表；Obs-I/O 不单开 task |
| 2026-08-30 | **HG-SPEC-SIGNOFF=approved**（T0 · 00 代签 · 维护者令「签收」）；状态 `active`；下一棒 00 拆 T2（验收含 Obs-I/O） |
| 2026-08-30 | **T2 冻结**：`POST /api/ops/lg-rag/stream` · `lg-rag-sse-v1`；Obs-I/O 随 T2 实现 |
| 2026-08-31 | **§9 G-L2**：本系列凡改 `10_flow_lg_rag` 节点须同步分域 indexes 全量 `implementedBy`；禁止并入 chat yaml |
| 2026-08-31 | **§10–§11**：分阶段联调注意事项 · 跨仓发版 · web task/checklist 指针 |
| 2026-08-31 | **T2 CLOSE**：§10 指针改 done/ · web slug `task_web_lg_rag_sse_t2` · 发版策略改为后续波纪律 |
| 2026-08-31 | **T3 实现回写 §10.2**：`thread_id` SoT · 独立表 · 窗口压缩 6/2 注入 `_ainvoke/_astream` · 跨用户 404 |
| 2026-08-31 | **§10.4**：链 [`WAVE_READINESS_lg_rag_sse_v0.md`](./WAVE_READINESS_lg_rag_sse_v0.md)（web T4 CLOSE 后查 T5 就绪） |
| 2026-08-31 | **T4 实现回写 §4.2/§10.3**：顶层可选 `cursor` · `ops_lg_rag_run_events` · `POST /lg-rag/replay` · 断连仍跑完 |
| 2026-08-31 | **T5 实现回写 §4.2/§10.4**：`answer` delta 多帧 + 终帧 `final`（aggregator / direct_answer 同协议 · token sink 桥 · 降级整段）· freeze 扩展 `lg-rag-sse-v1` |
| 2026-09-01 | **T5.1**：终答 delta 实时投递（pacing / anti-buffer）契约增量 · 动机 = 防 burst 观感 + 跨端通用（非改 event_type）· §4.2 旁注 + §10.4.1 + §11 勾选；实现另 task |
| 2026-09-01 | **T5.1 HG-SPEC-SIGNOFF=approved**（00 代签 · 维护者令「签收」· 20 审查 pass）；**不**授权 30；实现须另开 `lg-rag-sse-delta-realtime` |
| 2026-09-01 | **T5.1 实现回写**：`emit` 后台 persist（不阻塞 yield）· §10.4.1 实然更新 · task `lg-rag-sse-delta-realtime` |
| 2026-09-07 | **§10.6**：client idle 120s + SSE comment keepalive 30s；联调项去墙钟 300s；task `lg-rag-sse-idle-keepalive` |
| 2026-09-07 | **§10.7**：subtask `status=running` 起步帧（progress sink）· MVP；task `lg-rag-sse-subtask-live` |
| 2026-09-08 | **§10.7 增补**：`status=step` 里程碑（router 节点 + retrieve/grade/answer）· provider 禁 aread 整包；task `lg-rag-sse-subtask-steps` |
| 2026-10-14 | **§10.3 实然回写**：断连=落盘 `done{status:'disconnected'}`（**不**等同跑完）· task `lg-rag-sse-disconnect-completion` Wave A |
| 2026-10-14 | **§10.3 R2**：ASGI≥2.4 挂 `request.is_disconnected` 轮询沉降（不依赖 generator aclose）· 30-R2 |
| 2026-10-14 | **§10.3 R3**：改挂 `request.receive` **阻塞**等 `http.disconnect`（弃 peek 轮询；Starlette `is_disconnected` CancelScope 非阻塞读 live 假绿）· 30-R3 |
| 2026-10-14 | **§10.3 Wave B**：断连尽量跑完以 RunWorker 为准（HTTP 只订阅）；失败 `error{stage:lg_rag.worker_failed}`；MVP 单进程 · task `lg-rag-sse-run-worker` |

---

## 9. G-L2 indexes 义务（本系列硬约束 · 2026-08-31）

> 配套真值：[`../../_tech_graph/l2/README.md`](../../_tech_graph/l2/README.md) · [`../inform-graph-backfill/layers/G-L2_indexes.md`](../inform-graph-backfill/layers/G-L2_indexes.md) · 倒排 [`../../_tech_graph/l2/indexes/by_path_lg_rag.yaml`](../../_tech_graph/l2/indexes/by_path_lg_rag.yaml)

### 9.1 钉死

| 项 | 要求 |
|---|---|
| 范围 | 本系列（T0–T6 · Obs-I/O · Session 轨）凡触及 **`10_flow_lg_rag`** 上带 `implementedBy` 的节点，**必须**更新 G-L2 |
| 覆盖 | **`implementedBy` 全集**进 `by_path_lg_rag.yaml` + `by_symbol_lg_rag.yaml`（含 basic/router/supervisor/strategy；**不是**仅传输切片） |
| 分文件 | **禁止**写入 chat 的 `by_path.yaml` / `by_symbol.yaml` |
| 同步 | 改 flow yaml / 增删节点 / 改 symbol 的同一 task 内必须改 indexes；`graph-compile` 绿 |
| 后续波 | T3–T6 若新增 HTTP/节点/`implementedBy`，验收条默认含「L2 indexes 已同步」 |

### 9.2 非本约束

- 不要求全仓每个 `app/ops/**/*.py` 进 indexes  
- 不把 chat G-L2 迁入本系列义务  
- AST 自动生成仍属可选（W5）

### 9.3 各波次验收钩子（00 拆 task 时写入）

| 波次 | L2 最低要求 |
|---|---|
| T2（已开） | flow `lg_stream`/`lg_invoke` + **全图既有** `implementedBy` 已入 lg_rag indexes |
| T3 Session | 新 session 装配符号若挂 flow → 补 indexes |
| T4 断联 | replay/cursor 相关 `implementedBy` → 补 indexes |
| T5 token 流 | stream 符号变更 → 补 indexes |
| T5.1 投递时效 | 本波 docs-only · **不**改 indexes；实现波若改 stream 符号 → 同 T5 钩 |
| T6 弃用 chat | 文档为主；若删 lg_rag 边/节点 → 同步删 indexes 条目 |
| Obs-I/O | 默认不新增 flow 节点；若 `tracing` 挂进 flow `implementedBy` 再补 |
---

## 10. 前端接入与联调（分阶段 · 2026-08-31）

> **跨仓真值**：本文件 §10–§11 · api [`task_lg_rag_sse_stream_updates`](../../tasks/done/task_lg_rag_sse_stream_updates.md)（**CLOSED** · api [#97](https://github.com/Cyning12/ops-desk-api/pull/97) MERGED） · web [`task_web_lg_rag_sse_t2`](../../../ops-desk-web/docs/tasks/done/task_web_lg_rag_sse_t2.md)（**CLOSED** · web [#23](https://github.com/Cyning12/ops-desk-web/pull/23) MERGED） · 人工清单 [`CHECKLIST_lg_rag_sse_joint_release_v1.md`](../../../ops-desk-web/docs/checklists/CHECKLIST_lg_rag_sse_joint_release_v1.md)  
> **发版策略（后续波）**：api / web **各开 PR、禁止自动 merge**；**联调 checklist 对应波次全勾**后 **同日发版**（见 §11）。T2 已于 2026-08-31 合入。

### 10.0 总原则

| 项 | 钉死 |
|---|---|
| 契约 | `lg-rag-sse-v1` · `POST /api/ops/lg-rag/stream` · 事件 §4.2（**不**兼容 chat `thinking` 全集） |
| Chat 弃用 | 产品主线弃用 `/ops/chat/stream`；web **T2 即切主 Chat 到 lg-rag SSE**（invoke 页保留调试）；api **T6** 再删路由/文档 |
| 联调环境 | cookie 鉴权 · 同域或 dev proxy · api 须含 T2 合入 commit |
| 谁改码 | **web 00 统筹 → web 30 改码**；api 本会话仅 Spec/task，不在 web 仓改 Vue |

---

### 10.1 T2 · SSE updates（**已合入** · api #97 · web #23 · 2026-08-31）

| 维度 | 内容 |
|---|---|
| **前置** | api PR（`/stream` + Obs-I/O）**合入前可联调分支**；web task 已 active |
| **api 提供** | `POST /api/ops/lg-rag/stream` · body `{query, mode?, thread_id?}` · 默认 `mode=supervisor` · SSE 帧序 `run.start`→进度→`answer`→`done`/`error` |
| **web 交付** | `useLgRagSse`（或等价）· **ChatView 改走 `/stream`** · **废弃主路径 `useOpsChatSse`**（可保留文件供对照/单测，主 UI 不再调用）· `/lg-rag` invoke 页不动 |
| **联调项** | ① 登录 cookie ② `run.start` 含 `thread_id`/`mode` ③ 至少一帧 `node.progress`/`subtask.progress` ④ `answer` 整段 ⑤ `done` ⑥ 401→登录 ⑦ 422 表单预检 ⑧ 长问 supervisor：**client idle 超时**（默认 120s 无字节；有帧/keepalive 即重置；**非**整轮墙钟上限 · 见 §10.6） |
| **通过标准** | §11 人工 checklist T2 段全勾 · web `pnpm lint/test/build` 绿 · api 相关 pytest 绿 |
| **常见坑** | 仍走 chat/stream；忽略 `event:` 行只读 body；未 `credentials:'include'`；把 `route=refuse` 当 HTTP 错误；半帧 JSON 未缓冲 |

---

### 10.2 T3 · Session 连续性

| 维度 | 内容 |
|---|---|
| **前置** | T2 联调已通过 · api T3 task 合入 |
| **api 提供（2026-08-31 已实现）** | SoT = `thread_id`（**不**以 chat `session_id` / `GET /chat/sessions/latest` 为 SoT）。独立表 `ops_lg_rag_threads` + `ops_lg_rag_turns`。`POST /lg-rag/stream` 与 `/invoke` 加载归属当前用户的历史，窗口压缩（默认 `max_full_turns=6` · `group_size=2`，纯函数 `app/ops/lg_rag/continuity.py`）后装配进 `_ainvoke/_astream` 的 `messages`（历史 + 本轮 query）。缺 `thread_id`：服务端生成并设响应头 `X-Ops-Lg-Rag-Thread-Id`（stream 200）。跨用户 `thread_id` → **404**（不注入他用户历史）。超长 → 422。未登录 → 401。stream `done` 后尽量落盘本轮 user/assistant，失败只打日志。checkpointer 非跨请求产品 SoT。freeze 仍 **`lg-rag-sse-v1`**，**不**新增 `event_type`。 |
| **web 交付** | Chat 发送带稳定 `thread_id` · 刷新/重进会话行为 · 可选展示 session 元数据（另开 web task；本波可 api-only 先合） |
| **联调项** | 同 thread 续问上下文 · 新 thread 隔离 · 超长历史压缩后仍 SSE 正常 |
| **通过标准** | §11 T3 段 · 多轮 3+ 轮人工冒烟 |
| **常见坑** | 每问新 uuid 导致无法多轮 · 仍依赖 chat `session_id` 字段语义 |

---

### 10.3 T4 · 断联 / replay

| 维度 | 内容 |
|---|---|
| **前置** | T2 稳定 · T4 api 契约冻结 |
| **api 提供（2026-08-31 已实现 · Wave B 2026-10-14）** | live `POST /lg-rag/stream`：先 `start_run_worker`（进程内 asyncio.Task · `run_id` 单飞 · astream 只 emit→`ops_lg_rag_run_events`）再 `subscribe_run_sse` 推 fanout；帧可选顶层 `cursor`。**断连应然**：尽量跑完以 **worker** 为准（HTTP 断连只取消 subscriber，**不** cancel worker）→ 成功普通 `done` → History 完整 · `POST /lg-rag/replay` 200 补后半段；失败 `error{stage:lg_rag.worker_failed}` → `run_stream_closed` 真 → 「继续回复」= 同 `thread_id` **新** `/stream`（可选 `continue_from_run_id` 注入 partial · **禁** HITL resume · **禁** replay≡再调 LLM）。**实然**：MVP 单进程 fanout；多副本租约另立。Wave A ASGI disconnect 钩**停赌**；补偿仅 worker 死/超时无终帧可 `done{disconnected}`。真在飞仍 409+Retry-After；HITL `done{waiting_approval}` 零 diff。freeze 仍 **`lg-rag-sse-v1`**（不 silent 新 `event_type`；扩 `error.stage` / 可选 `done.status`）。**replay 恢复段/follow（2026-10-28 · task_lg_rag_replay_resume_ux_opt）**：HITL resume 恢复段在写窗（`hitl.resumed` 已落盘、新收尾帧未落）replay `follow=false` 命中 → 409+Retry-After:2（detail 与首段在飞 409 可区分 · 谓词 `run_resume_in_progress` · stale 阈 `LG_RAG_RESUME_STALE_SECONDS` 默认 900s 超阈放行）；`ReplayRequest.follow=true` opt-in 续流：推存量→DB 轮询按 seq 增量→见新收尾帧自然收尾 · keepalive comment 不占 seq · 上限 `LG_RAG_REPLAY_FOLLOW_MAX_SECONDS` 默认 900s 到点自然结束零伪造帧 · 在飞/在写窗不返 409；freeze 仍 `lg-rag-sse-v1` 零新 `event_type`。
| **web 交付** | 部分回复 +「继续回复」CTA（**须另开 web task · D3**）；断网/刷新读 History / replay 补后半段；`terminal_status`：`running`/`completed`/`error`/`disconnected`/`waiting_approval` 机读。 |
| **联调项** | 中途断连 → 等 worker settle → DB 普通 `done`（或 `error{worker_failed}`）→ replay 200 含后半段 · 重复 `seq` 不重复渲染 |
| **通过标准** | §11 T4 段 · 模拟 DevTools offline |
| **常见坑** | 前端重复 append 同一 `answer` · 未存 `run_id`/`seq` / `cursor` |

---

### 10.4 T5 · Token 流（终答 delta）

> **跨仓就绪闸（web T4 CLOSE 后必查）**：[`WAVE_READINESS_lg_rag_sse_v0.md`](./WAVE_READINESS_lg_rag_sse_v0.md) §1（从 T4 → 能否开 T5）。

| 维度 | 内容 |
|---|---|
| **前置** | T2 节点进度已稳定 · 建议 web T4 cursor/replay 已可用（见 WAVE_READINESS） |
| **api 提供（2026-08-31 已实现 · T5.1 2026-09-01）** | `answer` 多帧 delta：aggregator 与 router `direct_answer` 的终答 LLM 经 `BaseProvider.complete_stream` + contextvar token sink（`app/ops/lg_rag/answer_stream.py`）逐 chunk 发 `{"delta": "<chunk>"}` 多帧（按 `seq` 有序）；节点 updates 到后发终帧 `{"content": <full>, "final": true}`（32_000 截断沿用 · T2 兼容）。全部帧共享单调 `seq`（单 emit 循环），delta 与 `node.progress`/`subtask.progress` 不串台；delta/终帧照常落盘 `ops_lg_rag_run_events`（**T5.1**：persist **后台 task**，不阻塞 SSE yield），`POST /lg-rag/replay` 逐帧重放含 delta、形状同 live。流式不支持/异常 → 降级整段 answer（T2 行为）+ 日志；basic 占位空 answer 帧不变。freeze 仍 **`lg-rag-sse-v1`**，**不**新增 `event_type`。 |
| **web 交付** | Chat 区 **正确追加 `delta`、终帧 `content` 全量替换**（T5 协议义务）。打字机观感的跨端 SoT 在 **SSE 到达时间线**（T5.1），不把前端定时器假打字机当契约 |
| **联调项** | 增量拼接无乱码 · `done` 后停止追加 · 与 `node.progress` 并存不串台 · **T5.1**：终答阶段时间线非 burst（§11 T5.1） |
| **通过标准** | §11 T5 段 + **T5.1 段** |
| **常见坑** | T2 整段与 T5 delta 混用未分支；把「有很多 answer 帧」当成解析失败而忽略 burst 时间线（§10.4.1） |

#### 10.4.1 T5.1 · 终答 delta 实时投递（pacing / anti-buffer）· 2026-09-01

> **性质**：契约增量（**投递时效**）；不改 freeze、不新增 `event_type`、不改 `delta` / `content` / `final` 键语义。  
> **本波**：docs-only 落盘应然；缺口修复 **另 task**（建议 slug `lg-rag-sse-delta-realtime`，可 api-only 先合）。**不**授权本文件读者改 `app/**`。

##### 背景 / 动机

联调（2026-09-01 · Chat `POST /api/ops/lg-rag/stream` · `mode=supervisor`）：live EventStream 已发出多帧 `event_type=answer`（payload 含 `delta`，`seq` 单调），但 UI 观感仍「一次性出全文」。supervisor 路径常有长时间 `node.progress` / `subtask.progress`（UI「处理中…」）；终答 LLM 开始后，`answer` delta 常在短时间窗口内密集到达（**burst**）——客户端即使按 T5 正确追加，肉眼仍像整段蹦出。

产品裁定（维护者）：跨端通用方案 = **传输层真流式**（api 侧 delta 按生成节奏吐出 + 禁代理/框架缓冲）。**禁止**把「前端假打字机缓冲」写成契约 SoT 或默认交付。联调中偶发的业务错误（如 RAG DB 事务 aborted）与投递时效 **正交**，不扩本条 scope。

##### 00 定夺（钉死 · 维护者可后改）

| 项 | 钉死 |
|---|---|
| **SoT** | 打字机观感的跨端 SoT = **SSE 上 delta 的到达时间线**。web / iOS 正确追加即可；**不**把前端定时器缓冲当协议要求 |
| **吐出时效** | 终答 LLM 每产生可转发的 chunk，应经现有 token sink → emit → **尽快 yield 到 `StreamingResponse`**。禁止「等 aggregator / `direct_answer` 节点整段完成后再一次性吐出全部 delta」作为**默认路径** |
| **burst 定义（验收用）** | 在「首帧 `answer`+`delta` 至末帧 `answer`（`final` 或最后一枚 delta）」窗口内：若客户端 DevTools EventStream 时间戳显示几乎同一秒内倾泻大量 delta，而 provider 流式本身跨秒，则视为 **投递层异常或缓冲**（须排查），**不是**「客户端解析失败」的默认结论 |
| **降级** | provider 不支持流式 / 流式异常 → 仍允许整段 `content`（T2 行为）；须日志可观测。**不得**静默把已生成的多 chunk 攒成单帧 `content` 却仍声称 T5 流式成功 |
| **代理 / 部署** | 反代/网关须对 SSE 禁用响应缓冲（见下节检查清单）。指针：workspace `deploy/nginx/ops-desk.conf` 的 `location /api/` 已含 `proxy_buffering off` / `proxy_cache off`（须核实现网仍生效） |
| **框架层** | FastAPI / Starlette `StreamingResponse` 路径上，业务 yield 的 SSE 帧 **不得**被应用层故意 batch 到阈值下限。**默认：不人为攒批**。若实现合并小 chunk，须明示策略、可测上限，并仍周期性 flush |
| **freeze** | 沿用 `lg-rag-sse-v1`；不新 freeze；不新 `event_type` |
| **与 progress 关系** | `node.progress` / `subtask.progress` 长时间占主导是 supervisor **常态**。「进度阶段无 answer」≠「delta 投递失败」。打字机 / burst **只评估终答阶段**（首枚 delta 起） |
| **非目标（红线）** | 不把 web 假打字机缓冲写成 api 契约；不把 token 化扩展到 progress 帧（另波）；不改 replay 协议形状；不借机改 `thread_id` / `cursor` 语义 |
| **实现波次** | 本小节 = SPEC only。缺口修复另 task（建议 `lg-rag-sse-delta-realtime` / 分支 `task/lg-rag-sse-delta-realtime`）；可 api-only 先合 |

##### 框架层与攒批

- **默认建议：不人为攒批**。sink 收到可转发 chunk 即 emit 一帧 `answer`+`delta`。  
- 若未来为减帧而合并：须在本小节回写「最大攒批字节 / 最大攒批时长」，且 **仍须周期性 flush**（建议上限：≤50ms 或 ≤32 字节，以先到为准——实现 task 可微调数字，但不得改成「等节点结束」）。  
- replay（`POST /lg-rag/replay`）按已落盘顺序紧循环重放，**不**模拟 live pacing（形状不变；时间线以落盘 `ts_ms` / `seq` 为准）。

##### 代理 / 部署 · SSE 禁用缓冲检查清单

路径：`POST /api/ops/lg-rag/stream` 与 `POST /api/ops/lg-rag/replay`（均为 `text/event-stream`）。

| # | 检查项 | 通过口径 |
|---|---|---|
| 1 | api 响应头 | live/replay 已设 `Cache-Control: no-cache` · `X-Accel-Buffering: no`（现网 `router.py` 已有；实现波不得删） |
| 2 | Nginx（或等价反代） | `location` 覆盖上述路径：`proxy_buffering off` · `proxy_cache off` · 长读超时（现模板 `proxy_read_timeout 3600s`） |
| 3 | gzip / 压缩 | **禁止**对 `text/event-stream` 做会攒缓冲的 gzip（现模板 `gzip_types` 未含该 MIME；加类型前须评估） |
| 4 | HTTP/2、CDN、WAF | 若中间层有「最小块 / 响应缓冲」，对本路径关闭或 bypass |
| 5 | 本地 Vite dev proxy | `ops-desk-web/vite.config.ts` 的 `/api` 代理可能缓冲 SSE；联调 burst 须同时排除 dev proxy（直连 api 端口对照） |
| 6 | 应用层 | 无「攒满 N 帧再 write」的默认逻辑（见上节） |

真值指针（仓外 nginx 模板，本仓不复制正文）：`ops-desk-workspace/deploy/nginx/ops-desk.conf`（`location /api/`）。本仓部署叙述：`docs/tasks/done/task_deploy_prod.md`（SSE `proxy_buffering off`）。

##### 常见坑

- 把「EventStream 有很多 `answer` 帧」误判为前端解析错误，而忽略 **burst 时间线**  
- 只测短 query / router 路径，漏测 supervisor 长进度 + 终答  
- Vite dev proxy / nginx / CDN 缓冲导致「码已 yield、浏览器同秒收到」  
- 为「减少帧数」在服务端攒 delta，破坏跨端打字机 SoT  
- 用前端 `setTimeout` 假打字机掩盖投递问题 → iOS / 其他客户端仍差，且与 replay 时间线不一致  

##### 实现候选触点（指针 · 本波不改码）

| 触点 | 为何相关 |
|---|---|
| `app/ops/lg_rag/answer_stream.py` | token sink：chunk → emit |
| `app/ops/lg_rag/sse_stream.py` | sink → `pending_frames` → 主循环 yield；节点边界 `while not pending_frames.empty()` 吐净残留 |
| `app/ops/lg_rag/router.py` | `StreamingResponse` + 禁缓冲头 |
| `app/ops/lg_rag/event_store.py` | `persist_run_event`（每帧独立 `commit`）· T5.1 起由 emit **后台 task** 调用，不阻塞 yield |
| workspace nginx / web Vite proxy | 见上表检查项 2、5 |

##### 应然 vs 实然（T5.1 实现后 · 2026-09-01）

| | 结论 |
|---|---|
| **应然** | 终答阶段每可转发 chunk **尽快**出现在客户端 EventStream；禁止以「节点结束后批量 flush 全部 delta」为默认 |
| **实然（T5.1 已落地）** | `emit` **先返回 SSE 帧并入队**，`persist_run_event` 经 `asyncio.create_task` 后台执行；`done`/`error`/`finally` 前 `_drain_persist` 收尾。竞速 yield 意图保留；HTTP `X-Accel-Buffering: no`；nginx 模板 `/api/` `proxy_buffering off`；**默认不攒批** |
| **仍可能的外因** | Vite dev proxy / CDN 缓冲；provider 本身极快喷完（密帧允许 · 用慢 mock / 卡 persist 测区分） |

##### 思考轮（T5.1 · 摘要）

| 轮 | 结论 |
|---|---|
| R0 | 联调：有 delta 帧仍一次性出全文 → 问题在投递时效 / 缓冲，非缺 event_type |
| R1 | SoT = SSE 到达时间线；禁止前端假打字机入契约 |
| R2 | 不新 freeze / 不新 `answer.delta` event_type；沿用 T5 键 |
| R3 | 打字机只评估终答阶段；progress 长等待是 supervisor 常态 |
| R4 | 验收含 mock 慢 chunk + 反代检查项 + 降级可观测 |
| R5 | SPEC 先落盘；实现另 task；**HG-SPEC-SIGNOFF=approved**（2026-09-01 · 00 代签 · 维护者令「签收」· 20 审查 pass） |

| 项 | 值 |
|---|---|
| early_stop | no |
| residual_risks | persist-before-yield 是否为现网 burst 主因未用慢 mock 实证；Vite/nginx 中间层因环境而异 |

---

### 10.5 T6 · 弃用 chat（api 清扫 · web 已在 T2 切流）

| 维度 | 内容 |
|---|---|
| **前置** | T2–T5 产品可用 · 维护者定下线窗口 |
| **api** | 标记/移除 `/ops/chat/stream`（或 410）· 文档 · 图谱 |
| **api 实现（2026-08-31 · T6 已落地）** | `POST /api/ops/chat/stream` → **410 Gone**：JSON body `{"error": "chat_stream_deprecated", "migrate_to": "/api/ops/lg-rag/stream", "message": <人读迁移说明>}` + `Deprecation: true` + `Link: </api/ops/lg-rag/stream>; rel="successor-version"`；保留 `Depends(get_current_user)`（未登录仍 401，匿名探针不见迁移指针）。**不删 chat 代码/图/表**；保留端点 `GET /chat/models` · `GET /chat/sessions/latest` · WS `/chat/ws`（demo · 未鉴权）行为不变。task `lg-rag-deprecate-chat-stream` |
| **web** | 删 `useOpsChatSse` 死代码 · 移除 chat stream API 常量 · 更新 README |
| **联调项** | 全站无 chat stream 请求 · 监控无 404 洪流 |
| **通过标准** | §11 T6 段 · iOS 若仍用 chat 须另仓 task |

---

### 10.6 Idle 超时 + SSE comment keepalive（2026-09-07）

> **性质**：契约增量（**超时语义 + 保活**）；不改 freeze、不新增 `event_type`、不改 data JSON 键。  
> **动机**：supervisor 合法总时长常 >5min；旧 web 墙钟 300s 误杀。单节点（`rag_subtask` / `tool_exec`）在 `astream(updates)` 边界内可静默数分钟，仅改 idle 仍会被杀 → 须服务端 keepalive。

| 维度 | 钉死 |
|---|---|
| **客户端超时** | **idle**：默认 **120s** 无**字节**则 `kind=timeout`；任意 `reader.read()` 有数据即重置（含 SSE comment）；**不设**整轮墙钟上限 |
| **服务端 keepalive** | 等待下一图 update（及竞速 drain delta）期间，每 **30s** yield SSE 注释行 `: keepalive\n\n` |
| **禁止** | 用 `node.progress` / `subtask.progress` / `answer` 冒充心跳；keepalive **不**落盘 `ops_lg_rag_run_events`、**不**占 `seq` |
| **freeze** | 仍 **`lg-rag-sse-v1`**（comment 不进 data JSON 契约） |
| **web UI** | `subtask.progress` 单独区块展示；`node.progress` 为编排进度（实现在 web 仓） |
| **非范围** | invoke 页 axios 非流式墙钟；Nginx（已 3600s）；节点内 token 级 subagent 日志 / 新 `node.start` |
| **实现** | api：`sse_stream.py`；web：`useLgRagSse` idle + Chat 分区；task `lg-rag-sse-idle-keepalive` |

**联调项**

- [ ] 总时长 >5min、间隔 <120s 有业务帧或 keepalive → **不** timeout  
- [ ] 故意停写且无 keepalive → ≈120s `kind=timeout`；T4 续看仍可用  
- [ ] DevTools：可见 `: keepalive` 注释行；Network 事件列表无假 progress  
- [ ] Chat：`subtask.progress` 仅在「子任务过程」；`node.progress` 仅在「编排进度」

---

### 10.7 Subtask 中途可见（running + step 里程碑 + 可读 message · 2026-09-07 / 2026-09-08）

> **性质**：契约增量（**子任务过程时效**）；不改 freeze、**不**新增 `event_type`。  
> **动机**：`astream(updates)` 仅在节点结束后才发 `subtask.progress`；`rag_subtask` 内 router / evidence 可静默数分钟，UI 只见「处理中…」。  
> **MVP（2026-09-07）**：进入 `rag_subtask` / `info_extract` / `tool_exec` 时 **立即** 发一帧 `subtask.progress`（`status=running`）；节点结束后的既有完成帧补 `status=done`。  
> **增补（2026-09-08 · `lg-rag-sse-subtask-steps`）**：`rag_subtask` 内推送 `status=step` 里程碑——router 子图节点边界 + evidence `retrieve`/`grade`/`answer` 起止（`detail.phase` = `start`|`done`）；`rag_subtask` 改 `astream_router_agent`；evidence 经 `step_hook` ContextVar（**不**造 `lc_evidence_chain→lg_rag` 反向边）。另：provider `_stream_openai_compatible` **禁止**成功路径 `aread()` 整包缓冲，保证终答 delta 真流式。  
> **增补（2026-09-08 · `lg-rag-sse-subtask-message`）**：running / step / done 帧均带**可选 `message`**（中文短句）——api 侧 `subtask_message.py` **确定性模板**由 `step`+`detail`（及 running/done 上下文轻量键）生成；纯同步、不调 LLM、不塞 CoT / evidence 全文；统一截断 `SUBTASK_MESSAGE_MAX_LEN = 200`；未知 step / 缺 detail 走兜底短句（含 step 名），禁空串；生成异常打日志降级、帧仍发。**旧客户端忽略未知键即可，无需升级**。
> **仍非本波**：子任务内 token 流；新 `event_type=node.start`；web 假打字机。

| 维度 | 钉死 |
|---|---|
| **event_type** | 仍 **`subtask.progress`**（与完成摘要同类型） |
| **payload（running）** | 至少：`status: "running"` · `subtask_id`（或 `id`）· `type`（rag/extract/tool）· 可选 `input` 截断预览 · `agent_role` 顶层仍为节点名 |
| **payload（step）** | `status: "step"` · `subtask_id` · `type` · `step`（如 `router`/`rag`/`retrieve`/`grade`/`answer`）· 可选 `detail`（截断；evidence 步含 `phase`） |
| **payload（done）** | 节点 updates 映射的既有摘要键 + `status: "done"`（可选但推荐） |
| **payload（message）** | 三类帧均可选 `message: string`（UTF-8 · ≤200 字截断）；running 含 type/input 摘要一句；step 由 step+detail 模板映射（retrieve/grade/rewrite/answer 等，未知 step 兜底含 step 名）；done 基于 `subtask_result` 轻量键一句结果摘要；**旧客户端忽略未知键** |
| **投递机制** | 对齐 T5：contextvar **progress sink**（节点内 `await sink(...)` → SSE 主循环竞速 yield）；evidence 步经 **step_hook** 转 emit；**禁止**等节点返回才发 running/step |
| **落盘 / seq** | running / step 帧 **落盘**（与业务帧同 seq 单调）；replay 可重放 |
| **freeze** | 仍 **`lg-rag-sse-v1`** |
| **web** | 「子任务过程」收到 `status=running` 立即上屏；`status=step` 按时间线追加（同 `subtask_id`）；`done` 更新/替换该行 |
| **实现 task** | api `lg-rag-sse-subtask-live`（MVP）· `lg-rag-sse-subtask-steps`（step+aread）；web `web-lg-rag-sse-subtask-live` |

**联调项**

- [ ] 慢 `rag_subtask`：节点未结束前 EventStream 已有 `subtask.progress` + `status=running`  
- [ ] 长等待中可见 ≥1 帧 `status=step`（retrieve/grade 或 router 节点），不只 keepalive  
- [ ] 完成后同 id 有 `status=done`（或完成摘要帧）；thinking/subtasks 分区不串台  
- [ ] 过程区可见中文短句：running / step / done 帧 `message` 非空可直接 `append` 上屏（web 可覆盖展示；旧客户端忽略未知键不报错）  
- [ ] 终答 delta `ts_ms` 跨度拉开（非同 ms 倾泻）  
- [ ] T5 delta / T5.1 / keepalive / idle 不回归  

---

## 11. 跨仓发版与人工 checklist（维护者 · 2026-08-31）

> **执行副本（勾选用）**：[`ops-desk-web/docs/checklists/CHECKLIST_lg_rag_sse_joint_release_v1.md`](../../../ops-desk-web/docs/checklists/CHECKLIST_lg_rag_sse_joint_release_v1.md)

### 11.1 PR 与 merge 纪律

| 仓 | 分支（建议） | PR | merge |
|---|---|---|---|
| `ops-desk-api` | `task/lg-rag-sse-stream-updates` | 开 PR → **勿 auto-merge** | checklist 全勾 + 联调通过后与 web **同日** |
| `ops-desk-web` | `task/web-lg-rag-sse-t2` | 开 PR → **勿 auto-merge** | 依赖 api 可联调（分支或 master） |

### 11.2 发版顺序（联调通过后）

1. 维护者签 checklist（§11.3 摘要或 web 完整版）  
2. merge **api** PR → 部署 api（或 staging 已验证则 prod）  
3. merge **web** PR → 部署 web  
4. 生产冒烟：登录 → Chat 发问 → 网络面板 **仅** `/ops/lg-rag/stream` · 见进度与终答  
5. 记录 invoke CLOSE · task 归档  

### 11.3 Checklist 摘要（真值在 web 文件）

**T2 联调（发版闸门）**

- [ ] api `/stream` 200 + SSE 帧序正确  
- [ ] web Chat **不再**请求 `/ops/chat/stream`  
- [ ] `node.progress` / `subtask.progress` / `answer` / `done` UI 可见  
- [ ] 401/422/500 表现符合 task failure_paths  
- [ ] 维护者签「联调通过」  

**T5 / T5.1 联调（投递时效 · 2026-09-01）**

> 打字机只评估 **终答阶段**。supervisor 长 `node.progress` / `subtask.progress` 无 answer ≠ delta 失败。  
> freeze 仍 `lg-rag-sse-v1`；不新增 `event_type`。

- [ ] live：`complete_stream` 可用时，EventStream 在终答阶段出现 **多帧** `answer`+`delta`，且时间戳跨越可感知间隔（非仅 `done` 前同一瞬间倾泻）。若 provider 本身极快，允许密；但须证明非「节点结束后批量 flush」（对照项：mock 慢 chunk）  
- [ ] 人为制造慢 chunk（测试 / mock provider）时，客户端在 **节点未结束前** 即可开始见到 delta（不必等 `final`）  
- [ ] 降级路径：仅整段 `content`，日志有明确降级信号（不得静默攒多 chunk 为单帧却声称 T5 流式成功）  
- [ ] replay：含 `delta` 的已落盘帧仍按序可重放（形状不变；replay 不模拟 live pacing）  
- [ ] 部署检查：反向代理对 `/api/ops/lg-rag/stream`（及 replay）SSE 禁用缓冲的检查项已文档化（§10.4.1 清单；现网 nginx / Vite 已核）  

**Idle / keepalive（§10.6 · 2026-09-07）**

- [ ] client **idle 120s**（有字节重置），非整轮墙钟 300s  
- [ ] 长节点静默期 EventStream 可见 `: keepalive`；超时文案为「无响应」  
- [ ] Chat 子任务过程与编排进度分区可见  

**T3–T6**：见 web checklist 对应节（后续发版，不阻塞 T2 首次联合发版 unless 维护者另定）。T5.1 与 T6 **正交**。§10.6 与 T5.1 **正交**。

### 11.4 修订

| 日期 | 说明 |
|---|---|
| 2026-08-31 | 初版：分阶段联调注意事项 + 跨仓发版纪律 + checklist 指针 |
| 2026-08-31 | §10.5 回写 T6 api 实现句：`/chat/stream` → 410（迁移指针 + Deprecation 头）· 保留 models/sessions.latest/WS · 不删 chat 代码（task `lg-rag-deprecate-chat-stream`） |
| 2026-09-01 | §11.3 增 **T5.1** 勾选：终答 delta 时间线 / mock 慢 chunk / 降级可观测 / replay 形状 / 反代禁用缓冲 |
| 2026-09-07 | §10.6 idle 120s + comment keepalive；§10.2/§11.3 去掉墙钟 ≥300s 表述 |
| 2026-09-08 | §10.7 增补可选 `message`（确定性模板 · ≤200 字 · 旧客户端忽略未知键；task `lg-rag-sse-subtask-message`） |
