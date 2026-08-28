# Invoke：30/40 · catalog-manifest-yaml（S3）

| 字段 | 值 |
|---|---|
| hat_id | 30/40 |
| task_slug | catalog-manifest-yaml |
| git_branch | `task/catalog-manifest-yaml` |
| related_review | `task_catalog_manifest_yaml_audit_R1_20260828.md` |
| notes | **未** commit / **未** push；交 00 验收 |

## GATE_VERIFY

```text
## 人工闸扫描（GATE_VERIFY · 首输出）

| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---------------|--------------|-----------------|--------|-----------|------------|
| HG-TASK-DRAFT | approved | approved（PROMPT） | Y | N（22-R1） | ✅ |
| HG-AUDIT-R1 | approved | approved（PROMPT） | Y | Y | ✅ |
| HG-GRAPH-MODULES | approved | approved（PROMPT · 仅备注、不增一级） | Y | Y | ✅ |

reviews：task_catalog_manifest_yaml_audit_R1_20260828.md 存在且 R1 通过？ 是
pre-30 invoke：required ∩ {10,20,00} 齐全？ 是（00 + 10；required_invoke_hats=10,30 · default）
结论：可进入读码/改码
VERIFY: PASS · task_catalog_manifest_yaml.md
```

机械：`npx dsh-coding-kit verify --target . --task docs/tasks/active/task_catalog_manifest_yaml.md` → **VERIFY: PASS**

## 实现摘要

1. **`load_capability_manifest(path)`** `app/ops/capability/manifest.py`：YAML + JSON；`yaml.safe_load`；先全量校验再 register（整文件失败、不半套）
2. **adapter 白名单** 仅 `local_fn:app.ops.capability.defaults:<attr>`；kind 仅 `local_fn`；缺 id / 未知 kind / 密钥形字段 → `ManifestError`
3. **内置** `app/ops/capability/manifests/builtin.v1.yaml` 三枚对齐 `_DEFAULT_SPECS`（含 `utc_now_iso`）
4. **`ensure_default_capabilities`**：优先 load builtin；文件缺失回退 `_DEFAULT_SPECS`；已注册 skip（幂等）
5. **S3-b**：`ManifestLoadResult.version` + `capability_manifest_count`；模块级 `get_capability_manifest_metadata`；显式 `reload_capability_manifest`（测试/运维）；包内无 HTTP/router
6. **G-L1**：`capability` 行备注 + `10_flow_capability.graph.yaml` 增 `load_manifest` 节点；`./scripts/graph-compile.sh` 绿
7. GUIDE 一行指针回 ROADMAP §8

未改：`app/ops/chat/graph.py` · `lg_rag/multi/graph.py` 拓扑 · Builder YAML 解析 · S4 Critic/Eval · MCP/sandbox/cli/skill 从 manifest 注册

## 40 验证

| 项 | 结果 |
|---|---|
| ruff（触及路径） | 0 · All checks passed |
| pytest `test_capability_manifest` | **9 passed** |
| pytest gateway（除 langchain.debug smoke） | **26 passed, 1 skipped** |
| pytest strategy_builder（S1/S2 不回归） | **9 passed**（计入 37 绿集） |
| pytest intent_schema + intent_node + supervisor_catalog | 计入合计 **37 passed** |
| `test_as_structured_tools_and_tool_node_smoke` | **failed** · 本地 `langchain.debug` AttributeError（与 S1/S2 invoke 同环境已知问题 · 非 S3 逻辑回归） |
| chat/graph.py | 0 diff |
| lg_rag/multi/graph.py | 0 diff |
| graph-compile | exit 0 · OK: 10_flow_capability |

命令（绿集）：

    pytest tests/test_capability_manifest.py tests/test_strategy_builder.py tests/test_intent_schema.py tests/test_intent_node.py tests/test_lg_rag_supervisor_capability_catalog.py -q
    → 37 passed

    pytest tests/test_capability_gateway.py -k "not test_as_structured_tools" -q
    → 26 passed, 1 skipped

    ruff check app/ops/capability/manifest.py app/ops/capability/defaults.py tests/test_capability_manifest.py
    → All checks passed

    git diff -- app/ops/chat/graph.py app/ops/lg_rag/multi/graph.py → 空
    ./scripts/graph-compile.sh → done / OK: 10_flow_capability

## task 验收勾选

- [x] S3-a：fixture YAML/JSON load 后 `list_capabilities` 含声明 id；builtin 与 `utc_now_iso` 等三枚对齐
- [x] S3-a：非法 adapter / 非白名单 module / 非 local_fn → **整文件失败**，不留下半套
- [x] S3-a：`enabled: false` 跳过；无密钥字段
- [x] S3-a：`ensure_default_capabilities` 幂等（YAML 优先，缺文件回退硬编码）
- [x] S3-b：load 暴露 version + count；显式 reload 可测；无 HTTP/每请求钩子
- [x] G-L1 `capability` 备注 + flow + graph-compile
- [x] ruff / pytest 触及路径绿；`chat/graph.py` 与 lg_rag 图拓扑零 diff

## 变更路径（本 task 30）

- `app/ops/capability/manifest.py`（新建）
- `app/ops/capability/manifests/builtin.v1.yaml`（新建）
- `app/ops/capability/defaults.py`（ensure 接 loader）
- `tests/test_capability_manifest.py`（新建）
- `docs/_tech_graph/l1/01_modules.md` · `10_flow_capability.graph.yaml`（+ compile 产出 md/json）
- `docs/guides/GUIDE_capability-portable-core-mode-a_v0.md`（ROADMAP §8 指针）
- `docs/tasks/active/task_catalog_manifest_yaml.md`（验收勾选）
- 本 invoke

00 已落盘未提交文档（task/invoke/audit/ROADMAP）保留，未混改无关 active task。

| 2026-08-28 | 30/40 PASS（langchain.debug smoke 待 CI/本地环境） · 报 00 |
