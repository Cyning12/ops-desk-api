# PROMPT · 30 · lg-rag-supervisor-capability-catalog（H1）

`````text
你是 ops-desk-api 的 30（可含 40）。只实现 lg-rag-supervisor-capability-catalog（Agent Host H1）。

工作目录：/Users/cyning/Desktop/Ops-desk/ops-desk-api
分支：task/lg-rag-supervisor-capability-catalog。勿 push；未授权勿 commit。

GATE_VERIFY + npx dsh-coding-kit verify --target . --task docs/tasks/active/task_lg_rag_supervisor_capability_catalog.md
落盘 invoke_20260827_30_40_lg-rag-supervisor-capability-catalog.md

必读
  docs/tasks/active/task_lg_rag_supervisor_capability_catalog.md
  docs/spec/agent-infra/orchestration/ROADMAP_supervisor_capability_catalog_v0.md
  app/ops/lg_rag/multi/nodes.py（supervisor_node · _parse_subtasks）
  app/ops/capability/（list_capabilities · CapabilityFilter · defaults）
  docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md
  docs/standards/CODING_BACKEND_L2_v1_zh.md

范围（H1-a–f）
  supervisor_node：list_capabilities(filter 含 node_role=supervisor 或等价) → 格式化进 LLM messages
  _parse_subtasks 后：type=tool 时 tool ∈ 可见 id；非法 → 整 plan fallback 单 rag
  注册 ≥1 非 mock 低危 local_fn（只读/无副作用）
  span：capability_catalog_count；非法 tool metadata
  单测 + G-L1 lg_rag 备注 + graph-compile

硬约束
  不改 chat/graph.py 拓扑；不实现 Policy(H2)/PromptAssembly(H4)/Skill(H5)
  不引 Agently；不连真外网
  test_lg_rag_multi 不回归

40
  pytest 触及路径 + ruff + chat/graph.py 0 diff + graph-compile
  报告 00（本会话统筹窗）。简体中文。
`````
