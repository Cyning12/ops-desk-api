# M22 · 降级与容错

> **大纲编号**：#22 · **层**：LLM工厂  
> **当前状态**：**已落地**（机制在主线/可开关）  
> **上游目标图**：[`../../2026-09-23_agent-host-full-framework-outline_v0.md`](../../2026-09-23_agent-host-full-framework-outline_v0.md) §2/§3  
> **总览**：[`../00_overview_current_vs_target_v1_zh.md`](../00_overview_current_vs_target_v1_zh.md)

---

## 1. 一句话

同档重试+熔断；V1-C 跨档声明式降级链 + degraded 标记铁律。

## 2. 模块内架构

```mermaid
flowchart TD
  FAIL[调用失败/预算耗尽] --> CH[resolve_fallback_chain]
  CH --> SM[小模型档]
  SM --> RULE[rule: 档]
  RULE --> END[ok=False+degraded]
```

## 3. 代码 / 文档落点

**包路径**：`retry + circuit + TASK_TIER_FALLBACKS + capability fallback`

- llm/retry.py · circuit.py
- TASK_TIER_FALLBACKS
- capability/fallback.py

## 4. 与相邻模块的边

- 见总览依赖图；本模块在目标图中的位置为大纲 **#22**。
- 图谱真值：`docs/_tech_graph/l1/01_modules.md`（物理 module_id 可能合并多个大纲号）。

## 5. 相对目标的残余缺口

规则引擎 DSL（非范围）

## 6. 默认开关 / 安全默认（若适用）

- 多数治理增强：**默认 off / 观测**，enforce 需显式打开（承 Host v1.0 纪律）。
- 详 env 见各 task / `.env.example` / V1-E env 盘点文档。

---

*生成：2026-09-24 · 对照大纲 v0.2（2026-09-23）判定已刷新为 **v1.0 后（2026-09-24）**。*
