---
hat: 10-task
task_slug: rag_golden_eval_r4_r5
date: 2026-10-17
---

# invoke · 10-task 起草 · rag_golden_eval_r4_r5（R-4 四类 golden 结案评测 + R-5 Demo 证据表）

## 落稿摘要

- 起草帽：子 Agent e571aea2（Z 线 · 00 委派）。
- 防重复背景表（亲读实证）：task_golden-query-set-v1 已闭环 73 条四象限金标集（zh2en=26/zh2zh=20/en2en=16/negative=11 + runner + 18 份 r4 过程报告）· task_eval_goldenset_lg_rag（agent 四切片）· task_memory_golden_eval（记忆轨）；本 task 只做结案汇总/门槛判定/Demo 证据表三增量。
- 诚实面：SPEC-evaluation-observation 真值文件两仓未检索到 → 照登「无实证 · 以路线 A-P1-3 引用口径为准」（背景 + FP-8）。
- 闸设计：HG-EVAL-LIVE-RUN pending（结案真跑需库+真 LLM key · 30 交付物不依赖）；汇总脚本 CI 确定性（fake 报告样例喂入）；契约漂移 FP-5 上抛不改契约。
- 交付：docs/tasks/active/task_rag_golden_eval_r4_r5.md · lint PASS 一次过。

## 留 20 审要点

- zh2en≥1/3 门槛判定逻辑与路线 R-4 一致性 · confidence 老实标形态 · 与 golden-query-set-v1 的增量边界是否无重复立项。
