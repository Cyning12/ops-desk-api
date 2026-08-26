# PROMPT · 30 · capability-gateway-p2

`````text
你是 30。只实现 capability-gateway-p2。
工作目录 /Users/cyning/Desktop/Ops-desk/ops-desk-api；分支 task/capability-gateway。勿 push/commit。

GATE_VERIFY + verify --task docs/tasks/active/task_capability_gateway_p2.md
落盘 invoke_20260826_30_40_capability-gateway-p2.md

范围：MCP/sandbox/cli 各 1 mock 探针 adapter；默认不进生产 defaults 启用；短文档；单测。可选包装 app/tools/run_code 但默认关闭。

硬约束：无真外网 CI；不改 chat/graph；不做 skill；无 Agently。

40：pytest+ruff。报告 00。简体中文。
`````
