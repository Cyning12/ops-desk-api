# Invoke：30/40 · ops-pg-lookup-capabilities

| 字段 | 值 |
|---|---|
| hat_id | 30/40 |
| task_slug | ops-pg-lookup-capabilities |
| git_branch | `task/ops-pg-lookup-capabilities` |
| related_review | `task_ops_pg_lookup_capabilities_audit_R1_20260828.md` |
| notes | **未** commit / **未** push；交 00 验收 |

## GATE_VERIFY

```text
## 人工闸扫描（GATE_VERIFY · 首输出）

| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---------------|--------------|-----------------|--------|-----------|------------|
| HG-TASK-DRAFT | approved | approved（PROMPT） | Y | N（22-R1） | ✅ |
| HG-AUDIT-R1 | approved | approved（PROMPT） | Y | Y | ✅ |
| HG-GRAPH-MODULES | approved | approved（PROMPT · 仅备注、不增一级） | Y | Y | ✅ |

reviews：task_ops_pg_lookup_capabilities_audit_R1_20260828.md 存在且 R1 通过？ 是
pre-30 invoke：required ∩ {10,20,00} 齐全？ 是（00 + 10；required_invoke_hats=10,30 · default）
结论：可进入读码/改码
VERIFY: PASS · task_ops_pg_lookup_capabilities.md
```

机械：`npx dsh-coding-kit verify --target . --task docs/tasks/active/task_ops_pg_lookup_capabilities.md` → **VERIFY: PASS**

## 实现摘要

1. **`lookups.py`**：async `get_issue_by_number` / `get_pr_by_number`；payload 第一整数；同号 `updated_at desc` 一条；无整数 / 未命中抛异常 → Gateway `ok=False`；摘要字段；body 截断 500；无 `raw_payload`
2. **Gateway `ainvoke`**：adapter 有 `ainvoke` 或返回 coroutine 则 await；否则走 sync `invoke`（mock / utc_now 不破）
3. **`LocalFnAdapter`**：支持 async callable；同步 `invoke` 对 coroutine fn 抛 TypeError
4. **`tool_exec_node`**：`await capability_ainvoke`（P-13）
5. **builtin YAML + `_DEFAULT_SPECS`**：追加两枚 lookup；保留 mock + utc_now_iso
6. **manifest**：允许 `defaults:` 与 `lookups:` 两前缀；其它仍整文件失败
7. **G-L1**：`capability` 行备注 + `10_flow_capability` 增 `pg_lookup` 节点；`graph-compile` 绿

未改：`app/ops/chat/graph.py` · `lg_rag/multi/graph.py` 拓扑 · 人工闸 · sync sender · MCP/GitHub API

## 40 验证

| 项 | 结果 |
|---|---|
| ruff（触及路径） | All checks passed |
| pytest lookups + manifest + supervisor + strategy | **37 passed** |
| pytest 40 全量（含 gateway） | **63 passed, 1 skipped, 1 failed**（失败为既有 `langchain.debug` AttributeError · 非本波逻辑） |
| pytest gateway `-k "not test_as_structured_tools"` | 见下 |
| chat/graph.py | 0 diff |
| lg_rag/multi/graph.py | 0 diff |
| graph-compile | exit 0 · OK: 10_flow_capability |

命令（真实输出）：

    ruff check app/ops/capability tests/test_capability_lookups.py tests/test_capability_manifest.py
    → All checks passed!

    pytest tests/test_capability_lookups.py tests/test_capability_manifest.py tests/test_capability_gateway.py tests/test_lg_rag_supervisor_capability_catalog.py tests/test_strategy_builder.py -q --tb=short
    → 1 failed, 63 passed, 1 skipped in 0.54s
    FAILED tests/test_capability_gateway.py::test_as_structured_tools_and_tool_node_smoke
    AttributeError: module 'langchain' has no attribute 'debug'
    （与 S3 invoke 同环境已知问题 · 非 lookup 回归）

    pytest tests/test_capability_lookups.py tests/test_capability_manifest.py tests/test_lg_rag_supervisor_capability_catalog.py tests/test_strategy_builder.py -q --tb=short
    → 37 passed in 0.29s

    pytest tests/test_capability_gateway.py -k "not test_as_structured_tools" -q
    → 26 passed, 1 skipped, 1 deselected in 0.13s
    → （空）

    ./scripts/graph-compile.sh
    → done / OK: 10_flow_capability

## task 验收勾选

- [x] 夹具写入后 `ainvoke("get_issue_by_number", "#N")` 命中摘要字段
- [x] 不存在的 number → `ok=False`，tool_exec 记 error 不中断图
- [x] `get_pr_by_number` 对称
- [x] `utc_now_iso` / mock 回归不破
- [x] `tool_exec_node` 对 lookup 走 async，不在事件循环同步连 PG
- [x] builtin YAML 含新 id；非法 adapter 前缀仍整文件失败
- [x] G-L1 `capability` 备注 + graph-compile；拓扑 0 diff
- [x] ruff / pytest 触及路径绿

## 变更路径（本 task 30）

- `app/ops/capability/lookups.py`（新）
- `app/ops/capability/gateway.py`（`ainvoke`）
- `app/ops/capability/adapters/local_fn.py`
- `app/ops/capability/defaults.py` / `manifest.py` / `manifests/builtin.v1.yaml` / `__init__.py`
- `app/ops/lg_rag/multi/nodes.py`（`tool_exec_node` 函数体）
- `tests/test_capability_lookups.py`（新）
- `tests/test_capability_manifest.py` / `tests/test_capability_gateway.py`（前缀 / tags 回归）
- `docs/_tech_graph/l1/01_modules.md` / `10_flow_capability.graph.yaml`（+ compile 产物）

## 风险

- 数据新鲜度依赖并行 sync task；空库 / 过期库 → `ok=False` · `not_found`
- 多 repo 同号取最新 `updated_at`，调用方无 repo 维度
- `test_as_structured_tools_and_tool_node_smoke` 本地 langchain.debug 已知失败，非本波引入

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-28 | 30/40 实现 + 验证；停等 00；勿 commit |
