# 可复制 Prompt · 30（+40）· structured-output-gateway-p1

`````text
你是 ops-desk-api 的 30 执行帽（可含 40）。只实现 structured-output-gateway-p1。

工作目录：/Users/cyning/Desktop/Ops-desk/ops-desk-api
分支：task/structured-output-gateway（勿 push；未授权勿 commit）

首输出：读 task 闸表 → GATE_VERIFY 表 → npx dsh-coding-kit verify --target . --task docs/tasks/active/task_structured_output_gateway_p1.md
pending → 零 diff 停。落盘 docs/harness/invokes/by-task/structured-output-gateway-p1/invoke_20260826_30_40_structured-output-gateway-p1.md

必读：task_structured_output_gateway_p1.md；SPEC §3.1/§3.2/§4 P1/§6；app/ops/structured_output/parse.py；app/llm/factory.py；FRAGMENT_30；CODING_BACKEND_L2。

范围：complete_structured（建议 async acomplete_structured 对齐 provider.complete）；复用 parse_only；max_retries；OUTPUT CORRECTION 注入；raise_on_failure / StructuredFailure；单测 mock 第1次坏第2次好 + 预算耗尽。

硬约束：Host 权威；完整重生成非半截补丁；不接 P2 节点；不实现 P3 ensure 完整逻辑（参数可预留）；不改 chat/graph.py；无 Capability Gateway；无 Agently；无真 LLM。

40：pytest + ruff + graph.py 零 diff；回填 invoke。完成后报告 00：路径、命令结果、可否关账。简体中文。
`````
