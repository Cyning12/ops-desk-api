# invoke_20261115_30_implement

## 内容

30 实施：app/ops/goals/router.py（GET list + PATCH 流转 · pydantic Literal 前置 422 · GoalNotFoundError→404 / GoalStateTransitionError→409 · tenant 复用 resolve_header_against_session 先例）+ app/ops/router.py 注册 + tests/test_goals_rest.py 7 件。

## 结果

- pytest tests/test_goals_rest.py：7 passed（真 PG）一遍过。
- ruff app tests 绿。

## 偏差记录

无。
