# Invoke：30 · eval-goldenset-lg-rag（E2 金标）

| 字段 | 值 |
|---|---|
| hat_id | 30 |
| task_slug | eval-goldenset-lg-rag |
| git_branch | `task/eval-goldenset-lg-rag` |
| related_review | `task_eval_goldenset_lg_rag_audit_R1_20260828.md` |

## 人工闸扫描（GATE_VERIFY）

| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---------------|--------------|-----------------|--------|-----------|------------|
| HG-TASK-DRAFT | approved | 00 代签 | Y | N | ✅ |
| HG-AUDIT-R1 | approved | 00 代签 | Y | Y | ✅ |
| HG-GRAPH-MODULES | approved | 不改图 | Y | N | ✅ |

reviews：`task_eval_goldenset_lg_rag_audit_R1_20260828.md` 存在且 R1 通过？ **是**

pre-30 invoke：`required ∩ {10,20,00}` 齐全？ **是**

```text
$ npx dsh-coding-kit verify --target . --task docs/tasks/active/task_eval_goldenset_lg_rag.md
VERIFY: PASS · task_eval_goldenset_lg_rag.md
exit 0
```

结论：可进入改码。

## 实现摘要

1. 金标根 `evals/agent/golden/<module>/cases_v1.yaml`（与 RAG `evals/golden/` 隔离）
2. router ×3（route 枚举 rag/direct/refuse）；strategy_builder ×2（allowlist 集合相等）；supervisor ×2（subtask_types + supervisor_fallback）；e2e ×1（mock 全链到 END）
3. 确定性评估器 `tests/eval/eval_agent_graders.py`：枚举相等 / allowlist 集合 / tool id ∈ allowlist / plan schema
4. pytest `tests/eval/test_eval_agent_*.py`；mock LLM；未改 `app/`；未补 `module=`

## 命令与退出码（禁止伪造）

| 命令 | 退出码 | 结果 |
|---|---|---|
| `npx dsh-coding-kit verify --target . --task docs/tasks/active/task_eval_goldenset_lg_rag.md` | 0 | VERIFY: PASS |
| `pytest tests -q --tb=short -k eval_agent` | 0 | **17 passed**, 409 deselected |
| `ruff check tests/eval evals/agent` | 0 | All checks passed |
| `npx --yes dsh-coding-kit task lint-wiki-delta --target .` | 0 | LINT-WIKI-DELTA: PASS |

```text
$ git diff -- app/ops/chat/graph.py evals/golden/queries_v1.yaml evals/golden/run_eval.py evals/router/labeled_router_v1.yaml
（空）
$ git diff --stat -- app/
（空）
```

未做：`module=` span；E3 Dataset/CI；E4 score；E5 价表；LLM-as-judge。

| 2026-08-28 | 30 PASS · 报 00 |
