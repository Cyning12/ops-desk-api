# invoke · 10_task_draft · p1-t4-goal-entry

## 内容

按 issue #396 + 07 §5 T4 行落 task 档 docs/tasks/active/task_p1_t4_goal_entry.md + registry entry。

## 勘察定论（R0）

- 接线点：stream_lg_rag _prepare_thread 后（router.py:466）；tenant_id :463 / thread_id :465 已在手。
- alembic head=20261114_drop_legacy_chat_tables。
- conftest create_all → ORM Index 声明自动进测试库（并发用例可实证 uq）。
- T1 已对齐 OpsGoal/OpsLgRagRun 既有索引 __table_args__；本单仅补新增 uq 声明。
- T3 先例：continuity importlib 运行期解析 goals.store（lg-rag-outbound allow_indirect_imports=True）；router 承同一先例，.importlinter 零改动。
