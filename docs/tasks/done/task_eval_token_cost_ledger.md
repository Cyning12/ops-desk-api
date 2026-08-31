# Task：Eval E5 · Token / 费用账本（价表 + 导出）

> **状态**：completed（2026-08-29 · PR [#96](https://github.com/Cyning12/ops-desk-api/pull/96) **MERGED** · 2026-08-31 归档补登）  
> **类型**：测评 / Cost harness  
> **上游**：`docs/spec/agent-infra/04_eval_and_observability_plan_v0.md` §2.5 · `eval/ROADMAP` E5-a/b/c  
> **前置**：E4 [#95](https://github.com/Cyning12/ops-desk-api/pull/95) MERGED  
> **分支**：`task/eval-token-cost-ledger`  
> **帽子**：00 起草；30 已交付价表 + 导出。  
> **无关**：热路径 LLM 估费；完整计费中台。

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `eval-token-cost-ledger` |
| **git_branch** | `task/eval-token-cost-ledger` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **graph_change_layer** | `none` |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,00,30` |
| **orchestration** | Eval 轨 E5 收官 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | — | 2026-08-29 · 00 代签 |
| HG-AUDIT-R1 | approved | 30 | 2026-08-29 · 00 代签 |
| HG-GRAPH-MODULES | approved | — | 不新增一级模块 |

---

## CLOSE

| 项 | 值 |
|---|---|
| PR | [#96](https://github.com/Cyning12/ops-desk-api/pull/96) MERGED · 2026-08-29 |
| 交付 | `evals/agent/cost/` · `GUIDE_token_cost_ledger_v0.md` · pytest cost |
| 归档 | 2026-08-31 · 补登（合入后 active 未迁 done） |

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-29 | 00 起草；30 落地；PR #96 |
| 2026-08-31 | **归档补登** → `docs/tasks/done/`（随 lg-rag SSE PR 同带） |
