# Task：hitl-approved-replan-quality（approved 恒 replan + LLM 盲循环 · approved 步骤「自然完成」双重结构性不可达）

> **状态**：draft（10 落稿中 · 2026-10-11）
> **类型**：质量收口（消费回路血统延续 · 功能缺口 · 实证驱动 · T4 CLOSE 钉案② + SPEC §9 序1 立案）
> **依据**：SPEC `docs/spec/hitl-approval-consumption/SPEC-hitl-approval-consumption_v1.md` §9 序1（2026-10-11 维护者令登记 · 维护者令立项）· T4 CLOSE 钉案② `docs/tasks/close/close_hitl_replan_carry_and_persist_guard_20261010.md` §四.2 · 语义边界登记 `docs/acceptance/20261010_hitl-consumption-loop_local_acceptance.md`（分支 `acceptance/20261010-hitl-consumption-loop` · 引用以该分支为准）
> **分支**：`task/hitl-approved-replan-quality`（worktree 专用 · base 待 00 核）

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `hitl-approved-replan-quality` |
| **git_branch** | `task/hitl-approved-replan-quality` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | （待填 · 含 live 实证：approved 后单轮自然完成 done 的可达性） |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | （待填） |
| **graph_delta** | （待填） |
| **graph_delta_note** | （待填） |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 无文档站变更 |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,20,30,40` |
| **invoke_retention_profile** | `default` |
| **experience_capture** | `required` |
| **kpi_aggregator** | `n/a` |
| **orchestration** | 10 落稿 → 20 R1 → 维护者签 → 30（先实证复现再定方案）→ 40（含 live 实证）→ PR+CI 绿 → CLOSE |
| **freeze_id** | 无（预期零新表/零迁移/零新 SSE 事件/零新 payload 键） |

### 人工闸

| 闸 | 状态 | 说明 |
|---|---|---|
| HG-TASK-DRAFT | pending | （00 代录 · 非 10 职责） |
| HG-AUDIT-R1 | pending | （00 代录 · 非 10 职责） |
| HG-GRAPH-MODULES | pending | （00 代录 · 非 10 职责） |
| HG-PILOT-OPSDESK-GLAYER | n/a | 无外部试点面 |

## 背景与目标

### 实证锚点（逐字关键行 · 三源在案）

（待填：SPEC §9 序1 · T4 CLOSE 钉案② · 验收语义边界登记三条）

### 10 初步研判（开放 · 待 30 实证 · 不锁死）

（待填：双重结构性不可达机制链 ① LLM 不知晓保号行/盲循环 ② approved 非空恒 replan · 含锚点漂移校正记录）

### 候选修复方向（开放给 30 实证后定 · 起草不锁死）

（待填：① observe 对 approved/保号行可见性 ② 终态判定放宽 ③ 二者组合 ④ resume.py:131/41-51 语义重审随本 task 顺手收 or 另立）

**目标**：（待填）

## 现状锚点

（待填：锚点表 · 行号逐一实读核真）

## 钉死契约

（待填：无状态恢复纪律 · TB1-TB8/TA 组零回归 · 手动 resume 语义零 diff 等）

## 范围

（待填 F1…Fn）

### 非范围

（待填）

## failure_paths

（待填 FP 表）

## B1 · 旧测影响面

（待填）

## 验收标准

（待填 · 必含 live 实证：approved 后单轮自然完成 done 可达性）

## 依赖

（待填）

## 给执行帽的必读列表

（待填）

## 思考轮控制

（待填 · R0…Rn）

## KPI（00）

（待填 · 00 职责段 · 10 留骨架）

## 经验总结

（CLOSE 时回填）

## 修订

| 日期 | 版本 | 说明 |
|---|---|---|
| 2026-10-11 | v0-skeleton | 10 骨架先行落稿（全节标题+占位 · 增量填充中） |
