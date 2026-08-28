# Invoke：30 · eval-online-sample-scores（E4 线上抽样 score）

| 字段 | 值 |
|---|---|
| hat_id | 30 |
| task_slug | eval-online-sample-scores |
| git_branch | `task/eval-online-sample-scores` |
| related_review | `task_eval_online_sample_scores_audit_R1_20260828.md` |

## 人工闸扫描（GATE_VERIFY）

| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---------------|--------------|-----------------|--------|-----------|------------|
| HG-TASK-DRAFT | approved | 00 代签 | Y | N | ✅ |
| HG-AUDIT-R1 | approved | 00 代签 | Y | Y | ✅ |
| HG-GRAPH-MODULES | approved | 不改图 | Y | N | ✅ |

reviews：`task_eval_online_sample_scores_audit_R1_20260828.md` 存在且 R1 通过？ **是**

pre-30 invoke：`required ∩ {10,20,00}` 齐全？ **是**

    $ npx dsh-coding-kit verify --target . --task docs/tasks/active/task_eval_online_sample_scores.md
    VERIFY: PASS · task_eval_online_sample_scores.md
    exit 0

结论：可进入改码。

## 实现摘要

1. `app/ops/tracing.py`：`eval_score_sample_rate` / `score_current_trace`；关 tracing / rate miss / SDK 异常 → no-op
2. 调用点：`lg_rag/multi/nodes._record_span_metadata` 在 `supervisor_fallback is True` 时写 `stab.fallback=1`
3. GUIDE：`docs/spec/agent-infra/eval/GUIDE_online_sample_annotation_v0.md`；链自 `eval/README.md`
4. pytest：`tests/eval/test_eval_sample_scores.py`（mock；rate=0 零 SDK；rate=1 写分）
5. `.env.example` 补 `OPS_EVAL_SCORE_SAMPLE_RATE` 说明（未改 `.env`）

## 命令与退出码（禁止伪造）

| 命令 | 退出码 | 结果 |
|---|---|---|
| `npx dsh-coding-kit verify --target . --task docs/tasks/active/task_eval_online_sample_scores.md` | 0 | VERIFY: PASS |
| `pytest tests -q --tb=short -k eval_sample` | 0 | **8 passed**, 433 deselected |
| `pytest tests -q --tb=short -k 'eval_agent or eval_experiment'` | 0 | **24 passed**, 417 deselected |
| `ruff check app/ops/tracing.py app/ops/lg_rag/multi/nodes.py tests/eval/test_eval_sample_scores.py` | 0 | All checks passed |
| `npx --yes dsh-coding-kit task lint-wiki-delta --target .` | 0 | LINT-WIKI-DELTA: PASS |
| `git diff -- app/ops/chat/graph.py` | 0 | （空） |

未做：E5 价表；热路径 judge；扩金标；改 `chat/graph.py`；新 GHA secret；Langfuse SDK v4；merge PR。

| 2026-08-28 | 30 PASS · 报 00 |
