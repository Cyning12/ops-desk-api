# 模块边界登记表（G-L1 · D4-a 人签真值）

<!-- pdd
level_present: 0+1
deeper: ../l2/indexes/
audience: agent-30
-->

> **一句话**：ops-desk-api **一级模块** 边界真值。  
> **何时读**：改码前确认 module_id / 依赖出边；签 `HG-GRAPH-MODULES`。  
> **路径**：`docs/_tech_graph/l1/01_modules.md`（`HG-GRAPH-MODULES` 真值）。

---

## 模块表（必填）

| module_id | 名称 | 路径 glob | 依赖方向（仅指向谁） | 负责人/备注 |
|-----------|------|-----------|----------------------|-------------|
| `entry` | 入口与配置 | `app/main.py`, `app/config.py` | → `api`, `db` | FastAPI 实例、CORS、环境变量 |
| `api` | API 路由注册 | `app/ops/router.py`, `app/ops/*/router.py` | → `service`, `auth`, `db` | HTTP 入口、SSE 流封装 |
| `auth` | 鉴权模块 | `app/ops/auth.py`, `app/ops/deps.py`, `app/ops/security.py` | → `db` | 登录、登出、session cookie、invite token 验证、角色保护 |
| `chat` | Chat 业务 | `app/ops/chat/**` · `app/ops/session/**` | → `llm`, `db`, `rag` | LangGraph StateGraph、SSE/WS 双传输；**Session 连续性**（历史加载 · 窗口压缩 · SSE replay 契约）；**T6（2026-08-31）**：`POST /api/ops/chat/stream` 已 **410** 下线（迁移 `POST /api/ops/lg-rag/stream` · 不删 chat 代码/图/表 · models/sessions.latest/WS 保留）；拓扑详见 [`10_flow_chat.md`](./10_flow_chat.md) |
| `rag` | RAG 检索与入库 | `app/ops/rag/**` | → `db` | 混合召回（dense + FTS/sparse）与 ingest（影子写+DLQ）；查询 embed 默认 SiliconFlow HTTP（`RAG_EMBED_BACKEND`）；拓扑详见 [`10_flow_rag.md`](./10_flow_rag.md) |
| `lc_evidence_chain` | LangChain 旁路答问 | `app/ops/lc_evidence_chain/**` | → `rag`, `llm`, `db` | LCEL 旁路答问链，HTTP `POST /api/ops/lc-evidence/invoke`（cookie 鉴权 · freeze `lc-evidence-http-v1`），**默认不进入** `chat/graph`，被 `lg_rag` 黑盒复用；**§10.7 step**：可选 `step_hook` ContextVar（`step_hook.py`）供 retrieve/grade/answer 里程碑，**不**反向依赖 `lg_rag`；拓扑详见 [`10_flow_lc_evidence.md`](./10_flow_lc_evidence.md) |
| `structured_output` | Structured Output Gateway | `app/ops/structured_output/**` | → `llm` | LLM 文本 → parse/repair/validate/预算纠偏；供 `lg_rag` 结构化节点复用；**域 schema 在 `lg_rag/schemas`**（SO 内核不含业务模型）；**不是** Skill；拓扑详见 [`10_flow_structured_output.md`](./10_flow_structured_output.md) |
| `capability` | Capability Gateway | `app/ops/capability/**` | → — | 能力**进程内注册表** / 筛选 / 统一 invoke（local_fn · mock 探针 · skill stub；**非**跨进程注册中心）；**YAML/JSON manifest 加载 register**（仅 local_fn · 显式 reload · 禁止每请求）；**invoke 前 Policy 门**（高危/sandbox/cli 默认 blocked · Host-only 策略键；**阶段 H**：`tenant_scoped` 缺 ctx 租户谓词拒 · 有 `args_schema` 则形态校验 · span 含 args/policy/subtask 摘要）；**可迁移内核 · Mode A**（`list`+`invoke`；ToolNode 桥仅 `extras.langchain`）；**真 MCP · 默认关 · CI 不外网**；**本库 issue/PR 只读 lookup**（`get_issue_by_number` / `get_pr_by_number` · `ainvoke` · 禁止 MCP/GitHub 热路径）；**C1（2026-09-01）**：`harness.*` 白名单 CLI Capability 三条（`harness.verify` / `harness.task_lint`（task lint + lint-wiki-delta 两子操作）已实现 · `harness.status` 可选未做 · `harness_cli.py` 代码路径 `gateway.register` · 禁 shell · env 钉 `DSH_CODING_KIT_VERSION` · Policy 默认关 `policy_blocked`（双键 allow_high_risk+allow_cli）· 不进业务默认目录）；**C3（2026-09-01）**：受控 task 写盘纯服务 `task_writer.py`（`plan_task_write`/`apply_task_write` · allowlist 仅 `docs/tasks/active|draft` + `docs/harness/invokes/by-task/<slug>/` · dry-run 默认 `confirmed=False` · 禁代签机械挡 · 原子写）——**非 Gateway Capability · 不进 registry/manifest · 无 HTTP 路由**；拓扑详见 [`10_flow_capability.md`](./10_flow_capability.md) |
| `lg_rag` | LangGraph 旁路单 Agent | `app/ops/lg_rag/**` | → `lc_evidence_chain`, `llm`, `structured_output`, `capability` | 旁路三模式 basic / router / supervisor；HTTP `POST /api/ops/lg-rag/invoke`（freeze `lg-rag-http-v1`）与 **`POST /api/ops/lg-rag/stream`**（SSE updates · freeze `lg-rag-sse-v1` · 默认 mode=supervisor；帧可选顶层 `cursor`）；**T3**：stream/invoke 按 `thread_id` 加载独立表 `ops_lg_rag_threads`/`ops_lg_rag_turns` 历史，窗口压缩后注入图输入（默认 max_full_turns=6 · group_size=2）；**T4**：事件落盘 `ops_lg_rag_run_events` · **`POST /api/ops/lg-rag/replay`**（`after_seq`/`cursor` · 仅 `seq>`）；**T5**：终答 `answer` 多帧 delta（`{"delta"}`）+ 终帧 `{"content", "final": true}`（aggregator / direct_answer 经 `answer_stream.py` contextvar token sink 桥 `complete_stream`；流式不可用降级整段；**T5.1**：persist 后台不阻塞 SSE yield）；**§10.6**：等待 update 期间 SSE comment keepalive（不落盘、不占 seq；配合 client idle 120s）；**§10.7**：子任务 `status=running` 起步帧 + `status=step` 里程碑（`progress_stream.py` · `rag_subtask` 经 `astream_router_agent` + evidence `step_hook`；完成帧补 `status=done`；running/step/done 帧可选 `message` 中文短句——`subtask_message.py` 确定性模板 · `SUBTASK_MESSAGE_MAX_LEN=200` · 生成失败降级帧仍发）；黑盒复用 `ainvoke_evidence_answer`，**默认不进入** `chat/graph`；**supervisor 图 START→Intent→Strategy Builder allowlist→supervisor planner→…→aggregator→critic_node 条件边**（pass/end→END · retry_planner→supervisor · rebind→Builder；预算 1+1）；**H-β**：supervisor 总步默认 32（env `LG_RAG_SUPERVISOR_MAX_STEPS` · 非法/≤0 回退 32 · 耗尽→aggregate · 全局优先于 critic 回环；可选墙钟 `LG_RAG_SUPERVISOR_MAX_WALL_SECONDS` 默认 0=关）；结构化节点走 `structured_output` 管道 + **域 schema 在 `lg_rag/schemas`**；`tool_exec` 走 `capability`；**C2（2026-09-01）**：prompt 装配层 `app/ops/prompts/**` 归属本行（模板 id 全部 `lg_rag.*` 且被 supervisor/intent 消费）· 新增 `packs.py`（Prompt Pack 层 · pack=comms `render_pack` + `route_intent` 纯函数 · 无新 HTTP 路由 · product 渲染零变化）；拓扑详见 [`10_flow_lg_rag.md`](./10_flow_lg_rag.md) |
| `data` | 数据视图 | `app/ops/overview.py`, `app/ops/issues.py`, `app/ops/pulls.py`, `app/ops/graph.py` | → `db` | Issue/PR/Overview 指标/Graph 快照只读查询（供 Chat / iOS 只读消费） |
| `admin` | Admin 同步 | `app/ops/admin/**` | → `db` | 接收 GHA sync payload 并持久化到 data/chat 依赖的表；本仓 GHA sender + Bearer 机读 token（cookie maintainer 仍可用） |
| `llm` | LLM Provider | `app/llm/**` | → — | SiliconFlow / 百炼 provider 工厂；complete 路径上报 usage；grader 故障 refuse；**流式** `_stream_openai_compatible` 成功路径禁止 `aread()` 整包（真 token 流） |
| `db` | 数据库与 ORM | `app/db/**`, `alembic/**` | —（被依赖） | SQLAlchemy models、session、migrations |

## 跨模块契约

| 契约 | 提供方 module_id | 消费方 | 说明 |
|---|---|---|---|
| `ChatState` | `chat` | `chat` 内部节点 | LangGraph 状态字典 |
| `SseEvent` | `api` | `chat` / 前端 | SSE 事件 JSON 格式 |
| `ChatWsProtocol` | `chat` | 面试演示 / 未来 iOS | `WS /api/ops/chat/ws` message/cancel 入参 + 与 SSE 一致的事件 JSON（当前不鉴权，演示用户=首个 maintainer） |
| `AsyncSession` | `db` | `admin`, `data`（未来） | 数据库会话依赖 |
| `LatestChatSession` | `chat` | `iOS v1` | `GET /api/ops/chat/sessions/latest` 自动获取/创建最近 session |
| `SyncedRepo/Issue/PR/GraphSnapshot` | `admin` | `data`, `chat` | admin 写入的表同时供 data 只读接口和 chat 上下文加载 |
| `OpsIssue/OpsPullRequest/OpsGraphSnapshot` | `data` | `chat` | Chat 通过 data 层表消费同步后的数据 |
| `RetrievedChunk` / `RAG_VECTOR_BACKEND` | `rag` | `chat`, `lc_evidence_chain` | dense 默认 Qdrant Top-k id → PG hydrate；失败即时降级 pgvector；影子写 `RAG_QDRANT_SHADOW_WRITE` |
| `EvidenceItem` / `ChainResult` / `GateDecision` | `lc_evidence_chain` | CLI 冒烟 / `api` HTTP / web LC Evidence 页 | LCEL 旁路输出：evidence（含 grade + **snippet**）+ answer + meta.gate_action；HTTP 外壳 `{ok,data}`（freeze `lc-evidence-http-v1`）；**不改** graph 边 |
| `ParseOutcome` / `acomplete_structured` | `structured_output` | `lg_rag`（router / intent / supervisor / info_extract） | Host 权威结构化解析与预算纠偏；失败不伪造成功业务数据 |
| `CapabilityResult` / `invoke` / `ainvoke` | `capability` | `lg_rag`（`tool_exec_node`） | 统一能力调用（lookup 走 async）；未知 id → `ok=False`，不中断后续子任务 |

## 人签记录

| human_gate_id | status | 签核人 | 日期 | 说明 |
|---|---|---|---|---|
| HG-GRAPH-MODULES | approved | 见 `task_graph_bootstrap` | 2026-07-16 | 模块表覆盖 ops-desk-api 一级模块；图谱 bootstrap 已完成 |
| HG-GRAPH-MODULES | approved | 维护者（Phase α 迁路径） | 2026-07-27 | 真值迁至本文件；根 stub 已于 2026-08-26 清理（tech-graph-legacy-cleanup） |
| HG-GRAPH-MODULES | approved | 维护者（task_lg_rag_phase1 会话签收） | 2026-08-19 | 新增 `lg_rag` 一级模块（LangGraph 旁路 Phase 1） |
| HG-GRAPH-MODULES | approved | 维护者（task_lg_rag_phase2 会话签收） | 2026-08-19 | `lg_rag` 行更新 Phase 2 router 三路拓扑；依赖出边补 `llm`；不新增一级模块 |
| HG-GRAPH-MODULES | approved | 维护者（task_lg_rag_phase4 会话签收 · 00 模式） | 2026-08-21 | `lg_rag` 行更新 Phase 3 回环 + Phase 4 Supervisor 拓扑；不新增一级模块 |
| HG-GRAPH-MODULES | approved | 维护者（会话授权 B · 2026-08-26） | 2026-08-26 | 新增一级模块 `structured_output` + `capability`；`lg_rag` 依赖出边补齐；各立 G-L1 flow |
| HG-GRAPH-MODULES | approved | 维护者（H1 lg-rag-supervisor-capability-catalog · 00） | 2026-08-27 | `lg_rag` 行备注：supervisor 读 Capability 目录；不新增一级模块 |
| HG-GRAPH-MODULES | approved | 维护者（H2 capability-policy-sandbox · 00） | 2026-08-27 | `capability` 行备注：Policy 门；不新增一级模块 |
| HG-GRAPH-MODULES | approved | 00 代签（维护者 Prompt 授权 · task_host_comms_prompt_pack） | 2026-09-01 | `lg_rag` 行备注：C2 Prompt Pack 层 `app/ops/prompts/packs.py`（pack=comms）；prompts 归属 lg_rag 行；不新增一级模块 |
| HG-GRAPH-MODULES | approved | 维护者（H3 chat-session-continuity · 00） | 2026-08-27 | `chat` 行备注 Session 连续性；不新增一级模块 |
| HG-GRAPH-MODULES | approved | 维护者（S1 strategy-builder-allowlist · 00） | 2026-08-27 | `lg_rag` 行备注 Strategy Builder allowlist；不新增一级模块 |
| HG-GRAPH-MODULES | approved | 维护者（S2 intent-schema-v1 · 00 代签） | 2026-08-27 | `lg_rag` 行备注 supervisor Intent 节点；不新增一级模块 |
| HG-GRAPH-MODULES | approved | 维护者（S3 catalog-manifest-yaml · 00 代签） | 2026-08-28 | `capability` 行备注：manifest 加载；不新增一级模块 |
| HG-GRAPH-MODULES | approved | 维护者（S4 critic-rebind · 00 代签） | 2026-08-28 | `lg_rag` 行备注：supervisor 图 Critic 条件边；不新增一级模块 |
| HG-GRAPH-MODULES | approved | 维护者（ops-pg-lookup-capabilities · 00 代签） | 2026-08-28 | `capability` 行备注：本库 issue/PR 只读 lookup；不新增一级模块 |
| HG-GRAPH-MODULES | approved | 维护者（ops-sync-sender-migration · 00 代签） | 2026-08-28 | `admin` 行备注：本仓 GHA sender + Bearer 机读 token；`11_flow_sync_to_chat` 增 GHA 节点；不新增一级模块 |
| HG-GRAPH-MODULES | approved | 维护者（lg-rag-sse-stream-updates · 00 代签 · 「开工」） | 2026-08-30 | `lg_rag` 行备注：`POST /lg-rag/stream` · freeze `lg-rag-sse-v1`；**G-L2** 第二试点分文件 `by_path_lg_rag.yaml`（不与 chat 混排）；不新增一级模块 |
| HG-GRAPH-MODULES | approved | 维护者（lg-rag-session-continuity · 00 代签） | 2026-08-31 | `lg_rag` 行备注：`thread_id` 历史加载 + 窗口压缩注入；独立表；不新增一级模块 |
| HG-GRAPH-MODULES | approved | 维护者（lg-rag-sse-resume · 00 代签） | 2026-08-31 | `lg_rag` 行备注：SSE `cursor` + `ops_lg_rag_run_events` + `POST /lg-rag/replay`；不新增一级模块 |
| HG-GRAPH-MODULES | approved | 维护者（lg-rag-sse-token-stream · 00 代签） | 2026-08-31 | `lg_rag` 行备注：终答 `answer` 多帧 delta + 终帧 `final`（token sink 桥）；不新增一级模块 |
| HG-GRAPH-MODULES | approved | 维护者（lg-rag-sse-delta-realtime · 00 代签 · 「开工」） | 2026-09-01 | `lg_rag` / flow 备注：T5.1 persist 后台不阻塞 SSE yield；不新增一级模块 · 无新 implementedBy（G-L2 indexes 不动） |
| HG-GRAPH-MODULES | approved | 维护者（lg-rag-deprecate-chat-stream · 00 代签） | 2026-08-31 | `chat` 行备注：`/chat/stream` 已 410（T6）；`10_flow_chat` 加 deprecated 备注；不删节点/边/indexes；不新增一级模块 |
| HG-GRAPH-MODULES | approved | 维护者（host-harness-cli-capability · 00 代签） | 2026-09-01 | `capability` 行备注 + `10_flow_capability` 描述备注：`harness.*` 白名单三条（verify / task_lint 两子操作 · status 可选未做）；不新增一级模块 · 不增 implementedBy（G-L2 indexes 无需同步） |
| HG-GRAPH-MODULES | approved | 00 代签（维护者 Prompt 授权 · task_host_comms_task_writer） | 2026-09-01 | `capability` 行备注：C3 受控 task 写盘纯服务 `task_writer.py`（非 Gateway Capability · 不进 registry/manifest）；不新增一级模块 · 不增 implementedBy（G-L2 indexes 无需同步） |
| HG-GRAPH-MODULES | approved | 维护者（lg-rag-sse-idle-keepalive · 00 代签 · 「Implement plan」） | 2026-09-07 | `lg_rag` 行备注：§10.6 idle/keepalive；不新增一级模块 · 不增 implementedBy（G-L2 indexes 无需同步） |
| HG-GRAPH-MODULES | approved | 维护者（lg-rag-sse-subtask-live · 00 代签 · 维护者令开启） | 2026-09-07 | `lg_rag` 行备注：§10.7 subtask running 起步帧；`progress_stream.py` 进 G-L2 indexes；不新增一级模块 |
| HG-GRAPH-MODULES | approved | 维护者（lg-rag-sse-subtask-steps · 00 代签 · Implement plan） | 2026-09-08 | `lg_rag`/`lc_evidence_chain` 备注：§10.7 step 里程碑 + `emit_subtask_step` indexes；`step_hook` 无反向边；不新增一级模块 |
| HG-GRAPH-MODULES | approved | 00 代签（维护者令 · task_capability_contract_hardening · 30 回写） | 2026-09-17 | `capability` / `10_flow_capability` 备注：阶段 H 契约硬化（args_schema · tenant_scoped · 注册表口径）；不新增一级模块 · 不增 implementedBy |
| HG-GRAPH-MODULES | approved | 00 代签（维护者令 · task_supervisor_budget_h_beta · 30 回写） | 2026-09-17 | `lg_rag` 行备注：supervisor 总步预算默认 32 / 耗尽→aggregate；不新增一级模块 · 不增 implementedBy |

## 关联

- 顶层图（G-L0）：[`../l0/00_main.md`](../l0/00_main.md) · 源 [`../l0/00_main.graph.yaml`](../l0/00_main.graph.yaml)
- Chat 流程（G-L1 + chat G-L2）：[`10_flow_chat.md`](./10_flow_chat.md) · 源 [`10_flow_chat.graph.yaml`](./10_flow_chat.graph.yaml)
- LC Evidence 旁路流程（G-L1）：[`10_flow_lc_evidence.md`](./10_flow_lc_evidence.md) · 源 [`10_flow_lc_evidence.graph.yaml`](./10_flow_lc_evidence.graph.yaml)
- LG RAG 旁路流程（G-L1）：[`10_flow_lg_rag.md`](./10_flow_lg_rag.md) · 源 [`10_flow_lg_rag.graph.yaml`](./10_flow_lg_rag.graph.yaml)
- Structured Output Gateway（G-L1）：[`10_flow_structured_output.md`](./10_flow_structured_output.md) · 源 [`10_flow_structured_output.graph.yaml`](./10_flow_structured_output.graph.yaml)
- Capability Gateway（G-L1）：[`10_flow_capability.md`](./10_flow_capability.md) · 源 [`10_flow_capability.graph.yaml`](./10_flow_capability.graph.yaml)
- 方法倒排（G-L2）：[`../l2/indexes/`](../l2/indexes/)（chat · [`by_path.yaml`](../l2/indexes/by_path.yaml)；lg_rag · [`by_path_lg_rag.yaml`](../l2/indexes/by_path_lg_rag.yaml)）
- Mermaid 约定：[`../shared/99_mermaid_protocol.md`](../shared/99_mermaid_protocol.md)
