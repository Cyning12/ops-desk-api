# invoke_30 · 实现（fix-434-worker-thread-upsert）

## 内容

1. **修复**：`app/ops/schedule/worker.py::_execute_fire` R6 复核后、create_run 前
   补 thread upsert——thread 不存在则 `db.add(OpsLgRagThread(id=schedule.thread_id,
   user_id=schedule.user_id))` + `await db.flush()`（建行失败在 create_run 前暴露 ·
   走既有 except rollback+failed 不留半建 run 行）；已存在（属 creator）不动；
   外来 thread R6 failed 语义零改。模块 docstring 增 fix-434 条目。
2. **测试**（tests/test_schedule_worker.py 新增 TestThreadUpsert 三例）：
   - `test_missing_thread_row_created_on_fire`：无 turns schedule fire →
     ops_lg_rag_threads 行存在（id/user_id=creator）
   - `test_existing_thread_row_untouched_on_refire`：既有行二火后
     created_at/user_id 不变
   - `test_runs_card_endpoint_200_after_fire`：端到端 creator 会话
     GET /api/ops/lg-rag/threads/{tid}/runs → 200 · runs 含 fire.run_id
     （承 test_lg_rag_runs_readonly_api.py 形态 · body.data.runs）
3. **图谱**：`docs/_tech_graph/l1/01_modules.md` schedule 行（:40）fix-434 备注 +
   HG-GRAPH-MODULES 签收行（承 :41/:42 先例）。

## 验证台账

| 项 | 结果 |
|---|---|
| TestThreadUpsert 三例（真 PG · 五键 blank 前缀） | 3 passed |
| 目标六件（schedule_worker/schedule_rest/schedule_store/p3_t2b/ops_schedule_ddl/lg_rag_runs_readonly_api） | 105 passed |
| `ruff check app tests` | All checks passed（F841 未用变量一处已修） |
| 全量 pytest | （40 收口时回填 · 环境性红对照 base 396f7fed） |

## 偏差

- D1（承 10）：最小字段按模型裁剪——OpsLgRagThread 无 tenant_id 列
  （models.py:226-238），实落 id+user_id 两显式字段。
- 测试实现微调：端到端断言响应壳 `body["data"]["runs"]`（初版误用
  `data` 直迭代 · 一处失败已修正重跑绿）。

## 结果

30 实现完成，进 40 收口。
