# Task：Agent Host H5 · Skill Registry（P0）

> **状态**：active（draft · **阻塞**：H4 CLOSE）  
> **类型**：feature / agent-host-plan · H5  
> **上游规划**：`docs/spec/agent-infra/02_agent_host_plan_v0.md`  
> **ROADMAP**：`docs/spec/agent-infra/skill/ROADMAP_skill_registry_v0.md`  
> **GUIDE**：`docs/guides/GUIDE_capability-gateway-p3-skill-boundary_v0.md`  
> **分支**：`task/skill-registry-p0`  
> **前置 task**：`task_prompt_assembly_p1` CLOSE（provide → Prompt slot）

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `skill-registry-p0` |
| **git_branch** | `task/skill-registry-p0` |
| **test_strategy** | `required` |
| **test_strategy_note** | manifest/索引单测；match stub；provide 集成 mock；不执行 SKILL.md 解释器 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1`（可选 capability/lg_rag 备注） |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,30` |
| **orchestration** | agent-host-plan 第五棒 = H5 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | pending | 22-R1 | |
| HG-AUDIT-R1 | pending | 30 | |
| HG-GRAPH-MODULES | approved | 30 | 不新增一级模块（Registry 为子模块） |

---

## 背景与目标

**SkillRegistry**：元数据索引 + NL 匹配（v0 关键词/mock embed）→ `capability.provide(skill_id)` → PromptAssembly slot。入口三态：显式 / planner 结构化 / NL 匹配。

---

## 范围 / 非范围

**范围**：

- H5-a：索引 `docs/skills` 或 manifest（id · description · triggers）
- H5-b：`match(query, top_k)` stub
- H5-c：匹配后 provide → Prompt slot（依赖 H4）
- H5-d：与 `kind=skill` stub id 命名对齐

**非范围**：完整 Skill 执行引擎 · 模型可选跳过 SO · 替代 Capability invoke

---

## 验收标准

- [ ] 索引 + match 单测
- [ ] provide 集成 mock（不读整份 SKILL.md 执行）
- [ ] 与 GUIDE 划界一致
- [ ] ruff / pytest 绿

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-27 | 00 拆 task · 依赖 H4 |
