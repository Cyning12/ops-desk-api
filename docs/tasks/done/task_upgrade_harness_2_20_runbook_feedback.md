# Task：Harness 升级 2.22→2.24（api）· overlay / skills 复检

> **状态**：completed  

> **类型**：基础设施（upgrade + FEEDBACK + overlay/local 块复检）  
> **关联**：npm `@cyning/harness@2.24.0`（registry 最新；仓内 manifest 已 `2.24.0`）· local 块 · `graph_modules_path` · 前波 2.22 FEEDBACK / PR #23  
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
| **test_strategy_note** | `harness check` 报可升级 → upgrade 钉 `2.24.0`×2；local 块零手恢复；lint/strict；FEEDBACK 2.24 |
| **code_quality_bar** | `not_applicable` |
| **orchestration** | 00 改目标 2.24 → 30/40 upgrade+复检 → 00 验收关账 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| **HG-GRAPH-MODULES** | approved | **30** | 00 代签：仅过程轨 |
| HG-TASK-DRAFT | approved | 22-R1 | 维护者授权：registry 已至 2.24.0，本波钉升验证 + FEEDBACK（承接原 2.22 闸） |
| **HG-AUDIT-R1** | approved | **30** | 00 代签：无业务 API |

---

## 背景与目标

- **前波（已完成）**：`2.22.0` overlay 部分根治验证 · FEEDBACK `docs/harness/evidence/FEEDBACK_harness_2_22_0_from_ops_desk_api_20260728.md` · PR #23  
- **本波**：registry 最新为 **`2.24.0`**（中间含 2.22.1/2.22.2/2.23.0）；仓内已钉升至 **`2.24.0`**。  
- 目标：钉升到 **2.24.0**，复检 local 块 / `graph_modules_path` / skills（若 upgrade 引入）在合规路径下**零手恢复**，并落盘 2.24 FEEDBACK。

**完成态**：

- [x] manifest → `2.24.0`（`npx @cyning/harness check` 显示最新或已对齐）
- [x] profile `graph_modules_path=l1/01_modules` 仍在
- [x] AGENTS `<!-- cyning-harness-local:begin/end -->` 关键词在；upgrade×2 无需 backup 手恢复
- [x] `task lint` / `--strict`（或等价）PASS — 本 task lint PASS；`lint-wiki-delta` PASS；全局 `--strict` 仅无关 task 缺口（见自检）
- [x] FEEDBACK 2.24 落盘：`docs/harness/evidence/FEEDBACK_harness_2_24_0_from_ops_desk_api_20260813.md`
- [x] 30/40 invoke 回填

**不做**：改产品仓；默认 CI `--strict`；把仓特异词写回产品 marker；动 `task_ops_sync_sender_migration`

---

## 实施要点（30）

1. **脏树纪律**：upgrade 前工作树干净（本 task 改动先 commit；业务脏文件 stash/另分支）  
2. 建议分支：`task/upgrade-harness-2-20-runbook-feedback`（可自 `master` 变基/续作）  
3. `npx --yes @cyning/harness@2.24.0 upgrade --target . --yes`（按 RUNBOOK；必要时 `--force` 仅记 FEEDBACK）  
4. 同版本再 upgrade 一次（幂等/零手恢复）  
5. diff：`AGENTS.md` / `CLAUDE.md` / `.cursor/rules/05-harness-starter.mdc` / FRAGMENT · local 块不得丢  
6. `npx @cyning/harness check|verify` + lint；写 FEEDBACK；40 自检回填 task  

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

- [x] manifest=`2.24.0` · check 对齐最新
- [x] 合规路径：upgrade 后零手恢复（×2）
- [x] FEEDBACK 2.24 路径落盘；30 invoke 齐

---

### 自检结论（执行者）

> 30/40 回填。前波 2.22 结论保留在 FEEDBACK_2_22_0，不作为本波完成证据。未执行 `harness task close`（00 关账）。

| 项 | 内容 |
|---|---|
| **日期** | 2026-08-13 |
| **manifest** | `2.24.0`（from `2.22.0`） |
| **U2/local 零手恢复** | **PASS**（×2；第二次前因 S5 先 commit sync） |
| **lint / strict** | `task lint` PASS(0)；`lint-wiki-delta` PASS(0)；`--strict` FAIL(2) 仅 `task_ops_sync_sender_migration`（本波禁改） |
| **skills** | `skills check` PASS(0)；`skills build` PASS(0)（写产品包） |
| **FEEDBACK** | `docs/harness/evidence/FEEDBACK_harness_2_24_0_from_ops_desk_api_20260813.md` |
| **invoke** | `docs/harness/invokes/by-task/upgrade-harness-2-20-runbook-feedback/invoke_20260813_30_40_upgrade-harness-2-24.md` |

---

### KPI

| 项 | 分 |
|---|---|
| Task_KPI% | 100 |

### 经验

- Wiki: n/a（本波不改 coding_wiki）
- 可复用：upgrade 前先 commit 契约/产物（S5）；合规 local 块在 2.24 仍零手恢复 · 见 `docs/harness/evidence/FEEDBACK_harness_2_24_0_from_ops_desk_api_20260813.md`

## CLOSE

| 项 | 内容 |
|---|---|
| **日期** | 2026-08-13 |
| **00 验收** | PASS · manifest 2.24.0 · check 已是最新 · local/profile 在 · FEEDBACK 齐 |
| **已知外因** | 全局 `lint-wiki-delta --strict` 仅 `task_ops_sync_sender_migration`（本波禁改 · 不挡关账） |
| **归档** | `docs/tasks/done/task_upgrade_harness_2_20_runbook_feedback.md` |
| **HEAD** | `7abeddc`（关账前；CLOSE 文档可能再 commit） |

## 修订

| 日期 | 说明 |
|------|------|
| 2026-07-28 | 初版：2.20→2.22 overlay 验证（完成态曾勾满，未关账） |
| 2026-08-13 | 00：registry 最新 **2.24.0** · 仓内仍 2.22.0 → **改目标并重开完成态** · 派 30/40 |
| 2026-08-13 | 30/40：钉升 2.24.0 · FEEDBACK · 完成态勾选 · 待 00 验收关账 |
| 2026-08-13 | 00：验收 PASS · CLOSE |
