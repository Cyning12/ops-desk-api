# Task：capability-mine-endpoint（B1 · 用户态可见能力目录端点 GET /api/ops/capability/mine）

> **状态**：draft（10-task 起草中 · 骨架先行 · 逐节回填中）
> **类型**：新端点（只读观测面 · SPEC tool-catalog-page §2 B1 拆出）
> **依据**：`docs/spec/tool-catalog-page/SPEC-tool-catalog-page_v0.md`（HG-SPEC-SIGNOFF approved 2026-10-11）+ R1 审 `docs/harness/reviews/spec_tool-catalog-page_audit_R1_20261011.md`（PASS-WITH-NITS · N1–N3 本 task 携带回填）
> **分支**：`task/tool-catalog-page`（既有 · 勿切）

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `capability-mine-endpoint` |
| **git_branch** | `task/tool-catalog-page` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | TBD |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1`（预期 · 新 REST 路由行备注义务 · 30 按实判） |
| **graph_delta** | TBD |
| **graph_delta_note** | TBD |
| **wiki_delta** | `n/a` |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,20,30,40` |
| **invoke_retention_profile** | `default` |
| **experience_capture** | `required` |
| **kpi_aggregator** | `n/a` |
| **orchestration** | 10 落稿 → 20 R1 → 维护者签 → 30 → 40 → PR+CI 绿 → CLOSE |
| **freeze_id** | 无（纯 REST 查询面 · 零 SSE 帧改动 · 零 capability 执行语义改动） |

### 人工闸

| 闸 | 状态 | 说明 |
|---|---|---|
| HG-TASK-DRAFT | pending | 10 落稿后维护者签 |
| HG-AUDIT-R1 | pending | 20 R1 落盘后维护者签 |
| HG-GRAPH-MODULES | pending | 随交付按实判签录（新 REST 路由 G-L1 行备注义务） |
| HG-PILOT-OPSDESK-GLAYER | n/a | 无外部试点面 |

## 背景与目标

TBD

## 现状锚点

TBD

## 钉死契约

TBD

## 范围

TBD

### 非范围

TBD

## failure_paths

TBD

## B1 · 旧测影响面

TBD

## 验收标准

TBD

## 依赖

TBD

## 给执行帽的必读列表

TBD

## 思考轮控制

TBD

## 修订

| 日期 | 说明 |
|------|------|
| 2026-10-11 | 10 落稿骨架（全节标题 + TBD · 逐节回填中） |
