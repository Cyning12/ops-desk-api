# Invoke：30 · eval-langfuse-experiment-ci（E3 Dataset / Experiment mock）

| 字段 | 值 |
|---|---|
| hat_id | 30 |
| task_slug | eval-langfuse-experiment-ci |
| git_branch | `task/eval-langfuse-experiment-ci` |
| related_review | `task_eval_langfuse_experiment_ci_audit_R1_20260828.md` |

## 人工闸扫描（GATE_VERIFY）

| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---------------|--------------|-----------------|--------|-----------|------------|
| HG-TASK-DRAFT | approved | 00 代签 | Y | N | ✅ |
| HG-AUDIT-R1 | approved | 00 代签 | Y | Y | ✅ |
| HG-GRAPH-MODULES | approved | 不改图 | Y | N | ✅ |

reviews：`task_eval_langfuse_experiment_ci_audit_R1_20260828.md` 存在且 R1 通过？ **是**

pre-30 invoke：`required ∩ {10,20,00}` 齐全？ **是**（10 / 00 / 20 均在 `docs/harness/invokes/by-task/eval-langfuse-experiment-ci/`）

    $ npx dsh-coding-kit verify --target . --task docs/tasks/active/task_eval_langfuse_experiment_ci.md
    VERIFY: PASS · task_eval_langfuse_experiment_ci.md
    exit 0

结论：可进入改码。

## 实现摘要

1. GUIDE：`docs/spec/agent-infra/eval/GUIDE_langfuse_dataset_experiment_v0.md`；链自 `eval/README.md`
2. Runner：`evals/agent/run_experiment.py` 默认 dry-run / stdout JSON；Dataset `golden-<module>-v1`；score 仅 `acc.route_match` / `acc.strategy.allowlist_match` / `acc.plan_match`
3. pytest：`tests/eval/test_eval_experiment.py`（mock Langfuse；无 key dry-run 绿；grader 失败非 0）
4. 未改 `app/`、`chat/graph.py`、`tracing.py`、RAG `evals/golden/`、金标条数、pytest.yml、未升 Langfuse SDK v4

## 命令与退出码（禁止伪造）

| 命令 | 退出码 | 结果 |
|---|---|---|
| `npx dsh-coding-kit verify --target . --task docs/tasks/active/task_eval_langfuse_experiment_ci.md` | 0 | VERIFY: PASS |
| `pytest tests -q --tb=short -k eval_experiment` | 0 | **7 passed**, 426 deselected |
| `pytest tests -q --tb=short -k eval_agent` | 0 | **17 passed**, 416 deselected |
| `ruff check tests/eval evals/agent` | 0 | All checks passed |
| `npx --yes dsh-coding-kit task lint-wiki-delta --target .` | 0 | LINT-WIKI-DELTA: PASS |
| `python evals/agent/run_experiment.py --module router` | 0 | dry-run JSON · router `acc.route_match` 3/3 |
| `env -u LANGFUSE_PUBLIC_KEY -u LANGFUSE_SECRET_KEY python evals/agent/run_experiment.py --module router --push` | 2 | missing_langfuse_keys · 未打网 |
| `python evals/agent/run_experiment.py --module router --actuals`（覆盖 rag→direct） | 1 | grader mismatch · failed=1 |

    $ git diff --stat -- app/
    （空）
    $ git diff -- evals/agent/golden evals/golden .github/workflows
    （空）

未做：E4 `score_current_trace`；E5 价表；新 GHA secret job；扩 fixture；SDK v4。

| 2026-08-28 | 30 PASS · 报 00 |
