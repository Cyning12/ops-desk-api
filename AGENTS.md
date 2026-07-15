# ops-desk-api · Agent 导航

> **角色**：Ops Desk Kimi Code 的 FastAPI + LangGraph 后端。  
> **范围**：REST API、SSE Chat、数据库模型、LLM Provider、sync 接入。  
> **边界**：不实现前端页面、不实现 iOS UI。

## Open Folder 说明

在 Claude Code / Cursor 中，**应将本目录 `ops-desk-api/` 作为 Open Folder 根目录**。  
跨仓文档与统筹见 `../ops-desk-workspace/docs/`。

---

## 必读（按顺序）

1. **`README.md`** — 本仓说明
2. **`../ops-desk-workspace/docs/01-scope/00-project-brief.md`** — 项目范围与决策
3. **`../ops-desk-workspace/docs/02-backend-analysis/00-current-state.md`** — 后端现状与改造方向
4. **`../ops-desk-workspace/docs/02-backend-analysis/01-sse-chat-design.md`** — SSE Chat 详细设计
5. **`../ops-desk-workspace/docs/05-plan/00-migration-roadmap.md`** — 阶段计划

---

## 关键入口

| 路径 | 说明 |
|---|---|
| `app/main.py` | FastAPI 入口 |
| `app/config.py` | 环境变量配置 |
| `app/db/` | SQLAlchemy Base、models、session |
| `app/ops/router.py` | Ops Desk API 路由注册 |
| `app/ops/chat/` | Chat 模块：LangGraph、SSE、service |
| `app/ops/auth.py` | 登录鉴权 |
| `app/llm/` | LLM Provider 工厂与模型目录 |
| `alembic/` | 数据库迁移 |
| `tests/` | 测试 |

---

## 开发命令

```bash
# 安装依赖
uv pip install -r requirements.txt

# 本地运行
uvicorn app.main:app --reload --port 8000

# 代码检查
ruff check app tests

# 测试
pytest tests

# 数据库迁移
alembic revision --autogenerate -m "init"
alembic upgrade head
```

---

## 关键约束

- 数据库：PostgreSQL 15+，使用 `asyncpg` + SQLAlchemy 2.0 异步
- ORM/迁移：SQLAlchemy + Alembic
- Chat：LangGraph StateGraph + `graph.astream_events` + FastAPI `StreamingResponse`
- LLM：默认 SiliconFlow，百炼 fallback
- 鉴权：DB session，表 `ops_users` / `ops_sessions` / `ops_invite_tokens`
- 每次新增路由/表/事件类型必须同步更新 `docs/_tech_graph/`
