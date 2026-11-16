# invoke_40 · verify（p3-t3-schedule-worker）

## 验证台账

| 项 | 结果 |
|---|---|
| spec-wave task lint（`npx --yes spec-wave@3.5.0 task lint --file docs/tasks/active/task_p3_t3_schedule_worker.md`） | PASS |
| spec-wave verify（`npx spec-wave verify --target . --task ...`） | PASS（三闸 approved · 图谱锚点检查 vocabulary_empty 跳过为既有常态） |
| registry yaml safe_load | PASS（26 entries · 末 entry=p3-t3-schedule-worker） |
| pytest tests/test_schedule_worker.py（真 PG opsdesk_test） | 31/31 绿 |
| 迁移 scratch（opsdesk_mig_test）upgrade head | fires.created_at 列+默认 now() 实证 |
| scripts/graph-compile.sh | PASS |
| ruff check（worker.py · tests/test_schedule_worker.py） | 绿 |
| 全套件 pytest tests（脏树期） | 2396 passed / 1 skipped / 3 failed（结构性红） |
| 三红 commit 后复跑（test_tc8_diff_whitelist · test_diff_whitelist_scenario_stage_rewire · test_wave_gate_registry） | 4 passed · 结构性红确认转绿 |

## 三红归因（结构性 · 非本波缺陷）

- tests/test_wave_gate_registry.py：在途面=工作区/暂存 vs HEAD + untracked，
  closed entry 同样咬（`_is_banned`：app/ 路径不在该 entry allowed_app_files
  即 banned · alembic/ 默认 banned）。脏树期本波在途文件必然咬其他 entry →
  红；commit 后在途面空 → 绿。委派书已预警此常态。
- test_tc8_diff_whitelist / test_diff_whitelist_scenario_stage_rewire：
  同口径 diff whitelist 在途面审计，commit 后同步转绿。

## 结果

40 verify 完成（commit 53acc4bd · 三红结构性归因成立），进 PR。
