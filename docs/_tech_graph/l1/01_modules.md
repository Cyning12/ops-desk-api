# 模块边界登记表（G-L1 · D4-a 人签真值）

<!-- pdd
level_present: 0+1
deeper: ../l2/indexes/by_path.yaml
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
| `chat` | Chat 业务 | `app/ops/chat/**` · `app/ops/session/**` | → `llm`, `db`, `rag` | LangGraph StateGraph、SSE/WS 双传输；**Session 连续性**（历史加载 · 窗口压缩 · SSE replay 契约）；拓扑详见 [`10_flow_chat.md`](./10_flow_chat.md) |
| `rag` | RAG 检索与入库 | `app/ops/rag/**` | → `db` | 混合召回（dense + FTS/sparse）与 ingest（影子写+DLQ）；查询 embed 默认 SiliconFlow HTTP（`RAG_EMBED_BACKEND`）；拓扑详见 [`10_flow_rag.md`](./10_flow_rag.md) |
| `lc_evidence_chain` | LangChain 旁路答问 | `app/ops/lc_evidence_chain/**` | → `rag`, `llm`, `db` | LCEL 旁路答问链，HTTP `POST /api/ops/lc-evidence/invoke`（cookie 鉴权 · freeze `lc-evidence-http-v1`），**默认不进入** `chat/graph`，被 `lg_rag` 黑盒复用；拓扑详见 [`10_flow_lc_evidence.md`](./10_flow_lc_evidence.md) |
| `structured_output` | Structured Output Gateway | `app/ops/structured_output/**` | → `llm` | LLM 文本 → parse/repair/validate/预算纠偏；供 `lg_rag` 结构化节点复用；**域 schema 在 `lg_rag/schemas`**（SO 内核不含业务模型）；**不是** Skill；拓扑详见 [`10_flow_structured_output.md`](./10_flow_structured_output.md) |
| `capability` | Capability Gateway | `app/ops/capability/**` | → — | 能力注册 / 筛选 / 统一 invoke（local_fn · mock 探针 · skill stub）；**invoke 前 Policy 门**（高危/sandbox/cli 默认 blocked · Host-only 策略键）；**可迁移内核 · Mode A**（`list`+`invoke`；ToolNode 桥仅 `extras.langchain`）；**真 MCP · 默认关 · CI 不外网**；拓扑详见 [`10_flow_capability.md`](./10_flow_capability.md) |
| `lg_rag` | LangGraph 旁路单 Agent | `app/ops/lg_rag/**` | → `lc_evidence_chain`, `llm`, `structured_output`, `capability` | 旁路三模式 basic / router / supervisor，HTTP `POST /api/ops/lg-rag/invoke`（mode 分派 · freeze `lg-rag-http-v1`），黑盒复用 `ainvoke_evidence_answer`，**默认不进入** `chat/graph`；**supervisor 图 START→Strategy Builder allowlist→supervisor planner**（`list_capabilities` ∩ state allowlist）；结构化节点走 `structured_output` 管道 + **域 schema 在 `lg_rag/schemas`**；`tool_exec` 走 `capability`；拓扑详见 [`10_flow_lg_rag.md`](./10_flow_lg_rag.md) |
| `data` | 数据视图 | `app/ops/overview.py`, `app/ops/issues.py`, `app/ops/pulls.py`, `app/ops/graph.py` | → `db` | Issue/PR/Overview 指标/Graph 快照只读查询（供 Chat / iOS 只读消费） |
| `admin` | Admin 同步 | `app/ops/admin/sync.py`, `app/ops/admin/service.py`, `app/ops/admin/schema.py` | → `db` | 接收 GHA sync payload 并持久化到 data/chat 依赖的表 |
| `llm` | LLM Provider | `app/llm/**` | → — | SiliconFlow / 百炼 provider 工厂；complete 路径上报 usage；grader 故障 refuse |
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
| `ParseOutcome` / `acomplete_structured` | `structured_output` | `lg_rag`（router / supervisor / info_extract） | Host 权威结构化解析与预算纠偏；失败不伪造成功业务数据 |
| `CapabilityResult` / `invoke` | `capability` | `lg_rag`（`tool_exec_node`） | 统一能力调用；未知 id → `ok=False`，不中断后续子任务 |

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
| HG-GRAPH-MODULES | approved | 维护者（H3 chat-session-continuity · 00） | 2026-08-27 | `chat` 行备注 Session 连续性；不新增一级模块 |
| HG-GRAPH-MODULES | approved | 维护者（S1 strategy-builder-allowlist · 00） | 2026-08-27 | `lg_rag` 行备注 Strategy Builder allowlist；不新增一级模块 |

## 关联

- 顶层图（G-L0）：[`../l0/00_main.md`](../l0/00_main.md) · 源 [`../l0/00_main.graph.yaml`](../l0/00_main.graph.yaml)
- Chat 流程（G-L1 + chat G-L2）：[`10_flow_chat.md`](./10_flow_chat.md) · 源 [`10_flow_chat.graph.yaml`](./10_flow_chat.graph.yaml)
- LC Evidence 旁路流程（G-L1）：[`10_flow_lc_evidence.md`](./10_flow_lc_evidence.md) · 源 [`10_flow_lc_evidence.graph.yaml`](./10_flow_lc_evidence.graph.yaml)
- LG RAG 旁路流程（G-L1）：[`10_flow_lg_rag.md`](./10_flow_lg_rag.md) · 源 [`10_flow_lg_rag.graph.yaml`](./10_flow_lg_rag.graph.yaml)
- Structured Output Gateway（G-L1）：[`10_flow_structured_output.md`](./10_flow_structured_output.md) · 源 [`10_flow_structured_output.graph.yaml`](./10_flow_structured_output.graph.yaml)
- Capability Gateway（G-L1）：[`10_flow_capability.md`](./10_flow_capability.md) · 源 [`10_flow_capability.graph.yaml`](./10_flow_capability.graph.yaml)
- 方法倒排（G-L2）：[`../l2/indexes/by_path.yaml`](../l2/indexes/by_path.yaml)
- Mermaid 约定：[`../shared/99_mermaid_protocol.md`](../shared/99_mermaid_protocol.md)
