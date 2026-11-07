# M14 · 安全策略 · HITL

> **大纲编号**：#14 · **层**：控制面  
> **当前状态**：**部分落地 / 雏形**  
> **上游目标图**：[`../../2026-09-23_agent-host-full-framework-outline_v0.md`](../../2026-09-23_agent-host-full-framework-outline_v0.md) §2/§3  
> **总览**：[`../00_overview_current_vs_target_v1_zh.md`](../00_overview_current_vs_target_v1_zh.md)

---

## 1. 一句话

真 interrupt/resume；双鉴权；V1-A/B 接线。有单档 HITL_REQUIRED + 可撤销字段；缺 PRE_AUTHORIZED/HITL_EXEMPT 三档体系。

## 2. 模块内架构

```mermaid
flowchart TD
  NEED[hitl_required / 签发审批] --> INT[interrupt]
  INT --> DB[(ops_hitl_requests)]
  CB[callback/resume API] --> RES[Command resume]
  RES --> GRAPH[lg_rag 续跑]
```

## 3. 代码 / 文档落点

**包路径**：`app/ops/hitl/** · step_contract · 委派签发 HITL · manifest hitl_required`

- hitl/store|persistence|resume|router
- multi/nodes observe
- sse_stream 挂起帧

## 4. 与相邻模块的边

- 见总览依赖图；本模块在目标图中的位置为大纲 **#14**。
- 图谱真值：`docs/_tech_graph/l1/01_modules.md`（物理 module_id 可能合并多个大纲号）。

## 5. 相对目标的残余缺口

HITL 三档声明式；撤销执行器

## 6. 默认开关 / 安全默认（若适用）

- 多数治理增强：**默认 off / 观测**，enforce 需显式打开（承 Host v1.0 纪律）。
- 详 env 见各 task / `.env.example` / V1-E env 盘点文档。

---

*生成：2026-09-24 · 对照大纲 v0.2（2026-09-23）判定已刷新为 **v1.0 后（2026-09-24）**。*
