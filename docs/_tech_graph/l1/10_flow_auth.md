---
graph_id: 10_flow_auth
version: 2026-08-25
generated_at: 2026-08-27T03:52:14Z
source: 10_flow_auth.graph.yaml
---

# Authentication Flow

Login, logout, session validation, and iOS latest chat session flow

## Mermaid

```mermaid
flowchart TB
    client["用户 / iOS"]
    login["POST /api/ops/auth/login"]
    logout["POST /api/ops/auth/logout"]
    me["GET /api/ops/auth/me"]
    latest_session["GET /api/ops/chat/sessions/latest"]
    session_check["get_current_user"]
    maintainer_check["require_maintainer"]
    admin_sync["POST /api/ops/admin/sync"]
    db["PostgreSQL"]

    client -->|"POST username + invite_token"| login
    %% → app/ops/auth.py#L57
    login -->|"validate invite token; create ops_sessions"| db
    %% → app/ops/auth.py#L67
    login -->|"Set-Cookie: ops_session"| client
    %% → app/ops/auth.py#L103
    client -->|"POST with cookie"| logout
    %% → app/ops/auth.py#L111
    logout -->|"delete ops_sessions"| db
    %% → app/ops/auth.py#L121
    client -->|"GET with cookie"| me
    %% → app/ops/auth.py#L130
    me -->|"Depends"| session_check
    %% → app/ops/deps.py#L16
    client -->|"GET with cookie"| latest_session
    %% → app/ops/chat/router.py#L103
    latest_session -->|"Depends"| session_check
    %% → app/ops/deps.py#L16
    latest_session -->|"query / create ops_sessions_chat"| db
    %% → app/ops/chat/router.py#L113
    client -->|"POST with cookie"| admin_sync
    %% → app/ops/admin/sync.py#L28
    admin_sync -->|"Depends"| maintainer_check
    %% → app/ops/deps.py#L52
    maintainer_check -->|"Depends"| session_check
    %% → app/ops/deps.py#L52
    session_check -->|"query ops_sessions by token_hash"| db
    %% → app/ops/deps.py#L30

    classDef phase fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef doc fill:#fff8e1,stroke:#ff6f00,stroke-width:1px
    classDef infra fill:#e8f5e9,stroke:#2e7d32,stroke-width:1px
    class login,logout,me,latest_session,session_check,maintainer_check,admin_sync phase
    class client,db infra
```

## Structured Data

### Nodes

| ID | Label | Kind |
|----|-------|------|
| client | 用户 / iOS | external |
| login | POST /api/ops/auth/login | flow |
| logout | POST /api/ops/auth/logout | flow |
| me | GET /api/ops/auth/me | flow |
| latest_session | GET /api/ops/chat/sessions/latest | flow |
| session_check | get_current_user | flow |
| maintainer_check | require_maintainer | flow |
| admin_sync | POST /api/ops/admin/sync | flow |
| db | PostgreSQL | external |

### Edges

| From | To | Mark | Type | Label | Anchors |
|------|----|------|------|-------|---------|
| client | login | -> | depends_on | POST username + invite_token | 1 anchor(s) |
| login | db | -> | depends_on | validate invite token; create ops_sessions | 1 anchor(s) |
| login | client | -> | depends_on | Set-Cookie: ops_session | 1 anchor(s) |
| client | logout | -> | depends_on | POST with cookie | 1 anchor(s) |
| logout | db | -> | depends_on | delete ops_sessions | 1 anchor(s) |
| client | me | -> | depends_on | GET with cookie | 1 anchor(s) |
| me | session_check | -> | depends_on | Depends | 1 anchor(s) |
| client | latest_session | -> | depends_on | GET with cookie | 1 anchor(s) |
| latest_session | session_check | -> | depends_on | Depends | 1 anchor(s) |
| latest_session | db | -> | depends_on | query / create ops_sessions_chat | 1 anchor(s) |
| client | admin_sync | -> | depends_on | POST with cookie | 1 anchor(s) |
| admin_sync | maintainer_check | -> | depends_on | Depends | 1 anchor(s) |
| maintainer_check | session_check | -> | depends_on | Depends | 1 anchor(s) |
| session_check | db | -> | depends_on | query ops_sessions by token_hash | 1 anchor(s) |
