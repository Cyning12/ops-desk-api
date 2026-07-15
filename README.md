# ops-desk-api

Ops Desk Kimi Code 的后端 API 服务。

## 技术栈

- Python 3.11+
- FastAPI
- LangGraph
- SQLAlchemy 2.0 + Alembic
- asyncpg
- Pydantic v2
- pgvector

## 仓库职责

- REST API：Overview / Issues / Pulls / Graph / Auth
- SSE Chat：LangGraph 编排 + 流式返回
- 数据库模型与迁移
- LLM Provider 工厂（SiliconFlow / 百炼）
- GitHub sync admin endpoint

## 必读

1. **`AGENTS.md`** — 本仓 Agent 导航
2. `../ops-desk-workspace/docs/02-backend-analysis/00-current-state.md` — 后端现状分析
3. `../ops-desk-workspace/docs/02-backend-analysis/01-sse-chat-design.md` — SSE Chat 设计
4. `../ops-desk-workspace/docs/01-scope/00-project-brief.md` — 项目范围

## 开发命令

```bash
# 安装依赖
uv pip install -r requirements.txt

# 本地运行
uvicorn app.main:app --reload

# 检查
ruff check app tests
pytest tests

# 数据库迁移
alembic revision --autogenerate -m "init"
alembic upgrade head
```

## 相关仓库

| 仓库 | SSH 地址 |
|---|---|
| workspace | `git@github.com:Cyning12/ops-desk-workspace.git` |
| web | `git@github.com:Cyning12/ops-desk-web.git` |
| ios | `git@github.com:Cyning12/ops-desk-ios.git` |
