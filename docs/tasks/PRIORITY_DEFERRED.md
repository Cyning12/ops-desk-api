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
| DEF-001 | Langfuse SDK / 项目 v4 迁移 | [`docs/spec/langfuse-sdk-v4-migration/SPEC-langfuse-sdk-v4-migration_v1.md`](../spec/langfuse-sdk-v4-migration/SPEC-langfuse-sdk-v4-migration_v1.md) | Cloud 双轨至 **2026-11-16**；现 SDK 3.15 仍可用；**无需**升 Python；当前焦点在 RAG/Agent，观测非本周 P0 | ① 维护者令开工 ② **≥2026-10-01** 仍未排期则复评 ③ Migration Assistant / 生产 tracing 异常 | 2026-08-17 |
| DEF-002 | 本地/远程分支与陈旧 task 卫生 | 总轨 `agent-infra-upgrade` 00 invoke（拟 slug `repo-branch-task-hygiene`） | 当前焦点在 agent-infra 升级实现；无效分支/task 过多但不挡本轨 | ① `agent-infra-upgrade` 波次 1–3 验收完成 ② 维护者令开工 | 2026-08-26 |
| DEF-003 | Grader 混档证据（exact+relevant）作答约束 | [`docs/tasks/deferred/task_rag_answer_mixed_evidence.md`](./deferred/task_rag_answer_mixed_evidence.md) | 探讨未选型；占 active 使每次 00 勿混改成本高；Eval E0/E1 排在 sync + 真实 capability 之后 | ① 维护者令拉回 active ② `ops-pg-lookup-capabilities` 与 `ops-sync-sender-migration` 均 CLOSE 后复评 | 2026-08-28 |
| DEF-004 | 检索层长自然语言 query 零命中分析 | [`docs/tasks/deferred/task_retrieval_longquery_analysis.md`](./deferred/task_retrieval_longquery_analysis.md) | 分析型未开工；E2 金标会再暴露长句零命中；不占 active | ① 维护者令拉回 ② Eval E2 金标立项时并入或单开 | 2026-08-28 |
| DEF-005 | memory-facts 真实构建（memory-injection 结局 ④a 扩展接线） | [`docs/tasks/deferred/task_memory_facts_build_4a.md`](./deferred/task_memory_facts_build_4a.md) | 2026-10-20 维护者裁定当前走 ④b（收窄+休眠）；④a=真实构建 memory-facts 之时另行开工，开工前须先做遗留问题分析（对接文档 §清单 8 条） | ① 维护者令「真实构建 memory-facts」开工 ② 遗留问题分析完成并经 10-spec 立项 | 2026-10-20 |

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
| 2026-08-28 | DEF-003 / DEF-004：两条 RAG 草案迁出 active（维护者令）；active 仅留 sync sender |
| 2026-10-20 | DEF-005：memory-facts 真实构建（④a）登记对接文档（维护者裁定 #2 走 ④b · 同示未来 ④a 开工前先分析遗留问题） |
