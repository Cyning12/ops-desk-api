# M19 · 结果反馈（执行面）

> **大纲编号**：#19 · **层**：执行面  
> **当前状态**：**已落地**（机制在主线/可开关）  
> **上游目标图**：[`../../2026-09-23_agent-host-full-framework-outline_v0.md`](../../2026-09-23_agent-host-full-framework-outline_v0.md) §2/§3  
> **总览**：[`../00_overview_current_vs_target_v1_zh.md`](../00_overview_current_vs_target_v1_zh.md)

---

## 1. 一句话

综合 LLM + answer delta/终帧；流式降级整段。

## 2. 模块内架构

```mermaid
flowchart LR
  JOIN[工人结果] --> AGG[aggregator]
  AGG --> ANS[answer_stream token sink]
  ANS --> SSE[SSE delta/final]
```

## 3. 代码 / 文档落点

**包路径**：`aggregator + answer_stream`

- answer_stream.py
- sse_stream.py
- progress_stream.py

## 4. 与相邻模块的边

- 见总览依赖图；本模块在目标图中的位置为大纲 **#19**。
- 图谱真值：`docs/_tech_graph/l1/01_modules.md`（物理 module_id 可能合并多个大纲号）。

## 5. 相对目标的残余缺口

模板化小 LLM 档可选

## 6. 默认开关 / 安全默认（若适用）

- 多数治理增强：**默认 off / 观测**，enforce 需显式打开（承 Host v1.0 纪律）。
- 详 env 见各 task / `.env.example` / V1-E env 盘点文档。

---

*生成：2026-09-24 · 对照大纲 v0.2（2026-09-23）判定已刷新为 **v1.0 后（2026-09-24）**。*
