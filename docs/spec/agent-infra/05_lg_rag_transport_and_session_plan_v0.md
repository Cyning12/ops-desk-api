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
| `answer` | `aggregator` | 最终答案（T2 可整段；T5 可多帧 delta） |
| `done` | `system` | 正常结束 |
| `error` | `system` | 失败；`retryable` 布尔 |
| `cursor`（可选 · T4） | `system` | 供 replay 的游标提示 |

**非范围（T1）**

- 不定 replay 存储 schema（T4）。  
- 不定 WS 双通道（可后置）。

**T2 冻结（2026-08-30）**

- HTTP 路径：`POST /api/ops/lg-rag/stream`  
- freeze_id：`lg-rag-sse-v1`  
- 默认 `mode=supervisor`；`stream_mode=updates`；断连=服务端尽量跑完、无 replay

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