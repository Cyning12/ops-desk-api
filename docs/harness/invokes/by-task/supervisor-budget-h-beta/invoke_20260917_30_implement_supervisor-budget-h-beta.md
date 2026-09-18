# Invoke · 30 implement · supervisor-budget-h-beta

> **hat**：30  
> **日期**：2026-09-17  
> **分支**：`task/supervisor-budget-h-beta`  
> **task**：`docs/tasks/active/task_supervisor_budget_h_beta.md`

---

## 人工闸扫描（GATE_VERIFY · 首输出）

| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---------------|--------------|-----------------|--------|-----------|------------|
| HG-TASK-DRAFT | approved | approved | Y | Y | 可 |
| HG-AUDIT-R1 | approved | approved | Y | Y | 可 |
| HG-GRAPH-MODULES | approved | approved | Y | Y | 可 |

reviews：`docs/harness/reviews/task_supervisor_budget_h_beta_audit_R1_20260917.md` 存在且 R1 通过？是  
pre-30 invoke：`required ∩ {10,20,00}` 齐全？是  
机械：`npx --yes spec-wave verify --target . --task docs/tasks/active/task_supervisor_budget_h_beta.md` → **VERIFY: PASS**  
结论：**可进入读码/改码**

---

## 实现范围

B1+B2（薄）+B3+B4+B5。非范围：T/W/P、SSE freeze、`chat/graph.py`、commit/push。

## 改动文件列表

- `app/ops/lg_rag/multi/budget.py`（新）— `MAX_SUPERVISOR_STEPS` / env / bump / 耗尽 / 墙钟
- `app/ops/lg_rag/state.py` — `supervisor_step_count` · `supervisor_budget_exhausted` · `supervisor_started_at`
- `app/ops/lg_rag/multi/nodes.py` — 8 类节点中 5 个 bump；主闸 `route_next_subtask`
- `app/ops/strategy/intent.py` · `builder.py` · `critic.py` — 入口 bump；辅闸禁 retry/rebind
- `app/ops/lg_rag/multi/graph.py` — docstring 备注耗尽→aggregate
- `docs/_tech_graph/l1/01_modules.md` — G-L1 lg_rag H-β 备注 + 签收行
- `docs/_tech_graph/shared/graph.json` — graph-compile 时间戳
- `tests/test_supervisor_budget.py`（新）— 耗尽→aggregate / 辅闸 / env / 墙钟
- task 验收勾选回填

## 测试命令与结果

```text
ruff check app/ops/lg_rag/multi app/ops/lg_rag/state.py app/ops/strategy/{critic,intent,builder}.py \
  tests/test_supervisor_budget.py tests/test_lg_rag_multi.py tests/test_critic_rebind.py \
  tests/test_lg_rag_supervisor_capability_catalog.py
→ All checks passed!

pytest tests/test_supervisor_budget.py tests/test_lg_rag_multi.py \
  tests/test_critic_rebind.py tests/test_lg_rag_supervisor_capability_catalog.py -q
→ 41 passed

./scripts/graph-compile.sh → OK
npx --yes spec-wave task lint-wiki-delta --target . → LINT-WIKI-DELTA: PASS
chat/graph.py → 零 diff
```

## 残留风险

1. 默认 32 若真实金样仍紧，须回调 task/钉死表再改常量（禁 30 静默改小）。
2. 墙钟为薄实现（env 默认 0=关）；硬门化另跟进。

## 结论

**30 PASS** · 交 40 · 未 CLOSE · 未 commit/push
