# PROMPT · 30 · capability-gateway-p0

`````text
你是 ops-desk-api 的 30（可含 40）。只实现 capability-gateway-p0。

工作目录：/Users/cyning/Desktop/Ops-desk/ops-desk-api
分支：task/capability-gateway。勿 push；未授权勿 commit。

GATE_VERIFY + npx dsh-coding-kit verify --target . --task docs/tasks/active/task_capability_gateway_p0.md
落盘 invoke_20260826_30_40_capability-gateway-p0.md

必读：task_capability_gateway_p0.md；SPEC-capability-gateway_v0.md §3/§4 P0；app/ops/lg_rag/multi/nodes.py（MOCK_TOOLS/tool_exec）；FRAGMENT_30；CODING_BACKEND_L2。

范围：app/ops/capability/ Registry+local_fn；迁移 MOCK_TOOLS；tool_exec_node 改调 Gateway；未知 id 容错；span metadata；单测；G-L1 lg_rag 备注。

硬约束：不改 chat/graph.py；不实现 P1–P3；不引 Agently；不强制接入 app/tools/run_code；不连真外网。

40：pytest test_lg_rag_multi + 新测；ruff；graph.py 0；graph-compile。报告 00。简体中文。
`````
