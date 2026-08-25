# V3 人工项材料：kit 1.6.1 emit（无 normalize）vs 本仓现 normalize 产物

> 日期：2026-08-25 · 生成：graph 命令面切换 probe（/tmp/cmd-switch-probe）
> 人工核对点：IDE（Cursor）预览每图是否有边、非单行孤岛；emit 风格差异见各图注记。

## 00_main

### kit 1.6.1 emit（切换后形态）

```mermaid
flowchart TB
    client["用户 / 前端"]
    health["GET /health"]
    app["FastAPI App"]
    ops_router["/api/ops Router"]
    auth["Auth 路由"]
    overview["Overview 路由"]
    issues["Issues 路由"]
    pulls["Pulls 路由"]
    graph["Graph 快照路由"]
    admin_sync["Admin Sync 路由"]
    chat_router["Chat 路由（SSE + WS）"]
    lc_evidence_router["LC Evidence 路由"]
    lg_rag_router["LG RAG 路由"]
    chat_flow[">../l1/10_flow_chat.md"]
    lc_evidence_flow[">../l1/10_flow_lc_evidence.md"]
    lg_rag_flow[">../l1/10_flow_lg_rag.md"]
    llm["LLM Provider"]
    db["PostgreSQL"]
    struct_doc[">../l1/01_modules.md"]

    client -->|"GET"| health
    client -->|"HTTP / SSE"| app
    health -->|"mounted_on"| app
    app -->|"include_router"| ops_router
    %% → app/main.py#L33
    %% → app/ops/router.py#L15
    ops_router -->|"routes"| auth
    %% → app/ops/router.py#L17
    ops_router -->|"routes"| overview
    %% → app/ops/router.py#L18
    ops_router -->|"routes"| issues
    %% → app/ops/router.py#L19
    ops_router -->|"routes"| pulls
    %% → app/ops/router.py#L20
    ops_router -->|"routes"| graph
    %% → app/ops/router.py#L21
    ops_router -->|"routes"| admin_sync
    %% → app/ops/router.py#L22
    ops_router -->|"routes"| chat_router
    %% → app/ops/router.py#L23
    %% → app/ops/router.py#L24
    ops_router -->|"routes"| lc_evidence_router
    %% → app/ops/router.py#L25
    ops_router -->|"routes"| lg_rag_router
    %% → app/ops/router.py#L26
    chat_router -->|"::triggers"| chat_flow
    %% → app/ops/chat/router.py#L33
    lc_evidence_router -->|"::triggers"| lc_evidence_flow
    %% → app/ops/lc_evidence_chain/router.py#L117
    lg_rag_router -->|"::triggers"| lg_rag_flow
    %% → app/ops/lg_rag/router.py#L130
    chat_flow -->|"calls"| llm
    chat_flow -->|"persists"| db
    auth -->|"validates / creates"| db
    overview -->|"queries"| db
    issues -->|"queries"| db
    pulls -->|"queries"| db
    graph -->|"queries"| db
    admin_sync -->|"upserts"| db
    lc_evidence_router -->|"session / query"| db
    lg_rag_router -->|"optional checkpointer"| db
    app -->|"加载"| struct_doc
    app -->|"depends_on"| db

    classDef phase fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef doc fill:#fff8e1,stroke:#ff6f00,stroke-width:1px
    classDef infra fill:#e8f5e9,stroke:#2e7d32,stroke-width:1px
    class health,auth,overview,issues,pulls,graph,admin_sync,chat_router,lc_evidence_router,lg_rag_router phase
    class app,ops_router doc
    class client,chat_flow,lc_evidence_flow,lg_rag_flow,llm,db,struct_doc infra
```

### 本仓现产物（harness emit + normalize）

```mermaid
flowchart TB
    client["用户 / 前端"]
    health["GET /health"]
    app["FastAPI App"]
    ops_router["/api/ops Router"]
    auth["Auth 路由"]
    overview["Overview 路由"]
    issues["Issues 路由"]
    pulls["Pulls 路由"]
    graph["Graph 快照路由"]
    admin_sync["Admin Sync 路由"]
    chat_router["Chat 路由（SSE + WS）"]
    lc_evidence_router["LC Evidence 路由"]
    lg_rag_router["LG RAG 路由"]
    chat_flow[">../l1/10_flow_chat.md"]
    lc_evidence_flow[">../l1/10_flow_lc_evidence.md"]
    lg_rag_flow[">../l1/10_flow_lg_rag.md"]
    llm["LLM Provider"]
    db[PostgreSQL]
    struct_doc[">../l1/01_modules.md"]

    client -->|"GET"| health
    client -->|"HTTP / SSE"| app
    health -->|"mounted_on"| app
    app -->|"include_router"| ops_router
    %% → app/main.py#L33
    %% → app/ops/router.py#L15
    ops_router -->|"routes"| auth
    %% → app/ops/router.py#L17
    ops_router -->|"routes"| overview
    %% → app/ops/router.py#L18
    ops_router -->|"routes"| issues
    %% → app/ops/router.py#L19
    ops_router -->|"routes"| pulls
    %% → app/ops/router.py#L20
    ops_router -->|"routes"| graph
    %% → app/ops/router.py#L21
    ops_router -->|"routes"| admin_sync
    %% → app/ops/router.py#L22
    ops_router -->|"routes"| chat_router
    %% → app/ops/router.py#L23
    %% → app/ops/router.py#L24
    ops_router -->|"routes"| lc_evidence_router
    %% → app/ops/router.py#L25
    ops_router -->|"routes"| lg_rag_router
    %% → app/ops/router.py#L26
    chat_router -->|"::triggers"| chat_flow
    %% → app/ops/chat/router.py#L33
    lc_evidence_router -->|"::triggers"| lc_evidence_flow
    %% → app/ops/lc_evidence_chain/router.py#L117
    lg_rag_router -->|"::triggers"| lg_rag_flow
    %% → app/ops/lg_rag/router.py#L130
    chat_flow -->|"calls"| llm
    chat_flow -->|"persists"| db
    auth -->|"validates / creates"| db
    overview -->|"queries"| db
    issues -->|"queries"| db
    pulls -->|"queries"| db
    graph -->|"queries"| db
    admin_sync -->|"upserts"| db
    lc_evidence_router -->|"session / query"| db
    lg_rag_router -->|"optional checkpointer"| db
    app -->|"加载"| struct_doc
    app -->|"depends_on"| db

    classDef phase fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef doc fill:#fff8e1,stroke:#ff6f00,stroke-width:1px
    classDef infra fill:#e8f5e9,stroke:#2e7d32,stroke-width:1px

    class client,health,app,ops_router,auth,overview,issues,pulls,graph,admin_sync,chat_router,lc_evidence_router,lg_rag_router phase
    class chat_flow,lc_evidence_flow,lg_rag_flow,struct_doc doc
    class llm,db infra
```

---

## 10_flow_auth

### kit 1.6.1 emit（切换后形态）

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

### 本仓现产物（harness emit + normalize）

```mermaid
flowchart TB
    client["用户 / iOS"]
    login["POST /api/ops/auth/login"]
    logout["POST /api/ops/auth/logout"]
    me["GET /api/ops/auth/me"]
    latest_session["GET /api/ops/chat/sessions/latest"]
    session_check[get_current_user]
    maintainer_check[require_maintainer]
    admin_sync["POST /api/ops/admin/sync"]
    db[PostgreSQL]

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

    class client,login,logout,me,latest_session,session_check,maintainer_check,admin_sync phase
    class db infra
```

---

## 10_flow_chat

### kit 1.6.1 emit（切换后形态）

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

### 本仓现产物（harness emit + normalize）

```mermaid
flowchart TB
    client["用户 / 前端"]
    chat_stream["POST /api/ops/chat/stream"]
    chat_ws["WS /api/ops/chat/ws"]
    event_gen["ChatEventStreamer (SSE/WS 共享)"]
    chat_service[run_chat_stream]
    stategraph["Chat StateGraph"]
    intent[detect_intent]
    context[load_context]
    retrieve[hybrid_recall]
    grade["grade_chunks + gate"]
    refuse_answer["refuse on low relevance"]
    answer[generate_answer]
    rag["RAG hybrid_recall"]
    llm["LLM Provider"]
    db[PostgreSQL]
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
    intent -->|"[general|overview]"| retrieve
    %% → app/ops/chat/graph.py#L40
    context -->|"query ops_issues"| db
    context -->|"->"| answer
    %% → app/ops/chat/graph.py#L49
    retrieve -->|"hybrid_recall"| rag
    %% → app/ops/chat/rag_nodes.py#L64
    %% → app/ops/rag/retrieve.py::hybrid_recall
    retrieve -->|"vector / FTS query"| db
    retrieve -->|"->"| grade
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

    class client,chat_stream,chat_ws,event_gen,chat_service,stategraph,intent,context,retrieve,grade,refuse_answer,answer,admin_sync phase
    class main_doc doc
    class rag,llm,db infra
```

---

## 10_flow_lc_evidence

### kit 1.6.1 emit（切换后形态）

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

### 本仓现产物（harness emit + normalize）

```mermaid
flowchart TB
    client["用户 / 前端"]
    lc_invoke["POST /api/ops/lc-evidence/invoke（freeze lc-evidence-http-v1）"]
    chain["ainvoke_evidence_answer（LCEL · 不进入 chat/graph）"]
    retrieve[retrieve_evidence]
    grade["grade_chunk + decide_grade（gate）"]
    answer["answer_question（按 gate_action 应答/拒答）"]
    rag["RAG hybrid_recall"]
    llm["LLM Provider"]
    db[PostgreSQL]
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
    retrieve -->|"->"| grade
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

    class client,lc_invoke,chain,retrieve,grade,answer phase
    class main_doc doc
    class rag,llm,db infra
```

---

## 10_flow_lg_rag

### kit 1.6.1 emit（切换后形态）

```mermaid
flowchart TB
    client["用户 / 前端"]
    lg_invoke["POST /api/ops/lg-rag/invoke（freeze lg-rag-http-v1）"]
    basic_graph["basic 图 build_basic_agent（Phase 1 对照）"]
    router_graph["router 图 build_router_agent（Phase 2-3）"]
    sup_graph["supervisor 图 build_supervisor_agent（Phase 4）"]
    b_rag["rag_node"]
    r_router["router_node（#35;数字快路径 + LLM 三分类）"]
    r_direct["direct_answer_node"]
    r_refuse["refuse_node（固定文案）"]
    r_rag["rag_node（黑盒调 lc chain）"]
    r_evaluate["evaluate_node（复用 chain gate · 零额外 LLM）"]
    r_rewrite["rewrite_node（LLM 改写 · 熔断封顶）"]
    s_supervisor["supervisor_node（LLM 拆解 ≤4 · 失败 fallback 单 rag）"]
    s_dispatch["route_next_subtask（dispatch）"]
    s_rag["rag_subtask_node（复用 router 子图）"]
    s_extract["info_extract_node"]
    s_tool["tool_exec_node（Mock 注册表）"]
    s_aggregator["aggregator_node（LLM 综合）"]
    lc_chain["LC Evidence chain（黑盒 · 不展开 LCEL）"]
    llm["LLM Provider"]
    db["PostgreSQL"]
    main_doc[">../l0/00_main.md"]

    client -->|"POST {query, mode, thread_id}（cookie auth）"| lg_invoke
    %% → app/ops/lg_rag/router.py#L130
    lg_invoke -->|"[mode=basic]"| basic_graph
    %% → app/ops/lg_rag/router.py#L118
    lg_invoke -->|"[mode=router（默认）]"| router_graph
    %% → app/ops/lg_rag/router.py#L122
    lg_invoke -->|"[mode=supervisor]"| sup_graph
    %% → app/ops/lg_rag/router.py#L120
    lg_invoke -->|"200 {ok,data}"| client
    %% → app/ops/lg_rag/router.py#L152
    lg_invoke -->|"optional PG checkpointer（env LG_RAG_HTTP_CHECKPOINTER）"| db
    %% → app/ops/lg_rag/router.py#L125
    basic_graph -->|"START → rag → END"| b_rag
    %% → app/ops/lg_rag/graph.py#L58
    b_rag -->|"ainvoke_evidence_answer"| lc_chain
    %% → app/ops/lg_rag/nodes.py#L160
    %% → app/ops/lc_evidence_chain/chain.py::ainvoke_evidence_answer
    router_graph -->|"START → router"| r_router
    %% → app/ops/lg_rag/graph.py#L72
    r_router -->|"[rag]"| r_rag
    %% → app/ops/lg_rag/graph.py#L77
    r_router -->|"[direct → END]"| r_direct
    %% → app/ops/lg_rag/graph.py#L78
    r_router -->|"[refuse → END]"| r_refuse
    %% → app/ops/lg_rag/graph.py#L79
    r_router -->|"LLM 三分类（fallback=rag）"| llm
    %% → app/ops/lg_rag/nodes.py#L127
    r_rag --> r_evaluate
    %% → app/ops/lg_rag/graph.py#L82
    r_rag -->|"ainvoke_evidence_answer（写回 chain_meta）"| lc_chain
    %% → app/ops/lg_rag/nodes.py#L160
    %% → app/ops/lc_evidence_chain/chain.py::ainvoke_evidence_answer
    r_evaluate -->|"[low 且 retry<2 → rewrite；high/medium → END]"| r_rewrite
    %% → app/ops/lg_rag/graph.py#L87
    %% → app/ops/lg_rag/nodes.py#L204
    r_rewrite -->|"[有新 query → 重试 rag；熔断置空 → END]"| r_rag
    %% → app/ops/lg_rag/graph.py#L95
    %% → app/ops/lg_rag/nodes.py#L261
    r_direct -->|"complete"| llm
    %% → app/ops/lg_rag/nodes.py#L269
    r_rewrite -->|"complete"| llm
    %% → app/ops/lg_rag/nodes.py#L230
    sup_graph -->|"START → supervisor"| s_supervisor
    %% → app/ops/lg_rag/multi/graph.py#L52
    s_supervisor -->|"subtasks（≤4）"| s_dispatch
    %% → app/ops/lg_rag/multi/graph.py#L53
    s_dispatch -->|"[type=rag]"| s_rag
    %% → app/ops/lg_rag/multi/graph.py#L35
    %% → app/ops/lg_rag/multi/nodes.py#L238
    s_dispatch -->|"[type=extract]"| s_extract
    %% → app/ops/lg_rag/multi/graph.py#L36
    %% → app/ops/lg_rag/multi/nodes.py#L238
    s_dispatch -->|"[type=tool]"| s_tool
    %% → app/ops/lg_rag/multi/graph.py#L37
    %% → app/ops/lg_rag/multi/nodes.py#L238
    s_dispatch -->|"[耗尽/空 → aggregate]"| s_aggregator
    %% → app/ops/lg_rag/multi/graph.py#L38
    %% → app/ops/lg_rag/multi/nodes.py#L237
    s_rag -->|"回 dispatch（追加一条结果）"| s_dispatch
    %% → app/ops/lg_rag/multi/graph.py#L55
    s_extract -->|"回 dispatch（追加一条结果）"| s_dispatch
    %% → app/ops/lg_rag/multi/graph.py#L55
    s_tool -->|"回 dispatch（追加一条结果）"| s_dispatch
    %% → app/ops/lg_rag/multi/graph.py#L55
    s_rag -->|"ainvoke_router_agent（复用 router 子图）"| router_graph
    %% → app/ops/lg_rag/multi/nodes.py#L266
    %% → app/ops/lg_rag/graph.py::ainvoke_router_agent
    s_supervisor -->|"complete（拆解）"| llm
    %% → app/ops/lg_rag/multi/nodes.py#L200
    s_extract -->|"complete（抽取）"| llm
    %% → app/ops/lg_rag/multi/nodes.py#L299
    s_aggregator -->|"complete（综合 → END）"| llm
    %% → app/ops/lg_rag/multi/nodes.py#L361
    router_graph -->|"加载"| main_doc

    classDef phase fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef doc fill:#fff8e1,stroke:#ff6f00,stroke-width:1px
    classDef infra fill:#e8f5e9,stroke:#2e7d32,stroke-width:1px
    class lg_invoke,b_rag,r_router,r_direct,r_refuse,r_rag,r_evaluate,r_rewrite,s_supervisor,s_dispatch,s_rag,s_extract,s_tool,s_aggregator phase
    class basic_graph,router_graph,sup_graph doc
    class client,lc_chain,llm,db,main_doc infra
```

### 本仓现产物（harness emit + normalize）

```mermaid
flowchart TB
    client["用户 / 前端"]
    lg_invoke["POST /api/ops/lg-rag/invoke（freeze lg-rag-http-v1）"]
    basic_graph["basic 图 build_basic_agent（Phase 1 对照）"]
    router_graph["router 图 build_router_agent（Phase 2-3）"]
    sup_graph["supervisor 图 build_supervisor_agent（Phase 4）"]
    b_rag[rag_node]
    r_router["router_node（#数字快路径 + LLM 三分类）"]
    r_direct[direct_answer_node]
    r_refuse[refuse_node（固定文案）]
    r_rag["rag_node（黑盒调 lc chain）"]
    r_evaluate["evaluate_node（复用 chain gate · 零额外 LLM）"]
    r_rewrite["rewrite_node（LLM 改写 · 熔断封顶）"]
    s_supervisor["supervisor_node（LLM 拆解 ≤4 · 失败 fallback 单 rag）"]
    s_dispatch[route_next_subtask（dispatch）]
    s_rag["rag_subtask_node（复用 router 子图）"]
    s_extract[info_extract_node]
    s_tool["tool_exec_node（Mock 注册表）"]
    s_aggregator["aggregator_node（LLM 综合）"]
    lc_chain["LC Evidence chain（黑盒 · 不展开 LCEL）"]
    llm["LLM Provider"]
    db[PostgreSQL]
    main_doc[">../l0/00_main.md"]

    client -->|"POST {query, mode, thread_id}（cookie auth）"| lg_invoke
    %% → app/ops/lg_rag/router.py#L130
    lg_invoke -->|"[mode=basic]"| basic_graph
    %% → app/ops/lg_rag/router.py#L118
    lg_invoke -->|"[mode=router（默认）]"| router_graph
    %% → app/ops/lg_rag/router.py#L122
    lg_invoke -->|"[mode=supervisor]"| sup_graph
    %% → app/ops/lg_rag/router.py#L120
    lg_invoke -->|"200 {ok,data}"| client
    %% → app/ops/lg_rag/router.py#L152
    lg_invoke -->|"optional PG checkpointer（env LG_RAG_HTTP_CHECKPOINTER）"| db
    %% → app/ops/lg_rag/router.py#L125
    basic_graph -->|"START → rag → END"| b_rag
    %% → app/ops/lg_rag/graph.py#L58
    b_rag -->|"ainvoke_evidence_answer"| lc_chain
    %% → app/ops/lg_rag/nodes.py#L160
    %% → app/ops/lc_evidence_chain/chain.py::ainvoke_evidence_answer
    router_graph -->|"START → router"| r_router
    %% → app/ops/lg_rag/graph.py#L72
    r_router -->|"[rag]"| r_rag
    %% → app/ops/lg_rag/graph.py#L77
    r_router -->|"[direct → END]"| r_direct
    %% → app/ops/lg_rag/graph.py#L78
    r_router -->|"[refuse → END]"| r_refuse
    %% → app/ops/lg_rag/graph.py#L79
    r_router -->|"LLM 三分类（fallback=rag）"| llm
    %% → app/ops/lg_rag/nodes.py#L127
    r_rag -->|"->"| r_evaluate
    %% → app/ops/lg_rag/graph.py#L82
    r_rag -->|"ainvoke_evidence_answer（写回 chain_meta）"| lc_chain
    %% → app/ops/lg_rag/nodes.py#L160
    %% → app/ops/lc_evidence_chain/chain.py::ainvoke_evidence_answer
    r_evaluate -->|"[low 且 retry<2 → rewrite；high/medium → END]"| r_rewrite
    %% → app/ops/lg_rag/graph.py#L87
    %% → app/ops/lg_rag/nodes.py#L204
    r_rewrite -->|"[有新 query → 重试 rag；熔断置空 → END]"| r_rag
    %% → app/ops/lg_rag/graph.py#L95
    %% → app/ops/lg_rag/nodes.py#L261
    r_direct -->|"complete"| llm
    %% → app/ops/lg_rag/nodes.py#L269
    r_rewrite -->|"complete"| llm
    %% → app/ops/lg_rag/nodes.py#L230
    sup_graph -->|"START → supervisor"| s_supervisor
    %% → app/ops/lg_rag/multi/graph.py#L52
    s_supervisor -->|"subtasks（≤4）"| s_dispatch
    %% → app/ops/lg_rag/multi/graph.py#L53
    s_dispatch -->|"[type=rag]"| s_rag
    %% → app/ops/lg_rag/multi/graph.py#L35
    %% → app/ops/lg_rag/multi/nodes.py#L238
    s_dispatch -->|"[type=extract]"| s_extract
    %% → app/ops/lg_rag/multi/graph.py#L36
    %% → app/ops/lg_rag/multi/nodes.py#L238
    s_dispatch -->|"[type=tool]"| s_tool
    %% → app/ops/lg_rag/multi/graph.py#L37
    %% → app/ops/lg_rag/multi/nodes.py#L238
    s_dispatch -->|"[耗尽/空 → aggregate]"| s_aggregator
    %% → app/ops/lg_rag/multi/graph.py#L38
    %% → app/ops/lg_rag/multi/nodes.py#L237
    s_rag -->|"回 dispatch（追加一条结果）"| s_dispatch
    %% → app/ops/lg_rag/multi/graph.py#L55
    s_extract -->|"回 dispatch（追加一条结果）"| s_dispatch
    %% → app/ops/lg_rag/multi/graph.py#L55
    s_tool -->|"回 dispatch（追加一条结果）"| s_dispatch
    %% → app/ops/lg_rag/multi/graph.py#L55
    s_rag -->|"ainvoke_router_agent（复用 router 子图）"| router_graph
    %% → app/ops/lg_rag/multi/nodes.py#L266
    %% → app/ops/lg_rag/graph.py::ainvoke_router_agent
    s_supervisor -->|"complete（拆解）"| llm
    %% → app/ops/lg_rag/multi/nodes.py#L200
    s_extract -->|"complete（抽取）"| llm
    %% → app/ops/lg_rag/multi/nodes.py#L299
    s_aggregator -->|"complete（综合 → END）"| llm
    %% → app/ops/lg_rag/multi/nodes.py#L361
    router_graph -->|"加载"| main_doc

    classDef phase fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef doc fill:#fff8e1,stroke:#ff6f00,stroke-width:1px
    classDef infra fill:#e8f5e9,stroke:#2e7d32,stroke-width:1px

    class client,lg_invoke,basic_graph,router_graph,sup_graph,b_rag,r_router,r_direct,r_refuse,r_rag,r_evaluate,r_rewrite,s_supervisor,s_dispatch,s_rag,s_extract,s_tool,s_aggregator,lc_chain phase
    class main_doc doc
    class llm,db infra
```

---

## 10_flow_rag

### kit 1.6.1 emit（切换后形态）

```mermaid
flowchart TB
    caller["调用方（chat/rag_nodes · lc_evidence_chain）"]
    embed_query["query embed（bge-m3）"]
    hybrid_recall["hybrid_recall（入口）"]
    backend_gate["search_dense_with_fallback（即时降级）"]
    dense_qdrant["dense · Qdrant Cosine（默认）"]
    dense_pgvector["dense · pgvector fallback"]
    fts_pg["FTS / sparse 第二路（PG）"]
    hydrate["PG hydrate（Qdrant 命中回表）"]
    rrf_fuse["RRF 融合（k=60 · 两路等权）"]
    rerank["rerank（可选 · CE 精排）"]
    result["RetrievedChunk[]（fused top-5）"]
    siliconflow["SiliconFlow（/embeddings · /rerank）"]
    qdrant["Qdrant"]
    db["PostgreSQL（ops_knowledge_chunks）"]
    main_doc[">../l0/00_main.md"]

    caller -->|"query"| embed_query
    %% → app/ops/chat/rag_nodes.py#L68
    embed_query -->|"POST /embeddings（默认 ApiEmbedder；RAG_EMBED_BACKEND=local → 本机 ST）"| siliconflow
    %% → app/ops/rag/embedder.py#L92
    embed_query -->|"qvec"| hybrid_recall
    %% → app/ops/chat/rag_nodes.py#L73
    hybrid_recall -->|"dense 路选择"| backend_gate
    %% → app/ops/rag/retrieve.py#L200
    %% → app/ops/rag/backend.py#L57
    backend_gate -->|"[默认 qdrant · 失败再试 1 次]"| dense_qdrant
    %% → app/ops/rag/backend.py#L63
    %% → app/ops/rag/backend.py#L68
    backend_gate -->|"[err → 即时降级 #124; RAG_VECTOR_BACKEND=pgvector]"| dense_pgvector
    %% → app/ops/rag/backend.py#L64
    %% → app/ops/rag/backend.py#L78
    dense_qdrant -->|"query_points（hnsw_ef · with_payload 仅小字段）"| qdrant
    %% → app/ops/rag/retrievers/qdrant_retriever.py#L75
    dense_qdrant -->|"hit ids"| hydrate
    %% → app/ops/rag/retrievers/qdrant_retriever.py#L109
    hydrate -->|"SELECT ... WHERE id = ANY(:ids)"| db
    %% → app/ops/rag/retrievers/qdrant_retriever.py#L113
    hybrid_recall -->|"第二路 [fts 默认 #124; sparse C 臂]"| fts_pg
    %% → app/ops/rag/retrieve.py#L204
    fts_pg -->|"tsvector @@ plainto_tsquery（可选 glossary 展开）"| db
    %% → app/ops/rag/retrieve.py#L214
    hydrate -->|"semantic 路（k_each）"| rrf_fuse
    %% → app/ops/rag/retrieve.py#L217
    dense_pgvector -->|"semantic 路（k_each）"| rrf_fuse
    %% → app/ops/rag/retrieve.py#L217
    fts_pg -->|"keyword 路（k_each）"| rrf_fuse
    %% → app/ops/rag/retrieve.py#L217
    rrf_fuse -->|"[RAG_RERANK_ENABLED → 粗排 top-M 精排]"| rerank
    %% → app/ops/chat/rag_nodes.py#L76
    rrf_fuse -->|"[rerank off → 粗排 top-5]"| result
    %% → app/ops/chat/rag_nodes.py#L78
    rerank -->|"POST /rerank（[err] fail-closed 回退粗排）"| siliconflow
    %% → app/ops/rag/reranker.py#L171
    %% → app/ops/rag/reranker.py#L260
    rerank -->|"top-5（顶分地板 + 相对顶分过滤）"| result
    %% → app/ops/rag/reranker.py#L277
    %% → app/ops/rag/reranker.py#L287
    result -->|"RetrievedChunk[]（.fused）"| caller
    %% → app/ops/rag/retrieve.py#L233
    hybrid_recall -->|"加载"| main_doc

    classDef phase fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef doc fill:#fff8e1,stroke:#ff6f00,stroke-width:1px
    classDef infra fill:#e8f5e9,stroke:#2e7d32,stroke-width:1px
    class embed_query,hybrid_recall,backend_gate,dense_qdrant,dense_pgvector,fts_pg,hydrate,rrf_fuse,rerank phase
    class caller,result,siliconflow,qdrant,db,main_doc infra
```

### 本仓现产物（harness emit + normalize）

```mermaid
flowchart TB
    caller["调用方（chat/rag_nodes · lc_evidence_chain）"]
    embed_query["query embed（bge-m3）"]
    hybrid_recall[hybrid_recall（入口）]
    backend_gate[search_dense_with_fallback（即时降级）]
    dense_qdrant["dense · Qdrant Cosine（默认）"]
    dense_pgvector["dense · pgvector fallback"]
    fts_pg["FTS / sparse 第二路（PG）"]
    hydrate["PG hydrate（Qdrant 命中回表）"]
    rrf_fuse["RRF 融合（k=60 · 两路等权）"]
    rerank["rerank（可选 · CE 精排）"]
    result["RetrievedChunk[]（fused top-5）"]
    siliconflow["SiliconFlow（/embeddings · /rerank）"]
    qdrant[Qdrant]
    db[PostgreSQL（ops_knowledge_chunks）]
    main_doc[">../l0/00_main.md"]

    caller -->|"query"| embed_query
    %% → app/ops/chat/rag_nodes.py#L68
    embed_query -->|"POST /embeddings（默认 ApiEmbedder；RAG_EMBED_BACKEND=local → 本机 ST）"| siliconflow
    %% → app/ops/rag/embedder.py#L92
    embed_query -->|"qvec"| hybrid_recall
    %% → app/ops/chat/rag_nodes.py#L73
    hybrid_recall -->|"dense 路选择"| backend_gate
    %% → app/ops/rag/retrieve.py#L200
    %% → app/ops/rag/backend.py#L57
    backend_gate -->|"[默认 qdrant · 失败再试 1 次]"| dense_qdrant
    %% → app/ops/rag/backend.py#L63
    %% → app/ops/rag/backend.py#L68
    backend_gate -->|"[err → 即时降级 | RAG_VECTOR_BACKEND=pgvector]"| dense_pgvector
    %% → app/ops/rag/backend.py#L64
    %% → app/ops/rag/backend.py#L78
    dense_qdrant -->|"query_points（hnsw_ef · with_payload 仅小字段）"| qdrant
    %% → app/ops/rag/retrievers/qdrant_retriever.py#L75
    dense_qdrant -->|"hit ids"| hydrate
    %% → app/ops/rag/retrievers/qdrant_retriever.py#L109
    hydrate -->|"SELECT ... WHERE id = ANY(:ids)"| db
    %% → app/ops/rag/retrievers/qdrant_retriever.py#L113
    hybrid_recall -->|"第二路 [fts 默认 | sparse C 臂]"| fts_pg
    %% → app/ops/rag/retrieve.py#L204
    fts_pg -->|"tsvector @@ plainto_tsquery（可选 glossary 展开）"| db
    %% → app/ops/rag/retrieve.py#L214
    hydrate -->|"semantic 路（k_each）"| rrf_fuse
    %% → app/ops/rag/retrieve.py#L217
    dense_pgvector -->|"semantic 路（k_each）"| rrf_fuse
    %% → app/ops/rag/retrieve.py#L217
    fts_pg -->|"keyword 路（k_each）"| rrf_fuse
    %% → app/ops/rag/retrieve.py#L217
    rrf_fuse -->|"[RAG_RERANK_ENABLED → 粗排 top-M 精排]"| rerank
    %% → app/ops/chat/rag_nodes.py#L76
    rrf_fuse -->|"[rerank off → 粗排 top-5]"| result
    %% → app/ops/chat/rag_nodes.py#L78
    rerank -->|"POST /rerank（[err] fail-closed 回退粗排）"| siliconflow
    %% → app/ops/rag/reranker.py#L171
    %% → app/ops/rag/reranker.py#L260
    rerank -->|"top-5（顶分地板 + 相对顶分过滤）"| result
    %% → app/ops/rag/reranker.py#L277
    %% → app/ops/rag/reranker.py#L287
    result -->|"RetrievedChunk[]（.fused）"| caller
    %% → app/ops/rag/retrieve.py#L233
    hybrid_recall -->|"加载"| main_doc

    classDef phase fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef doc fill:#fff8e1,stroke:#ff6f00,stroke-width:1px
    classDef infra fill:#e8f5e9,stroke:#2e7d32,stroke-width:1px

    class caller,embed_query,hybrid_recall,backend_gate,dense_qdrant,dense_pgvector,fts_pg,hydrate,rrf_fuse,rerank,result,siliconflow phase
    class main_doc doc
    class qdrant,db infra
```

---

## 11_flow_sync_to_chat

### kit 1.6.1 emit（切换后形态）

```mermaid
flowchart LR
    client["用户 / iOS"]
    admin_sync["POST /api/ops/admin/sync"]
    issues_endpoint["GET /api/ops/issues"]
    pulls_endpoint["GET /api/ops/pulls"]
    graph_endpoint["GET /api/ops/graph"]
    chat_stream["POST /api/ops/chat/stream"]
    db["PostgreSQL"]

    client -->|"POST sync payload"| admin_sync
    %% → app/ops/admin/sync.py#L28
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
    class client,db infra
```

### 本仓现产物（harness emit + normalize）

```mermaid
flowchart LR
    client["用户 / iOS"]
    admin_sync["POST /api/ops/admin/sync"]
    issues_endpoint["GET /api/ops/issues"]
    pulls_endpoint["GET /api/ops/pulls"]
    graph_endpoint["GET /api/ops/graph"]
    chat_stream["POST /api/ops/chat/stream"]
    db[PostgreSQL]

    client -->|"POST sync payload"| admin_sync
    %% → app/ops/admin/sync.py#L28
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

    class client,admin_sync,issues_endpoint,pulls_endpoint,graph_endpoint,chat_stream phase
    class db infra
```

---

