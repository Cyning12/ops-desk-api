# ROADMAP：Session · Chat 连续性（H3）

> **层级**：L2 路线（session 域 · 波次 H3）  
> **状态**：`active`（task → [`task_chat_session_continuity.md`](../../../tasks/active/task_chat_session_continuity.md) · 阻塞 H2 推荐）
> **上游**：[`../02_agent_host_plan_v0.md`](../02_agent_host_plan_v0.md)

---

## 1. 目标

补齐 **SessionContinuity** 产品面：消息持久化、窗口压缩策略、SSE 事件游标/replay 设计；过长上下文由**编排触发 RAG**（非 session 内核）。

### 非目标

- 改 `chat/graph.py` 节点拓扑  
- lg_rag checkpointer 与 chat 强合并（可后续统一 thread 模型）  
- 完整长期记忆产品  

---

## 2. 交付项（规划级 · 00 可拆子 task）

| ID | 内容 | 验收 |
|---|---|---|
| H3-a | 消息历史持久化模型 + 加载进 graph 输入 | API/单测 |
| H3-b | 窗口策略：如前 N 轮全量，超出分组摘要（参数可配置） | 纯函数单测 |
| H3-c | SSE：event seq / cursor；断线 replay 契约草案 | 设计 + mock 流测 |
| H3-d | 与 `OpsSessionChat` 对齐 thread/session id | 不破坏现有 latest session API |

---

## 3. 建议 task

- **slug**：`chat-session-continuity`  
- **依赖**：H1/H2 非硬依赖；与 active RAG task 协调范围  

---

## 4. 修订记录

| 日期 | 说明 |
|---|---|
| 2026-08-27 | 初版 H3 条文 |
