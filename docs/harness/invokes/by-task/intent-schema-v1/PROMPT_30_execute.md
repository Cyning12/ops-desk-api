# PROMPT · 30 · intent-schema-v1（S2）

> **给谁**：新开的 **30**（可含 40）会话或子 agent。  
> **Open Folder**：`ops-desk-api/` 仓根。  
> **分支**：`task/intent-schema-v1`。

---

## 复制区（整段粘贴）

`````text
你是 ops-desk-api 的 30（可含 40）。只实现 intent-schema-v1（Strategy Builder S2）。

工作目录：以维护者 worktree 为准的 ops-desk-api 仓根
分支：task/intent-schema-v1。勿 push；未授权勿 commit（00 可另令 commit）。

GATE_VERIFY（首输出必填表 · 真值读 task 人工闸表）
  + npx dsh-coding-kit verify --target . --task docs/tasks/active/task_intent_schema_v1.md
落盘 docs/harness/invokes/by-task/intent-schema-v1/invoke_20260827_30_40_intent-schema-v1.md

必读
  docs/tasks/active/task_intent_schema_v1.md
  docs/spec/agent-infra/03_strategy_and_intent_plan_v0.md §5 / §8
  docs/spec/agent-infra/strategy/ROADMAP_strategy_builder_v0.md §6–§7
  docs/harness/reviews/task_intent_schema_v1_audit_R1_20260827.md
  app/ops/lg_rag/state.py
  app/ops/lg_rag/schemas/route.py（对照，勿改 router 语义）
  app/ops/lg_rag/multi/graph.py
  app/ops/strategy/builder.py
  app/ops/structured_output/complete.py（acomplete_structured）
  app/ops/prompts/templates.py（H4）
  docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md
  docs/standards/CODING_BACKEND_L2_v1_zh.md

范围（S2-a–b only）
  S2-a：
    IntentV1（Pydantic · extra=ignore）：domain ops_kb|general|unknown；needs_tool；needs_skill；is_composite；risk_hint low|medium|high；summary
    落 app/ops/lg_rag/schemas/intent.py 并导出
    LgRagState.intent: dict
    intent_node：app/ops/strategy/intent.py；acomplete_structured(max_retries=1)；Prompt 槽 lg_rag.intent.system
    失败：保守 fallback intent（unknown / 全 False / low / summary=""）+ span intent_fallback 与 structured_output_fallback；不拒图
    supervisor 图：START → intent → strategy_builder → supervisor …（静态；禁止 per-request compile）
    Builder 读 state.intent：needs_tool False → 空 allowed_capability_ids；True → 仍 ⊆ Registry∩Policy（S1 求交）；needs_skill 本波 allowed_skill_ids 仍 []；risk_hint 不得绕过 Policy
  S2-b：docs/guides/GUIDE_intent-vs-router-coexistence_v0.md（与 ROADMAP §7 一致即可）
  G-L1 lg_rag 备注 + 10_flow_lg_rag.graph.yaml 增 s_intent 节点/边 + graph-compile
  单测 + ruff

硬约束
  不改 app/ops/chat/graph.py 拓扑
  不改 router 图 / basic 图拓扑（mode=router 的 rag|direct|refuse 保持）
  不引 Agently；不连真外网
  Host 校验不可做成模型可选 tool
  不实现 S3 YAML / S4 Critic / Eval / Skill 引擎
  不混改无关 active task
  S1 allowlist 语义不回归

40
  pytest 触及路径 + ruff + chat/graph.py 0 diff + ./scripts/graph-compile.sh
  报告 00。简体中文。勾选 task 验收项；勿伪造测试结果。
`````

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-27 | 初版 S2 Intent 30 Prompt |
