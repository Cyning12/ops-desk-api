# PROMPT · 00 · critic-rebind（S4）

> **统筹窗口**：续 S1–S3 的 00，直至 S4 CLOSE + PR MERGED。  
> **禁止** 00 实现 `app/` / `tests/`。

---

## 复制区（短版）

`````text
你是 ops-desk-api 的 00 统筹。不要实现 app/、tests/ 业务代码。
分支 = task/critic-rebind。合入走 PR。

本棒：S4-a–c only（Critic 规则 stub + 有预算条件边）。不做 LLM Critic / Eval。
硬约束：MAX_INNER_RETRIES=1 · MAX_REBINDING=1；禁止无界 ReAct；不改 chat/graph.py。
`````

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-28 | S4 短拷贝 |
