# Invoke：30 执行编码 · harness-upgrade-2.13.0

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 30（含 40 自检） |
| task_slug | `harness-upgrade-2.13.0` |
| freeze_id | — |
| task_paths | `docs/tasks/active/task_harness_upgrade_2.13.0.md` |
| related_review_or_none | `docs/harness/reviews/task_harness_upgrade_2.13.0_audit_R1_20260726.md` |
| git_branch | `task/harness-upgrade-2.13.0` |
| worktree_root | — |
| created_utc_or_local | 2026-07-26 |
| notes | 仅 api 升至 2.13.0；web 本轮不升；避 F1b（不带 `--ide`） |

---

## 可复制 Prompt 快照

```text
更新cyning-harness到2.13.0，并回填checklist；授权提交，先只针对api进行升级
```

---

## 交付摘要

### 升级结论

| 项 | 结果 | 证据 |
|---|---|---|
| `upgrade --yes`（无 `--ide`） | **一把过** | apply →「已更新 local.json」→「已更新 manifest」· 无 S5 |
| manifest | **2.13.0** | `from_version: 2.11.1` · 仅五字段 · ide 保持 cursor,claude,agents |
| `harness check` | 已是最新 | `@cyning/harness@2.13.0` |
| `verify --task` | **PASS** | 双闸 approved；WARN：invoke 目录当时空（已补）；S5 脏工作区提醒（升级后预期） |
| `lifecycle dry-run --transition close` | **接线 OK** | close_* 六项均求值（非 unevaluated）；缺 invoke/未勾选/状态 active 时 correctly blocked |
| F1b | **未复现**（本轮未带 `--ide`） | 仍开 · 产品未修 |

### 同步触及

- `.cyning-harness/manifest.json` · `local.json`
- `docs/harness/prompts/`（10-task / 20-task-audit / 30 等 2.12+ 字段文案）
- `docs/harness/invokes/TEMPLATE_invoke.md`
- IDE starter（Cursor/Claude/AGENTS 片段；本轮 diff 未见实质改动则未脏）

### 跨仓

- **web / ios**：本轮按用户指示 **不升级**
- Projects checklist：回填 api → 2.13.0

### 下一棒

自检勾选 → `task close` · checklist 修订记录 · 可选 PR

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-07-26 | 30/40 · api 2.11.1→2.13.0 一把过 · dry-run close_* 接线确认 |
