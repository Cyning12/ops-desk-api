# Task：dsh-coding-kit 升级 1.5.2（patch 升级 + FEEDBACK 项修复核对）

> **状态**：active（闸已签 · 00 代签授权）  
> **类型**：基础设施 / harness 过程轨升级（patch）  
> **前置**：`task_dsh_coding_kit_upgrade_1_5_1`（已入 master）；FEEDBACK 已反哺 D1–D3 / R6  
> **关联**：`docs/harness/evidence/FEEDBACK_dsh_kit_1_5_1_mermaid_from_ops_desk_api_20260824.md` §6（D1 export 丢 label / D2 graph_id 命名空间 / D3 check-export 不互认 / R6 class 按 kind）  
> **分支**：`task/dsh-coding-kit-1-5-2`  
> **执行模式**：00 编排/验收；30 子 agent 执行

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `dsh-coding-kit-upgrade-1-5-2` |
| **git_branch** | `task/dsh-coding-kit-1-5-2` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 升级后：`npx dsh-coding-kit verify --target . --task <本task>` 跑通；`./scripts/graph-compile.sh` exit 0；pytest 无新增失败 |
| **code_quality_bar** | `not_applicable` |
| **graph_change_layer** | `none` |
| **wiki_delta** | `n/a` |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,30` |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | 2026-08-24 00 代签（维护者直接指令「更新 dsh_kit 到 1.5.2」+ 本窗授权） |
| HG-AUDIT-R1 | approved | 30 | 2026-08-24 00 代签（patch 升级，1.5.1 路径刚验证过） |

---

## 范围

1. `npm_config_cache=/tmp/npm-cache-lg npx --yes dsh-coding-kit@1.5.2` 按 1.5.1 已验证路径升级（check → refresh-ide-blocks → upgrade → 幂等复检）；local 块零手恢复复检。
2. **FEEDBACK 项修复核对**：实读 1.5.2 包源码，逐项判定 D1 / D2 / D3 / R6（class 按 kind）修复状态（已修/未修/部分 + 证据行号）；若有修复，**不切命令面**（切换仍须维护者另签），只更新结论。
3. 升级有出入 → FEEDBACK 落盘 `docs/harness/evidence/FEEDBACK_dsh_coding_kit_1_5_2_from_ops_desk_api_20260824.md`（无出入则免，修订行注明）。

## 非范围

- graph-compile.sh / CI 命令面切换
- 业务代码、图谱语义

## 验收标准

- [ ] manifest 钉 1.5.2；local 块零字节变化（diff 证据）
- [ ] verify / graph-compile / pytest 三项跑通（基线一致）
- [ ] D1/D2/D3/R6 修复状态结论表（含证据）记入 task 自检
- [ ] 有出入时 FEEDBACK 落盘

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-24 | 初版（00 起草 + 代签闸 · 维护者授权）：1.5.1→1.5.2 patch；附 FEEDBACK 项修复核对 |
