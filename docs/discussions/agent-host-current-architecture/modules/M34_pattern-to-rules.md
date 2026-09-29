# M34 · 高频模式→新规则

> **大纲编号**：#34 · **层**：反馈闭环  
> **当前状态**：**部分落地 / 雏形**  
> **上游目标图**：[`../../2026-09-23_agent-host-full-framework-outline_v0.md`](../../2026-09-23_agent-host-full-framework-outline_v0.md) §2/§3  
> **总览**：[`../00_overview_current_vs_target_v1_zh.md`](../00_overview_current_vs_target_v1_zh.md)

---

## 1. 一句话

聚类只产建议；**零自动改** redlines/manifest（守护断言）。

## 2. 模块内架构

```mermaid
flowchart LR
  RPT[suggested_rule] --> HUMAN[人工确认]
  HUMAN -->|是| RED[redlines/manifest]
  HUMAN -->|否| NOP[不生效]
```

## 3. 代码 / 文档落点

**包路径**：`suggested_rule 报告字段 + redlines 人工`

- episode_pattern_mine suggested_rule
- evals redlines

## 4. 与相邻模块的边

- 见总览依赖图；本模块在目标图中的位置为大纲 **#34**。
- 图谱真值：`docs/_tech_graph/l1/01_modules.md`（物理 module_id 可能合并多个大纲号）。

## 5. 相对目标的残余缺口

半自动回写工作流（人机协作台）

## 6. 默认开关 / 安全默认（若适用）

- 多数治理增强：**默认 off / 观测**，enforce 需显式打开（承 Host v1.0 纪律）。
- 详 env 见各 task / `.env.example` / V1-E env 盘点文档。

---

*生成：2026-09-24 · 对照大纲 v0.2（2026-09-23）判定已刷新为 **v1.0 后（2026-09-24）**。*
