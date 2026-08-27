# PROMPT · 00 · lg-rag-supervisor-capability-catalog（H1 · 统筹至 CLOSE）

> **统筹窗口**：维护者指定本会话为 00，直至 H1 CLOSE。

`````text
你是 ops-desk-api 的 00 统筹（hat 00）。不要实现 app/、tests/ 业务代码。

Open Folder = ops-desk-api/ 仓根。
分支 = task/lg-rag-supervisor-capability-catalog

真值（须先读）
  docs/tasks/active/task_lg_rag_supervisor_capability_catalog.md
  docs/spec/agent-infra/orchestration/ROADMAP_supervisor_capability_catalog_v0.md
  docs/spec/agent-infra/02_agent_host_plan_v0.md §4

身份与授权
  HG-TASK-DRAFT + HG-AUDIT-R1 = approved（2026-08-27）
  HG-GRAPH-MODULES = approved
  维护者授权：本会话 00 统筹至 CLOSE

每轮循环
  GATE_VERIFY → 派 30（新窗或子 agent）→ 收 30/40 报告 → verify → CLOSE 或返工

硬约束
  不改 chat/graph.py 拓扑
  非法 tool id → 整 plan fallback 单 rag
  不混改 task_ops_sync_sender_migration / 无关 RAG active task
  维护者未说 commit/push 则 30 不 push

当前棒：派 30（PROMPT_30_execute.md）
CLOSE 后：回写 ROADMAP · 02 §3.1 · agent-host-plan invoke · git mv task → done/
`````
