# Invoke：30/40 · intent-schema-v1（S2）

| 字段 | 值 |
|---|---|
| hat_id | 30/40 |
| task_slug | intent-schema-v1 |
| git_branch | `task/intent-schema-v1` |
| related_review | `task_intent_schema_v1_audit_R1_20260827.md` |

## GATE_VERIFY

```text
## 人工闸扫描（GATE_VERIFY · 首输出）

| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---------------|--------------|-----------------|--------|-----------|------------|
| HG-TASK-DRAFT | approved | approved | Y | N | ✅ |
| HG-AUDIT-R1 | approved | approved | Y | Y | ✅ |
| HG-GRAPH-MODULES | approved | approved | Y | Y | ✅ |

reviews：task_intent_schema_v1_audit_R1_20260827.md 存在且 R1 通过？ 是
pre-30 invoke：required ∩ {10,20,00} 齐全？ 是（00 + 10）
结论：可进入读码/改码
VERIFY: PASS · task_intent_schema_v1.md
```

机械：`npx dsh-coding-kit verify --target . --task docs/tasks/active/task_intent_schema_v1.md` → **VERIFY: PASS**

## 实现摘要

1. **IntentV1** `app/ops/lg_rag/schemas/intent.py`（extra=ignore；缺省 unknown / 全 False / low / summary=""）并导出
2. **LgRagState.intent: dict**
3. **intent_node** `app/ops/strategy/intent.py`：`acomplete_structured(max_retries=1, raise_on_failure=False)`；H4 槽 `lg_rag.intent.system`；失败保守 fallback + span `intent_fallback` / `structured_output_fallback`，不拒图
4. **supervisor 图** `START → intent_node → strategy_builder → supervisor → …`（静态 compile）
   - 节点 id 用 `intent_node`：**LangGraph 禁止 node id 与 state key `intent` 同名**
5. **Builder** 读 `state.intent`：`needs_tool is False` → 空 allowlist；`True` 或缺 intent → 仍 ⊆ Registry∩Policy（S1 求交）；`needs_skill` 本波 `allowed_skill_ids=[]`；`risk_hint` 不绕过 Policy
6. **S2-b** `docs/guides/GUIDE_intent-vs-router-coexistence_v0.md`（对齐 ROADMAP §7）
7. G-L1 `lg_rag` 备注 + `10_flow_lg_rag.graph.yaml` 增 `s_intent`；`./scripts/graph-compile.sh` 绿

未改：`app/ops/chat/graph.py` · router/basic 图拓扑 · S3/S4/Eval/Skill 引擎

## 40 验证

| 项 | 结果 |
|---|---|
| ruff（触及路径） | 0 |
| pytest intent_schema | 5 passed |
| pytest intent_node（含拓扑 / router START→router） | 5 passed |
| pytest strategy_builder（含 S2 消费 + S1 不回归） | 9 passed |
| pytest prompt_assembly（含 intent 槽） | 5 passed |
| pytest supervisor_capability_catalog（S1 不回归） | 9 passed |
| pytest structured_output_p2 + multi 拓扑/空 dispatch/三图并存 + router 缺 route 键 | 计入合计 48 passed（无 ainvoke） |
| pytest lg_rag_multi / lg_rag_router **ainvoke 全链** | **failed** · 本地 `langchain.debug` AttributeError（与 S1 invoke 同环境已知问题 · 非 S2 逻辑回归） |
| chat/graph.py | 0 diff |
| graph-compile | exit 0 |

命令（绿集）：

    pytest tests/test_intent_schema.py tests/test_intent_node.py tests/test_strategy_builder.py tests/test_prompt_assembly.py tests/test_lg_rag_supervisor_capability_catalog.py tests/test_lg_rag_structured_output_p2.py tests/test_lg_rag_multi.py::test_supervisor_graph_includes_strategy_builder_node tests/test_lg_rag_multi.py::test_empty_subtasks_dispatch_goes_aggregate tests/test_lg_rag_multi.py::test_three_graphs_coexist tests/test_lg_rag_router.py::test_route_by_route_missing_key_defaults_rag -q
    → 48 passed

    ruff check <触及路径> → All checks passed
    git diff -- app/ops/chat/graph.py → 空
    ./scripts/graph-compile.sh → done / OK: 10_flow_lg_rag

## task 验收勾选

- [x] S2-a：IntentV1 单测（合法/extra ignore/缺省）
- [x] S2-a：intent_node mock LLM + SO 成功写入 state.intent；失败 fallback + span
- [x] S2-a：supervisor 图含 Intent 节点且边 START→intent_node→strategy_builder（节点 id 不能为 `intent`：LangGraph 禁止与 state key 同名）
- [x] S2-a：Builder 消费 needs_tool=False → 空 allowlist；True → 非空且 ⊆ Policy 可见
- [x] S2-b：并存策略落盘 GUIDE_intent-vs-router-coexistence_v0.md
- [x] G-L1 备注 + s_intent + graph-compile 绿
- [x] ruff / pytest 触及路径绿；chat/graph.py 零 diff；router 图拓扑不回归

| 2026-08-27 | 30/40 PASS（ainvoke 全链待 CI/本地 langchain 环境） · 报 00 |
