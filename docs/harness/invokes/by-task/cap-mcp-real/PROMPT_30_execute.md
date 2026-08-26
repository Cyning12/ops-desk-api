# PROMPT · 30(+40) · cap-mcp-real

`````text
你是 ops-desk-api 的 30（可含 40）。只实现 task cap-mcp-real（Capability 真 MCP adapter · ROADMAP U3）。

Open Folder：ops-desk-api 仓根。分支：task/cap-mcp-real。勿 push；可本地 commit。

首动作（零 diff）：
1. GATE_VERIFY（FRAGMENT_30_gate_verify_v1_zh.md）
2. npx dsh-coding-kit verify --target . --task docs/tasks/active/task_cap_mcp_real.md
不通过则 STOP。

落盘：docs/harness/invokes/by-task/cap-mcp-real/invoke_20260826_30_40_cap-mcp-real.md

必读：task_cap_mcp_real.md · ROADMAP_portable_core_v0.md §U3 · SPEC-capability-gateway_v0.md · adapters/mcp.py · probes.py · registry CapabilityAdapter · CODING_BACKEND_L2_v1_zh.md

实现：
1. 新增 McpClientAdapter（可注入 transport/session）；invoke 仍映射 CapabilityResult
2. FakeTransport 单测：成功 tools/call + 失败/异常 → ok=False
3. env 默认关闭（如 OPS_CAPABILITY_MCP_ENABLED）；未启用不注册真 client
4. 保留 MockMcpAdapter + probes；既有 capability 测绿
5. 可选 integration 标记默认 skip
6. 文档/ROADMAP/G-L1 一行「真 MCP · 默认关 · CI 不外网」

硬约束：默认 CI 零外网；不改 chat/graph；不引 Agently；不把 SO 校验做成 MCP tool；优先薄 client+注入，避免强绑重 SDK。

40：pytest tests/test_capability_gateway.py（+ 新测）· ruff · chat/graph.py 零 diff · verify PASS · rg 证明默认路径无真网络调用。
报告 00。简体中文。不要 push。
`````
