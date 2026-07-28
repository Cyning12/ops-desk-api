# Task：补齐 tech-graph GitHub CI（api）

> **状态**：completed  
> **类型**：基础设施（CI）  
> **关联**：`.github/workflows/` · AGENTS Verify / graph-compile · web 金样对齐

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `api-tech-graph-ci` |
| **git_branch** | `task/api-tech-graph-ci` |
| **graph_change_layer** | `none` |
| **review_hat** | `20` |
| **thinking_profile** | `shortest` |
| **invoke_retention_profile** | `minimal` |
| **required_invoke_hats** | `30` |
| **test_strategy** | `recommended` |
| **test_strategy_note** | 本地/CI：`./scripts/graph-compile.sh`；pytest 仅核对触发分支与默认分支一致，不强制本棒全量跑 |
| **code_quality_bar** | `not_applicable` |
| **orchestration** | 单 task；00 代签双闸（基础设施惯例） |

| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 本仓未启用 WikiTrack |
### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| **HG-GRAPH-MODULES** | approved | **30** | 00 代签：仅加 CI；不改业务模块边界 / 图谱正文 |
| HG-TASK-DRAFT | approved | 22-R1 | 维护者下发 30 Prompt：补 tech-graph CI + 核对 pytest 分支 |
| **HG-AUDIT-R1** | approved | **30** | 00 代签：基础设施 CI；无业务 Python 改码 / 无强制 pre-commit |

---

## 背景与目标

web 已补 `.github/workflows/ci.yml` + `tech-graph.yml`；api 仅有 `pytest.yml`，缺图谱门禁。`AGENTS.md` 要求 PR 前 `./scripts/graph-compile.sh` 绿，须 CI 对齐。

**完成态**：

- [x] `.github/workflows/tech-graph.yml`：setup-node（`package-manager-cache: false`）+ PyYAML + `./scripts/graph-compile.sh`
- [x] 触发：`pull_request` + `push` → 默认分支 `master`
- [x] 核对 `pytest.yml` 触发分支与远程默认分支一致（已是 `master`，未改）
- [x] manifest 已是 `2.16.1` → 跳过 upgrade
- [x] invoke + R1 + 冒烟

**不做**：改 web/ios；回灌 cyning-harness；业务 Python；强制 pre-commit；P3b

---

## 失败路径

| 触发 | 行为 | 可重试 |
|---|---|---|
| graph-compile 本地非 0 | 修 yaml/脚本或报告阻塞，不顺手大改业务 | 是 |
| harness status --check 缺 R1 | 先落 R1 + 签闸再跑 | 是 |
| CI Node 误开 pnpm cache | 保持 `package-manager-cache: false` | 是 |

---

## 验收标准

- [x] `tech-graph.yml` 存在且与 web 金样同构（分支为 `master`）
- [x] 本地 `./scripts/graph-compile.sh` exit 0
- [x] `npx @cyning/harness status --target . --task <task> --check` exit 0
- [x] PR 已开（本棒默认）

---

### 自检结论（执行者）

| 项 | 内容 |
|---|---|
| **日期** | 2026-07-27 |
| **upgrade** | 跳过（manifest 已 `2.16.1`） |
| **tech-graph** | `.github/workflows/tech-graph.yml` · push/PR → `master` |
| **pytest 分支** | 已是 `master`，未改 |
| **graph-compile** | exit 0（生成物仅 timestamp，未纳入 commit） |
| **verify / status --check** | 均 exit 0 · `may_start_30=true` |
| **pytest** | 本地 `87 passed`（1 warning） |
| **结果** | CI + task/R1/invoke 落盘；开 PR |
