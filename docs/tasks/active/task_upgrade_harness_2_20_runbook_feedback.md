# Task：Harness 升级至 2.20.0（api）· wiki_delta RUNBOOK + FEEDBACK

> **状态**：active  
> **类型**：基础设施（过程轨 upgrade + wiki_delta 扫迁 + 产品 FEEDBACK）  
> **关联**：npm `@cyning/harness@2.20.0` · `RUNBOOK_upgrade_wiki_delta_v1_zh` · `--strict`  
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
| **test_strategy_note** | `upgrade --yes`；`check`；`lint-wiki-delta` 默认绿；`--strict`；可选挂 CI；FEEDBACK 落盘 |
| **code_quality_bar** | `not_applicable` |
| **orchestration** | 产品 RUNBOOK dogfood → FEEDBACK 回产品仓 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| **HG-GRAPH-MODULES** | approved | **30** | 00 代签：仅过程轨；不改 `docs/_tech_graph/` |
| HG-TASK-DRAFT | approved | 22-R1 | 维护者指令：升 2.20.0 + wiki_delta 扫迁 + FEEDBACK + PR |
| **HG-AUDIT-R1** | approved | **30** | 00 代签：无业务 API；禁改产品仓源码 / 禁 publish |

---

## 背景与目标

产品仓交付 **2.20.0**（`lint-wiki-delta --strict` 关账预检）与升级 RUNBOOK。本仓已钉 **2.19.0** 且启用 WikiTrack；本 task 升到 2.20.0、再扫迁、写 FEEDBACK。

**完成态**：

- [x] manifest → `2.20.0`
- [x] `lint-wiki-delta` 默认 PASS（缺字段补齐）
- [x] `--strict` 结果写入 FEEDBACK（PASS）
- [x] 挂 `lint-wiki-delta.yml`（npx-only · `package-manager-cache: false`）
- [x] FEEDBACK 落盘 + PR

**不做**：改 ops-desk-web；改 cyning-harness 产品源码；npm publish；默认 `--allow-wiki-gap`；直推 master

---

## 失败路径

| 触发 | 行为 | 可重试 |
|---|---|---|
| lint-wiki-delta missing>0 | 按决策树补 n/a\|none\|path + note | 是 |
| --strict 报 note/path | 补 note 或修正 path；写入 FEEDBACK | 是 |
| upgrade 冲 overlay | diff 后恢复 AGENTS/FRAGMENT | 是 |

---

## 验收标准

- [x] manifest `2.20.0` · `check` 对齐
- [x] 默认 `lint-wiki-delta` 绿或 FEEDBACK 列剩余缺口
- [x] FEEDBACK 路径 + PR URL

---

### 自检结论（执行者）

| 项 | 内容 |
|---|---|
| **日期** | 2026-07-28 |
| **manifest** | `2.20.0`（from `2.19.0`） |
| **lint-wiki-delta** | scanned=25 · missing=0 · issues=0 · PASS |
| **lint-wiki-delta --strict** | scanned=25 · missing=0 · issues=0 · **strict PASS** |
| **CI** | 已挂 `.github/workflows/lint-wiki-delta.yml`（硬失败 · 默认 lint；`--strict` 注释保留） |
| **FEEDBACK** | `docs/harness/evidence/FEEDBACK_harness_2_20_0_from_ops_desk_api_20260728.md` |
| **overlay** | AGENTS 定制行被 upgrade 冲掉后已恢复 |
