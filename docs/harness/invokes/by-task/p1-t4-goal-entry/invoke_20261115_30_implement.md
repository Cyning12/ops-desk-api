# invoke_20261115_30_implement

## 内容

30 实施：迁移 20261115_uq_goals_active_thread（部分唯一索引 · down_revision=20261114_drop_legacy_chat_tables）· models.py OpsGoal __table_args__ 补 Index+docstring 更新 · router.py stream 入口闸内 importlib 挂 resolve_goal_for_thread · tests/test_goal_entry_wiring.py 4 件。

## 结果

- tests/test_goal_entry_wiring.py 4 passed（真 PG）。
- 回归 158 passed 1 skipped（goal/sse/slots/continuity/memory/isolation/run_worker/run_store/chat_router 八套件）。
- 迁移 scratch 库 up→1 / down→0 / up→1 实证。
- ruff app tests 绿。

## 偏差记录

1. **revision id 超长**：初版 20261115_uq_ops_goals_active_thread 35 字符 > alembic_version varchar(32) → 改名 20261115_uq_goals_active_thread（31）；索引名不动。教训：alembic revision id ≤32 字符。
2. **本地 opsdesk_test 索引缺失**：create_all 不给既有表补索引 → 并发用例首跑 5 行；DROP TABLE 重建后 create_all 带全量 ORM 声明索引（含 uq）→ 竞态实证通过。CI 全新库天然无此问题。
3. FK 先例：override_auth 固定 id 用户不在 ops_users → turns 持久化 FK 炸；承 test_chat_history_api.py:117 先例加 seed_auth_user fixture。
4. 测试套件文件名勘误：memory continuity 实为 test_lg_rag_session_continuity.py / test_session_continuity.py。
