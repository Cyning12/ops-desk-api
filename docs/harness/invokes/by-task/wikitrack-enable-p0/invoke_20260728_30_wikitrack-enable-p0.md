# Invoke：30（含 40）· wikitrack-enable-p0

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 30（含 40） |
| task_slug | `wikitrack-enable-p0` |
| task_paths | `docs/tasks/active/task_wikitrack_enable_p0.md` |
| related_review_or_none | `docs/harness/reviews/task_wikitrack_enable_p0_audit_R1_20260728.md` |
| git_branch | `task/harness-upgrade-2-18-migrate` |
| created_utc_or_local | 2026-07-28 |
| notes | 承接 00：落地入口 + RUNBOOK |

---

## 人工闸扫描（GATE_VERIFY · 首输出）

| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---------------|--------------|-----------------|--------|-----------|------------|
| HG-TASK-DRAFT | approved | 维护者落地 | Y | N | Y |
| HG-AUDIT-R1 | approved | 00 代签 | Y | Y | Y |
| HG-GRAPH-MODULES | approved | 00 代签 | Y | Y | Y |

reviews：存在？ 是 · pre-30：required 含 00 → 已落盘

结论：可进入改 wiki / RUNBOOK

---

## 交付摘要

- **前置**：`upgrade` → manifest **2.18.1**；overlay 已恢复
- **coding_wiki**：四文件改为真实入口；`[[wikilink]]` 互链；真值用相对链（无双份）
- **RUNBOOK**：`docs/harness/RUNBOOK_wikitrack_enable_obsidian_v1_zh.md`（含 web 勾选清单）
- **校验**：check 已是最新 · wiki export nodes=4 edges=11 · verify PASS
- **下一棒**：交 web 按 RUNBOOK §6 勾选；本仓 PR 更新说明

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-07-28 | 落地 WikiTrack P0 · export 11 边 |
