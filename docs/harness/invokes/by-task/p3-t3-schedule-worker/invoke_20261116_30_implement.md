# invoke_30 · implement（p3-t3-schedule-worker）

## 内容

- `app/ops/schedule/worker.py`（新建 · ~380 行）：双闸 env
  （OPS_SCHEDULE_ENABLED 默认 off 非法回退+warning ·
  OPS_SCHEDULE_TICK_SECONDS 默认 30 非法/越界 [1,3600] 回退）·
  claim_due_schedules（SELECT FOR UPDATE SKIP LOCKED + NOT EXISTS
  预过滤 · 同事务 SAVEPOINT INSERT fires(claimed) · batch=50 ·
  推进/once_at/max_fires 三分支）· _execute_fire（状态机三出路 ·
  create_run+start_run_worker 内部通路不 await · query 前缀
  `[定时任务 · {name}]` · 显式 creator 归因 · 审计三元组）·
  run_schedule_tick · relink_stale_claimed_fires（CLAIM_STALE_SECONDS
  =120 · 补链只信台账）· start/stop_schedule_worker 五件套（承
  auto_resume.py:273-309 · 模块级句柄幂等复用 · CancelledError
  raise · Exception logger.exception 下周期重试）。
- `app/main.py`（3 处挂接）：import worker · lifespan on 才创建 ·
  finally 对称 stop（承 :84-110 auto_resume 先例 · off 零创建）。
- `app/db/models.py`：OpsScheduleFire 加 created_at 列（D5 · R10
  超时判据载体 · planned_fire_at 会把 fire_once 补跑误判超时）。
- `alembic/versions/20261116_ops_fires_created_at.py`（新建 ·
  down_revision=20261116_ops_schedules · ADD COLUMN IF NOT EXISTS
  timestamptz NOT NULL DEFAULT now() · scratch 真 PG upgrade head
  实证通过）。
- `tests/test_schedule_worker.py`（新建 · 31 用例六类 · autouse
  清场 fixture 独立引擎用后即 dispose · 插真行+删行纪律）。
- 图谱 docs/_tech_graph/l1/01_modules.md：schedule 行 deps 增
  lg_rag+worker 备注 · db 行 created_at 列登记（fires 7→8 列）·
  HG-GRAPH-MODULES 签收行（:145）。
- env 文档 docs/guides/GUIDE_env_inventory_v1.md：84→86 键
  （OPS_SCHEDULE_ENABLED / OPS_SCHEDULE_TICK_SECONDS · schedule 组）。

## 验证台账

| 项 | 结果 |
|---|---|
| pytest tests/test_schedule_worker.py（真 PG opsdesk_test） | 31/31 绿 |
| 迁移 scratch（opsdesk_mig_test）upgrade head | 列+默认 now() 实证 |
| ruff check（app/ops/schedule/worker.py · tests/test_schedule_worker.py） | 绿 |
| scripts/graph-compile.sh | PASS |
| 全套件 pytest tests | 2396 passed / 1 skipped / 3 failed（脏树期结构性红 · 见偏差） |

## 过程要点

- 共享库 T2 残留污染全局计数 → autouse 清场 fixture；asyncio.run()
  清 loop 致旧版 pytest-asyncio 炸 → fixture 内 set_event_loop 补回。
- 悬空 user 场景被 FK ON DELETE CASCADE 在 DB 层消灭 → R11 为防御性
  复核，测试 monkeypatch AsyncSession.get（entity is OpsUser → None）。
- 失败回滚不留半成品：create_run 抛错时 run_id 不落库（测试断言）。

## 偏差

- 全套件 3 红（test_tc8_diff_whitelist ·
  test_diff_whitelist_scenario_stage_rewire · test_wave_gate_registry）
  = 脏树期结构性红（diff whitelist/wave_gate 咬未登记在途面常态 ·
  委派书已预警）· commit+registry 落盘后复跑 · CI 终裁。

## 结果

30 交付完成，进 40。
