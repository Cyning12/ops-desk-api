# 发现即另开（V1-E D5）

> **任务**：`host-v1-splittability-hardening` · 2026-09-24 · 帽 30
> **纪律**：验证/实扫阻断 bug → **另开 fix task** · 本波只记证据 · **不顺手修**

## 条目表

| # | 发现点 | 证据 | 处置 | 状态 |
|---|--------|------|------|------|
| 1 | 双进程 fixture `_create_user` INSERT `ops_sessions` 未写 `tenant_id` → NOT NULL 违例 | `tests/test_multi_replica_dualproc.py:294-297` INSERT 列无 `tenant_id`；本地 PG `asyncpg.exceptions.NotNullViolationError`（2026-09-24 30 真跑 · 9 ERROR）；ORM `ops_sessions.tenant_id` 已 `nullable=False`（阶段 T 后） | **另开 fix task**（修 dualproc fixture / 对齐默认 tenant）；本波 D1 验证轨 **禁改** 生产语义，fixture 修复属测试基建另开 | **closed** · `fix/multi-replica-dualproc-tenant-session`（见修订） |
| — | （D2–D4 / B1 子集未发现生产语义阻断） | import-linter 12 KEPT · splittability 7 passed · capability/llm 子集 115 passed | — | — |

## 修订

| 日期 | 说明 |
|------|------|
| 2026-09-24 | 30 落盘：双进程 tenant_id 环境/fixture 漂移 1 条 |
| 2026-09-24 | **#1 closed**：`_create_user` INSERT 补 `tenant_id='ops-desk-pilot'`（∈ `ALLOWED_TENANTS`；`dualproc_server` 的 `"dualproc"` 是 HITL store 字段，非 session 租户——字面 `dualproc` 会 `422 unknown_tenant`）· fix SHA `1aaf11c` · PR 待开后补录 |
