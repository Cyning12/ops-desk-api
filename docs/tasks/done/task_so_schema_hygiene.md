# Task：Structured Output · 域 schema 卫生（schema hygiene）

> **状态**：completed（PR [#67](https://github.com/Cyning12/ops-desk-api/pull/67) MERGED · 2026-08-26 关账）  
> **类型**：refactor / agent-infra（升级轨波次 2）  
> **上游 ROADMAP**：`docs/spec/agent-infra/structured-output/ROADMAP_kernel_hygiene_v0.md` §H1  
> **总轨**：`agent-infra-upgrade`  
> **分支**：`task/so-schema-hygiene`  
> **前置**：`cap-portable-core` PR [#66](https://github.com/Cyning12/ops-desk-api/pull/66) MERGED  
> **无关**：勿与 `ops-sync-sender-migration` / `rag-answer-mixed-evidence` / `retrieval-longquery-analysis` 混改。

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `so-schema-hygiene` |
| **git_branch** | `task/so-schema-hygiene` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | `tests/test_structured_output_*.py` + `tests/test_lg_rag_structured_output_p2.py`（及既有 lg_rag multi 触及路径）全绿；mock only；不连真 LLM |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1` |
| **graph_delta** | `docs/_tech_graph/l1/01_modules.md`（可选备注） |
| **graph_delta_note** | 仅备注 SO 内核与 lg_rag schemas 边界；**不**新增一级模块 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 本波不晋升 WikiTrack；纯包边界搬家 |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,30` |
| **invoke_retention_profile** | `default` |
| **freeze_id** | 无 |
| **orchestration** | 总轨波次 2；完成后开 `cap-mcp-real` |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | 2026-08-26 00 代签 · 维护者授权全程自动推进 |
| HG-AUDIT-R1 | approved | 30 | 2026-08-26 00 代签；`docs/harness/reviews/task_so_schema_hygiene_audit_R1_20260826.md` |
| HG-GRAPH-MODULES | approved | 30 | 仅备注；不增一级 |

> **HG-SPEC-SIGNOFF**：现行 SO v0 已签；本 task 为 ROADMAP 卫生项，不重签 v0。

---

## 背景与目标

`app/ops/structured_output/schemas/` 现承载 lg_rag 域模型（`RouteDecision` / `SubtasksPlan` / `SubtaskItem` / `ExtractResult`），导致「带走 SO 内核 = 带走 RAG schema」。按 ROADMAP §H1 迁出至 `app/ops/lg_rag/schemas/`，SO 包只留通用管道。

---

## 范围 / 非范围

**范围（H1）**：

1. 新建 `app/ops/lg_rag/schemas/`，迁入上述四个模型（文件可对应 route/subtasks/extract）
2. `lg_rag/nodes.py` · `lg_rag/multi/nodes.py` 改 import
3. `structured_output.schemas`：短期 re-export（deprecated）或删除；包顶 `__all__` **不含**业务 schema
4. 更新单测 import；既有 SO / lg_rag structured 测试绿
5. 可选：G-L1 / flow 备注一句「域 schema 在 lg_rag」

**非范围**：

- 改 `parse_only` / `acomplete_structured` 管道语义
- 波次 4：节点改 `acomplete_structured`
- 把校验做成可选 Capability/MCP tool（**禁止**）
- 改 `app/ops/chat/graph.py`
- 引入 instructor / Agently
- 升 SPEC `_v1`

---

## 验收标准

- [x] 业务 schema 位于 `app/ops/lg_rag/schemas/`（或 ROADMAP 允许的等价域路径）
- [x] SO 包公开表面不含业务 schema（或仅 deprecated re-export 且文档标明）
- [x] lg_rag 节点 import 指向新路径
- [x] `pytest`：`test_structured_output_*` + `test_lg_rag_structured_output_p2`（及回归 multi）绿
- [x] ruff 触及路径绿；`chat/graph.py` 零 diff
- [x] 无 Agently；无真 LLM

---

## failure_paths

| 触发 | 行为 | 可重试 |
|---|---|---|
| 循环 import（lg_rag ↔ schemas） | 调整模块边界 / 延迟 import；不把 schema 留回 SO 内核 | Y |
| 漏改 import 导致测试红 | 全仓 rg 旧路径并修 | Y |
| 误改管道语义 / 校验变 tool | 打回 | N |
| 误改 chat/graph | 打回 | N |

---

## 依赖

- `docs/spec/agent-infra/structured-output/ROADMAP_kernel_hygiene_v0.md` §H1
- `docs/spec/agent-infra/00_architecture_and_boundaries.md` §5
- `docs/standards/CODING_BACKEND_L2_v1_zh.md`
- `docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`

---

## 给执行帽（30）必读

本 task · ROADMAP §H1 · FRAGMENT_30 · CODING_BACKEND_L2 · `app/ops/structured_output/schemas/**` · `app/ops/lg_rag/**/nodes.py` · 相关 tests

**硬约束**：只搬家 + 改 import；不改管道语义；禁止校验变可选 tool；不改 chat/graph。

---

## 思考轮

### 思考轮控制

| 字段 | 值 |
|---|---|
| **actual_last_round** | R4 |
| **early_stop** | yes |
| **early_stop_reason** | 搬家边界清晰；循环 import 为主要残风险，验收已覆盖 |
| **residual_risks** | schemas 原注释称防循环 import——迁到 lg_rag/schemas 后须验证无环；短期 re-export 删期 |

### R0
H1 仅搬家，不碰管道。

### R1
目标路径 `app/ops/lg_rag/schemas/`。

### R2
允许短期 re-export，但 `__all__` 不得冒充内核 API。

### R3
不改 chat/graph；不引入 Agently。

### R4
循环 import 用单测/import 冒烟验证；必要时拆 types-only 模块。

### R5
（提前停 · 未开）

---

### 自检结论

> pending · 30 完成后由 00 机械回填

---

## 修订记录

| 日期 | 说明 |
|---|---|
| 2026-08-26 | 10 起草 H1；00 代签三闸；总轨自动推进授权 |


### KPI

Task_KPI%: 100

## CLOSE

| 项 | 内容 |
|---|---|
| 日期 | 2026-08-26 |
| PR | [#67](https://github.com/Cyning12/ops-desk-api/pull/67) MERGED |
| 定稿 | 域 schema → lg_rag/schemas；SO deprecate re-export |
| 归档 | docs/tasks/done/task_so_schema_hygiene.md |
| 下一棒 | cap-mcp-real |
