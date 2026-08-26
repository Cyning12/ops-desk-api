# PROMPT · 30(+40) · cap-portable-core

> 00 派发用。复制区给子 agent。

## 复制区

`````text
你是 ops-desk-api 的 30（可含 40）。只实现 task cap-portable-core（Capability 可迁移内核 U1+U2）。

Open Folder：ops-desk-api 仓根。
分支：task/cap-portable-core（已含最新 master / PR #65）。勿擅自 push；未授权勿开新 PR。

首动作（零 diff）：
1. 输出 GATE_VERIFY 表（读 task 人工闸表真值；见 docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md）
2. npx dsh-coding-kit verify --target . --task docs/tasks/active/task_cap_portable_core.md
任一 blocks 30 的闸 pending 或 VERIFY 非 PASS → STOP，不改码。

落盘：docs/harness/invokes/by-task/cap-portable-core/invoke_20260826_30_40_cap-portable-core.md

必读：
- docs/tasks/active/task_cap_portable_core.md（验收 / 非范围 / failure_paths）
- docs/spec/agent-infra/capability/ROADMAP_portable_core_v0.md §U1 §U2
- docs/spec/agent-infra/00_architecture_and_boundaries.md §3 Mode A
- docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md
- docs/standards/CODING_BACKEND_L2_v1_zh.md
- app/ops/capability/**（含 __init__.py · adapters/langchain_tools.py）
- tests/test_capability_gateway.py · tests/test_lg_rag_multi.py
- docs/_tech_graph/l1/01_modules.md（仅 capability 行备注）

实现范围（U1+U2）：
1. 核心包默认路径零 langgraph：gateway/registry/types/adapters/local_fn 及 mcp/sandbox/cli/skill adapter 实现不 import langgraph
2. 将 as_tool_node / as_structured_tools 移出默认导出：建议 app.ops.capability.extras.langchain（或等价）；更新 adapters/__init__.py 与包 __init__.py
3. Mode A 主路径：list_capabilities(filter=…) + invoke；schemas_for_llm 保留纯数据
4. 调整单测 import：extras 仍可测 ToolNode smoke；默认 from app.ops.capability import 不拖 langgraph
5. U2：短文档（ROADMAP 附录或 docs/guides）钉死 filter 推荐 + plan-in-state（不 compile 新图）；list+filter 单测可增强；不强制改 supervisor prompt/算法
6. G-L1 capability 行备注「可迁移内核 · Mode A」；触及图谱则跑 ./scripts/graph-compile.sh（或仓内等价）

硬约束：
- 禁止改 app/ops/chat/graph.py 拓扑
- 禁止引入 Agently 运行时
- 禁止把 Host/SO 校验做成可选 Capability/MCP tool
- 禁止默认动态 StateGraph.compile 新图
- 未知 id → ok=False，不拖垮图
- 单测 mock；不连真 LLM / 真外网 MCP
- 勿混入其他 active task
- 若破坏性默认导出需要升 SPEC v1 → 停问 00/维护者，勿擅自升版

40 自检：
- pytest tests/test_capability_gateway.py tests/test_lg_rag_multi.py
- ruff check 触及路径
- rg -n 'langgraph' app/ops/capability 仅 extras（或零）
- app/ops/chat/graph.py 零 diff
- verify PASS
报告给 00。简体中文。维护者未说则不要 push。
`````
