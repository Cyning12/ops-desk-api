---
graph_id: 10_flow_structured_output
version: 2026-08-26
generated_at: 2026-08-30T11:37:35Z
source: 10_flow_structured_output.graph.yaml
---

# Structured Output Gateway 管道

LLM 原始文本 → extract/parse →（可选）deterministic repair → Pydantic/ensure/validate → 失败则预算内 OUTPUT CORRECTION 重试。Host 权威；供 lg_rag 结构化节点复用。不是 Skill。

## Mermaid

```mermaid
flowchart TB
    caller["调用方（lg_rag router / supervisor / info_extract）"]
    complete["acomplete_structured（触发 LLM）"]
    parse_only["parse_only（无 LLM 管道入口）"]
    extract["extract_json_object（剥 fence / 抽对象）"]
    repair["deterministic_repair（仅结构符号）"]
    validate["Pydantic + ensure_keys + custom validate"]
    outcome["ParseOutcome / T #124; StructuredFailure"]
    correction["OUTPUT CORRECTION 注入（预算内重试）"]
    llm["LLM Provider"]
    lg_rag_doc[">./10_flow_lg_rag.md"]
    modules_doc[">./01_modules.md"]

    caller -->|"complete_structured 路径"| complete
    %% → app/ops/lg_rag/nodes.py::_classify_route
    %% → app/ops/lg_rag/multi/nodes.py::supervisor_node
    caller -->|"已有 raw text → parse_only"| parse_only
    %% → app/ops/lg_rag/multi/nodes.py::info_extract_node
    complete -->|"provider.complete"| llm
    %% → app/ops/structured_output/complete.py::acomplete_structured
    complete -->|"raw → 管道"| parse_only
    %% → app/ops/structured_output/complete.py::acomplete_structured
    parse_only -->|"step 1"| extract
    %% → app/ops/structured_output/parse.py::parse_only
    extract -->|"parse 失败时"| repair
    %% → app/ops/structured_output/parse.py::_try_extract_with_optional_repair
    extract -->|"抽出 dict"| validate
    %% → app/ops/structured_output/parse.py::parse_only
    repair -->|"repair 后再抽"| validate
    %% → app/ops/structured_output/parse.py::_try_extract_with_optional_repair
    validate -->|"ok → data；fail → error（无半成功）"| outcome
    %% → app/ops/structured_output/parse.py::parse_only
    outcome -->|"fail 且预算内且非 no_retry"| correction
    %% → app/ops/structured_output/complete.py::acomplete_structured
    correction -->|"完整重生成"| complete
    %% → app/ops/structured_output/complete.py::acomplete_structured
    outcome -->|"成功 T 或 StructuredFailure"| caller
    %% → app/ops/structured_output/complete.py::acomplete_structured
    outcome -->|"接入面"| lg_rag_doc
    caller -->|"module_id=structured_output"| modules_doc

    classDef phase fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef doc fill:#fff8e1,stroke:#ff6f00,stroke-width:1px
    classDef infra fill:#e8f5e9,stroke:#2e7d32,stroke-width:1px
    class complete,parse_only,extract,repair,validate,outcome,correction phase
    class caller,llm,lg_rag_doc,modules_doc infra
```

## Structured Data

### Nodes

| ID | Label | Kind |
|----|-------|------|
| caller | 调用方（lg_rag router / supervisor / info_extract） | external |
| complete | acomplete_structured（触发 LLM） | flow |
| parse_only | parse_only（无 LLM 管道入口） | flow |
| extract | extract_json_object（剥 fence / 抽对象） | flow |
| repair | deterministic_repair（仅结构符号） | flow |
| validate | Pydantic + ensure_keys + custom validate | flow |
| outcome | ParseOutcome / T \| StructuredFailure | flow |
| correction | OUTPUT CORRECTION 注入（预算内重试） | flow |
| llm | LLM Provider | external |
| lg_rag_doc | >./10_flow_lg_rag.md | external |
| modules_doc | >./01_modules.md | external |

### Edges

| From | To | Mark | Type | Label | Anchors |
|------|----|------|------|-------|---------|
| caller | complete | -> | depends_on | complete_structured 路径 | 2 anchor(s) |
| caller | parse_only | -> | depends_on | 已有 raw text → parse_only | 1 anchor(s) |
| complete | llm | -> | depends_on | provider.complete | 1 anchor(s) |
| complete | parse_only | -> | depends_on | raw → 管道 | 1 anchor(s) |
| parse_only | extract | -> | depends_on | step 1 | 1 anchor(s) |
| extract | repair | ?> | branches | parse 失败时 | 1 anchor(s) |
| extract | validate | -> | depends_on | 抽出 dict | 1 anchor(s) |
| repair | validate | -> | depends_on | repair 后再抽 | 1 anchor(s) |
| validate | outcome | -> | depends_on | ok → data；fail → error（无半成功） | 1 anchor(s) |
| outcome | correction | ?> | branches | fail 且预算内且非 no_retry | 1 anchor(s) |
| correction | complete | ::triggers | triggers | 完整重生成 | 1 anchor(s) |
| outcome | caller | -> | depends_on | 成功 T 或 StructuredFailure | 1 anchor(s) |
| outcome | lg_rag_doc | -> | depends_on | 接入面 |  |
| caller | modules_doc | -> | depends_on | module_id=structured_output |  |
