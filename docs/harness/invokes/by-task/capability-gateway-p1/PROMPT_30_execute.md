# PROMPT · 30 · capability-gateway-p1

`````text
你是 ops-desk-api 的 30（可含 40）。只实现 capability-gateway-p1。
工作目录：/Users/cyning/Desktop/Ops-desk/ops-desk-api
分支：task/capability-gateway。勿 push；未授权勿 commit。

GATE_VERIFY + npx dsh-coding-kit verify --target . --task docs/tasks/active/task_capability_gateway_p1.md
落盘 invoke_20260826_30_40_capability-gateway-p1.md

必读：task_p1；SPEC §3.2 schemas_for_llm / §4 P1；app/ops/capability/*；FRAGMENT_30；CODING_BACKEND_L2。

范围：schemas_for_llm(*, filter)；可选 ToolNode/LangChain tool 适配 smoke（不强制挂 multi 主路径）；Filter 最小；单测；注释写清可选。

硬约束：不改 chat/graph.py；不改 multi/graph 拓扑；不做 MCP/skill；无 Agently；无真外网。

40：pytest+ruff+graph.py 0。报告 00。简体中文。
`````
