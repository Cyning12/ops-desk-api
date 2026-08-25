# Invoke：30 · dsh-coding-kit-upgrade-1-5-2（1.5.2）

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 30 |
| task_slug | `dsh-coding-kit-upgrade-1-5-2` |
| task_paths | `docs/tasks/active/task_dsh_coding_kit_upgrade_1_5_2.md` |
| related_review_or_none | none（20 帽 R<n> 审查序内待补） |
| git_branch | `task/dsh-coding-kit-1-5-2` |
| created_utc_or_local | 2026-08-25（task 起草 2026-08-24） |
| notes | 00 派工 1.5.1→1.5.2 patch 升级 + FEEDBACK 项修复核对 · 禁 git commit · 不关账 |

---

## 人工闸扫描（GATE_VERIFY · 首输出）

| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---------------|--------------|-----------------|--------|-----------|------------|
| HG-TASK-DRAFT | approved | 00 派工 | Y | N | Y |
| HG-AUDIT-R1 | approved | 00 代签 | Y | Y | Y |

reviews：本 task R<n> **无**（20 序内待补）→ 严格 verify BLOCKED 为预期，`--allow-no-review` 留痕豁免。

pre-30 invoke：required=`10,30` · 开工时 hat 10 缺（00 序内补件，本波由 30 补齐快照）→ 首跑 `--allow-invoke-gap` 留痕豁免；补齐后 verify 不再需要该旗标。

机械：`npx dsh-coding-kit verify --target . --task docs/tasks/active/task_dsh_coding_kit_upgrade_1_5_2.md` → 严格态 **BLOCKED exit 2**（missing R<n> review，序内预期）

结论：**可进入 30**（升级执行 + 修复核对 + 自检 + FEEDBACK；**不** commit、**不** close）

---

## 交付摘要

- **升级序列**（按 1.5.1 已验证路径）：check → refresh-ide-blocks --dry-run → stash -u → refresh --yes → pop → upgrade --yes → 幂等二跑（upgrade 二跑 + refresh 二刷 dry-run）
- **manifest**：1.5.1 → **1.5.2**（from_version=1.5.1 · preset=fullstack-node-py / ide 保留）
- **refresh**：rewrites=0 / files_written=0（1.5.1 波已改写 A1 字面，本波零改写）；local 块跳过×1（AGENTS）；**DEF-029 生效**：无 marker 检出段报 `.cursor/rules/05-harness-starter.mdc` A1 命中 1（仅报告不刷写）——对应 1.5.1 FEEDBACK K4 已修
- **check DEF-028 生效**：1.5.1 波「manifest 高于包版本=可能降级」误报语义，1.5.2 起 from_version 非 null 时输出跨产品线迁移文案（lib/cli.js L210-214）——对应 1.5.1 FEEDBACK K1 已修
- **local 块**：`git diff AGENTS.md CLAUDE.md` 空 = 零字节变化
- **FEEDBACK 项修复核对**（实读 1.5.2 包 `lib/cli-graph-yaml.js`，且与 1.5.1 包 diff **0 diff lines**）：D1 未修（L201-210）· D2 未修（L268-279/283-296）· D3 未修（同源 D2，L527-528）· R6 未修（L395-397 硬编码 id 白名单，不读 yaml kind）；DEF-023 已修三条未回退（formatAnchorComment L326-338 · L380-381 官方带标签边形态 · L356-358+L344-349 引号+entity code）
- **自检**：verify 豁免 PASS · graph-compile.sh exit 0（harness 面未动，产物 diff 仅 generated_at/freeze_id 日期戳，已 git checkout 还原）· pytest 3 failed/242 passed = 基线
- **FEEDBACK**：`docs/harness/evidence/FEEDBACK_dsh_coding_kit_1_5_2_from_ops_desk_api_20260824.md`
- **关账**：留给 00 · **未** commit · **未** task close

---

## 命令与退出码

| 命令 | exit |
|------|------|
| `dsh-coding-kit@1.5.2 check --target .`（before） | 0（状态：可升级；无降级误报） |
| `refresh-ide-blocks --dry-run` | 0（rewrites=0 · plain_mentions=1） |
| `git stash push -u` → `refresh-ide-blocks --yes` → `git stash pop` | 0（零写入，无新备份代） |
| `upgrade --target . --yes` | 0（1.5.1→1.5.2） |
| `upgrade` 二跑 / `refresh` 二刷 dry-run / `check`（after） | 0 / 0 / 0（幂等；check=已是最新） |
| `verify --task <本task>`（严格） | 2（BLOCKED · 缺 R<n>，序内预期） |
| `verify --task <本task> --allow-no-review --allow-invoke-gap`（首跑）/ `--allow-no-review`（invoke 补齐后） | 0（PASS · 留痕） |
| `./scripts/graph-compile.sh` | 0（harness 面未动） |
| `.venv/bin/pytest tests -q` | 1（3 failed/242 passed = 既有基线，缺表，无新增） |

所有 npx 均带 `npm_config_cache=/tmp/npm-cache-lg`。
