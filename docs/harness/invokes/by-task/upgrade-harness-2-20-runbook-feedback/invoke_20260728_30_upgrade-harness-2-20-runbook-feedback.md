# Invoke：30（含 40）· upgrade-harness-2-20-runbook-feedback

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 30（含 40） |
| task_slug | `upgrade-harness-2-20-runbook-feedback` |
| task_paths | `docs/tasks/active/task_upgrade_harness_2_20_runbook_feedback.md` |
| related_review_or_none | `docs/harness/reviews/task_upgrade_harness_2_20_runbook_feedback_audit_R1_20260728.md` |
| git_branch | `task/upgrade-harness-2-20-runbook-feedback` |
| created_utc_or_local | 2026-07-28 |
| notes | 产品 RUNBOOK dogfood · 2.20.0 |

---

## 人工闸扫描（GATE_VERIFY · 首输出）

| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---------------|--------------|-----------------|--------|-----------|------------|
| HG-TASK-DRAFT | approved | 维护者指令开工 | Y | N | Y |
| HG-AUDIT-R1 | approved | 00 代签 | Y | Y | Y |
| HG-GRAPH-MODULES | approved | 仅过程轨 | Y | Y | Y |

reviews：`task_upgrade_harness_2_20_runbook_feedback_audit_R1_20260728.md` 存在且 R1 通过？ **是**

pre-30 invoke：`minimal` · required=`30` → 无 preRequired 挡 → **是**

结论：**可进入 30**（upgrade / lint / FEEDBACK / PR）

---

## 交付摘要

- **upgrade**：`@cyning/harness@2.20.0 upgrade --yes` → exit 0
- **manifest**：`2.19.0` → `2.20.0`
- **overlay**：AGENTS 定制已恢复
- **lint-wiki-delta**：scanned=25 · missing=0 · PASS
- **lint-wiki-delta --strict**：**PASS** · issues=0
- **CI**：已挂 `.github/workflows/lint-wiki-delta.yml`（npx-only · cache false）
- **FEEDBACK**：`docs/harness/evidence/FEEDBACK_harness_2_20_0_from_ops_desk_api_20260728.md`
- **BACKFILL_DRAFT**：同目录可选稿

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-07-28 | 开工 · GATE_VERIFY PASS |
| 2026-07-28 | 升级完成 · strict PASS · FEEDBACK · 待 PR |
