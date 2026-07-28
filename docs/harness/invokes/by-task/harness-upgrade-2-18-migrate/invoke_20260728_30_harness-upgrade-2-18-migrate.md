# Invoke：30（含 40）· harness-upgrade-2-18-migrate

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 30（含 40 自检） |
| task_slug | `harness-upgrade-2-18-migrate` |
| task_paths | `docs/tasks/active/task_harness_upgrade_2-18-migrate.md` |
| related_review_or_none | `docs/harness/reviews/task_harness_upgrade_2-18-migrate_audit_R1_20260728.md` |
| git_branch | `task/harness-upgrade-2-18-migrate` |
| created_utc_or_local | 2026-07-28 |
| notes | 维护者：钉 @cyning/harness@2.18.0 + wiki_delta 存量迁移；无可视化 / 无业务 API |

---

## 人工闸扫描（GATE_VERIFY · 首输出）

| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---------------|--------------|-----------------|--------|-----------|------------|
| HG-TASK-DRAFT | approved | 维护者下发 30 Prompt | Y | N | Y |
| HG-AUDIT-R1 | approved | 00 代签 | Y | Y | Y |
| HG-GRAPH-MODULES | approved | 00 代签 · 仅过程轨 | Y | Y | Y |

reviews：`task_harness_upgrade_2-18-migrate_audit_R1_20260728.md` 存在？ 是

pre-30 invoke：`minimal` → 无 preRequired · 不挡

结论：可进入 upgrade / 文档迁移

---

## 交付摘要

- **upgrade**：`npx --yes @cyning/harness@2.18.0 upgrade --target . --yes` → exit 0（无 S5）
- **manifest**：`2.17.0` → `2.18.0`；preset=`fullstack-node-py`；ide=`cursor,claude,agents`（未裁）
- **wiki_delta 迁移**：`docs/tasks/**/task_*.md` 共 21 个 done + 本 active → `n/a` +「本仓未启用 WikiTrack」
- **experience=required ∩ wiki_delta=path**：本仓无此类 task · 无晋升指针义务
- **overlay**：upgrade 冲掉 AGENTS harness 段 pre-30 / G-L0 关键词与 FRAGMENT `l1/01_modules` → 已恢复
- **check**：已是最新 · exit 0
- **verify**：PASS · exit 0
- **质量门**：ruff OK · pytest 87 passed（`.venv`）
- **破坏性**：缺 `wiki_delta` → close BLOCK；PR 明示勿默认 `--allow-wiki-gap`
- **下一棒**：交还 00 · PR → CLOSE

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-07-28 | upgrade 2.17.0 → 2.18.0 + wiki_delta 存量迁移 |
| 2026-07-28 | check/verify/ruff/pytest 绿 · 待 PR |
