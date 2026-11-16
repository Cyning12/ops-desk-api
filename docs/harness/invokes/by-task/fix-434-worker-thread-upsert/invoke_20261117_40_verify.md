# invoke_40 · 收口验证（fix-434-worker-thread-upsert）

## 验证台账（全机判 · 真 PG postgresql+asyncpg://ops:ops_password@localhost:5432/opsdesk_test · 五键 blank 前缀）

| 验收条 | 结果 |
|---|---|
| upsert：无 turns schedule fire 后 thread 行存在（id/user_id=creator） | PASS · TestThreadUpsert::test_missing_thread_row_created_on_fire |
| 既有行二火后 created_at/user_id 不变 | PASS · test_existing_thread_row_untouched_on_refire |
| 端到端：fire 后 GET runs 卡片端点 200 · 含 fire.run_id（不再 404） | PASS · test_runs_card_endpoint_200_after_fire（断言 body.ok + data.runs 含 run_id） |
| R6 外来 thread 回归（failed · 不建行） | PASS · test_foreign_thread_failed（六文件回归内） |
| 六文件回归零红 | PASS · 105 passed（schedule_worker/schedule_rest/schedule_store/p3_t2b/ops_schedule_ddl/lg_rag_runs_readonly_api） |
| ruff check app tests | PASS · All checks passed（修 F841 一处） |
| 图谱两件 | PASS · 01_modules.md schedule 行 :40 fix-434 备注 + HG-GRAPH-MODULES 签收行（承 :41/:42） |
| 过闸四件 | PASS · registry active entry（yaml.safe_load 31 entries）· invokes {10,30,40} · R1 审查文 GO · spec-wave@3.5.0 task lint PASS（W3 draft 期合法 · 自检结论已回填） |

## 全量 pytest（.venv/bin/python -m pytest tests -q）

2442 passed · 2 skipped · **4 failed**（72.82s）——逐签对照：

| 失败用例 | 定性 | 依据 |
|---|---|---|
| test_hitl_decide_owner_fallback.py::test_db_frameless_run_decide_via_real_thread_owner | 环境性基线红 | base 396f7fed 同路径同红（临时 worktree 复核 2 failed, 2 passed）· hitl 面与本波零交集 |
| test_hitl_pending_decide.py::test_db_decide_survives_store_rebuild_then_resume | 环境性基线红 | 同上 |
| test_lg_rag_write_replay_guard.py::test_tc8_diff_whitelist | 脏树期结构性红 | 在途 app/ops/schedule/worker.py 改动未入他 entry（diff-whitelist-anchor-drift）allowed → 判 banned；base 干净树绿 · 提交后闭窗复绿 · CI 终裁（委派书钉明常态） |
| test_wave_gate_registry.py::test_wave_gate_registry | 脏树期结构性红 | 同上机理 |

## 偏差

- D1（承 10/30）：最小字段按模型裁剪（OpsLgRagThread 无 tenant_id 列 · 实落 id+user_id）。
- 测试实现微调：端到端断言响应壳 body["data"]["runs"]（初版误用 data 直迭代 · 修正后绿）。

## 限制登记

- 并发同 thread_id 双 fire 撞 PK → 走既有 except rollback+failed（不自动重火 · 台账可审计）——判据：极端小概率且语义安全（failure_paths 第一条）。

## 结果

40 收口验证全过（4 红逐签定性 · CI 终裁），进 50 close 波。
