# PROMPT · 30 · strategy-builder-allowlist（S1）

> **给谁**：新开的 **30**（可含 40）会话或子 agent。  
> **Open Folder**：`ops-desk-api/` 仓根。  
> **分支**：`task/strategy-builder-allowlist`。  
> **报告对象**：本仓 00 统筹窗。

---

## 复制区（整段粘贴）

`````text
你是 ops-desk-api 的 30（可含 40）。只实现 strategy-builder-allowlist（Strategy Builder S1）。

工作目录：以维护者 worktree 为准的 ops-desk-api 仓根
分支：task/strategy-builder-allowlist。勿 push；未授权勿 commit（00 可另令 commit）。

GATE_VERIFY（首输出必填表 · 真值读 task 人工闸表）
  + npx dsh-coding-kit verify --target . --task docs/tasks/active/task_strategy_builder_allowlist.md
落盘 invoke_20260827_30_40_strategy-builder-allowlist.md（by-task/strategy-builder-allowlist/）

必读
  docs/tasks/active/task_strategy_builder_allowlist.md
  docs/spec/agent-infra/03_strategy_and_intent_plan_v0.md
  docs/spec/agent-infra/strategy/ROADMAP_strategy_builder_v0.md
  docs/harness/reviews/task_strategy_builder_allowlist_audit_R1_20260827.md
  app/ops/lg_rag/state.py
  app/ops/lg_rag/multi/nodes.py（supervisor_node · tool id 校验）
  app/ops/lg_rag/multi/graph.py（仅挂 Builder 节点；禁止改 chat/graph.py）
  app/ops/capability/（list_capabilities · CapabilityFilter · policy · defaults）
  docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md
  docs/standards/CODING_BACKEND_L2_v1_zh.md

范围（S1-a–d only）
  S1-a：LgRagState（或等价）allowed_capability_ids（可选 allowed_skill_ids）
  S1-b：Strategy Builder 节点（首版规则/配置，可无 LLM）：写 allowlist ⊆ Registry ∩ Policy 可见；非法 id 剔除 + span
  S1-c：supervisor_node：list_capabilities(filter) ∩ state allowlist
        - supervisor 路径强制经 Builder（不允许 None「仅 filter」兼容）
        - 空 allowlist [] → 禁止 type=tool；整 plan fallback 单 rag
  S1-d：tool id Host 校验相对本轮可见集；非法 → 整 plan fallback 单 rag（继承 H1）
  实现落点建议：app/ops/strategy/ 薄包 + lg_rag 消费；图谱只更新 lg_rag G-L1 备注，不新增一级模块
  单测 + graph-compile + ruff

硬约束
  Mode A：list_capabilities + invoke
  静态图 + 动态 allowlist；禁止每请求 StateGraph.compile 新图
  Builder 不得绕过 Policy；不得由模型随意 register
  不改 app/ops/chat/graph.py 拓扑
  不引 Agently 运行时；不连真外网
  Host 校验不可做成模型可选 Capability/MCP tool
  不实现 S2 Intent / S3 YAML / S4 Critic / Eval
  不混改无关 active task（ops-sync-sender-migration、rag-answer-mixed-evidence、retrieval-longquery-analysis）
  test_lg_rag_multi / H1 语义不回归

40
  pytest 触及路径 + ruff + chat/graph.py 0 diff + ./scripts/graph-compile.sh
  报告 00（本会话统筹窗）。简体中文。勾选 task 验收项；勿伪造测试结果。
`````

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-27 | 初版 S1 allowlist 30 Prompt |
