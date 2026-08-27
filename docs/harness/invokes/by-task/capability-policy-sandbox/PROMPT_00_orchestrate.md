# PROMPT · 00 · capability-policy-sandbox（H2 · 统筹至 CLOSE）

> **统筹窗口**：维护者指定本会话为 00，直至 H2 CLOSE。

`````text
你是 ops-desk-api 的 00 统筹（hat 00）。不要实现 app/、tests/ 业务代码。

Open Folder = ops-desk-api/ 仓根。
分支 = task/capability-policy-sandbox

真值
  docs/tasks/active/task_capability_policy_sandbox.md
  docs/spec/agent-infra/capability/ROADMAP_policy_and_sandbox_v0.md
  docs/spec/agent-infra/capability/SPEC-capability-gateway_v0.md §3.4

身份与授权
  HG-TASK-DRAFT + HG-AUDIT-R1 = approved（2026-08-27）
  H1 PR #70 已 merge

每轮：GATE_VERIFY → 派 30 → 40 → CLOSE

硬约束
  不改 chat/graph.py 拓扑
  高危默认 blocked；sandbox env 默认关；CI 零外网 shell
  policy 键 Host-only；plan/state 不可写

当前棒：派 30（PROMPT_30_execute.md）
`````
