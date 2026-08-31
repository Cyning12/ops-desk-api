---
graph_id: 11_flow_sync_to_chat
version: 2026-08-28
generated_at: sha256-7b7553e5ef777ce2
source: 11_flow_sync_to_chat.graph.yaml
---

# Sync 数据到 Chat 上下文流程

GHA sender 组装 SyncPayload，经 admin sync 导入 repo/issue/PR/graph，再被只读接口和 Chat 上下文加载消费

## Mermaid

```mermaid
flowchart LR
    client["用户 / iOS"]
    gha_sender["GHA ops-sync-kimi-code"]
    admin_sync["POST /api/ops/admin/sync"]
    issues_endpoint["GET /api/ops/issues"]
    pulls_endpoint["GET /api/ops/pulls"]
    graph_endpoint["GET /api/ops/graph"]
    chat_stream["POST /api/ops/chat/stream"]
    db["PostgreSQL"]

    client -->|"POST sync payload"| admin_sync
    %% → app/ops/admin/sync.py#L28
    gha_sender -->|"POST SyncPayload Bearer"| admin_sync
    %% → app/ops/admin/sender/post.py#L12
    %% → .github/workflows/ops_sync_kimi_code.yml#L1
    admin_sync -->|"upserts ops_repos / ops_issues / ops_pull_requests / snapshots"| db
    %% → app/ops/admin/service.py#L46
    db -->|"query"| issues_endpoint
    %% → app/ops/issues.py#L40
    db -->|"query"| pulls_endpoint
    %% → app/ops/pulls.py#L38
    db -->|"query latest"| graph_endpoint
    %% → app/ops/graph.py#L21
    db -->|"load_issue_context"| chat_stream
    %% → app/ops/chat/nodes.py#L99
    issues_endpoint -->|"JSON list"| client
    pulls_endpoint -->|"JSON list"| client
    graph_endpoint -->|"JSON snapshot"| client
    chat_stream -->|"SSE"| client

    classDef phase fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef doc fill:#fff8e1,stroke:#ff6f00,stroke-width:1px
    classDef infra fill:#e8f5e9,stroke:#2e7d32,stroke-width:1px
    class admin_sync,issues_endpoint,pulls_endpoint,graph_endpoint,chat_stream phase
    class client,gha_sender,db infra
```

## Structured Data

### Nodes

| ID | Label | Kind |
|----|-------|------|
| client | 用户 / iOS | external |
| gha_sender | GHA ops-sync-kimi-code | external |
| admin_sync | POST /api/ops/admin/sync | flow |
| issues_endpoint | GET /api/ops/issues | flow |
| pulls_endpoint | GET /api/ops/pulls | flow |
| graph_endpoint | GET /api/ops/graph | flow |
| chat_stream | POST /api/ops/chat/stream | flow |
| db | PostgreSQL | external |

### Edges

| From | To | Mark | Type | Label | Anchors |
|------|----|------|------|-------|---------|
| client | admin_sync | -> | depends_on | POST sync payload | 1 anchor(s) |
| gha_sender | admin_sync | -> | depends_on | POST SyncPayload Bearer | 2 anchor(s) |
| admin_sync | db | -> | depends_on | upserts ops_repos / ops_issues / ops_pull_requests / snapshots | 1 anchor(s) |
| db | issues_endpoint | -> | depends_on | query | 1 anchor(s) |
| db | pulls_endpoint | -> | depends_on | query | 1 anchor(s) |
| db | graph_endpoint | -> | depends_on | query latest | 1 anchor(s) |
| db | chat_stream | -> | depends_on | load_issue_context | 1 anchor(s) |
| issues_endpoint | client | -> | depends_on | JSON list |  |
| pulls_endpoint | client | -> | depends_on | JSON list |  |
| graph_endpoint | client | -> | depends_on | JSON snapshot |  |
| chat_stream | client | -> | depends_on | SSE |  |
