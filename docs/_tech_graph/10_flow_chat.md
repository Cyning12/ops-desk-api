---
graph_id: 10_flow_chat
version: 2026-07-16
generated_at: 2026-07-24T01:45:15Z
source: 10_flow_chat.graph.yaml
---

# Chat 流式对话流程

用户通过 SSE 与后端对话的完整流程：HTTP 入口、LangGraph StateGraph 执行、LLM 调用、事件归档。

## Mermaid

```mermaid
flowchart TB
    client[用户 / 前端]
    chat_stream[POST /api/ops/chat/stream]
    chat_ws[WS /api/ops/chat/ws]
    event_gen[ChatEventStreamer (SSE/WS 共享)]
    chat_service[run_chat_stream]
    stategraph[Chat StateGraph]
    intent[detect_intent]
    context[load_context]
    answer[generate_answer]
    llm[LLM Provider]
    db[PostgreSQL]
    main_doc[>00_main.md]
    admin_sync[POST /api/ops/admin/sync]

    client --"POST sync payload"--> admin_sync
    // → app/ops/admin/sync.py#L45
    admin_sync --"upserts repo/issues/PRs/snapshots"--> db
    // → app/ops/admin/sync.py#L45
    chat_stream --"creates"--> event_gen
    // → app/ops/chat/router.py#L36
    client --"message / cancel"--> chat_ws
    // → app/ops/chat/ws.py#L80
    chat_ws --"creates"--> event_gen
    // → app/ops/chat/ws.py#L120
    chat_ws --"JSON frames"--> client
    chat_ws --"request_cancel"--> event_gen
    chat_stream --"inserts ops_runs"--> db
    event_gen --"SSE / WS 事件流"--> client
    event_gen --"invokes"--> chat_service
    // → app/ops/chat/streaming.py#L170
    chat_service --"astream_events"--> stategraph
    // → app/ops/chat/service.py#L9
    // → app/ops/chat/graph.py#L26
    stategraph --"first_node"--> intent
    // → app/ops/chat/graph.py#L17
    intent --"[issue_qa]"--> context
    // → app/ops/chat/graph.py#L21
    intent --"[overview|general]"--> answer
    // → app/ops/chat/graph.py#L21
    context --"query ops_issues"--> db
    context --"->"--> answer
    // → app/ops/chat/graph.py#L23
    answer --"complete_stream"--> llm
    // → app/ops/chat/nodes.py#L60
    chat_service --"inserts ops_run_events"--> db
    event_gen --"updates ops_runs"--> db
    answer --"加载"--> main_doc

    classDef phase fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef doc fill:#fff8e1,stroke:#ff6f00,stroke-width:1px
    classDef infra fill:#e8f5e9,stroke:#2e7d32,stroke-width:1px
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
| answer | generate_answer | flow |
| llm | LLM Provider | external |
| db | PostgreSQL | external |
| main_doc | >00_main.md | external |
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
| intent | context | -> | depends_on | [issue_qa] | 1 anchor(s) |
| intent | answer | -> | depends_on | [overview\|general] | 1 anchor(s) |
| context | db | -> | depends_on | query ops_issues |  |
| context | answer | -> | depends_on | -> | 1 anchor(s) |
| answer | llm | -> | depends_on | complete_stream | 1 anchor(s) |
| chat_service | db | -> | depends_on | inserts ops_run_events |  |
| event_gen | db | -> | depends_on | updates ops_runs |  |
| answer | main_doc | -> | depends_on | 加载 |  |
