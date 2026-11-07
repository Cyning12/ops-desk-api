# M33 · 失败案例→失败模式库

> **大纲编号**：#33 · **层**：反馈闭环  
> **当前状态**：**已落地**（机制在主线/可开关）  
> **上游目标图**：[`../../2026-09-23_agent-host-full-framework-outline_v0.md`](../../2026-09-23_agent-host-full-framework-outline_v0.md) §2/§3  
> **总览**：[`../00_overview_current_vs_target_v1_zh.md`](../00_overview_current_vs_target_v1_zh.md)

---

## 1. 一句话

V1-D：failure/partial 入 episode；离线指纹聚类报告。

## 2. 模块内架构

```mermaid
flowchart LR
  FAIL[failure episode] --> MINE[pattern_mine]
  MINE --> YAML[reports/episode_patterns]
```

## 3. 代码 / 文档落点

**包路径**：`ops_memory_episodes + episode_pattern_mine`

- episode_gate/service
- scripts/episode_pattern_mine.py

## 4. 与相邻模块的边

- 见总览依赖图；本模块在目标图中的位置为大纲 **#33**。
- 图谱真值：`docs/_tech_graph/l1/01_modules.md`（物理 module_id 可能合并多个大纲号）。

## 5. 相对目标的残余缺口

实时聚类；跨进程

## 6. 默认开关 / 安全默认（若适用）

- 多数治理增强：**默认 off / 观测**，enforce 需显式打开（承 Host v1.0 纪律）。
- 详 env 见各 task / `.env.example` / V1-E env 盘点文档。

---

*生成：2026-09-24 · 对照大纲 v0.2（2026-09-23）判定已刷新为 **v1.0 后（2026-09-24）**。*
