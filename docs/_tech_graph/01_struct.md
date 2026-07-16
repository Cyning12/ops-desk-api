# 模块边界登记表（L0-b · D4-a 人签真值）

> **用途**：`docs/_tech_graph/01_struct.md` — **一级模块** 边界；**HG-GRAPH-MODULES** approved 后方可 **30 执行改码**。  
> **范围**：Ops Desk 后端 API（`ops-desk-api`）。

---

## 模块表（必填）

| module_id | 名称 | 路径 glob | 依赖方向（仅指向谁） | 负责人/备注 |
|-----------|------|-----------|----------------------|-------------|
| `entry` | 入口与配置 | `app/main.py`, `app/config.py` | → `api`, `db` | FastAPI 实例、CORS、环境变量 |
| `api` | API 路由注册 | `app/ops/router.py`, `app/ops/*/router.py` | → `service`, `auth`, `db` | HTTP 入口、SSE 流封装 |
| `auth` | 鉴权模块 | `app/ops/auth.py`, `app/ops/deps.py` | → `db` | 登录、登出、session cookie |
| `chat` | Chat 业务 | `app/ops/chat/**` | → `llm`, `db` | LangGraph StateGraph、SSE 事件 |
| `data` | 数据视图 | `app/ops/overview.py`, `app/ops/issues.py`, `app/ops/pulls.py`, `app/ops/graph.py` | → `db` | Issue/PR/Overview/Graph 快照只读查询 |
| `admin` | Admin 同步 | `app/ops/admin/sync.py` | → `db` | 接收 GHA sync payload 并持久化 |
| `llm` | LLM Provider | `app/llm/**` | → — | SiliconFlow / 百炼 provider 工厂 |
| `db` | 数据库与 ORM | `app/db/**`, `alembic/**` | —（被依赖） | SQLAlchemy models、session、migrations |

## 跨模块契约

| 契约 | 提供方 module_id | 消费方 | 说明 |
|---|---|---|---|
| `ChatState` | `chat` | `chat` 内部节点 | LangGraph 状态字典 |
| `SseEvent` | `api` | `chat` / 前端 | SSE 事件 JSON 格式 |
| `AsyncSession` | `db` | `admin`, `data`（未来） | 数据库会话依赖 |

## 人签记录

| human_gate_id | status | 签核人 | 日期 | 说明 |
|---|---|---|---|---|
| HG-GRAPH-MODULES | approved | 见 `task_graph_bootstrap` | 2026-07-16 | 模块表覆盖 ops-desk-api 一级模块；图谱 bootstrap 已完成 |

## 关联

- 顶层图：[`00_main.md`](./00_main.md) · 源 [`00_main.graph.yaml`](./00_main.graph.yaml)
- Chat 流程：[`10_flow_chat.md`](./10_flow_chat.md) · 源 [`10_flow_chat.graph.yaml`](./10_flow_chat.graph.yaml)
- Mermaid 约定：[`99_mermaid_protocol.md`](./99_mermaid_protocol.md)
