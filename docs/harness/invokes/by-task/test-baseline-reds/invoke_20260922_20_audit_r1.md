# invoke · 20-task-audit · test-baseline-reds R1 审查快照

> hat=20 · task=test-baseline-reds · 2026-09-22 · 分支 fix/test-baseline-reds
> 审查文：docs/harness/reviews/task_test_baseline_reds_audit_R1_20260922.md

## 结论

内容审查通过 · 零阻塞 · 退回项无。流程闸：HG-TASK-DRAFT / HG-AUDIT-R1 均 pending（维护者签后 00 代录）· HG-GRAPH-MODULES approved。HG-AUDIT-R1 pending，故审查文仅附维护者签闸清单，未附 30 Prompt。

## 亲跑复核（与 task 基线对照 · 全部一致）

| 项 | 命令/方式 | 结果 |
|----|-----------|------|
| D1 红基线 | pytest tests/test_chat_ws.py -q | 2 failed / 4 passed + Event loop is closed 噪音 |
| D2 红基线 | pytest tests/test_capability_http_adapter.py -q -k proxy | 1 failed / 1 passed（DID NOT RAISE） |
| D3 flaky | 单测 ×15 连跑 | 6 failed / 9 passed = 40%（task 记 8/20≈40%） |
| D3 失败取样 | 抓断言 | assert (3 == 2) · status=pass embedded=3 remaining=0 |
| L3/R3 表状态 | pg_tables 查询 | 无 ops_knowledge_chunks · 26 表（drop 恢复红基线属实） |
| CI 假绿 | 读 .github/workflows/pytest.yml + conftest:74-93 | 无 postgres service → DB_AVAILABLE=False → DB 用例全 skip，属实 |
| 断言过期 | 读 graph.py:45-50 / rag_nodes.py:107,175 / test_chat_ws.py:160 | 现行检索链必发 tool_result → 环境全修断言仍不匹配，论断成立 |
| 改动边界 | git diff master...HEAD --stat | 仅 docs/（task + 10 份 10 帽 invoke） |
| task lint | npx spec-wave task lint | PASS |

## 思考轮审查

R0–R3 回填闭合；R3 反向实证（补表+净化 env → 实得 tool_result）坐实断言过期为主根因；early_stop at R3 理由具体、岔路已逐条排除、residual_risks 有归属 → 合规。

## 非阻塞注记

- A2 末句措辞略绕，语义=打桩后断言与宿主 OS 无关（不退回）。
- HG-TASK-DRAFT blocks 含 20-R1 而 pending：本 R1 由父帽委派启动，签闸清单已要求维护者 30 前补签两道闸。
