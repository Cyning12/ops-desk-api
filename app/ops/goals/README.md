# app/ops/goals

P1 Goal 模块（issue #385 · 设计真源 ops-desk-workspace 07-p1-goal-design.md）。

- `store.py`：ops_goals 读写唯一收口。状态机规则式（07 §1 矩阵），LLM 不自判 status。
- 接线在 P1-T4（router 入口懒创建 + 部分唯一索引）；REST 面在 P1-T2。
