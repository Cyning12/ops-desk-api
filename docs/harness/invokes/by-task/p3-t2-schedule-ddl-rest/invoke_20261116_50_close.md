# invoke_50 · close（p3-t2-schedule-ddl-rest）

## 内容

- PR Cyning12/ops-desk-api#420 squash merge 完成（merge commit
  8bdc5c37 · CI 四 job 全绿：check / import-linter / lint-wiki-delta /
  pytest 2347+ 全过）。
- 本 invoke：task 档 active → done；registry entry status=closed +
  wave_tip=8bdc5c37。
- 交付物：alembic 迁移 20261116_ops_schedules（ops_schedules +
  ops_schedule_fires 双表 · 全含 tenant_id ·
  uq_ops_schedule_fires_planned 幂等键）+ models OpsSchedule/
  OpsScheduleFire + app/ops/schedule 包（store + router 四端点 ·
  配额 20/user·200/tenant · 422 词表逐字）+ 图谱 01_modules.md 登记 +
  三个测试文件 44 用例。

## 过程要点

- 跨波汇合冲突和解（D1）：p3-t4 归因测试对契约钉名双表
  DROP/CREATE 临时表致 CI 19 红；改写为插真行+finally 删行，
  该文件追加入本波 allowed_tree_files（registry note + task D1
  登记）。
- 本地全量 35 红系既有环境性问题（tests/test_check_vector_waterline.py
  裸 load_dotenv + worktree 在仓树内命中仓根 .env 渗入 72 键），与
  本波 diff 无关；CI（无 .env）终裁全绿。
- rebase origin/master 解两处冲突（01_modules.md 签收行 +
  registry 双 entry）均保留双方。

## 验证台账

| 项 | 结果 |
|---|---|
| CI check / import-linter / lint-wiki-delta / pytest（PR #420） | 全 pass |
| 目标 44 用例（真 PG opsdesk_test） | 绿 |
| 迁移 up/down/up scratch（opsdesk_mig_test） | 幂等达成 |
| alembic check autogenerate 双表漂移 | 零（既有漂移为仓史债） |
| spec-wave verify（task 档） | PASS |
| ruff check app tests | 绿 |
