# invoke · 50_close · ci-pytest-pg-service

- 时刻：2026-11-15 · 关账（wave_tip d002e4f0 · PR #386 CI 四绿）
- 关账人：本窗口（维护者 m02028「本窗口任务继续」授权）

## 验证台账

| 项 | 证据 |
|----|------|
| CI 真跑 PG 绿 | PR #386 末跑 pytest 2m10s pass（check/import-linter/lint-wiki-delta 同绿） |
| 本地不回归 | 干净 worktree /tmp/opsdesk-api-384repro（无 .env · 3d6eaecd）2100 passed / 2 skipped / 0 failed（48.90s） |
| 时长膨胀 | skip 态 1m36s → 真跑 2m10s（+34s ≤ +2min 上限） |
| 扩展继承 | template1 预建 vector/uuid-ossp → conftest CREATE DATABASE 继承（本地同构复跑实证 2094 passed） |

## 偏差登记（三件）

1. **扩面 · TC-B4 测试修复**：CI 真跑暴露潜伏竞态（bus 发布先于事件行对其它会话可见 → 归属闸抢跑抛 LgRagRunNotFoundError）。修法=测试侧有界等待循环（tests/test_lg_rag_sse_run_worker.py），零断言弱化。registry entry 已追登记。
2. **扩面 · template1 扩展步骤**：首轮 CI 2095 errors「type "vector" does not exist」——conftest 建库后扩展缺失（本地库 T4 时手动预建掩盖）。pytest.yml 加 Prepare PG extensions 步（psql -d template1）。
3. **skip 名冊差额**：CI 4 skipped vs 本地 2 skipped（环境型差异）；CI 日志 blob 下载网络不稳未逐名复核，本地 -rs 已证 PG 缺失类归零。非阻塞。

## 结论

验收 4 条全过；issue #384 可关（由维护者/本窗口在 issue 侧登记）。
