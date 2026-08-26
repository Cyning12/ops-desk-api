# PROMPT · 30 · structured-output-gateway-p2

`````text
你是 ops-desk-api 的 30（可含 40）。只实现 structured-output-gateway-p2。

工作目录：/Users/cyning/Desktop/Ops-desk/ops-desk-api
分支：task/structured-output-gateway。勿 push；未授权勿 commit。

首输出：GATE_VERIFY（读 task 闸表）+ npx dsh-coding-kit verify --target . --task docs/tasks/active/task_structured_output_gateway_p2.md
pending → 零 diff 停。落盘 invoke_20260826_30_40_structured-output-gateway-p2.md

必读：task_p2；SPEC §4 P2/§5；app/ops/structured_output/*；app/ops/lg_rag/nodes.py（_parse_route/_classify_route）；app/ops/lg_rag/multi/nodes.py（supervisor/_parse_subtasks/info_extract）；FRAGMENT_30；CODING_BACKEND_L2。

范围：三处接入 Gateway；Pydantic schema；保留 fallback（supervisor→单 rag；router→rag；extract→空结构）；span metadata 加 structured_output_fallback；单测 mock；G-L1 备注。

选型提示：节点已 complete 时可 complete 一次 + parse_only，避免双重 LLM；或 acomplete_structured 且小 max_retries——注释说明。router 历史宽容字符串路径勿无故收紧致误 fallback 暴增。

硬约束：不改 chat/graph.py；不改图拓扑边；无 Capability Gateway；无 Agently；无真 LLM；勿动无关 active / app/tools 草稿。

40：pytest 相关 lg_rag + structured_output；ruff；graph.py 0 diff；graph-compile。报告 00。简体中文。
`````
