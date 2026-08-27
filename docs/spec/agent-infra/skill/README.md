# Skill · 域夹（L1）

> **track**：`agent-infra` / skill  
> **规划轨**：[`../02_agent_host_plan_v0.md`](../02_agent_host_plan_v0.md) 波次 **H5**（**CLOSE**）  
> **下游消费**：[`../03_strategy_and_intent_plan_v0.md`](../03_strategy_and_intent_plan_v0.md)（Skill match 可作为 Strategy Builder 输入）  
> **划界 GUIDE**：[`GUIDE_capability-gateway-p3-skill-boundary_v0.md`](../../../guides/GUIDE_capability-gateway-p3-skill-boundary_v0.md)

---

## 本夹文件

| 文件 | 说明 |
|---|---|
| [`ROADMAP_skill_registry_v0.md`](./ROADMAP_skill_registry_v0.md) | H5：元数据 + NL 匹配 + provide（**done**） |

**两层 Skill**：`docs/skills`（人读） vs `kind=skill`（运行时 provide/invoke）。  
**非** Strategy Builder：match → provide 是注入；本轮可见集裁剪见 strategy 域。
