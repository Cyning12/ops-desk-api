# Session · 域夹（L1）

> **track**：`agent-infra` / session  
> **当前主线规划**：[`../05_lg_rag_transport_and_session_plan_v0.md`](../05_lg_rag_transport_and_session_plan_v0.md)（lg-rag SSE · **active · 已签收**）  
> **实现落点（目标）**：`app/ops/lg_rag/` · 传输层 · 可选 `app/ops/session/`  
> **历史落点（H3）**：`app/ops/chat/` · `app/db/`（**归档参考 · 不作为新契约兼容目标**）

---

## 本夹文件

| 文件 | 说明 | 状态 |
|---|---|---|
| [`ROADMAP_lg_rag_session_continuity_v0.md`](./ROADMAP_lg_rag_session_continuity_v0.md) | **主线**：lg-rag 多轮 / 压缩 / SSE 断点（继承 H3 思想） | `active` |
| [`ROADMAP_chat_continuity_v0.md`](./ROADMAP_chat_continuity_v0.md) | H3 Chat 连续性（已落地参考） | **归档参考** |

**边界**：新 Spec **不**以兼容 `chat/graph` / `/chat/stream` 为验收条件；H3 文档保留供复用设计思想与测试套路。  
**G-L2**：见 L0 [`05` §9](../05_lg_rag_transport_and_session_plan_v0.md)；Session 实现波须同步 `l2/indexes/*_lg_rag.yaml`。
