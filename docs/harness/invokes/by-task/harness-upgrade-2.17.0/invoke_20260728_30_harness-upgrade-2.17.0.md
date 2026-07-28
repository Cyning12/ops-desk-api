# Invoke：30（含 40）· harness-upgrade-2.17.0

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 30（含 40 自检） |
| task_slug | `harness-upgrade-2.17.0` |
| task_paths | `docs/tasks/active/task_harness_upgrade_2.17.0.md` |
| related_review_or_none | `docs/harness/reviews/task_harness_upgrade_2.17.0_audit_R1_20260728.md` |
| git_branch | `task/harness-upgrade-2.17.0` |
| created_utc_or_local | 2026-07-28 |
| notes | 维护者：更新 cyning-harness 到最新版 |

---

## 交付摘要

- **upgrade**：`npx @cyning/harness@2.17.0 upgrade --target . --yes` → exit 0（无 S5）
- **manifest**：`2.16.1` → `2.17.0`；preset=`fullstack-node-py`；ide=`cursor,claude,agents`（未裁）
- **check**：已是最新 · exit 0
- **status --json**：`obs_status_list.v1` · exit 0
- **status --check**：may_start_30=true · exit 0
- **verify**：PASS
- **overlay**：upgrade 曾将 FRAGMENT/`AGENTS` harness 段冲成产品默认；已保留本仓 `l1/01_modules` + pre-30 / G-L0 关键词（净 diff 仅 manifest）
- **下一棒**：PR → 维护者 merge

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-07-28 | upgrade 2.16.1 → 2.17.0 |
