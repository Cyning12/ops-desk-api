# invoke · 30 实施 · p4-t6-run-tree-ddl（2026-11-18）

## 闸扫描（30 前置 GATE_VERIFY · 真值在 task 人工闸表）

| gate | status | blocks_30 | 30 影响 |
|------|--------|-----------|--------|
| HG-TASK-DRAFT | approved | 30 | — |
| HG-AUDIT-R1 | approved | 30 | ✅ 可 30 |
| HG-GRAPH-MODULES | approved | — | ✅ |

npx --yes spec-wave@3.5.0 verify --target . --task docs/tasks/active/task_p4_t6_run_tree_ddl.md → VERIFY: PASS（三闸 approved · 30 放行）。

## 实施清单（契约 19 §7/§11.4 逐字对齐）

1. 迁移 alembic/versions/20261118_lg_rag_run_tree.py（down_revision=20261116_ops_fires_created_at · 原生 op.execute · IF NOT EXISTS/IF EXISTS 幂等 · 可逆）：§7.2 SQL 逐字三列（parent_run_id/subtask_id VARCHAR(64) NULL · depth INTEGER NOT NULL DEFAULT 0）+ uq_ops_lg_rag_runs_parent_subtask 部分唯一索引（(parent_run_id, subtask_id) WHERE parent_run_id IS NOT NULL）+ idx_ops_lg_rag_runs_parent。
2. app/db/models.py：OpsLgRagRun 增三列 mapped_column（parent_run_id 无 FK 承 run_events 顺序容错先例 · 无 DB CHECK 契约逐字 · 深度硬上限由 claim 层断言承载）· __table_args__ 对齐两索引（uq 承 uq_ops_goals_active_thread 先例 postgresql_where）消 autogenerate 漂移。
3. app/ops/lg_rag/run_store.py：create_run 扩 parent_run_id/subtask_id/depth 三可选 kw（缺省 None/None/0 · 既有调用面零 diff）；新增 claim_child_run(*, parent_run_id, subtask_id, child_run_id) -> tuple[str, bool] | None（§7.4 SQL 逐字 ON CONFLICT DO NOTHING 新写路径 · 归属从父行取值 §8.2 · 父缺失/父 depth!=0 → 拒建 + logger.exception · 撞 uq SELECT 取回复用 created=False）；list_thread_runs_page 投影加 parent_run_id/depth。
4. app/ops/lg_rag/runs_router.py：_load_runs_page 装配加 parent_run_id/depth（§11.4 加性 · 既有字段零改 · 无新端点）。
5. 测试：tests/test_lg_rag_run_tree_ddl.py（scratch 库迁移 up/down + 索引/列形态 + 部分唯一谓词功能实证 + models 元数据对齐）· tests/test_lg_rag_run_tree_projection.py（claim 继承/重入/并发仅一胜/深度断言/父缺失 + REST 投影契约）· tests/test_lg_rag_runs_readonly_api.py 键集断言补两加性字段 + 既有 run 默认 null/0 断言。

## 偏差登记（最小改动 · 如实登记）

- tests/test_lg_rag_runs_readonly_api.py 入本波改动面（registry allowed_tree_files 已补登）：§11.4 加性字段使该档既有「投影键集精确等值」断言必然更新——加性变更的机械后果 · 非范围扩张。
- 本地存量 opsdesk_test 为 create_all 管理（create_all 不管 ALTER），按 conftest 漂移补丁同模式对本地库手工幂等对齐（ADD COLUMN IF NOT EXISTS ×3 + 两索引 IF NOT EXISTS）；CI 全新库 create_all 直含 · 零代码面改动。

## 验证结果

- 目标测试：pytest 四个测试档 -q → **24 passed**（真 PG · 五键 blank 前缀）。
- ruff check app tests → All checks passed。
- 全量 pytest tests -q --tb=line（脏树期）：2436 passed / 28 failed / 1 skipped。28 红逐签对照（cfe76b23 干净基线 worktree 同跑）：
  - 4 红基线同红（环境性 · 与本次改动零因果）：test_chat_history_api ×2（assert 0 == 2 / assert 0 == 1 计数型 · 共享库他波残留）· test_hitl_decide_owner_fallback / test_hitl_pending_decide（UniqueViolationError ops_users_pkey · 并行 agent 同固定 id 抢种）。
  - 21 红重跑即绿（并发性 flaky · 共享 DB/端口）：capability_lookups/lg_rag_multi/structured_output_p2/supervisor_catalog/multi_replica_dualproc 等 —— 基线面同集全绿 · 本树重跑同集 21/21 绿。
  - 3 红结构性脏树期（委派书/task 失败路径钉明 · 提交后复绿 · CI 终裁）：test_wave_gate_registry + test_lg_rag_write_replay_guard::test_tc8_diff_whitelist + test_strategy_scenario::test_diff_whitelist_scenario_stage_rewire（后两者 banned 前置 alembic/ 咬在途未跟踪迁移文件 · 其 committed 面为各自 _BASE.._WAVE_TIP 闭窗不含本波）。
