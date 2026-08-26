# Invoke：30（含 40）· dsh-coding-kit-upgrade-1-7-1

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 30（含 40） |
| task_slug | `dsh-coding-kit-upgrade-1-7-1` |
| task_paths | `docs/tasks/done/task_dsh_coding_kit_upgrade_1_7_1.md` |
| related_review_or_none | `docs/harness/reviews/task_dsh_coding_kit_upgrade_1_7_1_audit_R1_20260826.md` |
| git_branch | `task/dsh-coding-kit-1-7-1` |
| created_utc_or_local | 2026-08-26 |
| notes | 00 代签后同会话 30；过程轨 + 试点文档；**未**动 `app/`；**未** `--yes` close；**未** push（待授权） |

---

## 人工闸扫描（GATE_VERIFY · 首输出）

| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---------------|--------------|-----------------|--------|-----------|------------|
| HG-TASK-DRAFT | approved | 复制区 B 可代签 | Y | Y | Y |
| HG-AUDIT-R1 | approved | 00 代签 + R1 文 | Y | Y | Y |
| HG-GRAPH-MODULES | —（graph_change_layer=none） | — | — | N | Y |

reviews：`task_dsh_coding_kit_upgrade_1_7_1_audit_R1_20260826.md` 存在且 R1 通过？ **是**

pre-30 invoke：required=`10,30,40` · 帽 10 已先落盘 → verify 无需 `--allow-invoke-gap`。

机械：`npx dsh-coding-kit@1.7.1 verify --target . --task docs/tasks/done/task_dsh_coding_kit_upgrade_1_7_1.md` → **VERIFY: PASS exit 0**

结论：**可进入 30**（升级 + 文档迁移 + CLOSE dry-run；**不** `--yes` close、**不** push）

---

## 交付摘要

- **CLI 探查**：顶层 help 与 1.6.1 同形；`task close` 无 `--help`（`task --help` 才有用法，含 `--allow-no-pr-merge` / `--allow-no-hub`）
- **升级序列**：check（可升级 · 裸 SPEC WARN **8**）→ refresh dry-run（rewrites=0 · skipped_local=1）→ upgrade --yes（1.6.1→1.7.1）
- **manifest**：1.6.1 → **1.7.1**（from_version=1.6.1）
- **local 块**：AGENTS/CLAUDE diff 空
- **00-orchestrator**：upgrade **未**写入；自 kit 资产手补；FEEDBACK 已落盘
- **30-execute-code.md**：换成 kit 1.7.1 正文（READY ≠ PASS）
- **验证**：verify PASS · graph-compile exit 0（时间戳已还原）· pytest 3 failed / 298 passed（基线，无新增）
- **关账**：无 `--yes` 且无 PR → `CLOSE: BLOCKED`（`close_pr_merged`）；`--allow-no-pr-merge` 留痕 → **`CLOSE: READY · dsh-coding-kit-upgrade-1-7-1`**（不含完成态 PASS）；**未** `task close --yes`

---

## 命令与退出码

| 命令 | exit |
|------|------|
| `dsh-coding-kit@1.7.1 check --target .` | 0（可升级；WARN 裸 SPEC 8） |
| `refresh-ide-blocks --dry-run --json` | 0（rewrites=0 · skipped_local_blocks=1） |
| `upgrade --target . --yes` | 0（1.6.1→1.7.1） |
| `verify --task <本task>` | 0（PASS） |
| `./scripts/graph-compile.sh` | 0 |
| `.venv/bin/pytest tests -q` | 1（3 failed / 298 passed = 基线） |
| `task close --file <本task>`（无 --yes） | 2（`CLOSE: BLOCKED` · close_pr_merged 无 PR） |
| 同上 + `--allow-no-pr-merge` | 0（`CLOSE: READY · dsh-coding-kit-upgrade-1-7-1`） |

所有 npx 均带 `npm_config_cache=/tmp/npm-cache-lg`。
