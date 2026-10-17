---
hat: 10-task
task_slug: prod_vector_waterline_check
date: 2026-10-17
---

# invoke · 10-task 起草 · prod_vector_waterline_check（生产向量水位/对账核查）

## 落稿摘要

- 起草帽：子 Agent e571aea2（Z 线 · 00 委派）。
- 实证锚点：backend.py:27 默认 qdrant · :38-39 collection 缺省 ops_knowledge · shadow_write.py DLQ 表 ops_qdrant_dlq · docker-compose.yml qdrant:v1.19.0 · 本地对账先例 reports/qdrant_reconcile_20260813T125801Z.yaml（非生产证据）。
- 范围：只读脚本 scripts/check_vector_waterline.py（Qdrant 条数 vs PG ops_knowledge_chunks 对账 + DLQ 深度 + ingest 水位）+ runbook（docs/guides/ 先例）+ 报告模板；降级三态（Qdrant 不可达→PG 单侧+「Qdrant 面无实证」）。
- 闸设计：HG-PROD-READONLY-ACCESS pending（仅阻生产执行 · 脚本交付不依赖）；test_strategy=脚本单测 fake/桩 CI 确定性。
- 交付：docs/tasks/active/task_prod_vector_waterline_check.md · lint PASS 一次过。

## 留 20 审要点

- 只读纪律是否钉死（禁写/禁改配置）· 降级三态断言可机断性 · 生产执行回填位 TC-WL-8 形态。
