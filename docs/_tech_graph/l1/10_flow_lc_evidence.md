---
graph_id: 10_flow_lc_evidence
version: 2026-08-24
generated_at: 2026-08-27T03:52:14Z
source: 10_flow_lc_evidence.graph.yaml
---

# LC Evidence 旁路答问流程

POST /api/ops/lc-evidence/invoke → LCEL chain（retrieve → grade(gate) → answer）；旁路独立链路，默认不进入 chat/graph；gate 拒答仍返回 200 {ok,data}（freeze lc-evidence-http-v1）。

## Mermaid

```mermaid
flowchart TB
    client["用户 / 前端"]
    lc_invoke["POST /api/ops/lc-evidence/invoke（freeze lc-evidence-http-v1）"]
    chain["ainvoke_evidence_answer（LCEL · 不进入 chat/graph）"]
    retrieve["retrieve_evidence"]
    grade["grade_chunk + decide_grade（gate）"]
    answer["answer_question（按 gate_action 应答/拒答）"]
    rag["RAG hybrid_recall"]
    llm["LLM Provider"]
    db["PostgreSQL"]
    main_doc[">../l0/00_main.md"]

    client -->|"POST {query}（cookie auth）"| lc_invoke
    %% → app/ops/lc_evidence_chain/router.py#L117
    lc_invoke -->|"ainvoke"| chain
    %% → app/ops/lc_evidence_chain/router.py#L124
    lc_invoke -->|"200 {ok,data}（gate refuse 仍 200）"| client
    %% → app/ops/lc_evidence_chain/router.py#L138
    chain -->|"first step"| retrieve
    %% → app/ops/lc_evidence_chain/chain.py#L115
    retrieve -->|"hybrid_recall"| rag
    %% → app/ops/lc_evidence_chain/retrieve.py#L34
    %% → app/ops/rag/retrieve.py::hybrid_recall
    retrieve -->|"vector / FTS query（经 rag）"| db
    retrieve --> grade
    %% → app/ops/lc_evidence_chain/chain.py#L118
    grade -->|"kept evidence + meta.gate_action"| answer
    %% → app/ops/lc_evidence_chain/chain.py#L118
    grade -->|"grade_chunk"| llm
    %% → app/ops/lc_evidence_chain/grader.py#L27
    answer -->|"complete"| llm
    %% → app/ops/lc_evidence_chain/answer.py#L116
    answer -->|"加载"| main_doc

    classDef phase fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef doc fill:#fff8e1,stroke:#ff6f00,stroke-width:1px
    classDef infra fill:#e8f5e9,stroke:#2e7d32,stroke-width:1px
    class lc_invoke,chain,retrieve,grade,answer phase
    class client,rag,llm,db,main_doc infra
```

## Structured Data

### Nodes

| ID | Label | Kind |
|----|-------|------|
| client | 用户 / 前端 | external |
| lc_invoke | POST /api/ops/lc-evidence/invoke（freeze lc-evidence-http-v1） | flow |
| chain | ainvoke_evidence_answer（LCEL · 不进入 chat/graph） | flow |
| retrieve | retrieve_evidence | flow |
| grade | grade_chunk + decide_grade（gate） | flow |
| answer | answer_question（按 gate_action 应答/拒答） | flow |
| rag | RAG hybrid_recall | external |
| llm | LLM Provider | external |
| db | PostgreSQL | external |
| main_doc | >../l0/00_main.md | external |

### Edges

| From | To | Mark | Type | Label | Anchors |
|------|----|------|------|-------|---------|
| client | lc_invoke | -> | depends_on | POST {query}（cookie auth） | 1 anchor(s) |
| lc_invoke | chain | -> | depends_on | ainvoke | 1 anchor(s) |
| lc_invoke | client | -> | depends_on | 200 {ok,data}（gate refuse 仍 200） | 1 anchor(s) |
| chain | retrieve | -> | depends_on | first step | 1 anchor(s) |
| retrieve | rag | ::triggers | triggers | hybrid_recall | 2 anchor(s) |
| retrieve | db | -> | depends_on | vector / FTS query（经 rag） |  |
| retrieve | grade | -> | depends_on | -> | 1 anchor(s) |
| grade | answer | -> | depends_on | kept evidence + meta.gate_action | 1 anchor(s) |
| grade | llm | -> | depends_on | grade_chunk | 1 anchor(s) |
| answer | llm | -> | depends_on | complete | 1 anchor(s) |
| answer | main_doc | -> | depends_on | 加载 |  |
