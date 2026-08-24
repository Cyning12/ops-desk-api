# Invoke：30 · dsh-coding-kit-upgrade-1-5-1（1.5.1）

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 30 |
| task_slug | `dsh-coding-kit-upgrade-1-5-1` |
| task_paths | `docs/tasks/active/task_dsh_coding_kit_upgrade_1_5_1.md` |
| related_review_or_none | none（20 帽 R<n> 审查序内待补） |
| git_branch | `task/dsh-coding-kit-1-5-1` |
| created_utc_or_local | 2026-08-24 |
| notes | 00 派工 harness→kit 1.5.1 过程轨迁移 · 禁 git commit · 不关账 |

---

## 人工闸扫描（GATE_VERIFY · 首输出）

| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---------------|--------------|-----------------|--------|-----------|------------|
| HG-TASK-DRAFT | approved | 00 派工 | Y | N | Y |
| HG-AUDIT-R1 | approved | 00 代签 | Y | Y | Y |

reviews：本 task R<n> **无**（20 序内待补）→ 严格 verify BLOCKED 为预期，`--allow-no-review` 留痕豁免 PASS。

pre-30 invoke：required=`10,30` · hat 10 缺（00 序内补件）→ `--allow-invoke-gap` 留痕豁免。

机械：`npx dsh-coding-kit verify --target . --task docs/tasks/active/task_dsh_coding_kit_upgrade_1_5_1.md --allow-no-review --allow-invoke-gap` → **VERIFY: PASS**（exit 0）

结论：**可进入 30**（kit CLI 探查 / refresh-ide-blocks / upgrade / 自检 / FEEDBACK；**不** commit、**不** close）

---

## 交付摘要

- **kit CLI 探查**：init/upgrade/refresh-ide-blocks/check/verify/graph --help + lib 源码实读；沿用 `.cyning-harness/` 约定
- **refresh-ide-blocks --yes**：AGENTS/CLAUDE 各 A1×1（`npx @cyning/harness` → `npx dsh-coding-kit`）；local 块跳过；备份落 `.cyning-harness/backups/refresh-ide-blocks/2026-08-24T15-29-58-404Z/`；幂等二刷 rewrites=0
- **upgrade --yes**：manifest 2.24.0 → **1.5.1**（from_version=2.24.0 · preset/ide 保留）；幂等二跑 from_version 不漂移
- **local 块**：diff 证明零字节变化（见 FEEDBACK §4）
- **自检**：verify 豁免 PASS · graph-compile.sh exit 0（harness 面未动）· pytest 3failed/242passed=基线
- **graph 子命令面**：kit 1.5.1 自带 `graph yaml compile|check|export` + `ingest|snapshot|axioms`（结论记 task/FEEDBACK §7，切换属 probe task）
- **FEEDBACK**：`docs/harness/evidence/FEEDBACK_dsh_coding_kit_1_5_1_from_ops_desk_api_20260824.md`
- **关账**：留给 00 · **未** commit · **未** task close

---

## 命令与退出码

| 命令 | exit |
|------|------|
| `dsh-coding-kit@1.5.1 check --target .`（before） | 0（报「manifest 高于包版本」· 跨产品线版本号不可比） |
| `refresh-ide-blocks --dry-run` | 0（A1×2 计划） |
| `refresh-ide-blocks --yes`（stash -u 过 preflight 后） | 0（写 2 文件 + 备份） |
| `upgrade --target . --yes` | 0（2.24.0→1.5.1） |
| `upgrade` 二跑 / refresh 二刷 dry-run | 0 / 0（幂等） |
| `verify --task <本task>`（严格） | 2（BLOCKED · 缺 R<n>） |
| `verify --task <本task> --allow-no-review --allow-invoke-gap` | 0（PASS · 留痕） |
| `./scripts/graph-compile.sh`（前/后） | 0 / 0 |
| `.venv/bin/pytest tests -q`（前/后） | 3failed/242passed · 同基线 |

---

## 40 自检

| 验收项 | 结果 |
|--------|------|
| manifest=1.5.1 | PASS |
| local 块零手恢复（diff 证明） | PASS |
| verify 跑通（kit 实际命令面） | PASS（豁免留痕 · 严格态缺口序内） |
| graph-compile.sh exit 0 | PASS |
| pytest 无新增失败 | PASS |
| graph 子命令面结论入 task | PASS |
| FEEDBACK 落盘 | PASS |

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-08-24 | 30：kit 1.5.1 迁移执行 · FEEDBACK · 自检勾选 · 不 commit 不关账 |
