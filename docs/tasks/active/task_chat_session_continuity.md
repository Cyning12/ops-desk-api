# Task：Agent Host H3 · Chat Session 连续性

> **状态**：active（draft · **阻塞**：H2 CLOSE 推荐）  
> **类型**：feature / agent-host-plan · H3  
> **上游规划**：`docs/spec/agent-infra/02_agent_host_plan_v0.md`  
> **ROADMAP**：`docs/spec/agent-infra/session/ROADMAP_chat_continuity_v0.md`  
> **分支**：`task/chat-session-continuity`  
> **协调**：与 `task_rag_answer_mixed_evidence` · `task_retrieval_longquery_analysis` 范围勿混

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `chat-session-continuity` |
| **git_branch** | `task/chat-session-continuity` |
| **test_strategy** | `required` |
| **test_strategy_note** | 消息持久化 API/单测；窗口压缩纯函数；SSE cursor mock；不改 graph 拓扑 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1`（若触 chat flow 备注） |
| **graph_delta_note** | 可选 `10_flow_chat` 备注 Session 连续性；**不**改 chat graph 节点拓扑 |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,30` |
| **orchestration** | agent-host-plan 第三棒 = H3 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | pending | 22-R1 | |
| HG-AUDIT-R1 | pending | 30 | |
| HG-GRAPH-MODULES | approved | 30 | 仅备注/POINTER |

---

## 背景与目标

补齐 **SessionContinuity**：消息持久化、窗口压缩、SSE 游标/replay 契约；过长上下文由编排触发 RAG（非 session 内核）。

---

## 范围 / 非范围

**范围**：

- H3-a：消息历史持久化 + 加载进 graph 输入
- H3-b：窗口策略（如前 N 轮全量，超出分组摘要 · 可配置）
- H3-c：SSE event seq/cursor + replay 契约（设计 + mock 流测）
- H3-d：与 `OpsSessionChat` / latest session API 对齐

**非范围**：

- 改 `app/ops/chat/graph.py` 拓扑  
- lg_rag checkpointer 与 chat 强合并  
- 完整长期记忆产品

---

## 验收标准

- [ ] 消息可持久化并按 session 加载
- [ ] 压缩策略单测（参数化 N 轮 / 分组）
- [ ] SSE replay 契约文档 + mock 测试
- [ ] 现有 `/sessions/latest` 不破坏
- [ ] ruff / pytest 绿

---

## failure_paths

| 触发 | 行为 |
|---|---|
| session 不存在 | 创建或 404（对齐现 API） |
| 压缩失败 | 降级截断或拒载（task 内钉死） |

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-27 | 00 拆 task |
