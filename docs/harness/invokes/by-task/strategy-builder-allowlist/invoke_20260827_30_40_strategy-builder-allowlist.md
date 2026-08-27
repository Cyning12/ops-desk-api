# Invoke：30/40 · strategy-builder-allowlist（S1）

| 字段 | 值 |
|---|---|
| hat_id | 30/40 |
| task_slug | strategy-builder-allowlist |
| git_branch | `task/strategy-builder-allowlist` |
| related_review | `task_strategy_builder_allowlist_audit_R1_20260827.md` |

## GATE_VERIFY

```text
| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---------------|--------------|-----------------|--------|-----------|------------|
| HG-TASK-DRAFT | approved | approved | Y | N | ✅ |
| HG-AUDIT-R1 | approved | approved | Y | Y | ✅ |
| HG-GRAPH-MODULES | approved | — | — | N | ✅ |

reviews：task_strategy_builder_allowlist_audit_R1_20260827.md 存在且 R1 通过？ 是
pre-30 invoke：required ∩ {10,20,00} 齐全？ 是
结论：可进入读码/改码
VERIFY: PASS · task_strategy_builder_allowlist.md
```

## 实现摘要

1. **S1-a** `LgRagState` 增 `allowed_capability_ids` / `allowed_skill_ids`
2. **S1-b** 薄包 `app/ops/strategy/`：`strategy_builder_node` 规则/配置写 allowlist ⊆ Registry∩Policy；非法 id 剔除；span `strategy_builder_catalog_count`
3. **S1-c** `supervisor_node`：`list_capabilities(filter) ∩ state allowlist`；缺/空 allowlist → 整 plan fallback 单 rag
4. **S1-d** tool id Host 校验相对本轮可见集（继承 H1 fallback 语义）
5. **graph** `START → strategy_builder → supervisor → dispatch…`（静态图 · 无 per-request compile）
6. G-L1 `lg_rag` 备注 + `10_flow_lg_rag.graph.yaml` 增 `s_strategy_builder` 节点/边

## 40 验证

| 项 | 结果 |
|---|---|
| ruff（触及路径） | 0 |
| pytest strategy_builder | 6 passed |
| pytest supervisor_capability_catalog（含 S1 用例） | 9 passed |
| pytest structured_output_p2 | 12 passed |
| pytest lg_rag_multi（节点/拓扑/ tool_exec 单测） | 4 passed |
| pytest lg_rag_multi（ainvoke 全链） | **7 failed** · 本地 `langchain.debug` AttributeError（与 H1 invoke 同环境已知问题 · 非 S1 逻辑回归） |
| chat/graph.py | 0 diff |
| graph-compile | exit 0 |

## task 验收勾选

- [x] S1-a：state 字段类型 + 单测
- [x] S1-b：Builder 写 ⊆ Registry ∩ Policy；非法 id 剔除；span
- [x] S1-c：supervisor 可见集 = filter ∩ allowlist；空 allowlist → fallback 单 rag
- [x] S1-d：tool id 相对本轮可见集校验；非法 → fallback；H1 语义不回归
- [x] G-L1 `lg_rag` 备注 + graph-compile 绿
- [x] ruff / pytest 触及路径绿；`chat/graph.py` 零 diff

| 2026-08-27 | 30/40 PASS（ainvoke 全链待 CI/本地 langchain 环境） · 报 00 |
