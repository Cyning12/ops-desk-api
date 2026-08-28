---
graph_id: 10_flow_capability
version: 2026-08-28
generated_at: 2026-08-28T02:18:29Z
source: 10_flow_capability.graph.yaml
---

# Capability Gateway 注册与 invoke

能力注册表 + Filter + 统一 invoke/ainvoke；YAML/JSON manifest 加载 register（仅 local_fn · defaults/lookups 前缀）；local_fn 默认含本库 issue/PR 只读 lookup；可选 schemas_for_llm/ToolNode；mcp/sandbox/cli mock 探针与 skill stub 默认关闭。不是业界 LLM Gateway。首接入面：lg_rag tool_exec_node。

## Mermaid

```mermaid
flowchart TB
    caller["调用方（lg_rag tool_exec_node）"]
    load_manifest["load_capability_manifest（YAML/JSON → register）"]
    register["register / defaults.ensure_default_capabilities"]
    list_filter["list_capabilities / schemas_for_llm（Filter）"]
    invoke["invoke / ainvoke(capability_id, args)"]
    pg_lookup["lookups.get_issue/pr_by_number（本库 PG 只读）"]
    local_fn["LocalFnAdapter"]
    probes["mcp / sandbox / cli probes（默认关闭）"]
    skill_stub["skill provide/invoke stub（无完整引擎）"]
    result["CapabilityResult（ok / output / error）"]
    fc_optional["可选 as_tool_node（不挂 multi 主路径）"]
    lg_rag_doc[">./10_flow_lg_rag.md"]
    modules_doc[">./01_modules.md"]

    load_manifest -->|"Host register（仅 local_fn）"| register
    %% → app/ops/capability/manifest.py::load_capability_manifest
    register -->|"编目可见"| list_filter
    %% → app/ops/capability/gateway.py::list_capabilities
    list_filter -->|"可选 FC 暴露"| fc_optional
    %% → app/ops/capability/adapters/langchain_tools.py::as_structured_tools
    caller -->|"tool 子任务"| invoke
    %% → app/ops/lg_rag/multi/nodes.py::tool_exec_node
    invoke -->|"kind=local_fn（默认）"| local_fn
    %% → app/ops/capability/gateway.py::_dispatch
    %% → app/ops/capability/gateway.py::_adispatch
    invoke -->|"kind=mcp#124;sandbox#124;cli（若已 register）"| probes
    %% → app/ops/capability/probes.py::register_p2_probes
    invoke -->|"kind=skill → provide/invoke stub"| skill_stub
    %% → app/ops/capability/gateway.py::provide
    local_fn -->|"async lookup（P-13 ainvoke）"| pg_lookup
    %% → app/ops/capability/lookups.py::get_issue_by_number
    pg_lookup -->|"摘要字段（无 raw_payload）"| result
    %% → app/ops/capability/lookups.py::get_issue_by_number
    local_fn -->|"ok / error"| result
    %% → app/ops/capability/gateway.py::invoke
    probes -->|"mock 探针结果"| result
    skill_stub -->|"stub / NotImplemented → ok=False"| result
    result -->|"写入 subtask_results；未知 id 不垮图"| caller
    %% → app/ops/lg_rag/multi/nodes.py::tool_exec_node
    register -->|"显式 register_p2_probes(enabled=…)"| probes
    result -->|"接入面"| lg_rag_doc
    caller -->|"module_id=capability"| modules_doc

    classDef phase fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef doc fill:#fff8e1,stroke:#ff6f00,stroke-width:1px
    classDef infra fill:#e8f5e9,stroke:#2e7d32,stroke-width:1px
    class load_manifest,register,list_filter,invoke,pg_lookup,local_fn,probes,skill_stub,result,fc_optional phase
    class caller,lg_rag_doc,modules_doc infra
```

## Structured Data

### Nodes

| ID | Label | Kind |
|----|-------|------|
| caller | 调用方（lg_rag tool_exec_node） | external |
| load_manifest | load_capability_manifest（YAML/JSON → register） | flow |
| register | register / defaults.ensure_default_capabilities | flow |
| list_filter | list_capabilities / schemas_for_llm（Filter） | flow |
| invoke | invoke / ainvoke(capability_id, args) | flow |
| pg_lookup | lookups.get_issue/pr_by_number（本库 PG 只读） | flow |
| local_fn | LocalFnAdapter | flow |
| probes | mcp / sandbox / cli probes（默认关闭） | flow |
| skill_stub | skill provide/invoke stub（无完整引擎） | flow |
| result | CapabilityResult（ok / output / error） | flow |
| fc_optional | 可选 as_tool_node（不挂 multi 主路径） | flow |
| lg_rag_doc | >./10_flow_lg_rag.md | external |
| modules_doc | >./01_modules.md | external |

### Edges

| From | To | Mark | Type | Label | Anchors |
|------|----|------|------|-------|---------|
| load_manifest | register | -> | depends_on | Host register（仅 local_fn） | 1 anchor(s) |
| register | list_filter | -> | depends_on | 编目可见 | 1 anchor(s) |
| list_filter | fc_optional | ?> | branches | 可选 FC 暴露 | 1 anchor(s) |
| caller | invoke | -> | depends_on | tool 子任务 | 1 anchor(s) |
| invoke | local_fn | -> | depends_on | kind=local_fn（默认） | 2 anchor(s) |
| invoke | probes | ?> | branches | kind=mcp\|sandbox\|cli（若已 register） | 1 anchor(s) |
| invoke | skill_stub | ?> | branches | kind=skill → provide/invoke stub | 1 anchor(s) |
| local_fn | pg_lookup | ?> | branches | async lookup（P-13 ainvoke） | 1 anchor(s) |
| pg_lookup | result | -> | depends_on | 摘要字段（无 raw_payload） | 1 anchor(s) |
| local_fn | result | -> | depends_on | ok / error | 1 anchor(s) |
| probes | result | -> | depends_on | mock 探针结果 |  |
| skill_stub | result | -> | depends_on | stub / NotImplemented → ok=False |  |
| result | caller | -> | depends_on | 写入 subtask_results；未知 id 不垮图 | 1 anchor(s) |
| register | probes | ?> | branches | 显式 register_p2_probes(enabled=…) |  |
| result | lg_rag_doc | -> | depends_on | 接入面 |  |
| caller | modules_doc | -> | depends_on | module_id=capability |  |
