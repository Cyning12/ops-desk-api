# ROADMAP：Structured Output · 内核卫生（kernel hygiene）v0

> **层级**：L2 升级路线（structured-output 域）  
> **状态**：`stable`（**H1 DONE** · PR #67；H2 默认跳过）  
> **上游**：[`../01_upgrade_roadmap.md`](../01_upgrade_roadmap.md) 波次 `so-schema-hygiene`（**后于** capability portable，可穿插）  
> **现行契约**：[`SPEC-structured-output-gateway_v0.md`](./SPEC-structured-output-gateway_v0.md)  
> **架构边界**：[`../00_architecture_and_boundaries.md`](../00_architecture_and_boundaries.md) §5

---

## 1. 目标

保持 `parse_only` / `acomplete_structured` 管道为**与业务域无关的内核**；把 lg_rag 专用 Pydantic 模型迁出本包，降低「带走 SO = 带走 RAG 路由 schema」的耦合。

### 非目标（本 ROADMAP 主波）

- 强制 lg_rag 全面改用 `acomplete_structured`（可选后置）  
- 改 evaluate / grader 质量语义  
- 把校验注册为 Capability/MCP 可选 tool（**禁止**）  
- 引入 instructor / Agently 运行时

---

## 2. 波次拆分

### H1 · 域 schema 搬家（总表波次 2 · 卫生优先）

| 项 | 要求 |
|---|---|
| 迁出 | `RouteDecision` / `SubtasksPlan` / `SubtaskItem` / `ExtractResult` → 建议 `app/ops/lg_rag/schemas/`（或 `app/ops/domain_schemas/lg_rag/`） |
| 内核保留 | `extract` / `repair` / `parse` / `complete` / `ParseOutcome` / `StructuredFailure` |
| 调用方 | `lg_rag` nodes 改 import；`structured_output.schemas` 可留短期 re-export 再删 |
| 验收 | 既有 `test_structured_output_*` + `test_lg_rag_structured_output_p2` 绿；包公开 `__all__` 不含业务 schema（或标明 deprecated re-export） |

### H2 · 可选：节点改用 `acomplete_structured`（总表波次 4 · 后置）

| 项 | 要求 |
|---|---|
| 动机 | 需要 Host 预算纠偏时，合并「complete + 校验」避免节点手写双重路径 |
| 约束 | 延迟敏感路径可继续 `parse_only`；纠偏 LLM 经 `llm_ctx`，非「上一 node 对象」 |
| 验收 | 选定 1 个节点试点 + mock 单测；fallback / metadata 语义不回归 |

### H3 · 明确不做

- 模型自选是否校验  
- SO 与 Capability 合并成单一 Gateway  
- 默认改 `chat/graph`

---

## 3. 耦合诊断（升级依据）

| 层 | 耦合度 | 动作 |
|---|---|---|
| extract / repair / parse / complete | 低（pydantic + llm.factory） | 保留 |
| `schemas/*` | 高（lg_rag 域） | **H1 迁出** |
| lg_rag 节点 fallback | 中（业务语义） | 留在节点，不进内核 |

---

## 4. 修订记录

| 日期 | 说明 |
|---|---|
| 2026-08-26 | 初版：schema 抽离优先；acomplete 接入后置；禁止校验变可选 tool |
| 2026-08-26 | **H1 落地**：域 schema → `app/ops/lg_rag/schemas/`（PR #67）；H2 跳过 |
