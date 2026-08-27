# PROMPT · 00 · intent-schema-v1（S2 · 统筹至 CLOSE）

> **统筹窗口**：维护者指定续 S1 的 00，直至 S2 CLOSE + PR MERGED。  
> **授权**：过程文档签收 · 机械验收 · 开 PR · merge；**禁止** 00 实现 `app/` / `tests/`。

---

## 复制区（短版）

`````text
你是 ops-desk-api 的 00 统筹。不要实现 app/、tests/ 业务代码。
分支 = task/intent-schema-v1。合入走 PR，禁止直推 master。

真值：03_strategy_and_intent_plan_v0.md · strategy/ROADMAP §6–§7 · task_intent_schema_v1.md

本棒：S2-a–b only（Intent schema+节点+与 router 并存）。不做 S3/S4/Eval。
硬约束：静态图；acomplete_structured max_retries=1；失败保守 fallback；不改 chat/graph.py 与 router 图拓扑。
`````

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-27 | S2 短拷贝 |
