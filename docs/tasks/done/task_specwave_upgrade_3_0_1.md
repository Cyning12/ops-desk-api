# Task：spec-wave 升级 3.0.1（3.0.0 → 3.0.1 · patch · 过程轨）

> **状态**：`done`（2026-09-23 · 钉版四面齐 3.0.1 · 机械闸全绿：check 零 WARN / verify PASS / lint-wiki-delta PASS / graph-compile exit 0 / pytest 32 passed · FEEDBACK F-1~F-4 落盘 · PR #172 合并 master · CLOSE 归档 done/）  
> **类型**：基础设施 / harness 过程轨升级（patch · 默认路径零破坏）  
> **前置**：manifest / package 钉 `3.0.0`（`task_specwave_upgrade_3_0_0` done · PR #139）；npm 最新 **`3.0.1`**  
> **分支**：`task/specwave-3-0-1`（base：`origin/master` 6ddd9c7 · 与 agent-host-framework-alignment 分支隔离）  
> **执行模式**：过程轨；**不改** `app/` 业务逻辑（宿主向量已是 `spec-wave@{_kit_pin()}` env 钉版）

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `specwave-upgrade-3-0-1` |
| **git_branch** | `task/specwave-3-0-1`（base：`origin/master`） |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | `node_modules/.bin/spec-wave check --target .` 零 WARN；`--version` = 3.0.1；`verify --task` 本 task PASS；`./scripts/graph-compile.sh` exit 0；`pytest tests/test_capability_harness_cli.py` PASS（mock 钉 `spec-wave@3.0.1`）；CI `lint-wiki-delta.yml` 钉 `spec-wave@3.0.1` |
| **code_quality_bar** | `not_applicable` |
| **graph_change_layer** | `none` |
| **graph_delta** | `none` |
| **graph_delta_note** | 过程轨升级；compile 产物可能因 kit 变化改写，不改 YAML 源 |
| **wiki_delta** | `none` |
| **wiki_delta_note** | 本波不晋升 coding_wiki；FEEDBACK 走 evidence（含长程任务反馈内容） |
| **experience_capture** | `recommended` |
| **kpi_aggregator** | `CLOSE` |
| **invoke_retention_profile** | `minimal` |
| **required_invoke_hats** | `30` |
| **close_pr_policy** | `required`（维护者定夺推送/PR 时机） |
| **review_hat** | `20` |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | approved | 20-R1, 30 | 2026-09-23 · 维护者本窗直令开工（「先更新 specwave 版本」· 承 specwave-3-0-0 先例 00 代签） |
| HG-AUDIT-R1 | approved | 30 | 2026-09-23 · patch 升级无业务面；维护者本窗授权（同令覆盖） |

---

## 背景与目标

本仓 spec-wave 钉 **3.0.0**。npm 最新 **3.0.1**（patch · 2026-09-18）。npm diff 3.0.0→3.0.1 增量：

| 主题 | 增量 |
|------|------|
| cli-pins | `readTruthVersion` 收敛 existsSync↔read TOCTOU；package.json 不可解析/不可读独立文案（exit 2 语义不变） |
| cli-shared | `parseHumanGates` 新增 options.warnings：### 人工闸 节存在但解析 0 行 → 显式告警（**不改 exit / may_start_30**） |
| cli-host / host | sticky 增 `buildTableSourceForSticky` 导出；host cmd 调整 |

目标：package/manifest/CI/tests 全面钉齐 **spec-wave@3.0.1**，check/verify/compile/pytest 全绿，FEEDBACK（含长程任务反馈）落盘。

## 范围

1. `package.json` exact → `3.0.1`；`npm install`；lock 对齐。
2. `npx spec-wave upgrade --yes`：manifest `version` → 3.0.1、`from_version` = 3.0.0。
3. `sync prompts` dry-run 审清单（本波预期 skip 全量 + TASK_TEMPLATE 仓内定制 conflict 保留 · 拒 `--force`）。
4. CI `.github/workflows/lint-wiki-delta.yml` 三处 `@3.0.0` → `@3.0.1`。
5. `tests/test_capability_harness_cli.py` 全部 3.0.0 字面 → 3.0.1（16 处 · 含非法注入用例版本段）。
6. **确认** `app/ops/capability/harness_cli.py` 仍为 `spec-wave@{_kit_pin()}`（**不改**）；`scripts/graph-compile.sh` 默认 GRAPH_CLI=spec-wave（仅验收）。
7. 机械闸：check / verify --task / graph-compile.sh / pytest test_capability_harness_cli.py 全绿。
8. FEEDBACK 落盘 `docs/harness/evidence/FEEDBACK_spec_wave_3_0_1_from_ops_desk_api_20260923.md`（含长程任务反馈：词汇登记档告警噪音 · 图谱漂移检测诉求 · 消费侧钉版散落 · pins 真值源假定）。

## 非范围

- `app/` 任何业务逻辑改动（含 harness_cli.py 本体）
- 自定义 host-adapt 表迁移（仓内无强制自定义表义务 · 承 3.0.0 裁定）
- 推送 / PR（维护者定夺时机）

## failure_paths

| 路径 | 处置 |
|---|---|
| `upgrade --yes` 冲掉仓内定制（manifest 异常 / prompts 被改写） | STOP · dry-run 对照包内 assets · 手合 + FEEDBACK（拒 `--force`） |
| `sync prompts` 出现 HG-GRAPH-MODULES 等仓内定制被覆盖 | STOP · 保留仓内版 + FEEDBACK |
| graph-compile 产物因 kit 变化出现意外 diff | 审 diff · 仅生成物变化可接受；YAML 源被改 → 回退 |
| pytest mock 钉版漏改（3.0.0 残留） | grep `3\.0\.0` 全测试文件清零后重跑 |

## 验收标准

- [x] `spec-wave --version` = 3.0.1；manifest version=3.0.1 / from_version=3.0.0。
- [x] `check --target .` 零新增 WARN（「已是最新」）；`verify --task` 本 task PASS（exit 0 · 2026-09-23）。
- [x] `./scripts/graph-compile.sh` exit 0（compile + check + normalize guard · 2026-09-23；生成噪音 graph.json freeze_id 日期跳变已回退）。
- [x] `pytest tests/test_capability_harness_cli.py` 全绿（32 passed · mock 钉 3.0.1 · .venv）。
- [x] CI yml 三处钉 3.0.1；测试文件零 3.0.0 残留。
- [x] FEEDBACK 文档落盘 `docs/harness/evidence/FEEDBACK_spec_wave_3_0_1_from_ops_desk_api_20260923.md`（含长程任务反馈 F-1~F-4）。

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|----|------|------------|----------------------|----------------|
| R0 | patch 升级 + 长程任务反馈落盘；零业务面 | no | — | none |
| R1 | 钉版四面 = package/lock · manifest · CI 3 处 · 测试 16 处；harness_cli env 钉版不改本体 | no | — | 测试字面漏改由 grep 清零兜底 |
| R2 | HG-TASK-DRAFT / HG-AUDIT-R1 维护者令 approved；机械闸 check/verify/compile/pytest | no | — | none |
| R3 | 单 task 直通；FEEDBACK 随本 task 落盘 evidence/ | yes | 范围已框死在 R1 四面 + FEEDBACK | 无 |
| R4 | （未开） | — | early_stop at R3 | — |
| R5 | （未开） | — | early_stop at R3 | — |

**actual_last_round**：R3 · **early_stop**：yes · **residual_risks**：见 R1

### R0 · 问题框定

patch 升级（3.0.0→3.0.1）+ 长程任务反馈落盘；零业务面、零图谱源改动。

### R1 · 升级面枚举

钉版四面：package.json exact + lock · .coding-kit/manifest.json · CI lint-wiki-delta.yml 3 处 · tests/test_capability_harness_cli.py 16 处；harness_cli 为 env 钉版（DSH_CODING_KIT_VERSION）不改本体。

### R2 · 闸

HG-TASK-DRAFT / HG-AUDIT-R1 维护者本窗令 approved（承 specwave-3-0-0 先例 00 代签）；机械闸 check / verify --task / graph-compile.sh / pytest。

### R3 · 粒度

单 task 直通；FEEDBACK 随本 task 落盘 evidence/（含长程任务反馈四项）。

### R4 ·（未开 · early_stop）

### R5 ·（未开 · early_stop）

### 自检结论（执行者）

- 钉版四面（package/lock · manifest · CI · tests）全部对齐 3.0.1；`app/` 零改动。
- `sync prompts` dry-run：11 skip + 1 conflict（TASK_TEMPLATE 仓内定制保留 · 未覆盖）——零 prompt 增量。
- 机械闸结果见验收勾选项与 FEEDBACK。
