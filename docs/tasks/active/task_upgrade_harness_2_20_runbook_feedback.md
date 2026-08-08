# Task：Harness 升级 2.20→2.22（api）· overlay 部分根治复检

> **状态**：active  
> **类型**：基础设施（upgrade + wiki_delta FEEDBACK + overlay U2 验证）  
> **关联**：npm `@cyning/harness@2.22.0` · local 块 · `graph_modules_path` · PR #23  
> **合入**：走 PR（禁直推 master）

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `upgrade-harness-2-20-runbook-feedback` |
| **git_branch** | `task/upgrade-harness-2-20-runbook-feedback` |
| **graph_change_layer** | `none` |
| **graph_delta** | `none` |
| **graph_delta_note** | 仅过程轨 / overlay 契约 / FEEDBACK；不改业务图谱 |
| **wiki_delta** | `none` |
| **wiki_delta_note** | 本轮不改 coding_wiki 正文 |
| **review_hat** | `20` |
| **thinking_profile** | `shortest` |
| **invoke_retention_profile** | `minimal` |
| **required_invoke_hats** | `30` |
| **experience_capture** | `recommended` |
| **test_strategy** | `recommended` |
| **test_strategy_note** | upgrade 2.22×2；local 块零手恢复；lint/strict；FEEDBACK |
| **code_quality_bar** | `not_applicable` |
| **orchestration** | 2.20 FEEDBACK → 2.21 复检 → 2.22 overlay 部分根治验证 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| **HG-GRAPH-MODULES** | approved | **30** | 00 代签：仅过程轨 |
| HG-TASK-DRAFT | approved | 22-R1 | 维护者：升 2.22 验证 U2 部分根治 + FEEDBACK |
| **HG-AUDIT-R1** | approved | **30** | 00 代签：无业务 API |

---

## 背景与目标

产品 **2.22.0** 对 ops U2 做部分根治（local 块 + `graph_modules_path` + overlay hint）。本仓迁契约后钉升，验证「合规下零手恢复」。

**完成态**：

- [x] manifest → `2.22.0`
- [x] profile `graph_modules_path=l1/01_modules`
- [x] AGENTS local 块关键词在；upgrade×2 无需 backup 手恢复
- [x] lint / `--strict` PASS
- [x] FEEDBACK 2.22 落盘

**不做**：改产品仓；默认 CI `--strict`；把仓特异词写回产品 marker

---

## 失败路径

| 触发 | 行为 | 可重试 |
|---|---|---|
| local 仍被冲 | 核对 marker 外位置；记 FEEDBACK severity | 是 |
| FRAGMENT 仍 01_struct | 查 profile 字段与 hint | 是 |
| lint missing>0 | 补字段 | 是 |
| 脏树 S5 | 先 commit 契约再 upgrade | 是 |

---

## 验收标准

- [x] manifest=2.22.0 · check 最新
- [x] 合规路径：upgrade 后零手恢复
- [x] FEEDBACK 路径 + PR URL

---

### 自检结论（执行者）

| 项 | 内容 |
|---|---|
| **日期** | 2026-07-28 |
| **manifest** | `2.22.0` |
| **U2 合规零手恢复** | **PASS**（×2 upgrade + 负面对照产品块仍冲） |
| **lint / strict** | PASS · scanned=25 |
| **FEEDBACK** | `docs/harness/evidence/FEEDBACK_harness_2_22_0_from_ops_desk_api_20260728.md` |
| **PR** | https://github.com/Cyning12/ops-desk-api/pull/23 |
