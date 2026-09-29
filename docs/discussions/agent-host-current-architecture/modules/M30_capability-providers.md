# M30 · 本域能力统一接入

> **大纲编号**：#30 · **层**：能力提供方  
> **当前状态**：**已落地**（机制在主线/可开关）  
> **上游目标图**：[`../../2026-09-23_agent-host-full-framework-outline_v0.md`](../../2026-09-23_agent-host-full-framework-outline_v0.md) §2/§3  
> **总览**：[`../00_overview_current_vs_target_v1_zh.md`](../00_overview_current_vs_target_v1_zh.md)

---

## 1. 一句话

统一经 gateway invoke；tenant 谓词；MCP 默认关。

## 2. 模块内架构

```mermaid
flowchart LR
  ID[capability_id] --> GW[gateway.ainvoke]
  GW --> LF[local_fn]
  GW --> LK[issue/PR lookup]
  GW --> HC[harness_cli]
  GW --> MK[mock/probe]
```

## 3. 代码 / 文档落点

**包路径**：`local_fn / lookup / harness.* / task_writer / mock / skill stub`

- lookups.py
- harness_cli.py
- task_writer.py
- skill_stub.py

## 4. 与相邻模块的边

- 见总览依赖图；本模块在目标图中的位置为大纲 **#30**。
- 图谱真值：`docs/_tech_graph/l1/01_modules.md`（物理 module_id 可能合并多个大纲号）。

## 5. 相对目标的残余缺口

远程注册中心实现（v2.0）

## 6. 默认开关 / 安全默认（若适用）

- 多数治理增强：**默认 off / 观测**，enforce 需显式打开（承 Host v1.0 纪律）。
- 详 env 见各 task / `.env.example` / V1-E env 盘点文档。

---

*生成：2026-09-24 · 对照大纲 v0.2（2026-09-23）判定已刷新为 **v1.0 后（2026-09-24）**。*
