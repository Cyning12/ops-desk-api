# Invoke：30 · eval-token-cost-ledger（E5 Token/费用账本）

| 字段 | 值 |
|---|---|
| hat_id | 30 |
| task_slug | eval-token-cost-ledger |
| git_branch | `task/eval-token-cost-ledger` |
| related_review | `task_eval_token_cost_ledger_audit_R1_20260829.md` |

## 人工闸扫描（GATE_VERIFY）

| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---------------|--------------|-----------------|--------|-----------|------------|
| HG-TASK-DRAFT | approved | 00 代签 | Y | N | ✅ |
| HG-AUDIT-R1 | approved | 00 代签 | Y | Y | ✅ |
| HG-GRAPH-MODULES | approved | 不改图 | Y | N | ✅ |

reviews：`task_eval_token_cost_ledger_audit_R1_20260829.md` 存在且 R1 通过？ **是**

pre-30 invoke：`required ∩ {10,20,00}` 齐全？ **是**

    $ npx dsh-coding-kit verify --target . --task docs/tasks/active/task_eval_token_cost_ledger.md
    VERIFY: PASS · task_eval_token_cost_ledger.md
    exit 0

结论：可进入改码。

## 实现摘要

1. GUIDE：`docs/spec/agent-infra/eval/GUIDE_token_cost_ledger_v0.md`（usage 审计 · Host vs Langfuse · `price_missing`/`usage_missing`）；链自 `eval/README.md`
2. 价表：`evals/agent/cost/price_table_v1.yaml`（siliconflow/bailian 默认模型占位价 + `effective_from`）
3. 脚本：`evals/agent/cost/export_cost.py` + fixture `fixtures/usage_sample.json`（usage×单价；禁 LLM 估费）
4. pytest：`tests/eval/test_eval_cost.py`
5. **未改** `app/`（可选 metadata 钉死跳过）；`chat/graph.py` 零 diff

## 命令与退出码（禁止伪造）

| 命令 | 退出码 | 结果 |
|---|---|---|
| `npx dsh-coding-kit verify --target . --task docs/tasks/active/task_eval_token_cost_ledger.md` | 0 | VERIFY: PASS |
| `pytest tests -q --tb=short -k eval_cost` | 0 | **8 passed**, 441 deselected |
| `pytest tests -q --tb=short -k 'eval_agent or eval_experiment or eval_sample'` | 0 | **32 passed**, 417 deselected |
| `ruff check evals/agent/cost tests/eval/test_eval_cost.py` | 0 | All checks passed |
| `npx --yes dsh-coding-kit task lint-wiki-delta --target .` | 0 | LINT-WIKI-DELTA: PASS |
| `git diff -- app/ops/chat/graph.py` | 0 | （空） |

未做：全路径补 usage；热路径 `cost.*` score；新 GHA Langfuse secret；SDK v4；扩金标；改 `chat/graph.py`；merge PR。

| 2026-08-29 | 30 PASS · 报 00 |
