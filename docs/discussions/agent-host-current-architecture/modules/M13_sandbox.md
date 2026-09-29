# M13 · 沙箱隔离

> **大纲编号**：#13 · **层**：控制面  
> **当前状态**：**不适用**（域或阶段）  
> **上游目标图**：[`../../2026-09-23_agent-host-full-framework-outline_v0.md`](../../2026-09-23_agent-host-full-framework-outline_v0.md) §2/§3  
> **总览**：[`../00_overview_current_vs_target_v1_zh.md`](../00_overview_current_vs_target_v1_zh.md)

---

## 1. 一句话

单进程用 Policy 阻断替代沙箱；无 microVM。触发条件=不可信代码或跨进程。

## 2. 模块内架构

```mermaid
flowchart LR
  KIND[sandbox/cli kind] --> POL[Policy 默认 blocked]
```

## 3. 代码 / 文档落点

**包路径**：`Policy sandbox/cli 默认 blocked`

- policy.py 词表
- 无独立 sandbox 运行时

## 4. 与相邻模块的边

- 见总览依赖图；本模块在目标图中的位置为大纲 **#13**。
- 图谱真值：`docs/_tech_graph/l1/01_modules.md`（物理 module_id 可能合并多个大纲号）。

## 5. 相对目标的残余缺口

microVM + 网络默认拒绝（v2.0 触发）

## 6. 默认开关 / 安全默认（若适用）

- 多数治理增强：**默认 off / 观测**，enforce 需显式打开（承 Host v1.0 纪律）。
- 详 env 见各 task / `.env.example` / V1-E env 盘点文档。

---

*生成：2026-09-24 · 对照大纲 v0.2（2026-09-23）判定已刷新为 **v1.0 后（2026-09-24）**。*
