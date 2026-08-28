---
graph_id: 10_flow_chat
version: 2026-08-25
generated_at: 2026-08-28T01:06:21Z
source: 10_flow_chat.graph.yaml
---

# Chat 流式对话流程

用户通过 SSE 与后端对话的完整流程：HTTP 入口、LangGraph StateGraph 执行（含 RAG 检索链）、LLM 调用、事件归档。

## Mermaid

```mermaid
flowchart TB
    client["用户 / 前端"]
    chat_stream["POST /api/ops/chat/stream"]
    chat_ws["WS /api/ops/chat/ws"]
    event_gen["ChatEventStreamer (SSE/WS 共享)"]
    chat_service["run_chat_stream"]
    stategraph["Chat StateGraph"]
    intent["detect_intent"]
    context["load_context"]
    retrieve["hybrid_recall"]
    grade["grade_chunks + gate"]
    refuse_answer["refuse on low relevance"]
    answer["generate_answer"]
    rag["RAG hybrid_recall"]
    llm["LLM Provider"]
    db["PostgreSQL"]
    main_doc[">../l0/00_main.md"]
    admin_sync["POST /api/ops/admin/sync"]

    client -->|"POST sync payload"| admin_sync
    %% → app/ops/admin/sync.py#L29
    admin_sync -->|"upserts repo/issues/PRs/snapshots"| db
    %% → app/ops/admin/sync.py#L36
    chat_stream -->|"creates"| event_gen
    %% → app/ops/chat/router.py#L75
    client -->|"message / cancel"| chat_ws
    %% → app/ops/chat/ws.py#L79
    chat_ws -->|"creates"| event_gen
    %% → app/ops/chat/ws.py#L165
    chat_ws -->|"JSON frames"| client
    chat_ws -->|"request_cancel"| event_gen
    chat_stream -->|"inserts ops_runs"| db
    event_gen -->|"SSE / WS 事件流"| client
    event_gen -->|"invokes"| chat_service
    %% → app/ops/chat/streaming.py#L232
    chat_service -->|"astream_events"| stategraph
    %% → app/ops/chat/service.py#L31
    %% → app/ops/chat/graph.py#L29
    stategraph -->|"first_node"| intent
    %% → app/ops/chat/graph.py#L37
    intent -->|"[issue_qa]"| context
    %% → app/ops/chat/graph.py#L40
    intent -->|"[general#124;overview]"| retrieve
    %% → app/ops/chat/graph.py#L40
    context -->|"query ops_issues"| db
    context --> answer
    %% → app/ops/chat/graph.py#L49
    retrieve -->|"hybrid_recall"| rag
    %% → app/ops/chat/rag_nodes.py#L64
    %% → app/ops/rag/retrieve.py::hybrid_recall
    retrieve -->|"vector / FTS query"| db
    retrieve --> grade
    %% → app/ops/chat/graph.py#L50
    grade -->|"[refuse]"| refuse_answer
    %% → app/ops/chat/graph.py#L51
    grade -->|"[generate_answer]"| answer
    %% → app/ops/chat/graph.py#L51
    grade -->|"grade_chunks"| llm
    answer -->|"complete_stream"| llm
    %% → app/ops/chat/nodes.py#L176
    chat_service -->|"inserts ops_run_events"| db
    event_gen -->|"updates ops_runs"| db
    answer -->|"加载"| main_doc

    classDef phase fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef doc fill:#fff8e1,stroke:#ff6f00,stroke-width:1px
    classDef infra fill:#e8f5e9,stroke:#2e7d32,stroke-width:1px
    class chat_stream,chat_ws,event_gen,chat_service,intent,context,retrieve,grade,refuse_answer,answer,admin_sync phase
    class stategraph doc
    class client,rag,llm,db,main_doc infra
```

## Structured Data

### Nodes

| ID | Label | Kind |
|----|-------|------|
| client | 用户 / 前端 | external |
| chat_stream | POST /api/ops/chat/stream | flow |
| chat_ws | WS /api/ops/chat/ws | flow |
| event_gen | ChatEventStreamer (SSE/WS 共享) | flow |
| chat_service | run_chat_stream | flow |
| stategraph | Chat StateGraph | struct |
| intent | detect_intent | flow |
| context | load_context | flow |
| retrieve | hybrid_recall | flow |
| grade | grade_chunks + gate | flow |
| refuse_answer | refuse on low relevance | flow |
| answer | generate_answer | flow |
| rag | RAG hybrid_recall | external |
| llm | LLM Provider | external |
| db | PostgreSQL | external |
| main_doc | >../l0/00_main.md | external |
| admin_sync | POST /api/ops/admin/sync | flow |

### Edges

| From | To | Mark | Type | Label | Anchors |
|------|----|------|------|-------|---------|
| client | admin_sync | -> | depends_on | POST sync payload | 1 anchor(s) |
| admin_sync | db | -> | depends_on | upserts repo/issues/PRs/snapshots | 1 anchor(s) |
| chat_stream | event_gen | -> | depends_on | creates | 1 anchor(s) |
| client | chat_ws | -> | depends_on | message / cancel | 1 anchor(s) |
| chat_ws | event_gen | -> | depends_on | creates | 1 anchor(s) |
| chat_ws | client | -> | depends_on | JSON frames |  |
| chat_ws | event_gen | -> | depends_on | request_cancel |  |
| chat_stream | db | -> | depends_on | inserts ops_runs |  |
| event_gen | client | -> | depends_on | SSE / WS 事件流 |  |
| event_gen | chat_service | -> | depends_on | invokes | 1 anchor(s) |
| chat_service | stategraph | -> | depends_on | astream_events | 2 anchor(s) |
| stategraph | intent | -> | depends_on | first_node | 1 anchor(s) |
| intent | context | ?> | branches | [issue_qa] | 1 anchor(s) |
| intent | retrieve | ?> | branches | [general\|overview] | 1 anchor(s) |
| context | db | -> | depends_on | query ops_issues |  |
| context | answer | -> | depends_on | -> | 1 anchor(s) |
| retrieve | rag | ::triggers | triggers | hybrid_recall | 2 anchor(s) |
| retrieve | db | -> | depends_on | vector / FTS query |  |
| retrieve | grade | -> | depends_on | -> | 1 anchor(s) |
| grade | refuse_answer | ?> | branches | [refuse] | 1 anchor(s) |
| grade | answer | ?> | branches | [generate_answer] | 1 anchor(s) |
| grade | llm | -> | depends_on | grade_chunks |  |
| answer | llm | -> | depends_on | complete_stream | 1 anchor(s) |
| chat_service | db | -> | depends_on | inserts ops_run_events |  |
| event_gen | db | -> | depends_on | updates ops_runs |  |
| answer | main_doc | -> | depends_on | 加载 |  |
