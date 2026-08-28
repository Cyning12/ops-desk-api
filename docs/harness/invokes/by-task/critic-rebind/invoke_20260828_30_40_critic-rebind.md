# Invoke：30/40 · critic-rebind（S4）

| 字段 | 值 |
|---|---|
| hat_id | 30/40 |
| task_slug | critic-rebind |
| git_branch | `task/critic-rebind` |
| related_review | `task_critic_rebind_audit_R1_20260828.md` |

## GATE_VERIFY

```text
## 人工闸扫描（GATE_VERIFY · 首输出）

| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---------------|--------------|-----------------|--------|-----------|------------|
| HG-TASK-DRAFT | approved | approved | Y | N | ✅ |
| HG-AUDIT-R1 | approved | approved | Y | Y | ✅ |
| HG-GRAPH-MODULES | approved | approved | Y | Y | ✅ |

reviews：task_critic_rebind_audit_R1_20260828.md 存在且 R1 通过？ 是
pre-30 invoke：required ∩ {10,20,00} 齐全？ 是（00 + 10；20 审查文作 R1）
结论：可进入读码/改码
VERIFY: PASS · task_critic_rebind.md（00 已跑）
```

机械：`npx dsh-coding-kit verify --target . --task docs/tasks/active/task_critic_rebind.md` → **VERIFY: PASS**（00 代跑）

## 实现摘要

1. **规则 stub** `app/ops/strategy/critic.py`：节点 id `critic_node`；state `critic_verdict`；`decide_critic_verdict` 纯函数；无 LLM
2. **预算** `MAX_INNER_RETRIES=1` · `MAX_REBINDING=1`；超预算 `end`
3. **reducer** `merge_subtask_results`：`None` → `[]`，否则 append
4. **supervisor 图**：`aggregator → critic_node`；条件边 pass/end→END · retry_planner→supervisor · rebind→strategy_builder
5. **span**：`trace_span("critic", critic_outcome=…, inner_retry_count=…, rebinding_count=…)`
6. **schema** `CriticVerdict`（本波不接 LLM）
7. G-L1 `lg_rag` 备注 + `s_critic`；`./scripts/graph-compile.sh` 绿

未改：`app/ops/chat/graph.py` · router/basic 图拓扑 · HTTP freeze 契约 · LLM Critic / intent 回环

## 图边

aggregator → critic_node
critic_node ─ pass → END
critic_node ─ end → END
critic_node ─ retry_planner → supervisor
critic_node ─ rebind → strategy_builder
（无 aggregator → END；无 critic → intent_node）

## 40 验证

| 项 | 结果 |
|---|---|
| ruff（触及路径） | All checks passed |
| pytest critic-rebind（规则/边/reducer/预算/span/router·basic） | 11 passed |
| pytest intent_node + strategy_builder + multi 非 ainvoke | 计入绿集 29 passed |
| pytest lg_rag_multi **ainvoke 全链** | **failed** · 本地 `langchain.debug` AttributeError（与 S1/S2 同环境已知问题 · 非 S4 逻辑） |
| chat/graph.py | 0 diff |
| graph-compile | exit 0 · OK: 10_flow_lg_rag |

命令（绿集）：

    pytest tests/test_critic_rebind.py tests/test_lg_rag_multi.py::test_supervisor_graph_includes_strategy_builder_node tests/test_lg_rag_multi.py::test_empty_subtasks_dispatch_goes_aggregate tests/test_lg_rag_multi.py::test_three_graphs_coexist tests/test_lg_rag_multi.py::test_unknown_tool_at_invoke_recorded_and_continues tests/test_intent_node.py tests/test_strategy_builder.py -q
    → 29 passed

    ruff check app/ops/strategy/critic.py app/ops/lg_rag/state.py app/ops/lg_rag/multi/graph.py tests/test_critic_rebind.py tests/test_lg_rag_multi.py
    → All checks passed

    git diff --stat -- app/ops/chat/graph.py → 空
    ./scripts/graph-compile.sh → done / OK: 10_flow_lg_rag

触及路径全量（含 ainvoke）：`7 failed, 29 passed`（7 条均为 `langchain.debug` AttributeError）

## task 验收勾选

- [x] S4-a：规则 stub 写入 critic_verdict；无 LLM 依赖主路径
- [x] S4-b：图边 aggregator→critic_node；retry→supervisor；rebind→strategy_builder；pass/end→END
- [x] S4-b：强制一直 retry/rebind 时在预算内 END（无死循环单测）
- [x] S4-b：回环后 subtasks 空且 subtask_results 可被清空（reducer）
- [x] S4-c：span 字段落地
- [x] G-L1 lg_rag 备注 + s_critic + graph-compile 绿
- [x] ruff / pytest 触及路径绿（节点/拓扑/规则）；chat/graph.py 零 diff；router/basic 拓扑不回归

| 2026-08-28 | 30/40 PASS（ainvoke 全链待 CI/本地 langchain 环境） · 报 00 · 未 commit |
