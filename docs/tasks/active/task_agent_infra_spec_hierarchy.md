# Task：Agent Infra · SPEC 文档分层（L0/L1/L2）

> **状态**：active（闸已签 · 待 PR 合入后关账）  
> **类型**：docs-only / agent-infra 过程轨  
> **总轨**：`agent-infra-upgrade`（波次 0 · 实现前置）  
> **分支**：`docs/agent-infra-spec-hierarchy`  
> **上游**：`docs/discussions/2026-08-26_lg-rag-agent-capability-architecture.md`  
> **无关**：勿与 `ops-sync-sender-migration` / `rag-answer-mixed-evidence` / `retrieval-longquery-analysis` 混改；**禁止**改 `app/` / `tests/`。

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `agent-infra-spec-hierarchy` |
| **git_branch** | `docs/agent-infra-spec-hierarchy` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `recommended` |
| **test_strategy_note** | 无 pytest 义务；核对目录树与 POINTER 可读；`npx dsh-coding-kit verify --task` PASS |
| **code_quality_bar** | `not_applicable` |
| **graph_change_layer** | `none` |
| **graph_delta** | `none` |
| **graph_delta_note** | 纯文档分层；不改 `docs/_tech_graph/` |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 本波不晋升 WikiTrack |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,30` |
| **invoke_retention_profile** | `default` |
| **freeze_id** | 无 |
| **close_pr_policy** | `required` |
| **orchestration** | 总轨波次 0；合入后开 `cap-portable-core` |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | 2026-08-26 00 代签 · 维护者 Prompt 授权（选 A · 开工） |
| HG-AUDIT-R1 | approved | 30 | 2026-08-26 00 代签；`docs/harness/reviews/task_agent_infra_spec_hierarchy_audit_R1_20260826.md` |
| HG-GRAPH-MODULES | approved | 30 | graph_change_layer=none；不挡图谱 |

---

## 背景与目标

把 `docs/spec/agent-infra/` 收成可读分层：L0 总纲/架构/升级总表；L1 域夹；L2 现行 SPEC + ROADMAP；旧 SPEC 路径改 POINTER。为后续 `cap-portable-core` / `so-schema-hygiene` / `cap-mcp-real` 提供稳定读序真值。

---

## 范围 / 非范围

**范围**：

- L0：`README.md` · `00_architecture_and_boundaries.md` · `01_upgrade_roadmap.md`
- L1/L2：`capability/` · `structured-output/`（README · SPEC 迁入 · ROADMAP）
- 根级旧 `SPEC-*_v0.md` → POINTER
- 索引/讨论/DESIGN 链更新（`docs/spec/README.md` 等）
- 可选：`PROMPT_00_agent-infra-upgrade.md` 入仓

**非范围**：

- 任何 `app/` / `tests/` 实现
- 升 SPEC `_v1` / 重签 v0（`HG-SPEC-SIGNOFF` 不要求）
- 波次 1–4 业务改码
- 清理本地/远程分支（总轨收官后另开 `repo-branch-task-hygiene`）

---

## 验收标准

- [ ] 目录树符合 `docs/spec/agent-infra/README.md` 所示分层
- [ ] 两份根 POINTER 指向域夹 SPEC；域夹 SPEC 正文完整（非空壳）
- [ ] `01_upgrade_roadmap` 钉死顺序 1→2→3（4 可选）可读
- [ ] 无 `app/` / `tests/` / `docs/_tech_graph/` 业务 diff
- [ ] PR 开出并（维护者）合入 master 后可关账

---

## failure_paths

| 触发 | 行为 | 可重试 |
|---|---|---|
| 误带 `app/` 进 PR | 从 PR 剔除后重推 | Y |
| POINTER 断链 | 修相对路径后重 lint 读序 | Y |
| 与无关 active task 混 commit | 打回；只留 agent-infra docs | N |

---

## 依赖

- `docs/spec/agent-infra/01_upgrade_roadmap.md`
- 总轨 Prompt：`docs/harness/invokes/by-task/_prompts/PROMPT_00_agent-infra-upgrade.md`

---

## 给执行帽必读

本 task · agent-infra README 读序 · 00 派发计划（总轨 invoke）

> **执行说明**：本波 docs-only；由 **00 代执行落地**（commit/PR），不派业务 30。

---

## 思考轮

### 思考轮控制

| 字段 | 值 |
|---|---|
| **actual_last_round** | R3 |
| **early_stop** | yes |
| **early_stop_reason** | docs-only 分层边界清晰；无实现歧义 |
| **residual_risks** | 旧链未更新的外部引用仍依赖 POINTER；合入前勿开实现枝抢写路径 |

### R0
先合文档分层（方案 A），再开 portable-core。

### R1
旧 SPEC 路径保留 POINTER，避免断链。

### R2
ROADMAP 与 v0 SPEC 分离，不污染已签契约。

### R3
分支清理另 task，本波不碰。

### R4
（提前停 · 未开）

### R5
（提前停 · 未开）

---

### 自检结论

> 2026-08-26 · 00 代执行 docs 落地 · **过程 PASS（待 PR merge 关账）**

- [x] 分层目录与 POINTER 已提交
- [x] task lint PASS · verify PASS
- [x] 无 `app/` / `tests/` diff
- [x] PR [#65](https://github.com/Cyning12/ops-desk-api/pull/65) 已开（待维护者合入）

**50 结论**：docs 波次可合入；合入后关账并开 `cap-portable-core`

---

## 修订记录

| 日期 | 说明 |
|---|---|
| 2026-08-26 | 10 起草；00 代签双闸；方案 A 开工 |
