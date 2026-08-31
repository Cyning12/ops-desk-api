# ROADMAP：Session · lg-rag 连续性（继承 H3 · 非 chat 兼容）

> **层级**：L2 路线（session 域 · 传输主线配套）  
> **状态**：`active`（随 [`../05_lg_rag_transport_and_session_plan_v0.md`](../05_lg_rag_transport_and_session_plan_v0.md) · L0 `HG-SPEC-SIGNOFF` **approved** · 2026-08-30）  
> **上游**：L0 `05` · 思想继承 [`ROADMAP_chat_continuity_v0.md`](./ROADMAP_chat_continuity_v0.md)（H3 · **归档参考**）  
> **不授权 30**

---

## 1. 目标

为 **`lg_rag` 主线**补齐 SessionContinuity：

- thread / session 与产品会话对齐  
- 消息（或等价 checkpoint）持久化与窗口压缩  
- SSE `seq` / cursor 与断线 replay（或 run-resume）  

过长上下文仍由**编排触发 RAG**，非 session 内核职责。

### 与 H3 的关系

| 项 | H3（chat） | 本 ROADMAP |
|---|---|---|
| 思想 | 持久化 · 压缩 · cursor/replay | **继承** |
| 接入面 | `app/ops/chat/` · chat SSE | **`lg_rag` + 新 SSE** |
| 兼容 chat | 是（当时目标） | **否** · 不要求事件/API 兼容 |
| 实现复用 | — | 可参考 `compress_window` / replay 测试思路；**允许重写**，不强制搬模块 |

### 非目标

- 保证 `/chat/stream` 行为不变或双写兼容  
- lg_rag checkpointer 与 chat 表结构强合并（可后续统一，非本路强制）  
- 完整长期记忆产品  
- Token 流协议细节（属 L0 T5）

---

## 2. 交付项（规划级 · 对应 L0 T3/T4）

| ID | 内容 | 对应 L0 | 验收方向 |
|---|---|---|---|
| L-a | `thread_id` / session 产品模型与加载策略 | T3 | API + 单测 |
| L-b | 窗口策略（前 N 轮全量 · 超出摘要；参数可配）迁到 lg-rag 输入装配 | T3 | 纯函数单测 |
| L-c | SSE seq/cursor；断线 replay 或 resume 契约 | T4 | 设计 + mock 流测 |
| L-d | 与现有 ops session API 对齐或**新** session 面（不强制兼容 chat latest） | T3 | 文档冻结 |
| L-e | **G-L2**：本波若改/增 `10_flow_lg_rag` `implementedBy`，同步 `by_path_lg_rag` / `by_symbol_lg_rag`（见 L0 `05` §9） | T3+ | indexes ⊆ 双向一致 |

**依赖**：L0 T0/T1 签收；实现上建议 T2（有流）后再做满 T4。  
**L2 义务**：继承 [`../05_lg_rag_transport_and_session_plan_v0.md`](../05_lg_rag_transport_and_session_plan_v0.md) §9——本系列不豁免「只改 session 不碰 indexes」。

---

## 3. 建议 task（签收后由 00 拆）

- 不在本文件直接授权；建议 slug 例：`lg-rag-session-continuity`、`lg-rag-sse-resume`  
- Obs-I/O **不**落本域 task（见 L0 §3）

---

## 4. 修订记录

| 日期 | 说明 |
|---|---|
| 2026-08-30 | 初版：继承 H3 思想；明确非 chat 兼容；挂 L0 `05` |
| 2026-08-30 | 随 L0 `05` **签收** → `active` |
| 2026-08-31 | 挂钩 L0 `05` §9：Session 波次亦须维护 lg_rag G-L2 indexes |
