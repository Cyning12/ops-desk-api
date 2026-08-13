# 模块边界登记表（G-L1 · D4-a 人签真值）

<!-- pdd
level_present: 0+1
deeper: ../l2/indexes/by_path.yaml
audience: agent-30
-->

> **一句话**：ops-desk-api **一级模块** 边界真值。  
> **何时读**：改码前确认 module_id / 依赖出边；签 `HG-GRAPH-MODULES`。  
> **路径**：`docs/_tech_graph/l1/01_modules.md`（根 `01_struct.md` 为过渡 stub）。

---

## 模块表（必填）

| module_id | 名称 | 路径 glob | 依赖方向（仅指向谁） | 负责人/备注 |
|-----------|------|-----------|----------------------|-------------|
| `entry` | 入口与配置 | `app/main.py`, `app/config.py` | → `api`, `db` | FastAPI 实例、CORS、环境变量 |
| `api` | API 路由注册 | `app/ops/router.py`, `app/ops/*/router.py` | → `service`, `auth`, `db` | HTTP 入口、SSE 流封装 |
| `auth` | 鉴权模块 | `app/ops/auth.py`, `app/ops/deps.py`, `app/ops/security.py` | → `db` | 登录、登出、session cookie、invite token 验证、角色保护 |
| `chat` | Chat 业务 | `app/ops/chat/**` | → `llm`, `db`, `rag` | LangGraph StateGraph、SSE/WS 双传输、共享 ChatEventStreamer |
| `rag` | RAG 检索与入库 | `app/ops/rag/**` | → `db` | 混合召回（dense: pgvector\|qdrant Flag；FTS/sparse 仍 PG）；ingest；影子写+DLQ |
| `data` | 数据视图 | `app/ops/overview.py`, `app/ops/issues.py`, `app/ops/pulls.py`, `app/ops/graph.py` | → `db` | Issue/PR/Overview 指标/Graph 快照只读查询（供 Chat / iOS 只读消费） |
| `admin` | Admin 同步 | `app/ops/admin/sync.py`, `app/ops/admin/service.py`, `app/ops/admin/schema.py` | → `db` | 接收 GHA sync payload 并持久化到 data/chat 依赖的表 |
| `llm` | LLM Provider | `app/llm/**` | → — | SiliconFlow / 百炼 provider 工厂 |
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
| `RetrievedChunk` / `RAG_VECTOR_BACKEND` | `rag` | `chat` | dense 默认 Qdrant Top-k id → PG hydrate；失败即时降级 pgvector；影子写 `RAG_QDRANT_SHADOW_WRITE` |

## 人签记录

| human_gate_id | status | 签核人 | 日期 | 说明 |
|---|---|---|---|---|
| HG-GRAPH-MODULES | approved | 见 `task_graph_bootstrap` | 2026-07-16 | 模块表覆盖 ops-desk-api 一级模块；图谱 bootstrap 已完成 |
| HG-GRAPH-MODULES | approved | 维护者（Phase α 迁路径） | 2026-07-27 | 真值迁至本文件；根 stub 保留 ≥1 Epic（C2） |

## 关联

- 顶层图（G-L0）：[`../l0/00_main.md`](../l0/00_main.md) · 源 [`../l0/00_main.graph.yaml`](../l0/00_main.graph.yaml)
- Chat 流程（G-L1 + chat G-L2）：[`10_flow_chat.md`](./10_flow_chat.md) · 源 [`10_flow_chat.graph.yaml`](./10_flow_chat.graph.yaml)
- 方法倒排（G-L2）：[`../l2/indexes/by_path.yaml`](../l2/indexes/by_path.yaml)
- Mermaid 约定：[`../shared/99_mermaid_protocol.md`](../shared/99_mermaid_protocol.md)
