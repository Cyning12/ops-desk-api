# Invoke：30 · dsh-coding-kit-upgrade-1-6-1（1.6.1）

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 30 |
| task_slug | `dsh-coding-kit-upgrade-1-6-1` |
| task_paths | `docs/tasks/active/task_dsh_coding_kit_upgrade_1_6_1.md` |
| related_review_or_none | none（20 帽 R<n> 审查序内待补） |
| git_branch | `task/dsh-coding-kit-1-6-1` |
| created_utc_or_local | 2026-08-25 |
| notes | 00 派工 1.5.2→1.6.1 minor 升级 + FEEDBACK 项修复核对 · 禁 git commit · 不关账 |

---

## 人工闸扫描（GATE_VERIFY · 首输出）

| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---------------|--------------|-----------------|--------|-----------|------------|
| HG-TASK-DRAFT | approved | 00 派工 | Y | N | Y |
| HG-AUDIT-R1 | approved | 00 代签 | Y | Y | Y |

reviews：本 task R<n> **无**（20 序内待补）→ 严格 verify BLOCKED 为预期，`--allow-no-review` 留痕豁免。

pre-30 invoke：required=`10,30` · 帽 10 快照本波已落盘 → verify 无需 `--allow-invoke-gap`。

机械：`npx dsh-coding-kit@1.6.1 verify --target . --task docs/tasks/active/task_dsh_coding_kit_upgrade_1_6_1.md` → 严格态 **BLOCKED exit 2**（missing R<n> review，序内预期）

结论：**可进入 30**（升级执行 + 修复核对 + 自检 + FEEDBACK；**不** commit、**不** close）

---

## 交付摘要

- **CLI 面探查（minor 跳版 · 对照 1.5.2）**：顶层 help 唯一变更 = `verify [--task FILE | --spec FILE]`（新增 --spec 模式，PRD_DEF-003 后续棒）；verify --help 新增 `--allow-no-spec-review`；upgrade / refresh-ide-blocks / check / graph / task / gate-check / audit / status / timeline / lifecycle / discipline / skills / wiki / sync 子命令面 **零变更**；无参数删除、无语义反转 → 无破坏性变更
- **升级序列**（按 1.5.1/1.5.2 已验证路径）：check（可升级，无降级误报）→ refresh-ide-blocks --dry-run（rewrites=0 · plain_mentions=1）→ stash -u → refresh --yes（零写入）→ pop → upgrade --yes（1.5.2→1.6.1）→ 幂等二跑（upgrade 二跑 1.6.1→1.6.1 from_version 保持 1.5.2 / refresh 二刷 rewrites=0 / check=已是最新）
- **manifest**：1.5.2 → **1.6.1**（from_version=1.5.2 · preset=fullstack-node-py / ide 保留）
- **local 块**：`git diff AGENTS.md CLAUDE.md` 空 = 零字节变化；refresh 报告自述「跳过 local 块: 1」（AGENTS）
- **FEEDBACK 项修复核对**（实读 1.6.1 包源码；`lib/cli-graph-yaml.js` 与 1.5.2 diff **79 行**——1.5.2 波为 0 行）：**D1 已修**（DEF-031 · L200-201+206/211/216）· **D2 已修**（DEF-032① L281-302 · ③ L40-44）· **D3 已修**（DEF-032② L548-551）· **R6 已修**（DEF-033 L401-424 · kind→class 映射 + id 推断兜底）· **K7 已修**（DEF-030 · cli.js L85-89/213-215 判据收窄至 2.x 词表；upgrade from_version=直接前驱语义不变）· **K8** kit 侧 freeze_id 为固定常量 `TECH_GRAPH_S2_FREEZE_20260519_V2_3`（cli-graph-yaml.js L5/270/318），日滚动系本仓 `graph_yaml_to_json.py` 行为，维持 checkout 还原处置
- **DEF-023 回退抽查**：三条均**未回退**（formatAnchorComment L332-338 · 带标签边官方形态 L380/387 · 引号+entity code L350-354/363-364；全 lib `grep -- '--"'` 0 命中）
- **自检**：verify 严格态 BLOCKED（缺 R<n> 序内预期）→ `--allow-no-review` 留痕豁免 PASS exit 0 · graph-compile.sh exit 0（产物 diff 仅 generated_at 时间戳，已 git checkout 还原）· pytest 3 failed/242 passed = 基线
- **FEEDBACK**：`docs/harness/evidence/FEEDBACK_dsh_coding_kit_1_6_1_from_ops_desk_api_20260825.md`
- **关账**：留给 00 · **未** commit · **未** task close

---

## 命令与退出码

| 命令 | exit |
|------|------|
| `dsh-coding-kit@1.6.1 check --target .`（before） | 0（状态：可升级；from_version=1.5.1 kit 线 → DEF-030 判据收窄生效，无跨产品线/降级误报） |
| `refresh-ide-blocks --dry-run` | 0（rewrites=0 · plain_mentions=1 · DEF-029 检出报告仍在） |
| `git stash push -u` → `refresh-ide-blocks --yes` → `git stash pop` | 0（零写入，无新备份代） |
| `upgrade --target . --yes` | 0（1.5.2→1.6.1 · from_version=1.5.2） |
| `upgrade` 二跑 / `refresh` 二刷 dry-run / `check`（after） | 0 / 0 / 0（幂等；check=已是最新） |
| `verify --task <本task>`（严格） | 2（BLOCKED · 缺 R<n>，序内预期） |
| `verify --task <本task> --allow-no-review` | 0（PASS · 留痕豁免） |
| `./scripts/graph-compile.sh` | 0（harness 面未动） |
| `.venv/bin/pytest tests -q` | 1（3 failed/242 passed = 既有基线，缺表，无新增） |

所有 npx 均带 `npm_config_cache=/tmp/npm-cache-lg`。
