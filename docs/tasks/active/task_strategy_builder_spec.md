# Task：策略轨 + 测评轨 SPEC 落盘（docs-only）

> **状态**：active（2026-08-27 · 文档维护）  
> **类型**：docs / agent-infra 规划  
> **上游**：会话结论 · [`03_strategy_and_intent_plan_v0.md`](../../spec/agent-infra/03_strategy_and_intent_plan_v0.md) · [`04_eval_and_observability_plan_v0.md`](../../spec/agent-infra/04_eval_and_observability_plan_v0.md)  
> **分支**：`task/strategy-builder-allowlist`（S1 预备 · 含 03/04 SPEC 落盘）  
> **范围**：仅 `docs/spec/agent-infra/**` + 本 task；**禁止**业务改码（无 30）

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `strategy-builder-spec` |
| **git_branch** | `task/strategy-builder-allowlist` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `n/a`（纯文档） |
| **code_quality_bar** | `n/a` |
| **graph_change_layer** | `n/a` |
| **wiki_delta** | `n/a` |
| **review_hat** | `20` |
| **required_invoke_hats** | `10`（docs） |
| **freeze_id** | 无 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | pending | — | 维护者确认 SPEC 落盘范围 |
| HG-AUDIT-R1 | n/a | 30 | 本 task **无 30**；实现另开 S1/E1 task |
| HG-GRAPH-MODULES | n/a | — | 不改图谱 |

---

## 目标

1. **策略轨**：H5 后 Intent→Strategy Builder→Work Planner→Critic；YAML 目录；命名边界  
2. **测评轨**：每模块观测/测评点；Langfuse vs LangSmith；混合架构（非完整自建）

---

## 验收标准

- [x] L0：`03_strategy_and_intent_plan_v0.md`
- [x] L1：`strategy/README.md` + `ROADMAP_strategy_builder_v0.md`
- [x] 回写：`README.md` · `00_architecture` §4.1 · `02` 下游指针 · orchestration/skill/capability README
- [x] L0：`04_eval_and_observability_plan_v0.md` + `eval/`（Langfuse/Smith 边界 · 混合架构）
- [x] 回写：`README` · `00` §7.1 · `03` 交叉引用
- [ ] 维护者 S0/E0 签收后拆实现 task

---

## 非范围

- 任何 `app/` 改码  
- 拆 S1–S4 / E1–E4 实现 task 的完整 Harness 派发（签收后另开）

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-27 | 初版 · SPEC 落盘（策略轨） |
| 2026-08-27 | 补测评轨 04 + eval 域 |
