# invoke · 50_close · p1-t2-goal-rest

- 时刻：2026-11-15 · 关账（wave_tip 19e3f9ba · PR #392 CI 四绿）
- 关账人：本窗口（维护者 m02028「本窗口任务继续」授权）

## 验证台账

| 项 | 证据 |
|----|------|
| 目标测试 | tests/test_goals_rest.py 7 件真 PG 绿（本地 + CI 真跑 2m33s pass） |
| CI | PR #392 四绿（lint-wiki-delta/pytest/check/import-linter） |
| wave gate | 合并尖本地 2 passed |
| 合并尖全量 | 干净 worktree（3bd7ae50 · 含 T3）2116 passed / 2 skipped / 0 failed |

## 偏差登记（一件）

1. ruff I001（tests/test_goals_rest.py 函数内 import 序）——首 commit 前漏跑 ruff，amend 修复。教训：commit 前 ruff 必跑（承 T3 先例）。

## 结论

验收 8 条全过：GET/PATCH 路由 · 422/404/409/401 错误面 · tenant 复用先例 · 零新表/迁移/SSE 帧。P1-T4（入口接线 + uq 索引）依赖面已就绪。
