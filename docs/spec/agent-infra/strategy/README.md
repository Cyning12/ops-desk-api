# Strategy · 域夹（L1）

> **track**：`agent-infra` / strategy  
> **规划轨**：[`../03_strategy_and_intent_plan_v0.md`](../03_strategy_and_intent_plan_v0.md)  
> **上游 Host**：[`../02_agent_host_plan_v0.md`](../02_agent_host_plan_v0.md)（H1–H5 CLOSE）  
> **实现落点（建议）**：`app/ops/strategy/`（00 定夺）；消费侧 `app/ops/lg_rag/multi/`

---

## 本夹文件

| 文件 | 说明 |
|---|---|
| [`ROADMAP_strategy_builder_v0.md`](./ROADMAP_strategy_builder_v0.md) | Strategy Builder · allowlist · Critic 再赋能 · manifest |

上级：[`../03_strategy_and_intent_plan_v0.md`](../03_strategy_and_intent_plan_v0.md) · [`../00_architecture_and_boundaries.md`](../00_architecture_and_boundaries.md)

---

## 一句话

**Strategy Builder** 按意图裁本轮可见能力写入 state；**Work Planner（supervisor）** 只在赋能集内拆 plan；**Policy** 仍为 Host 硬闸；结果不达标先同 catalog 再试，能力缺口才 rebind。
