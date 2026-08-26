# Task 优先级：暂不排期（PRIORITY_DEFERRED）

> **用途**：记录「已知、有 SPEC/盘点，但 **当前不建 active task、不驱动 30**」的项。  
> **不是** Harness 硬闸；是维护者排期指引，避免会话里被「官方 Prompt / 截止日」自动拉高优先级。  
> **纪律**：条目进本表 ≠ 永久不做；满足 **Revisit 触发器** 后再开 `docs/tasks/active/task_*.md`。

---

## 怎么用

| 动作 | 规则 |
|---|---|
| 新发现「可做但非当前焦点」 | 先写 SPEC 或盘点笔记 → **加一行本表** → **不要**落 `active/task_*.md` |
| Agent / 会话 | 读到本表条目时：**拒开工**；可更新 SPEC 正文，勿擅自开 task |
| 启动 | 维护者删除或改写本表对应行，并显式下令「开 task」后再走 00/10 |

---

## 暂不排期清单

| ID | 主题 | 文档 | 暂不搞的理由 | Revisit 触发器 | 登记日 |
|---|---|---|---|---|---|
| DEF-001 | Langfuse SDK / 项目 v4 迁移 | [`docs/spec/SPEC-langfuse-sdk-v4-migration_v1.md`](../spec/SPEC-langfuse-sdk-v4-migration_v1.md) | Cloud 双轨至 **2026-11-16**；现 SDK 3.15 仍可用；**无需**升 Python；当前焦点在 RAG/Agent，观测非本周 P0 | ① 维护者令开工 ② **≥2026-10-01** 仍未排期则复评 ③ Migration Assistant / 生产 tracing 异常 | 2026-08-17 |
| DEF-002 | 本地/远程分支与陈旧 task 卫生 | 总轨 `agent-infra-upgrade` 00 invoke（拟 slug `repo-branch-task-hygiene`） | 当前焦点在 agent-infra 升级实现；无效分支/task 过多但不挡本轨 | ① `agent-infra-upgrade` 波次 1–3 验收完成 ② 维护者令开工 | 2026-08-26 |

---

## 明确排除（勿误读为本表）

- 已在 `docs/tasks/active/` 的 task：以 active 闸表为准，**不受**本表「暂不搞」保护。  
- 紧急生产故障（tracing 全挂、密钥轮换等）：走 `fix/` + 补 task，不经本表拖延。

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-17 | 首版；登记 DEF-001 Langfuse v4 |
| 2026-08-26 | 登记 DEF-002：agent-infra 收官后清理分支/陈旧 task |
