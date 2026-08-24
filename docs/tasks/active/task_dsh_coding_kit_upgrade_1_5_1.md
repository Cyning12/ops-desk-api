# Task：dsh-coding-kit 升级 1.5.1（过程轨从 @cyning/harness 2.24.0 迁移）

> **状态**：active（闸已签 · 00 代签授权）  
> **类型**：基础设施 / harness 过程轨升级  
> **先例**：`task_upgrade_harness_2_20_runbook_feedback`（done · 2.24.0 钉升 + FEEDBACK 体例）  
> **背景**：npm `@cyning/harness@2.24.0` 已 deprecate，迁移至 `dsh-coding-kit`（当前最新 1.5.1）  
> **关联预留**：`docs/spec/SPEC-harness-to-dsh-kit-graph-migrate_v0.md`（graph 命令面切换属另 task，见 `task_dsh_kit_graph_migrate_probe`）  
> **分支**：`task/dsh-coding-kit-1-5-1`  
> **执行模式**：00 编排/验收；30 子 agent 执行

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `dsh-coding-kit-upgrade-1-5-1` |
| **git_branch** | `task/dsh-coding-kit-1-5-1` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 升级后：`npx dsh-coding-kit verify --target .` 可跑通；`pytest tests -q` 无新增失败；`./scripts/graph-compile.sh` exit 0（仍走 harness 命令面，切换另案） |
| **code_quality_bar** | `not_applicable`（过程轨） |
| **graph_change_layer** | `none` |
| **wiki_delta** | `n/a` |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,30` |
| **orchestration** | 单 task |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | 2026-08-24 00 代签（维护者本窗授权「签收过程文档」+ 直接指令升级 1.5.1） |
| HG-AUDIT-R1 | approved | 30 | 2026-08-24 00 代签（同上；过程轨升级有 2.24 先例与 RUNBOOK） |

---

## 范围

1. 用 `npm_config_cache=/tmp/npm-cache-lg npx --yes dsh-coding-kit@1.5.1` 探查 CLI 面（--help），按其官方路径执行 upgrade/init 到本仓（**先读 kit 自带说明**，勿凭 harness 旧命令记忆硬套）。
2. 升级产物：`.cyning-harness/`（或 kit 新目录约定）manifest 钉 1.5.1、prompts/invokes 模板、IDE 块（AGENTS.md / CLAUDE.md / .cursor）。
3. **local 块零手恢复**复检：`<!-- cyning-harness-local:begin/end -->` 内定制（HG-PILOT / G-L0 关键词、图谱闸路径）升级后仍在；被冲则恢复并记 FEEDBACK。
4. `graph-compile.sh` **仍指向 @cyning/harness**（命令面切换属 probe task 的 SPEC 前置，不在本 task）；但须在 task 内记录 kit 1.5.1 是否自带 graph 子命令（供 probe task）。
5. 升级后 verify/lint 跑通；CI 相关 yml 若引用 @cyning/harness 且 kit 有对应命令，**记录但不动**（切换另案）。

## 非范围

- graph-compile.sh 命令面切换（probe task + SPEC 前置条件）
- 业务代码
- W2 图谱绘制

## failure_paths

| 触发 | 行为 | 可重试 |
|---|---|---|
| kit CLI 面与 harness 不兼容 | 记录差异，回滚 .cyning-harness 改动，FEEDBACK 记 severity | Y |
| local 块被冲 | 恢复并记 FEEDBACK | Y |
| npm 缓存权限 | npm_config_cache=/tmp 前缀（本机已知坑） | Y |

---

## 验收标准

- [x] manifest 钉 dsh-coding-kit 1.5.1；升级产物入库（manifest 已钉；入库待 00 统一 commit）
- [x] local 块零手恢复（diff 证明 · 见自检与 FEEDBACK §4）
- [x] `npx dsh-coding-kit verify --target .` 跑通（kit 实际命令面：`verify` 须 `--task`；严格态 BLOCKED 于缺 R<n>（20 序内）与 pre-30 invoke hat 10（00 序内）；`--allow-no-review --allow-invoke-gap` 留痕豁免 **PASS exit 0**）；graph-compile.sh 仍绿（exit 0 · harness 面未动）；pytest 无新增失败（3failed/242passed = 基线）
- [x] kit graph 子命令面调查结果记入 task（见自检「graph 子命令面」；供 probe task）
- [x] FEEDBACK 落盘 `docs/harness/evidence/FEEDBACK_dsh_coding_kit_1_5_1_from_ops_desk_api_20260824.md`

---

### 自检结论（执行者 30）

> 30 回填。未执行 git commit 与 task close（00 统一提交 / 验收关账）。

| 项 | 内容 |
|---|---|
| **日期** | 2026-08-24 |
| **manifest** | `1.5.1`（from_version `2.24.0` · preset `fullstack-node-py` 与 ide 原样保留 · kit 沿用 `.cyning-harness/` 约定） |
| **执行路径** | `check` → `refresh-ide-blocks --dry-run` → （stash -u 过 preflight）`refresh-ide-blocks --yes` → `upgrade --yes` → 幂等二跑复检 → `verify` |
| **IDE 块** | AGENTS.md / CLAUDE.md 各 A1×1（`npx @cyning/harness` → `npx dsh-coding-kit`）；备份 `.cyning-harness/backups/refresh-ide-blocks/2026-08-24T15-29-58-404Z/`；二刷 dry-run rewrites=0（幂等） |
| **local 块 diff 证据** | `git diff AGENTS.md CLAUDE.md` 仅上述一行/文件；`cyning-harness-local:begin/end` 块不在 diff 中 = 零字节变化（pre-30 / HG-PILOT / G-L0 / graph_modules_path 关键词完整） |
| **verify** | 严格：BLOCKED exit 2（missing R<n> review · 20 序内）；豁免留痕：PASS exit 0（另暴露 pre-30 invoke 缺 hat 10 · 00 序内补件） |
| **graph-compile.sh** | exit 0（升级前后均绿；产物 diff 仅 generated_at 时间戳；仍指向 @cyning/harness 未动） |
| **pytest** | 3 failed / 242 passed（chat_ws/chat_router 本地缺表基线 · 升级前后一致 · 无新增） |
| **graph 子命令面** | kit 1.5.1 **自带**：`graph yaml compile|check|export`（--graph-id/--target/--input/--output/--all/--no-recursive/--graph-json）+ `graph ingest|snapshot` + `graph axioms check`；graph-compile.sh 现行参数面同形存在，切换=换命令头+等价回归，执行属 probe task（详见 FEEDBACK §7） |
| **CI yml 引用** | `.github/workflows/lint-wiki-delta.yml` L3/33/37 引用 `@cyning/harness@2.22.0`（kit 有同名 `task lint-wiki-delta`）· **只记录未改动** |
| **mdc 滞留** | `.cursor/rules/05-harness-starter.mdc` 无 product marker（refresh 块 0 不刷写）· L19 旧字面滞留 · 记录不动（FEEDBACK K4） |
| **FEEDBACK** | `docs/harness/evidence/FEEDBACK_dsh_coding_kit_1_5_1_from_ops_desk_api_20260824.md` |
| **invoke** | `docs/harness/invokes/by-task/dsh-coding-kit-upgrade-1-5-1/invoke_20260824_30_dsh-coding-kit-upgrade-1-5-1.md` |
| **遗留** | 00：10 invoke 快照 · 20 R<n> 审查 · `.cyning-harness/backups/` 入库/gitignore 决策 · 统一 commit |

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-24 | 初版（00 起草 + 代签闸 · 维护者授权）：harness→kit 1.5.1 过程轨升级；命令面切换留 probe task |
| 2026-08-24 | 30：升级执行完成。kit CLI 面探查：沿用 `.cyning-harness/` 约定；`upgrade` 只重写 manifest（不再 cp prompts/IDE）；IDE 字面迁移走独立 `refresh-ide-blocks`（默认 dry-run · --yes 有脏树 preflight · local 块永不改写）；`verify` 须 `--task` 且新增 R<n>/pre-30 invoke 硬闸（留痕豁免旗标）；kit **自带 graph 子命令面**（`graph yaml compile\|check\|export` + `ingest\|snapshot\|axioms`），graph-compile.sh 参数面同形，切换留 probe task。自检全过（见上节）；FEEDBACK + 30 invoke 落盘；未 commit |
