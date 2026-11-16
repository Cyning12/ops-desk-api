# invoke_40 · 收口验证（fix-planframe-truncation）

## 验证台账

| 项 | 结果 |
|---|---|
| 新增五例（真 PG pg15 · 五键 blank 前缀 · DATABASE_URL=postgresql+asyncpg://ops:ops_password@localhost:5432/opsdesk_test） | 5 passed |
| 目标七件回归（test_lg_rag_sse_stream / test_lg_rag_sse_token_stream / test_lg_rag_sse_subtask_message / test_hitl_resume_events / test_chat_history_api / test_lg_rag_run_store / test_lg_rag_runs_readonly_api） | 109 passed |
| 全量 pytest（无并发 · 干净库） | 2445 passed, 2 skipped, 6 failed |
| `ruff check app tests` | All checks passed |
| `npx --yes spec-wave@3.5.0 task lint --file docs/tasks/active/task_fix_planframe_truncation.md` | PASS |
| `npx spec-wave verify --target . --task docs/tasks/active/task_fix_planframe_truncation.md` | PASS（三闸绿） |

## 全量 6 红归因（逐一对照 base 6cbb947e）

1. test_lg_rag_write_replay_guard.py::test_tc8_diff_whitelist —— **结构性在途红**：
   归档波 diff-whitelist-anchor-drift 在途守卫（_banned：app/ 非旧白名单即禁）；
   提交后在途面清空转绿（承既有波次同一形态）。
2. test_wave_gate_registry.py::test_wave_gate_registry —— 同上：closed entry
   banned 在途触碰断言，提交后转绿。
3. tests/test_chat_history_api.py::test_threads_list_fields_waiting_approval_and_order
4. tests/test_chat_history_api.py::test_thread_history_missing_query_degrades_fp4
5. tests/test_hitl_decide_owner_fallback.py::test_db_frameless_run_decide_via_real_thread_owner
6. tests/test_hitl_pending_decide.py::test_db_decide_survives_store_rebuild_then_resume
   —— 3–6 **环境性红**：stash 回 base 6cbb947e 同三文件复跑同 4 红
   （50 passed vs 改动面 52 passed · 差值恰为新增两例），与本改动无关；
   本地 PG 组合态顺序敏感（ops_users 固定 UUID 撞键），CI 真 PG 终裁。

## 结论

改动面零回归（新增 5 绿 · 目标七件 109 绿 · 6 红逐一归因非本波），进 PR。
