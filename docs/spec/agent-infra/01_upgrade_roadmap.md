# Agent Infra · 升级总表（L0）

> **层级**：L0 升级路线（跨域）  
> **状态**：`active`（规划真值 · **不**授权 30）  
> **来源**：2026-08-26 架构讨论 + 后续「可迁移 Capability / SO 抽离顺序」会话结论  
> **配套**：[`00_architecture_and_boundaries.md`](./00_architecture_and_boundaries.md) · 各域 `ROADMAP_*`

---

## 1. 原则

1. **先硬化可迁移面，再扩协议**：Capability Mode A 内核去 LangGraph 依赖优先于真 MCP。  
2. **SO 大管道已完成**：下一波仅卫生项（域 schema 抽离），不抢主波次。  
3. **ROADMAP → task → 闸 → 30**：本表与域 ROADMAP 均不直接授权改码。  
4. **静态图 + 动态 plan** 保持；不做默认动态构图。

---

## 2. 推荐顺序（钉死）

| 序 | 波次 ID | 域 | 内容摘要 | 详规 |
|---|---|---|---|---|
| **1** | `cap-portable-core` | capability | 内核去 LG；`langchain_tools`/`ToolNode` 移出默认导出；钉死 `list`/`invoke` 给 planner | [`capability/ROADMAP_portable_core_v0.md`](./capability/ROADMAP_portable_core_v0.md) |
| **2** | `so-schema-hygiene` | structured-output | 域 schema 迁出 `structured_output` 包（如 `lg_rag/schemas`）；管道只留通用 API | [`structured-output/ROADMAP_kernel_hygiene_v0.md`](./structured-output/ROADMAP_kernel_hygiene_v0.md) |
| **3** | `cap-mcp-real` | capability | 真 MCP client adapter（替换/并行 mock 探针）；进程内 invoke 契约不变 | 同 portable ROADMAP §后续 |
| **4** | `so-complete-adopt`（可选） | structured-output | 选定节点改用 `acomplete_structured`（纠偏）；默认仍不强制 | 同 hygiene ROADMAP §后续 |
| **—** | 明确暂缓 | — | 动态 StateGraph compile；模型可选「校验 tool」；默认改 `chat/graph` | — |

**穿插规则**：波次 2 可与波次 1 **同 PR 穿插**（半日级）或紧随其后；不得早于波次 1 开大 SO 重构。

---

## 3. 与已落地 P0–P3 的关系

| 域 | v0 P0–P3 | 本升级表 |
|---|---|---|
| Capability | Registry · local_fn · schemas_for_llm · 可选 ToolNode 桥 · mock MCP/sandbox/cli · skill stub | **之上的可迁移硬化与真 MCP** |
| Structured Output | parse_only · acomplete · lg_rag 接入 · ensure/validate/no_retry · 并存 DESIGN | **之上的包边界卫生与可选纠偏接入** |

现行契约条文仍以各域 `SPEC-*_v0.md` 为准；本表只排**下一里程碑**。

---

## 4. 开 task 时最小字段建议

- `graph_change_layer`：多为 `G-L1`（模块备注 / flow POINTER）；纯搬家可说明 n/a 但仍过 compile 若触图谱  
- `review_hat`：默认 `20`  
- 验收：引用对应 ROADMAP 波次验收表  
- **无关**：勿与 `ops-sync-sender-migration` / RAG 检索 task 混改

---

## 5. 修订记录

| 日期 | 说明 |
|---|---|
| 2026-08-26 | 初版：Capability 可迁移优先 → SO schema 卫生 → MCP → 可选 acomplete 接入 |
