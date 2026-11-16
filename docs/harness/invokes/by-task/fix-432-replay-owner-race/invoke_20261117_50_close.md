# invoke · 50_close · fix-432-replay-owner-race

- 时刻：2026-11-17 · 关账（wave_tip 2be501d4 · PR #435 CI 四绿 · squash merge）
- 关账人：exec-fix-432（维护者预授权链 issue Cyning12/ops-desk-workspace#23 m03064/m03283/m03694 夜间自动执行）

## 验证台账

| 项 | 证据 |
|----|------|
| 目标用例 10 连跑零红 | 真 PG opsdesk_test · 五键 blank 前缀 · 10/10 passed（0.13-0.14s/轮 · 真跑非 skip） |
| 全文件回归 | tests/test_lg_rag_sse_run_worker.py 7 passed in 0.41s |
| 全量 pytest | 2441 passed / 3 skipped（73.01s · 唯一红=脏树期 wave_gate_registry 结构性常态 · 提交后 2 passed 自证） |
| ruff | check app tests All checks passed |
| CI 四绿（终裁） | PR #435：check 15s · import-linter 10s · lint-wiki-delta 12s · pytest 2m43s pass |
| 修法边界 | diff +19/-8 单文件（tests/）· 零 app/ 改动 · 零断言弱化（diff 自证） |

## 偏差登记

无（生产侧容忍窗备易经 R1 核查项 3 论证否决 · 裁定测试侧承 #384 波先例 · 非偏差属裁定留痕）。

## 结论

验收 5 条全过；issue #432 由本窗口附评论关闭（修法+PR 号）。
