# Task：dsh-coding-kit 升级 1.6.1（minor 升级 + FEEDBACK 项修复核对）

> **状态**：active（闸已签 · 00 代签授权）  
> **类型**：基础设施 / harness 过程轨升级（minor）  
> **前置**：1.5.1 / 1.5.2 升级已入 master；FEEDBACK 反哺 D1–D3 / R6 / K7 / K8 在案  
> **关联**：`docs/harness/evidence/FEEDBACK_dsh_coding_kit_1_5_2_from_ops_desk_api_20260824.md`  
> **分支**：`task/dsh-coding-kit-1-6-1`  
> **执行模式**：00 编排/验收；30 子 agent 执行

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `dsh-coding-kit-upgrade-1-6-1` |
| **git_branch** | `task/dsh-coding-kit-1-6-1` |
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
| HG-TASK-DRAFT | approved | 22-R1 | 2026-08-25 00 代签（维护者直接指令「更新 coding-kit 到 1.6.1」+ 本窗授权） |
| HG-AUDIT-R1 | approved | 30 | 2026-08-25 00 代签（升级路径 1.5.1/1.5.2 连续验证过） |

---

## 范围

1. `npm_config_cache=/tmp/npm-cache-lg npx --yes dsh-coding-kit@1.6.1` 按已验证序列升级（check → refresh-ide-blocks → upgrade → 幂等复检）；local 块零手恢复复检。**minor 跳版注意**：先探查 CLI 面有无新增/变更子命令（--help diff 1.5.2 记忆），有破坏性变化须记录并停下报 00。
2. **FEEDBACK 项修复核对**（实读 1.6.1 包源码，证据行号）：D1（export 丢边 label）/ D2（graph_id 命名空间）/ D3（check-export 互认）/ R6（class 按 kind）/ K7（from_version 覆盖）/ K8（freeze_id 日滚动——属本仓产物行为，核对 kit 侧是否提供固定项）；DEF-023 已修三条未回退抽查。
3. 升级有出入 → FEEDBACK 落盘 `docs/harness/evidence/FEEDBACK_dsh_coding_kit_1_6_1_from_ops_desk_api_20260825.md`（无出入修订行注明免落）。

## 非范围

- graph-compile.sh / CI 命令面切换（仍须维护者另签）
- 业务代码、图谱语义

## 验收标准

- [ ] manifest 钉 1.6.1；local 块零字节变化（diff 证据）
- [ ] verify / graph-compile / pytest 三项跑通（基线一致）
- [ ] D1/D2/D3/R6/K7/K8 修复状态结论表（含证据）记入 task 自检；CLI 面变更点记录
- [ ] 有出入时 FEEDBACK 落盘

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-25 | 初版（00 起草 + 代签闸 · 维护者授权）：1.5.2→1.6.1 minor；附 FEEDBACK 项修复核对 |
