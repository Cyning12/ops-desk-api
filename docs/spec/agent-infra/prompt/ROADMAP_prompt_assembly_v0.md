# ROADMAP：Prompt · 装配层（H4）

> **层级**：L2 路线（prompt 域 · 波次 H4）  
> **状态**：`active`（task → [`task_prompt_assembly_p1.md`](../../../tasks/active/task_prompt_assembly_p1.md) · H1 CLOSE 后可并行）
> **上游**：[`../02_agent_host_plan_v0.md`](../02_agent_host_plan_v0.md)

---

## 1. 目标

从 `lg_rag` / `chat` / `lc_evidence` 节点抽出 **PromptAssembly**：命名模板、变量绑定、按 `node_role`/`mode` slot 装配；为 H5 Skill `provide` 预留注入点。

### 非目标

- 复制 Agently 全 Prompt slot 系统  
- 把 schema 校验塞进 Prompt 模块  

---

## 2. 交付项

| ID | 内容 | 验收 |
|---|---|---|
| H4-a | `app/ops/prompts/` 包 + 加载 API（如 `render(template_id, vars, slots=…)`） | 单测 |
| H4-b | 迁移 supervisor/router 等 1–2 个节点 off 硬编码 | 行为不回归 |
| H4-c | 版本/id 字段（文件路径或 semver 字符串） | 文档 |
| H4-d | CORRECTION 文案模板可配置（SO 调用方注入，非 SO 内核） | 可选 |

---

## 3. 建议 task

- **slug**：`prompt-assembly-p1`  
- **可与 H2 尾穿插**（无硬依赖 H3）

---

## 4. 修订记录

| 日期 | 说明 |
|---|---|
| 2026-08-27 | 初版 H4 条文 |
