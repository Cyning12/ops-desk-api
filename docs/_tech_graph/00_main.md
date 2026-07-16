---
graph_id: 00_main
version: 2026-07-16
generated_at: 2026-07-16T06:14:19Z
source: 00_main.graph.yaml
---

# ops-desk-api 顶层流程总图

Ops Desk 后端 API 的架构总图：FastAPI 入口、各业务路由、LangGraph Chat 流程、数据库表与外部依赖的关系。

## Mermaid

```mermaid
flowchart TB
    client[用户 / 前端]
    health[GET /health]
    app[FastAPI App]
    ops_router[/api/ops Router]
    auth[Auth 路由]
    overview[Overview 路由]
    issues[Issues 路由]
    pulls[Pulls 路由]
    graph[Graph 快照路由]
    admin_sync[Admin Sync 路由]
    chat_router[Chat 路由]
    chat_flow[>10_flow_chat.md]
    llm[LLM Provider]
    db[PostgreSQL]
    struct_doc[>01_struct.md]

    client --"GET"--> health
    client --"HTTP / SSE"--> app
    health --"mounted_on"--> app
    app --"include_router"--> ops_router
    // → app/main.py#L31
    // → app/ops/router.py#L12
    ops_router --"routes"--> auth
    // → app/ops/router.py#L14
    ops_router --"routes"--> overview
    // → app/ops/router.py#L15
    ops_router --"routes"--> issues
    // → app/ops/router.py#L16
    ops_router --"routes"--> pulls
    // → app/ops/router.py#L17
    ops_router --"routes"--> graph
    // → app/ops/router.py#L18
    ops_router --"routes"--> admin_sync
    // → app/ops/router.py#L19
    ops_router --"routes"--> chat_router
    // → app/ops/router.py#L20
    chat_router --"::triggers"--> chat_flow
    // → app/ops/chat/router.py#L48
    chat_flow --"calls"--> llm
    chat_flow --"persists"--> db
    auth --"validates / creates"--> db
    overview --"queries"--> db
    issues --"queries"--> db
    pulls --"queries"--> db
    graph --"queries"--> db
    admin_sync --"upserts"--> db
    app --"加载"--> struct_doc
    app --"depends_on"--> db

    classDef phase fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef doc fill:#fff8e1,stroke:#ff6f00,stroke-width:1px
    classDef infra fill:#e8f5e9,stroke:#2e7d32,stroke-width:1px
```

## Structured Data

### Nodes

| ID | Label | Kind |
|----|-------|------|
| client | 用户 / 前端 | external |
| health | GET /health | flow |
| app | FastAPI App | struct |
| ops_router | /api/ops Router | struct |
| auth | Auth 路由 | flow |
| overview | Overview 路由 | flow |
| issues | Issues 路由 | flow |
| pulls | Pulls 路由 | flow |
| graph | Graph 快照路由 | flow |
| admin_sync | Admin Sync 路由 | flow |
| chat_router | Chat 路由 | flow |
| chat_flow | >10_flow_chat.md | external |
| llm | LLM Provider | external |
| db | PostgreSQL | external |
| struct_doc | >01_struct.md | external |

### Edges

| From | To | Mark | Type | Label | Anchors |
|------|----|------|------|-------|---------|
| client | health | -> | depends_on | GET |  |
| client | app | -> | depends_on | HTTP / SSE |  |
| health | app | -> | depends_on | mounted_on |  |
| app | ops_router | -> | depends_on | include_router | 2 anchor(s) |
| ops_router | auth | -> | depends_on | routes | 1 anchor(s) |
| ops_router | overview | -> | depends_on | routes | 1 anchor(s) |
| ops_router | issues | -> | depends_on | routes | 1 anchor(s) |
| ops_router | pulls | -> | depends_on | routes | 1 anchor(s) |
| ops_router | graph | -> | depends_on | routes | 1 anchor(s) |
| ops_router | admin_sync | -> | depends_on | routes | 1 anchor(s) |
| ops_router | chat_router | -> | depends_on | routes | 1 anchor(s) |
| chat_router | chat_flow | ::triggers | triggers |  | 1 anchor(s) |
| chat_flow | llm | -> | depends_on | calls |  |
| chat_flow | db | -> | depends_on | persists |  |
| auth | db | -> | depends_on | validates / creates |  |
| overview | db | -> | depends_on | queries |  |
| issues | db | -> | depends_on | queries |  |
| pulls | db | -> | depends_on | queries |  |
| graph | db | -> | depends_on | queries |  |
| admin_sync | db | -> | depends_on | upserts |  |
| app | struct_doc | -> | depends_on | 加载 |  |
| app | db | -> | depends_on | depends_on |  |

## Sub-graph Links

- `Struct`: [`01_struct.md`](01_struct.md)（手写 · 无 `.graph.yaml`）
- `Version`: [`02_version.md`](02_version.md)（手写 · 无 `.graph.yaml`）
- 子图编辑源见 `docs/_tech_graph/*.graph.yaml`

