# Task：Harness 升级至 2.16.1（api）+ 过程可观测冒烟

> **状态**：completed  
> **类型**：基础设施（过程轨 upgrade）  
> **关联**：npm `@cyning/harness@2.16.1` · timeline / status --check · P1/P2 过程可观测

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `harness-upgrade-2.16.1` |
| **test_strategy** | `recommended` |
| **test_strategy_note** | `upgrade --yes`（不带 `--ide`，避 F1b）；`check` 最新；`status --json` / `timeline --json` / 可选 `status --check` 冒烟；无业务 pytest 义务（有则只报告） |
| **code_quality_bar** | `not_applicable` |
| **orchestration** | 单 task；00 代签双闸（RUNBOOK 基础设施惯例） |
| **git_branch** | `task/harness-upgrade-2.16.1` |
| **graph_change_layer** | `none` |
| **review_hat** | `20` |
| **review_hat_reason** | `""` |
| **thinking_profile** | `shortest` |
| **invoke_retention_profile** | `minimal` |
| **required_invoke_hats** | `30` |
| **experience_capture** | `recommended` |

| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 本仓未启用 WikiTrack |
### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| **HG-GRAPH-MODULES** | approved | **30** | 00 代签：仅过程轨 sync；不改业务模块边界 |
| HG-TASK-DRAFT | approved | 22-R1 | 维护者下发 30 Prompt：钉到 2.16.1 + 过程可观测冒烟 |
| **HG-AUDIT-R1** | approved | **30** | 00 代签：基础设施 upgrade；无业务逻辑 / 无强制 hook / 无 P3b |

---

## 背景与目标

产品 **2.16.1**（含 2.14→2.16 P1/P2：harness timeline · status --check exit 2 · hook/CI 样例可选）。本仓 `manifest=2.14.0`，需 upgrade 并为后续 P3b（Ops Desk 只读消费 JSON）铺路。

**完成态**：

- [x] manifest → `2.16.1`
- [x] `upgrade --yes`（无 `--ide`）一把过
- [x] `harness check` 已是最新
- [x] 冒烟：`status --json` · `timeline --json`（有 task）；可选 `status --check`
- [x] invoke + 自检回填

**不做**：web/ios 升级；业务改码；强制 pre-commit；P3b 看板接线

---

## 失败路径

| 触发 | 行为 | 可重试 |
|---|---|---|
| S5 dirty 挡 upgrade | 先 commit/stash；人判 `--force` | 是 |
| ide 被静默裁成单 cursor | 记录摩擦，不擅自 `--ide` 重跑 | 人判 |
| status/timeline 契约异常 | 记录 stdout；不改产品仓 | 是 |

---

## 验收标准

- [x] manifest 2.16.1 · 仍仅五字段 · preset=`fullstack-node-py`
- [x] check 指向 2.16.1 / 已是最新
- [x] status/timeline 冒烟可用（exit 记录）
- [x] 纪律层 commit（不 push / 不开 PR，除非人明示）

---

### 自检结论（执行者）

| 项 | 内容 |
|---|---|
| **日期** | 2026-07-27 |
| **manifest** | `2.16.1`（from 2.14.0）· 五字段 · ide 三轨未裁 |
| **check** | 已是最新 · exit 0 |
| **status/timeline** | `obs_status.v1` / `obs_timeline.v1` · timeline WARN 无 HGM exit 0 · `--check` 绿路径 exit 0 |
| **ide 是否被裁** | 否（仍 cursor,claude,agents） |
| **摩擦** | upstream sync 冲掉 pre-30 文案与 `l1/01_modules`；已写回 overlay |
| **pytest** | 缺 asyncpg · 仅报告 |
| **下一棒** | 维护者审 diff；可选 PR；不 push（本棒） |
