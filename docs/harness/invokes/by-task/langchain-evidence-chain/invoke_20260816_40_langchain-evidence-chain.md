# Invoke：40 · langchain-evidence-chain

| 字段 | 值 |
|---|---|
| hat_id | 40 |
| task_slug | `langchain-evidence-chain` |
| git_branch | `task/langchain-evidence-chain` |
| created_utc_or_local | 2026-08-16 |
| notes | 子 agent 40 自检 · 00 落档 |

## 命令与退出码

| 命令 | EXIT |
|---|---|
| harness verify（task 表） | 0 · PASS |
| `git diff master -- app/ops/chat/graph.py` | 0 · 空 |
| ruff（包+单测） | 0 |
| pytest `tests/test_lc_evidence_chain.py` | 0 · 10 passed |
| graph-compile | 0 |

## 验收摘要

全部 task 验收项 **pass**（CLI 本轮为存在性+import；未强制连 DB 全量 smoke）。

## 交接

建议进入 **50** 关账。
