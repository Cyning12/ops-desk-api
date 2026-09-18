# Task：spec-wave 升级 3.0.0（2.4.2 → 3.0.0 · major · 过程轨）

> **状态**：in_progress  
> **类型**：基础设施 / harness 过程轨升级（major：适配表 schema v1→v2 **可选**；默认路径零破坏）  
> **前置**：manifest / package 钉 `2.4.2`（`task_specwave_upgrade_2_4_2` done · PR #136）；npm 最新 **`3.0.0`**  
> **分支**：`task/specwave-3-0-0`（**从 origin/master 切** · 独立 worktree，与主仓 budget 脏树隔离）  
> **执行模式**：Open Folder = 本 worktree / 仓根；过程轨；**不改** `app/` 业务逻辑（宿主向量已是 `spec-wave@{_kit_pin()}`）

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `specwave-upgrade-3-0-0` |
| **git_branch** | `task/specwave-3-0-0`（base：`origin/master`） |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | `node_modules/.bin/spec-wave check --target .` 已是最新零 WARN；`--version` = 3.0.0；`verify --task` 本 task PASS；`./scripts/graph-compile.sh` exit 0；`pytest tests/test_capability_harness_cli.py` PASS（mock 钉 `spec-wave@3.0.0`）；CI `lint-wiki-delta.yml` 钉 `spec-wave@3.0.0` |
| **code_quality_bar** | `not_applicable` |
| **graph_change_layer** | `none` |
| **graph_delta** | `none` |
| **graph_delta_note** | 过程轨升级；compile 产物可能因 kit 变化改写，不改 YAML 源 |
| **wiki_delta** | `none` |
| **wiki_delta_note** | 本波不晋升 coding_wiki；FEEDBACK 走 evidence + doc-health/feedback |
| **experience_capture** | `recommended` |
| **kpi_aggregator** | `CLOSE` |
| **invoke_retention_profile** | `minimal` |
| **required_invoke_hats** | `30` |
| **close_pr_policy** | `required` |
| **review_hat** | `20` |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | approved | 20-R1, 30 | 2026-09-18 · 维护者授权 00 代签全部过程文档（见 invoke open） |
| HG-AUDIT-R1 | approved | 30 | 20-task-audit R1 PASS-WITH-NOTES（`reviews/task_specwave_upgrade_3_0_0_audit_R1_20260918.md`）· 2026-09-18 维护者授权 00 代签 |

---

## 背景与目标

本仓 spec-wave 钉 **2.4.2**（`package.json` exact + `.coding-kit/manifest.json`）。npm 最新 **3.0.0**（major）。上游包内 `MIGRATION.md` 最短路径：钉 `spec-wave@3.0.0` → `npx spec-wave upgrade --yes` → CI/脚本字面 →（推荐）`refresh-ide-blocks` / `skills install` / `sync prompts`。

### 2.4.2 → 3.0.0 关键增量（解包 3.0.0 包内 `MIGRATION.md` 定稿节）

| 主题 | 增量 |
|------|------|
| major 声明 | 架构跃迁：适配表 schema v1→v2 **可选**；门禁随包内置；多宿主物化 |
| 默认路径 | **什么都不用做**于自定义适配表：仅用内置宿主时 `host validate/apply/update` 行为不变；旧格式表（无 `schema_version`）按 v1 继续可读 |
| 可选迁移 | 自定义表作者欲用新能力时：加 `schema_version: 2` + 根级 `command_sets` 等（见包内 MIGRATION「2.4.2 → 3.0.0」节） |
| 本仓裁定 | **不**迁移自定义 host-adapt 表（仓内无强制自定义表义务）；不强制 `host apply --profile expanded` |
| bin 面 | 安装终点仍仅 `spec-wave`；过渡 bin `specgate` / `dsh-coding-kit` 同入口 |

目标：package/manifest/CI/tests 全面钉齐 **spec-wave@3.0.0**，跑通 upgrade + 推荐刷写，check/verify/pytest/compile 全绿。

## 范围

### A. 依赖与 manifest

1. `package.json` `"spec-wave": "2.4.2"` → `"3.0.0"`（**exact**）；`npm install`；`package-lock.json` resolved 对齐 3.0.0
2. `npx spec-wave upgrade --yes`：`.coding-kit/manifest.json` `version` → 3.0.0、`from_version` = 2.4.2；**不删** `.cyning-harness/`

### B. IDE 块与 prompts（推荐步 · 本波收编为必做）

3. `refresh-ide-blocks`（先 dry-run 审报告 → `--yes`）；**`cyning-harness-local` 定制块零改写**
4. `sync prompts --yes`：包内为准；diff 核对；若冲掉 `HG-GRAPH-MODULES` 等仓内定制 → **STOP** 手合 + FEEDBACK（拒 `--force`）
5. `skills install`（`.dsh/skills` · 不入库）

### C. CI / tests 钉版字面

6. **CI** `.github/workflows/lint-wiki-delta.yml`：三处 `spec-wave@2.4.2` → `spec-wave@3.0.0`
7. **测试钉版** `tests/test_capability_harness_cli.py`：所有 `2.4.2` env/argv 字面 → `3.0.0`（含非法注入用例版本段）
8. **确认** `app/ops/capability/harness_cli.py` 仍为 `spec-wave@{_kit_pin()}`（**本波不改**该文件）；`scripts/graph-compile.sh` 默认 `GRAPH_CLI=spec-wave`（已是 · 仅验收）

### D. 验收机械闸

9. `check` / `verify --task` / `graph-compile.sh` / `pytest tests/test_capability_harness_cli.py` 全绿；FEEDBACK 落盘

### E. 新命令体检（偏差不挡）

10. `assets verify --target .` 与 `pins check --target .` 各跑一次留痕

## 非范围

- 不改 `app/` 任何文件（宿主向量已正确；env 名 `DSH_CODING_KIT_VERSION` 保留）
- 不强制自定义适配表 schema v2 迁移；不强制 `host apply` / `host update`（无 sticky 时跳过）
- 不删 `.cyning-harness/`；不清零历史档 `2.4.2` / `dsh-coding-kit` 史实字面（done/reviews/invokes/feedback）
- 不动 `docs/harness/prompts/DAG.md`；不手改 `.cursor/commands/kit-*` 上游资产（偏差走 FEEDBACK）
- 不 `npm publish`；不擅自 `gh pr merge`；代签仅限维护者已授权的过程闸（本波已授权）
- 不以 `--force` 覆盖含仓内定制行的 prompts 本地补丁

## 验收标准

- [ ] `package.json` `"spec-wave": "3.0.0"`（exact）；`package-lock.json` 中 spec-wave `version`/`resolved` = 3.0.0
- [ ] `.coding-kit/manifest.json` `version` = 3.0.0 · `from_version` = 2.4.2
- [ ] `node_modules/.bin/spec-wave --version` 输出 3.0.0
- [ ] `node_modules/.bin/spec-wave check --target .` exit 0 ·「已是最新」· **零 WARN**
- [ ] `refresh-ide-blocks` dry-run 已审并 `--yes`；`git diff AGENTS.md CLAUDE.md` 中 `cyning-harness-local` 块内容零变化
- [ ] `sync prompts` 后：`grep -n "HG-GRAPH-MODULES" docs/harness/prompts/30-execute-code.md` 有命中
- [ ] CI：`grep -c "spec-wave@3.0.0" .github/workflows/lint-wiki-delta.yml` = 3；`grep -n "spec-wave@2.4.2" .github/workflows/` 零命中
- [ ] `grep -n 'spec-wave@{_kit_pin()}' app/ops/capability/harness_cli.py` 命中 1 处（本波未改该文件亦可）
- [ ] `pytest tests/test_capability_harness_cli.py` PASS；测试内无残留 `"2.4.2"` 钉版字面（`grep -n '2\.4\.2' tests/test_capability_harness_cli.py` 零命中）
- [ ] `grep -n 'GRAPH_CLI:-spec-wave' scripts/graph-compile.sh` 命中；`./scripts/graph-compile.sh` exit 0
- [ ] `node_modules/.bin/spec-wave verify --target . --task docs/tasks/active/task_specwave_upgrade_3_0_0.md` PASS
- [ ] `assets verify` / `pins check` 基线结果已留痕（FEEDBACK 或 invoke；偏差不挡）
- [ ] FEEDBACK 落盘 `docs/spec/doc-health/feedback/`

## failure_paths

| ID | 触发 | 行为 |
|----|------|------|
| F-1 | `npm install` 失败 / lockfile 解析异常 | STOP；不重试超过一次；记录 registry 状态入 FEEDBACK |
| F-2 | `upgrade` 未写 `.coding-kit/manifest.json` 或写旧根 | STOP · FEEDBACK kit |
| F-3 | `sync prompts` 冲掉 `HG-GRAPH-MODULES` 等本地补丁行 | 拒 `--force`；STOP 手合保留后 FEEDBACK |
| F-4 | `refresh-ide-blocks` 改写 `cyning-harness-local` 块 | git checkout 回滚该文件 · FEEDBACK kit |
| F-5 | verify 结论机读闸 BLOCKED（审查文缺结论节 / 内容量不足 / 否定词共现） | 退回 20-task-audit 按现行口径补结论节；`--allow-no-review` 仅作留痕豁免不滥用 |
| F-6 | `pytest` 断言漂移（argv/环境变量字面未同步） | 按范围 C-7 逐处对齐；禁改测试语义 |
| F-7 | graph-compile 产物仅戳/格式 diff | 接受并入库（若有） |
| F-8 | `assets verify` / `pins check` 报偏差 | 不挡本波；结果留痕 FEEDBACK |
| F-9 | CI 绿前 PR 被催合 | close_pr_policy=required；不擅自 merge |
| F-10 | 误把自定义适配表强制升 v2 或误跑破坏性 host apply | STOP；本波非范围；回滚相关文件 |

## 依赖

- 前置 task：[`task_specwave_upgrade_2_4_2.md`](../done/task_specwave_upgrade_2_4_2.md)（done · PR #136）
- 上游迁移真值：spec-wave@3.0.0 包内 `MIGRATION.md`（最短路径 + 「2.4.2 → 3.0.0」定稿节）
- 钉版实证面：`package.json` · `.coding-kit/manifest.json` · `.github/workflows/lint-wiki-delta.yml` · `tests/test_capability_harness_cli.py`

## 给执行帽（30）必读

1. 本 task 人工闸表（`HG-AUDIT-R1` **approved 前拒开工**）
2. `docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`（GATE_VERIFY 首输出）
3. spec-wave@3.0.0 包内 `MIGRATION.md`（钉版 → upgrade → 字面 → refresh/skills/sync）
4. **本波不改 `app/`**；仅 CI + tests 钉版字面 + package/manifest + 推荐刷写
5. 工作目录必须是干净分支 `task/specwave-3-0-0`（独立 worktree from master）；勿在含 budget 脏改的主工作区改码
6. verify 结论机读：审查文须含「结论/签收」起首节 + 通过词 + 实质内容 ≥20 字符 + 无否定共现（F-5）

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|----|------|------------|---------------------|----------------|
| R0 | 事实：npm latest=3.0.0；仓钉 2.4.2；MIGRATION 默认路径零破坏、schema v2 可选 → 背景落定 | no | — | — |
| R1 | 钉版面盘点：package/lock/manifest/CI/tests；app 向量已是 spec-wave → 本波零触碰 → 范围 C 收窄 | no | — | — |
| R2 | major breaking 面：仅自定义适配表作者可选迁移；本仓无强制义务 → 非范围锁定 F-10 | no | — | — |
| R3 | refresh/sync 冲突面：local 块零改写 + HG-GRAPH-MODULES 保留验收 → 冲突策略同 2.4.2 波 | no | — | — |
| R4 | 验收机验：version/manifest/CI 计数=3/tests 零残留 2.4.2/verify PASS → 验收标准落定 | no | — | — |
| R5 | 分支隔离：主仓 budget 脏树 → 独立 worktree from master → 执行纪律落定 | yes | 过程轨 major 升级面已钉死、默认路径零破坏、无业务逻辑风险 | ① sync 可能冲本地补丁（F-3）；② assets/pins 新偏差（F-8 不挡）；③ 其他仓仍钉 2.4.2 非本波范围 |

**actual_last_round**：R5 · **early_stop**：yes · **reason（early_stop）**：见 R5 行 · **residual_risks**：见 R5 行

### R0 · 事实框定

npm latest=3.0.0；仓钉 2.4.2；包内 MIGRATION 声明默认路径零破坏。

### R1 · 钉版面

package/lock/manifest/CI/tests 为必改面；`harness_cli.py` 已是 `spec-wave@{_kit_pin()}` → 本波不改 app。

### R2 · breaking 边界

schema v1→v2 可选；本仓不强制自定义表迁移；F-10 锁定误升风险。

### R3 · sync/refresh 冲突

local 块零改写 + `HG-GRAPH-MODULES` 保留；冲补丁则 STOP（F-3/F-4）。

### R4 · 验收锚定

version/manifest/CI 计数=3/tests 零残留 2.4.2/verify PASS 双锚。

### R5 · 分支隔离

独立 worktree from master；不碰主仓 budget 脏树。

- 20-task-audit 认为不足 → 退回 10-task 补轮再审 R+1

### 自检结论

| 命令 | 退出码 |
|------|--------|
| `spec-wave task lint --file docs/tasks/active/task_specwave_upgrade_3_0_0.md` | 0 · LINT: PASS（2026-09-18 · 00 起草后） |

### KPI

_（CLOSE 时回填）_
