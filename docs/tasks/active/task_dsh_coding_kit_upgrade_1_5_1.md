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

- [ ] manifest 钉 dsh-coding-kit 1.5.1；升级产物入库
- [ ] local 块零手恢复（diff 证明）
- [ ] `npx dsh-coding-kit verify --target .` 跑通；graph-compile.sh 仍绿；pytest 无新增失败
- [ ] kit graph 子命令面调查结果记入 task（供 probe task）
- [ ] 若升级过程有出入：FEEDBACK 落盘 `docs/harness/evidence/FEEDBACK_dsh_coding_kit_1_5_1_from_ops_desk_api_20260824.md`

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-24 | 初版（00 起草 + 代签闸 · 维护者授权）：harness→kit 1.5.1 过程轨升级；命令面切换留 probe task |
