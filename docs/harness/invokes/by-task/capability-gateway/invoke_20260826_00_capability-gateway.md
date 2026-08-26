# Invoke：00 · capability-gateway（统筹 · 全波次收官）

| 字段 | 值 |
|------|-----|
| hat_id | 00 |
| git_branch | `task/capability-gateway` |
| 前置 | structured-output PR #58 MERGED · 四子 task 已归档 done/ |

## 子 task 终态

| 子 task | 状态 | 30 |
|---|---|---|
| P0 | CLOSE PASS | [Review](109766b3-5b32-4e21-9db2-66aff3466b0e) |
| P1 | CLOSE PASS | [Review](6926fcb9-789e-489d-b38f-75cbcc0b7c22) |
| P2 | CLOSE PASS | [Review](ee799432-1a82-4063-a532-a266f1fadc22) |
| P3 | CLOSE PASS | [Review](5f02faa7-faeb-45be-b125-0d2eac62e454) |

## 终验

- pytest 触及 40 passed（capability+multi+parse_only 抽验）
- ruff 0 · chat/graph.py 0
- SPEC §8 P0–P3 落地状态已写

## 下一棒

commit（排除 `app/tools/` 若仍为无关草稿）→ PR → 合入后归档四 capability task

| 2026-08-26 | 归档 structured-output · 全波次 capability P0–P3 收官 |
