# ROADMAP：Orchestration · Supervisor 赋能目录闭环（H1）

> **层级**：L2 路线（orchestration 域 · 波次 H1）  
> **状态**：`done`（H1 CLOSE · 2026-08-27 → [`task_lg_rag_supervisor_capability_catalog.md`](../../../tasks/done/task_lg_rag_supervisor_capability_catalog.md)）  
> **上游**：[`../02_agent_host_plan_v0.md`](../02_agent_host_plan_v0.md)  
> **下游**：[`../03_strategy_and_intent_plan_v0.md`](../03_strategy_and_intent_plan_v0.md)（Strategy Builder 裁可见集；本 H1 为 Work Planner 读目录）  
> **架构边界**：[`../00_architecture_and_boundaries.md`](../00_architecture_and_boundaries.md) §4 / §4.1

---

## 1. 目标

让 **supervisor planner 与 Capability Gateway 形成闭环**：拆 plan 前可见赋能列表；plan 中 `type=tool` 的 `tool` 字段必须来自该列表（或 Host 校验拒绝/降级）。

### 非目标

- 改 supervisor 图拓扑（仍 planner → dispatch ⇄ workers → aggregator）  
- 引入 Skill NL 匹配（H5）  
- 全面改用 `acomplete_structured`  
- 动态 compile 新图  

---

## 2. 交付项

| ID | 内容 | 验收 |
|---|---|---|
| H1-a | `supervisor_node` 调 `list_capabilities(filter=CapabilityFilter(node_role="supervisor", …))` | 单测断言 filter 入参 |
| H1-b | 赋能目录格式化进 system/user（id · description · risk_level 摘要） | mock LLM messages 含目录片段 |
| H1-c | `_parse_subtasks` 后校验：`type=tool` 时 `tool` ∈ 可见 id 集；非法 → 整 plan fallback 单 rag（保留现语义）或单条降级（00 定夺，默认整 plan fallback） | 单测非法 id |
| H1-d | 注册 ≥1 个**非 mock** 低危 `local_fn`（只读/无副作用）供 plan 选用 | defaults 或独立注册模块 |
| H1-e | span metadata：`capability_catalog_count` · 非法 tool 时 `structured_output_fallback` 或专用键 | 与现 tracing 兼容 |
| H1-f | G-L1 `lg_rag` 备注一句「supervisor 读 Capability 目录」+ graph-compile（若触图谱） | compile 绿 |

---

## 3. 建议 task

- **slug**：`lg-rag-supervisor-capability-catalog`  
- **分支**：`task/lg-rag-supervisor-capability-catalog`  
- **test_strategy**：`required` · mock LLM + capability registry  
- **graph_change_layer**：`G-L1`

---

## 4. 修订记录

| 日期 | 说明 |
|---|---|
| 2026-08-27 | 初版 H1 条文 |
| 2026-08-27 | 挂下游 Strategy Builder 轨（03） |
