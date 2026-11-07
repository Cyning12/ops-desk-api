# M32 · 成功案例→记忆

> **大纲编号**：#32 · **层**：反馈闭环  
> **当前状态**：**部分落地 / 雏形**  
> **上游目标图**：[`../../2026-09-23_agent-host-full-framework-outline_v0.md`](../../2026-09-23_agent-host-full-framework-outline_v0.md) §2/§3  
> **总览**：[`../00_overview_current_vs_target_v1_zh.md`](../00_overview_current_vs_target_v1_zh.md)

---

## 1. 一句话

事实抽取离线；V1-D 成功 episode 可召回「相似经验」。成功「模式」级沉淀仍浅。

## 2. 模块内架构

```mermaid
flowchart LR
  DONE[run 终态] --> EXT[事实抽取]
  DONE --> EP[write_episode success]
  EP --> REC[相似经验召回]
```

## 3. 代码 / 文档落点

**包路径**：`memory extract（事实/偏好）+ episode success 召回`

- memory/extract.py
- episode_service
- continuity

## 4. 与相邻模块的边

- 见总览依赖图；本模块在目标图中的位置为大纲 **#32**。
- 图谱真值：`docs/_tech_graph/l1/01_modules.md`（物理 module_id 可能合并多个大纲号）。

## 5. 相对目标的残余缺口

成功模式级资产化

## 6. 默认开关 / 安全默认（若适用）

- 多数治理增强：**默认 off / 观测**，enforce 需显式打开（承 Host v1.0 纪律）。
- 详 env 见各 task / `.env.example` / V1-E env 盘点文档。

---

*生成：2026-09-24 · 对照大纲 v0.2（2026-09-23）判定已刷新为 **v1.0 后（2026-09-24）**。*
