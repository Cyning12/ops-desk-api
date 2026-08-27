# Orchestration · 域夹（L1）

> **track**：`agent-infra` / orchestration  
> **规划轨**：[`../02_agent_host_plan_v0.md`](../02_agent_host_plan_v0.md) 波次 **H1**（**CLOSE**）  
> **下游**：[`../03_strategy_and_intent_plan_v0.md`](../03_strategy_and_intent_plan_v0.md) · [`../strategy/`](../strategy/)（Work Planner 消费 allowlist）  
> **实现落点**：`app/ops/lg_rag/multi/` · `app/ops/lg_rag/graph.py`

---

## 本夹文件

| 文件 | 说明 |
|---|---|
| [`ROADMAP_supervisor_capability_catalog_v0.md`](./ROADMAP_supervisor_capability_catalog_v0.md) | H1：supervisor ↔ Capability 赋能目录闭环（**done**） |

上级：[`../02_agent_host_plan_v0.md`](../02_agent_host_plan_v0.md) · [`../00_architecture_and_boundaries.md`](../00_architecture_and_boundaries.md)

---

## 一句话

静态 supervisor 图不变；**planner 读 `list_capabilities`**，plan 里 tool 字段只许选可见 id，SO 仍 `parse_only` 校验 `SubtasksPlan`。  
下一轨：可见集由 **Strategy Builder** 写入 state，supervisor 变为 **Work Planner**（见 strategy 域）。
