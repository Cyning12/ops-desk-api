# Invoke：30（含 40）· harness-upgrade-2.19.0

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 30（含 40） |
| task_slug | `harness-upgrade-2.19.0` |
| task_paths | `docs/tasks/active/task_harness_upgrade_2.19.0.md` |
| related_review_or_none | `docs/harness/reviews/task_harness_upgrade_2.19.0_audit_R1_20260728.md` |
| git_branch | `task/harness-upgrade-2-18-migrate` |
| created_utc_or_local | 2026-07-28 |
| notes | 延伸 2.19.0 · 同波关账 |

---

## 人工闸扫描（GATE_VERIFY）

| human_gate_id | task表status | 一致？ | 30可开工？ |
|---------------|--------------|--------|------------|
| HG-TASK-DRAFT | approved | Y | Y |
| HG-AUDIT-R1 | approved | Y | Y |
| HG-GRAPH-MODULES | approved | Y | Y |

结论：可开工

---

## 交付摘要

- **upgrade**：`@cyning/harness@2.19.0 upgrade --yes` → exit 0
- **manifest**：`2.18.2` → `2.19.0`
- **lint-wiki-delta**：`--scope all` · scanned=23 · missing=0 · PASS
- **overlay**：已恢复
- **文档**：RUNBOOK / coding_wiki 钉 2.19.0
- **下一棒**：与姊妹 task 一并 `task close --yes`

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-07-28 | 2.19.0 upgrade + 文档对齐 |
