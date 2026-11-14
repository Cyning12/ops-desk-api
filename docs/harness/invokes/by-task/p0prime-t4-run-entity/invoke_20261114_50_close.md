# invoke_20261114_50_close · p0prime-t4-run-entity CLOSE

- 时间：2026-11-14 · 执行：lead（P0' 维护者签收 m00177「签收，开始」）
- PR #373（task/p0prime-t4-run-entity）CI 四件全绿（check/lint-wiki-delta/import-linter/pytest）→ merge **8287cfa1**。
- registry：status=closed · wave_tip=8287cfa1；task 单迁 docs/tasks/done/。

## 验证台账
- 目标用例：tests/test_lg_rag_run_store.py 6 件新 + test_lg_rag_sse_run_worker.py 既有 → 本地真 PG（opsdesk_test）**12 passed**（TC-B5 经补行子路径零改动通过）。
- 回归：lg_rag+hitl 十套件 **145 passed**（env 四键 blank 承 T3 体例）。
- 迁移：alembic upgrade head / downgrade -1 / upgrade head 于 scratch 库 opsdesk_t4mig 真 PG 实证（vector/uuid-ossp 扩展须超级用户预建，已记 task 单教训）。
- 干净 worktree（/tmp/opsdesk-api-t4 · detached bbc7c11d · .venv 符号链接 · 无 .env）全量：**2085 passed / 2 skipped / 1 failed**。
- ruff app+tests 绿；graph-compile 过（4 条既有 warn 一期不 fail）；lint-imports 12 kept 0 broken。

## 偏差登记
1. **test_ta2_ttl_db_store_expired_not_consumed 红为既有问题，非本 diff 引入**：baseline cc622403（T3 merge 后 master）同跑同红；CI pytest 无 PG service 该件 skip 故 CI 绿（承 T3 已登记「CI DB 用例假绿」观察）。本地 PG 起后才显现，建议另立 task 排查（hitl 审批消费 TTL 方向），不阻塞 T4 CLOSE。
2. .importlinter 补 run_store ignore 白名单两条（原 registry 面未含该文件，面同步扩记；承 event_store/thread_store 先例）。
3. 本地 PG 解锁副作用：DB 标记用例由全 skip 转真跑——N-R2-1（resume 链丢失缺陷真 PG 复测，T3 偏差①）现已具备本地复测条件，建议随 T5/T6 或专项处理。
4. /tmp/opsdesk-api-baseline（detached e1dee703 · T1 遗留）与 /tmp/opsdesk-api-t4 两 worktree 于 CLOSE 后清理。
