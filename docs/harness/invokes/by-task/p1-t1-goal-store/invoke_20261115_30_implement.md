# invoke_20261115_30_implement

## 内容

实施：① app/ops/goals/{__init__,store,README}——resolve（懒创建+竞态重读）/get/list/patch（状态机矩阵+显式抛错）+ sanitize_objective 单行化截 200；② models.py 补 OpsGoal/OpsLgRagRun __table_args__ 对齐既有 DB 索引名（零新迁移）。

## 结果

- tests/test_goal_store.py 6 件全绿（真 PG）：sanitize/状态机全矩阵/tenant 隔离/patch 显式抛错/读路径吞错。

## 偏差记录

1. 竞态重读路径（IntegrityError catch）无真实唯一索引可触（索引属 T4）——单测覆盖到幂等层，竞态窗口登记 R-1。
