# M12 · 成本控制

> **大纲编号**：#12 · **层**：控制面  
> **当前状态**：**已落地**（机制在主线/可开关）  
> **上游目标图**：[`../../2026-09-23_agent-host-full-framework-outline_v0.md`](../../2026-09-23_agent-host-full-framework-outline_v0.md) §2/§3  
> **总览**：[`../00_overview_current_vs_target_v1_zh.md`](../00_overview_current_vs_target_v1_zh.md)

---

## 1. 一句话

usage 账本 + V1-C 会话/任务预算硬闸（默认 off）+ Cost per Successful Task 口径；耗尽走降级链。

## 2. 模块内架构

```mermaid
flowchart LR
  CALL[LLM call] --> CHK[check_budget]
  CHK -->|enforce 超限| DEG[降级链]
  CALL --> USAGE[ops_llm_usage]
  USAGE --> COST[cost_per_successful_task]
```

## 3. 代码 / 文档落点

**包路径**：`app/llm/usage.py · budget.py · model_catalog 单价`

- llm/budget.py
- llm/usage.py
- MODEL_UNIT_PRICES

## 4. 与相邻模块的边

- 见总览依赖图；本模块在目标图中的位置为大纲 **#12**。
- 图谱真值：`docs/_tech_graph/l1/01_modules.md`（物理 module_id 可能合并多个大纲号）。

## 5. 相对目标的残余缺口

跨租户统筹预算；对账级计费

## 6. 默认开关 / 安全默认（若适用）

- 多数治理增强：**默认 off / 观测**，enforce 需显式打开（承 Host v1.0 纪律）。
- 详 env 见各 task / `.env.example` / V1-E env 盘点文档。

---

*生成：2026-09-24 · 对照大纲 v0.2（2026-09-23）判定已刷新为 **v1.0 后（2026-09-24）**。*
