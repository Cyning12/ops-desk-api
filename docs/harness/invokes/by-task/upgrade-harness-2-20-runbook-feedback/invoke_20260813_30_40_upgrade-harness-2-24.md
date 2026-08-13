# Invoke：30（含 40）· upgrade-harness-2-20-runbook-feedback（2.24.0）

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 30（含 40） |
| task_slug | `upgrade-harness-2-20-runbook-feedback` |
| task_paths | `docs/tasks/active/task_upgrade_harness_2_20_runbook_feedback.md` |
| related_review_or_none | `docs/harness/reviews/task_upgrade_harness_2_20_runbook_feedback_audit_R1_20260728.md`（沿用） |
| git_branch | `task/upgrade-harness-2-20-runbook-feedback` |
| created_utc_or_local | 2026-08-13 |
| notes | 00 派工钉升 2.24.0 · 不关账 |

---

## 人工闸扫描（GATE_VERIFY · 首输出）

| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---------------|--------------|-----------------|--------|-----------|------------|
| HG-TASK-DRAFT | approved | 00 派工 | Y | N | Y |
| HG-AUDIT-R1 | approved | 00 代签 | Y | Y | Y |
| HG-GRAPH-MODULES | approved | 仅过程轨 | Y | Y | Y |

reviews：`task_upgrade_harness_2_20_runbook_feedback_audit_R1_20260728.md` 存在？ **是**（沿用前波）

pre-30 invoke：`minimal` · required=`30` → 无 preRequired 挡；另有 00 dispatch → **是**

机械：`npx @cyning/harness verify --target . --task docs/tasks/active/task_upgrade_harness_2_20_runbook_feedback.md` → **VERIFY: PASS**

结论：**可进入 30**（upgrade / lint / FEEDBACK；40 自检；**不** `task close`）

---

## 交付摘要

- **分支**：自 `origin/master` 新建 `task/upgrade-harness-2-20-runbook-feedback`；带入 2.24 retarget task + 00 dispatch  
- **upgrade**：`2.22.0` → **`2.24.0`**（×2；中间因 S5 先 commit sync）  
- **零手恢复**：AGENTS local / FRAGMENT `l1/01_modules` / CLAUDE / cursor mdc → **PASS ×2**  
- **skills**：`skills check` PASS；`skills build` PASS（写产品包 skills/）  
- **lint**：本 task `task lint` PASS；`lint-wiki-delta` PASS；`--strict` 被无关 `task_ops_sync_sender_migration` 挡住（未改）  
- **FEEDBACK**：`docs/harness/evidence/FEEDBACK_harness_2_24_0_from_ops_desk_api_20260813.md`  
- **关账**：留给 00 · **未**执行 `harness task close`

---

## 命令与退出码

| 命令 | exit |
|------|------|
| `npx @cyning/harness check`（before） | 0（可升级） |
| `npx --yes @cyning/harness@2.24.0 upgrade --target . --yes`（#1） | 0 |
| 同命令（#2 · 脏树） | 1（S5） |
| 同命令（#2 · 提交后） | 0 |
| `npx @cyning/harness check`（after） | 0（已是最新） |
| `verify --task …upgrade…` | 0 |
| `task lint --file …upgrade…` | 0 |
| `task lint-wiki-delta` | 0 |
| `task lint-wiki-delta --strict --json` | 2（无关 task） |
| `skills check` | 0 |
| `skills build` | 0 |

---

## 40 自检

| 验收项 | 结果 |
|--------|------|
| manifest=2.24.0 | PASS |
| graph_modules_path / local 块 | PASS |
| 零手恢复 ×2 | PASS |
| FEEDBACK + 30/40 invoke | PASS |
| 全局 `--strict` | 记缺口 · 非本波 |

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-08-13 | 30/40：钉升 2.24.0 · FEEDBACK · 自检勾选 · 不关账 |
