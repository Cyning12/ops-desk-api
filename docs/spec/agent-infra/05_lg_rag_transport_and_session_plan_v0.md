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
| **T5** | `token-stream` | aggregator（等）token 级 SSE | 否 |
| **T6** | `deprecate-chat` | 文档/前端切流 · chat 下线窗口 | 否 |

**顺序建议**：T0/T1 签收 →（实现可穿插 Obs-I/O）→ T2 → T3/T4 → T5 → T6。  
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
| `answer` | `aggregator` / `direct_answer` | 最终答案（**T5 已实现**：token delta 多帧 `{"delta": "<chunk>"}` 按 `seq` 有序拼接 + 终帧 `{"content": "<full>", "final": true}`；T2 兼容——旧客户端仅看 `content` 行为不变；流式降级时仅终帧整段） |
| `done` | `system` | 正常结束 |
| `error` | `system` | 失败；`retryable` 布尔 |
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
- 断连仍「尽量跑完」、无 cancel；replay 仅已落盘帧

**T5 冻结补充（2026-08-31）**

- 同 freeze_id：`lg-rag-sse-v1`（`answer` 扩多帧 delta + 终帧 `final` 标记；**不**新增 `event_type`）  
- 客户端规则：见 `delta` 追加、见 `content` **全量替换**、`done` 后停止追加；禁止把 `content` 帧 append 到 delta 结果（§10.4 常见坑）  
- token 归属**仅** aggregator / direct_answer 的终答 LLM（`complete_stream` + contextvar token sink）；流式不可用/异常 → 降级整段（T2 行为）+ 日志；终帧沿用 32_000 截断

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
| **联调项** | ① 登录 cookie ② `run.start` 含 `thread_id`/`mode` ③ 至少一帧 `node.progress`/`subtask.progress` ④ `answer` 整段 ⑤ `done` ⑥ 401→登录 ⑦ 422 表单预检 ⑧ 长问 supervisor 超时（client timeout ≥300s 对齐 invoke 页） |
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
| **api 提供（2026-08-31 已实现）** | live `POST /lg-rag/stream` 每帧可选顶层 `cursor="{run_id}:{seq}"`；事件尽量落盘 `ops_lg_rag_run_events`。**新** `POST /api/ops/lg-rag/replay`：body `{run_id, after_seq}` 或 `{cursor}` → SSE 重放该 run 且 `seq > after_seq`（形状同 live）。须登录；未知/跨用户 `run_id` → **404**；非法 cursor → 422。断连服务端仍「尽量跑完」图（**无** cancel）。落盘失败不阻断已发 SSE；replay 仅已提交帧。freeze 仍 **`lg-rag-sse-v1`**（不强制 `event_type=cursor`）。**不** import chat/session。 |
| **web 交付** | 断网/刷新后恢复策略 UI · 可选「从 cursor 续看」（另开 web task；本波可 api-only 先合） |
| **联调项** | 中途断连后行为符合 api 钉死（T2=跑完不收齐；T4=可 replay） · 重复 `seq` 不重复渲染 |
| **通过标准** | §11 T4 段 · 模拟 DevTools offline |
| **常见坑** | 前端重复 append 同一 `answer` · 未存 `run_id`/`seq` / `cursor` |

---

### 10.4 T5 · Token 流（终答 delta）

> **跨仓就绪闸（web T4 CLOSE 后必查）**：[`WAVE_READINESS_lg_rag_sse_v0.md`](./WAVE_READINESS_lg_rag_sse_v0.md) §1（从 T4 → 能否开 T5）。

| 维度 | 内容 |
|---|---|
| **前置** | T2 节点进度已稳定 · 建议 web T4 cursor/replay 已可用（见 WAVE_READINESS） |
| **api 提供（2026-08-31 已实现）** | `answer` 多帧 delta：aggregator 与 router `direct_answer` 的终答 LLM 经 `BaseProvider.complete_stream` + contextvar token sink（`app/ops/lg_rag/answer_stream.py`）逐 chunk 发 `{"delta": "<chunk>"}` 多帧（按 `seq` 有序）；节点 updates 到后发终帧 `{"content": <full>, "final": true}`（32_000 截断沿用 · T2 兼容）。全部帧共享单调 `seq`（单 emit 循环），delta 与 `node.progress`/`subtask.progress` 不串台；delta/终帧照常落盘 `ops_lg_rag_run_events`，`POST /lg-rag/replay` 逐帧重放含 delta、形状同 live。流式不支持/异常 → 降级整段 answer（T2 行为）+ 日志；basic 占位空 answer 帧不变。freeze 仍 **`lg-rag-sse-v1`**，**不**新增 `event_type`。 |
| **web 交付** | Chat 区打字机 · 与 T2 整段 `answer` 兼容（首帧/增量协议见 T5 freeze） |
| **联调项** | 增量拼接无乱码 · `done` 后停止追加 · 与 `node.progress` 并存不串台 |
| **通过标准** | §11 T5 段 |
| **常见坑** | T2 整段与 T5 delta 混用未分支 |

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

**T3–T6**：见 web checklist 对应节（后续发版，不阻塞 T2 首次联合发版 unless 维护者另定）。

### 11.4 修订

| 日期 | 说明 |
|---|---|
| 2026-08-31 | 初版：分阶段联调注意事项 + 跨仓发版纪律 + checklist 指针 |
| 2026-08-31 | §10.5 回写 T6 api 实现句：`/chat/stream` → 410（迁移指针 + Deprecation 头）· 保留 models/sessions.latest/WS · 不删 chat 代码（task `lg-rag-deprecate-chat-stream`） |
