# ROADMAP：Skill · Registry 与 NL 匹配（H5）

> **层级**：L2 路线（skill 域 · 波次 H5）  
> **状态**：`active`（task → [`task_skill_registry_p0.md`](../../../tasks/active/task_skill_registry_p0.md) · 阻塞 H4 CLOSE）
> **上游**：[`../02_agent_host_plan_v0.md`](../02_agent_host_plan_v0.md) · 建议 H4 后

---

## 1. 目标

建立 **SkillRegistry**：从 `docs/skills` 与/或注册表读元数据（id · description · triggers）；支持 **NL 匹配**（v0 可用关键词/embedding mock）→ `capability.provide(skill_id)` 注入 Prompt；**不**执行 SKILL.md 全文解释器。

### 非目标

- 完整 Skill 执行引擎  
- 模型自选是否走 SO 校验  
- 替代 Capability 执行面  

---

## 2. 入口三态（规划钉死）

| 入口 | 说明 |
|---|---|
| 显式 | 人/配置/harness 指定 `skill_id` |
| Planner 结构化 | plan 字段引用 skill_id（同 tool 校验思路） |
| NL 匹配 | `match(query) → [skill_id…]` → provide |

---

## 3. 交付项

| ID | 内容 | 验收 |
|---|---|---|
| H5-a | Skill 元数据索引（扫描 docs/skills 或手工 manifest） | 单测 |
| H5-b | `match(query, top_k)` stub（关键词或 mock embed） | 单测 |
| H5-c | 匹配后 `provide` → PromptAssembly slot（依赖 H4） | 集成 mock |
| H5-d | 与 `kind=skill` stub 对齐 id 命名 | GUIDE 一致 |

---

## 4. 建议 task

- **slug**：`skill-registry-p0`  
- **依赖**：H4 PromptAssembly 推荐先完成

---

## 5. 修订记录

| 日期 | 说明 |
|---|---|
| 2026-08-27 | 初版 H5 条文 |
