# invoke_50 · close（p3-t3-schedule-worker）

## 内容

- PR Cyning12/ops-desk-api#424 squash merge 完成（merge commit
  34b1609c · CI 四 job 全绿：check / import-linter / lint-wiki-delta /
  pytest 全过）。
- 本 invoke：task 档 active → done；registry entry status=closed +
  wave_tip=34b1609c。
- 交付物：`app/ops/schedule/worker.py`（双闸 OPS_SCHEDULE_ENABLED/
  OPS_SCHEDULE_TICK_SECONDS · claim_due_schedules SELECT ... FOR UPDATE
  SKIP LOCKED 抢占 batch=50 · _execute_fire 状态机 claimed→fired/failed/
  skipped · run_schedule_tick 补跑 fire_once · relink_stale_claimed_fires
  启动补链 CLAIM_STALE_SECONDS=120 · start/stop 五件套承
  auto_resume.py:273-309 先例）+ main.py lifespan 三处挂接 +
  models.py fires.created_at（server_default=now()）+ 迁移
  20261116_ops_fires_created_at + tests/test_schedule_worker.py 31 用例
  + 图谱 01_modules.md schedule/db 行备注与 HG-GRAPH-MODULES 签收行 +
  env 文档 84→86 键登记。

## 过程要点

- 并行波次 CONFLICTING 一次（P3-T5 #422/#423 先合 master e83537a9）：
  rebase origin/master，registry.yaml 单冲突保留双方 entry
  （p3-t5 在前 p3-t3 在后）强推，复跑 35 passed，PR MERGEABLE。
- 首轮 CI pytest 红两例（T2/T4 裸 INSERT ops_schedule_fires 不带
  created_at）：根因 models.py created_at 无 server_default，CI 新库走
  create_all 不跑迁移；补 server_default=now() 对齐迁移后
  create_all 口径 scratch 库全套件 2422 passed / 1 skipped。
- 本地目标测试 31 用例 + 结构性 4 件全绿；CI（无 .env）终裁全绿。

## 验证台账

| 项 | 结果 |
|---|---|
| CI check / import-linter / lint-wiki-delta / pytest（PR #424） | 全 pass |
| 目标 31 用例（真 PG opsdesk_test） | 绿 |
| 全套件 2422 passed / 1 skipped（create_all 口径 opsdesk_ci_test） | 绿 |
| ruff check app tests | 绿 |
| lint-imports | 零新 forbidden（.importlinter 零改动登记） |
| spec-wave task lint / verify | PASS |
| registry yaml safe_load | PASS（27 entries） |
| scripts/graph-compile.sh | PASS |

## 结果

P3-T3 close。清理：删除 task/p3-t3-schedule-worker 与 close 分支 +
worktree + scratch DB（opsdesk_ci_test）。
