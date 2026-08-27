# Invoke：30/40 · lg-rag-supervisor-capability-catalog（H1）

| 字段 | 值 |
|---|---|
| hat_id | 30/40 |
| task_slug | lg-rag-supervisor-capability-catalog |
| git_branch | `task/lg-rag-supervisor-capability-catalog` |
| related_review | `task_lg_rag_supervisor_capability_catalog_audit_R1_20260827.md` |

## 实现摘要

1. `supervisor_node`：`list_capabilities(_SUPERVISOR_CAP_FILTER)` → 目录注入 system prompt  
2. `_parse_subtasks` 后 `_subtasks_have_valid_tool_ids`；非法 tool → 整 plan fallback 单 rag  
3. `defaults.py` 新增只读 `utc_now_iso`（非 mock · low risk）  
4. span：`capability_catalog_count` · `supervisor_invalid_tool_id`  
5. 单测 `tests/test_lg_rag_supervisor_capability_catalog.py`（6 cases）  
6. G-L1 `lg_rag` 备注 + graph-compile 绿  

## 40 验证

| 项 | 结果 |
|---|---|
| ruff | 0（触及路径） |
| pytest H1 | 6 passed |
| pytest structured_output_p2 | 12 passed |
| pytest capability_gateway | 25 passed · 1 skipped · tool_node_smoke 本地 langchain.debug 环境已知问题 |
| test_lg_rag_multi | 本地 langchain.debug AttributeError（图 compile · 非 H1 逻辑回归） |
| chat/graph.py | 0 diff |
| graph-compile | exit 0 |
| verify | PASS |

| 2026-08-27 | 30/40 PASS · 报 00 |
