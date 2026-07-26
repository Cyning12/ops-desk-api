# Invoke：30 执行编码 · harness-upgrade-2.11.1

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 30（含 40 自检） |
| task_slug | `harness-upgrade-2.11.1` |
| freeze_id | — |
| task_paths | `docs/tasks/active/task_harness_upgrade_2.11.1.md` |
| related_review_or_none | `docs/harness/reviews/task_harness_upgrade_2.11.1_audit_R1_20260726.md` |
| git_branch | `task/harness-upgrade-2.11.1` |
| worktree_root | — |
| created_utc_or_local | 2026-07-26 |
| notes | 2.11.1 F1/F2 遗留回归；api 主仓 + web dogfood；ios 因工作区已脏未升 |

---

## 可复制 Prompt 快照

```text
更新 cyning-harness 到 2.11.1，进行之前的遗留问题回归（F1/F2）
```

---

## 交付摘要

### 回归结论

| ID | 期望 | 结果 | 证据 |
|---|---|---|---|
| **F1**（local.json 自脏 → S5） | 干净仓 `upgrade --yes` 一把过 | **PASS** | api `2.2.1→2.11.1`：apply 成功后才「已更新 local.json」· 无 S5；web 在 commit profile 后重跑同样一把过 |
| **F2**（死字段静默丢失） | 重写前 WARN 清单 | **PASS** | 注入 `name/harness_version/tech_graph_dir/tasks_dir/hooks` 后重跑：`WARN: manifest 以下非标准字段将被移除…`；落盘仅五字段 |
| **F3**（ide 裁剪） | 未进 2.11.1 | 用 `--ide` 对齐 | 见下「新摩擦」 |

### 新摩擦（建议记入摩擦本）

| # | 步骤 | 现象 | 期望 |
|---|---|---|---|
| **F1b** | `upgrade --yes --ide cursor,claude,agents` | 向导先 `patch_profile_ide` 写脏 `profile.json`，随后 apply 被 S5 中止 | `--ide` 写入应在 apply 成功之后（与 F1 local.json 同序） |

### 验证命令

- api：`npx @cyning/harness@2.11.1 check` → 已是最新；`verify --task …` → PASS；`lifecycle show` / `discipline show` OK；`ruff` + `pytest tests` → **87 passed**
- web：`check` → 已是最新；manifest `2.11.1` / `from_version: 2.11.0`

### 变更路径（api）

- `.cyning-harness/manifest.json` · `local.json`
- `docs/harness/prompts/`：V2 新帽就位；删除 obsolete `10-requirements.md` / `22-task-audit.md`
- task / review / invoke

### 跨仓

- `ops-desk-web`：`task/harness-upgrade-2.11.1` · manifest → 2.11.1（未在本 invoke 关 web 账）
- `ops-desk-ios`：工作区非干净，跳过

### 下一棒

CLOSE（api）· web 自行 commit/PR · Projects checklist 标 `regressed` · 可选开产品 patch 修 F1b

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-07-26 | 30/40 · F1/F2 PASS · 记 F1b |
