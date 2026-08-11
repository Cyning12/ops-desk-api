# Invoke：30（含 40）· golden-query-set-v1

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 30（含 40 自检） |
| task_slug | `golden-query-set-v1` |
| task_paths | `docs/tasks/active/task_golden_query_set_v1.md` |
| related_review_or_none | `docs/harness/reviews/task_golden_query_set_v1_audit_R1_20260811.md` |
| git_branch | `task/golden-query-set-v1` |
| created_utc_or_local | 2026-08-11 |
| notes | R-4 eval runner；复用 `hybrid_recall`/`grade_chunks`/`decide`；minimal invoke |

---

## GATE_VERIFY（首输出摘要）

| human_gate_id | task表status | blocks_30 | 30可开工？ |
|---|---|---|---|
| HG-TASK-DRAFT | approved | N | Y |
| HG-AUDIT-R1 | approved | Y | Y |

reviews R1 存在且签收：是 · `invoke_retention_profile=minimal` → 无 preRequired · 结论：可开工

---

## 交付范围

1. `evals/golden/run_eval.py`：加载 yaml → retrieve→grade → 断言 → 报告
2. `evals/golden/hygiene_denylist.yaml`：含金样原文污染源登记
3. `tests/test_golden_eval_runner.py`：卫生过滤 + 断言纯函数单测
4. 报告字段：分象限 recall@5、评级稳定性、观测 SPEC 三字段

禁止：旁路重写 retrieve/grade；直推 master。
