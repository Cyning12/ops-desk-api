# PROMPT · 30 · critic-rebind（S4）

> **给谁**：新开的 **30**（可含 40）。  
> **Open Folder**：`ops-desk-api/` 仓根。  
> **分支**：`task/critic-rebind`。

---

## 复制区（整段粘贴）

`````text
你是 ops-desk-api 的 30（可含 40）。只实现 critic-rebind（Strategy Builder S4）。

工作目录：以维护者 worktree 为准的 ops-desk-api 仓根
分支：task/critic-rebind。勿 push；未授权勿 commit。

GATE_VERIFY（首输出必填表 · 真值读 task 人工闸表）
  + npx dsh-coding-kit verify --target . --task docs/tasks/active/task_critic_rebind.md
落盘 docs/harness/invokes/by-task/critic-rebind/invoke_20260828_30_40_critic-rebind.md

必读
  docs/tasks/active/task_critic_rebind.md
  docs/spec/agent-infra/03_strategy_and_intent_plan_v0.md §2 / §4
  docs/spec/agent-infra/strategy/ROADMAP_strategy_builder_v0.md §9
  docs/harness/reviews/task_critic_rebind_audit_R1_20260828.md
  app/ops/lg_rag/multi/graph.py
  app/ops/lg_rag/multi/nodes.py（aggregator · route_next_subtask · subtask_results）
  app/ops/lg_rag/state.py
  app/ops/strategy/builder.py
  docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md
  docs/standards/CODING_BACKEND_L2_v1_zh.md

范围（S4-a–c only）
  critic_node：app/ops/strategy/critic.py · 规则 stub（无 LLM 主路径）
  节点 id critic_node（禁止与 state key 同名）
  state：critic_verdict dict；inner_retry_count；rebinding_count
  subtask_results 自定义 reducer：None 清空，否则 append
  图：aggregator → critic_node；条件边
    pass → END
    retry_planner → supervisor（同 allowlist）
    rebind → strategy_builder
    end → END
  预算 MAX_INNER_RETRIES=1 · MAX_REBINDING=1；超预算强制 end
  规则：无 error → pass；error+空 allowlist → rebind；error+非空 → retry_planner；超预算 → end
  回环时覆盖 subtasks=[] 且 subtask_results=None
  span：critic_outcome · inner_retry_count · rebinding_count
  可选 CriticVerdict schema 不必接 LLM
  G-L1 lg_rag 备注 + 10_flow_lg_rag.graph.yaml 增 s_critic + graph-compile
  单测：规则 / 边 / 强制一直 retry 或 rebind 必 END（无死循环）

硬约束
  不改 app/ops/chat/graph.py、router 图、basic 图拓扑
  禁止每请求 compile；禁止无预算 ReAct
  Builder 不得绕过 Policy；rebind 只再跑 Builder，不自动扩权
  不实现 intent→② 回环、LLM Critic、Eval
  不混改无关 active task
  S1–S3 语义不回归

40
  pytest 触及路径 + ruff + chat/graph.py 0 diff + ./scripts/graph-compile.sh
  报告 00。简体中文。勾选 task 验收项；勿伪造测试结果。
`````

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-28 | 初版 S4 30 Prompt |
