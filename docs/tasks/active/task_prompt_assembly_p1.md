# Task：Agent Host H4 · Prompt 装配层（P1）

> **状态**：active（draft · 可与 H2 尾并行 · **不依赖 H3**）  
> **类型**：feature / agent-host-plan · H4  
> **上游规划**：`docs/spec/agent-infra/02_agent_host_plan_v0.md`  
> **ROADMAP**：`docs/spec/agent-infra/prompt/ROADMAP_prompt_assembly_v0.md`  
> **分支**：`task/prompt-assembly-p1`  
> **建议开工**：H1 CLOSE 后（避免与 H1 prompt 注入冲突）

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `prompt-assembly-p1` |
| **git_branch** | `task/prompt-assembly-p1` |
| **test_strategy** | `required` |
| **test_strategy_note** | `render()` 单测；迁移 1–2 节点 off 硬编码；行为不回归 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `n/a`（或 G-L1 备注 `prompt` 模块 POINTER · 00 定夺） |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,30` |
| **orchestration** | agent-host-plan 第四棒 = H4 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | pending | 22-R1 | |
| HG-AUDIT-R1 | pending | 30 | |
| HG-GRAPH-MODULES | approved | 30 | 若仅新包无一级模块行则 n/a |

---

## 背景与目标

建立 `app/ops/prompts/`：**模板 + 变量 + slot 装配**；从 lg_rag/chat 抽离硬编码 system；为 H5 Skill `provide` 预留注入点。

---

## 范围 / 非范围

**范围**：

- H4-a：`app/ops/prompts/` + `render(template_id, vars, slots=…)`
- H4-b：迁移 supervisor 和/或 router 至少 1 个节点
- H4-c：模板 version/id 字段
- H4-d（可选）：SO CORRECTION 文案模板位（调用方注入）

**非范围**：Agently 全 slot 系统 · schema 校验进 Prompt 包 · 改 chat/graph 拓扑

---

## 验收标准

- [ ] render API + 单测
- [ ] ≥1 节点迁移后 multi/router 单测不回归
- [ ] 模板 id/version 文档
- [ ] ruff / pytest 绿

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-27 | 00 拆 task |
