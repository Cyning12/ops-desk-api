# Task：Harness 升级 2.20→2.21（api）· wiki_delta RUNBOOK + FEEDBACK 复检

> **状态**：active  
> **类型**：基础设施（过程轨 upgrade + wiki_delta 扫迁 + 产品 FEEDBACK）  
> **关联**：npm `@cyning/harness@2.21.0` · 吸收 web+ops 2.20 FEEDBACK · PR #23  
> **合入**：走 PR（禁直推 master）

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `upgrade-harness-2-20-runbook-feedback` |
| **git_branch** | `task/upgrade-harness-2-20-runbook-feedback` |
| **graph_change_layer** | `none` |
| **graph_delta** | `none` |
| **graph_delta_note** | 仅过程轨 / 文档 / FEEDBACK；不改业务图谱 |
| **wiki_delta** | `none` |
| **wiki_delta_note** | 本轮不改 coding_wiki 正文；FEEDBACK/CI/task 属过程轨 |
| **review_hat** | `20` |
| **thinking_profile** | `shortest` |
| **invoke_retention_profile** | `minimal` |
| **required_invoke_hats** | `30` |
| **experience_capture** | `recommended` |
| **test_strategy** | `recommended` |
| **test_strategy_note** | `upgrade --yes`；`check`；`lint-wiki-delta`；`--strict`；§0b 复检；gitignore local.json |
| **code_quality_bar** | `not_applicable` |
| **orchestration** | 2.20 dogfood FEEDBACK → 产品 2.21 回填 → 本仓吸收复检 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| **HG-GRAPH-MODULES** | approved | **30** | 00 代签：仅过程轨；不改 `docs/_tech_graph/` |
| HG-TASK-DRAFT | approved | 22-R1 | 维护者：升 2.20 + FEEDBACK；续升 2.21 吸收复检 |
| **HG-AUDIT-R1** | approved | **30** | 00 代签：无业务 API；禁改产品仓源码 / 禁 publish |

---

## 背景与目标

产品仓已发版 **2.21.0**（吸收 web F-220-\* + ops U\*）。本 task 先 dogfood 2.20 写 FEEDBACK，再按 §0b 升 2.21 复检落地。

**完成态**：

- [x] manifest → `2.20.0` → **`2.21.0`**
- [x] `lint-wiki-delta` 默认 PASS；`--strict` PASS
- [x] 挂 / 钉 `lint-wiki-delta.yml`（`@2.21.0` · `package-manager-cache: false`）
- [x] 吸收：gitignore `local.json`；overlay §1.2 恢复
- [x] FEEDBACK（2.20）+ 复检证据（2.21）+ PR #23

**不做**：改 ops-desk-web；改 cyning-harness 产品源码；npm publish；默认 `--allow-wiki-gap`；直推 master

---

## 失败路径

| 触发 | 行为 | 可重试 |
|---|---|---|
| lint-wiki-delta missing>0 | 按决策树补 n/a\|none\|path + note | 是 |
| --strict 报 note/path | 补 note 或修正 path；写入 FEEDBACK | 是 |
| upgrade 冲 overlay | diff 后恢复 AGENTS/FRAGMENT（§1.2） | 是 |

---

## 验收标准

- [x] manifest `2.21.0` · `check` 对齐
- [x] 默认 `lint-wiki-delta` 绿 · `--strict` 绿
- [x] 两仓 FEEDBACK 吸收矩阵写入复检证据
- [x] FEEDBACK / 复检路径 + PR URL

---

### 自检结论（执行者）

| 项 | 内容 |
|---|---|
| **日期** | 2026-07-28 |
| **manifest** | `2.21.0`（from `2.20.0`；此前 from `2.19.0`） |
| **lint-wiki-delta** | scanned=25 · missing=0 · PASS |
| **lint-wiki-delta --strict** | scanned=25 · issues=0 · **strict PASS** |
| **wiki export** | schema v1 · nodes=7 · edges=33 · warnings=[] |
| **CI** | `@cyning/harness@2.21.0` · cache false |
| **local.json** | 已 gitignore + 停止跟踪 |
| **FEEDBACK 2.20** | `docs/harness/evidence/FEEDBACK_harness_2_20_0_from_ops_desk_api_20260728.md` |
| **复检 2.21** | `docs/harness/evidence/FEEDBACK_harness_2_21_0_recheck_from_ops_desk_api_20260728.md` |
| **overlay** | 2.21 upgrade 仍冲 AGENTS/FRAGMENT · 已按 §1.2 恢复 |
| **PR** | https://github.com/Cyning12/ops-desk-api/pull/23 |
