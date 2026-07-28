# Invoke：00 · wikitrack-enable-p0（统筹分派）

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 00 |
| task_slug | `wikitrack-enable-p0` |
| task_paths | `docs/tasks/active/task_wikitrack_enable_p0.md` |
| related_review_or_none | `docs/harness/reviews/task_wikitrack_enable_p0_audit_R1_20260728.md` |
| git_branch | `task/harness-upgrade-2-18-migrate` |
| created_utc_or_local | 2026-07-28 |
| notes | 维护者要求：先 2.18.1，再落地 WikiTrack；产出可复用方案交 web |

---

## 00 决策

1. **版本闸**：文档动作前必须 `manifest=2.18.1`（本分支已从 2.18.0 upgrade）。  
2. **范围**：启用 `docs/coding_wiki` 入口 + RUNBOOK；**禁止双份正文**。  
3. **交棒**：同会话 30 执行改 wiki / 写 RUNBOOK / 校验；web **不在本仓改码**，只收 RUNBOOK。  
4. **存量 task**：已标 `n/a` 的 done **不回刷**；启用后新 task 禁用默认 `n/a`。  
5. **合入**：可与 PR #22（2.18.x + wiki_delta 迁移）同波，PR 说明升至 2.18.1 + WikiTrack P0。

## 给 30 的必读

- [`docs/harness/RUNBOOK_wikitrack_enable_obsidian_v1_zh.md`](../../RUNBOOK_wikitrack_enable_obsidian_v1_zh.md)（边写边填 api 记录）
- task 验收与 failure_paths
- 产品模板互链：`npx` 包内 `coding_wiki/templates`（2.18.1）

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-07-28 | 00 分派 WikiTrack P0 |
