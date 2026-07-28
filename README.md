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

项目使用 `uv` 管理依赖。`uv sync` 会根据 `pyproject.toml` 自动创建/更新 `.venv`，`uv run` 会自动使用这个虚拟环境，**不需要手动 `source` 激活**。

### 首次启动

1. 准备 PostgreSQL 数据库（详见 [`ops-desk-workspace/docs/04-infrastructure/00-local-postgresql-setup.md`](../ops-desk-workspace/docs/04-infrastructure/00-local-postgresql-setup.md)）
2. 安装依赖并启动：

```bash
uv sync --extra dev
make dev
```

### 常用命令

```bash
# 本地运行（会自动先 sync 依赖）
make dev

# 代码检查
make lint

# 测试
make test

# 数据库迁移
make migrate

# 生成新的迁移文件
make revision msg="add users table"
```

### 最短 alias（推荐加到 ~/.zshrc）

```bash
alias opsd='cd /Users/cyning/Desktop/Ops-desk/ops-desk-api && make dev'
```

之后每次开发只需要敲：

```bash
opsd
```

### 一键启动（首次 setup + 运行）

```bash
uv sync --extra dev && uv run uvicorn app.main:app --reload --port 8000
```

### 为什么不需要 `source .venv/bin/activate`？

`uv` 会优先使用项目目录下的 `.venv`。`uv sync` 会创建它，`uv run` 会自动进入它运行命令，依赖只装在这个 `.venv` 里，**不会污染系统 Python**。

### 使用系统全局 Python（不推荐）

如果你确认想装到当前激活的 Python（可能是系统 Python），可以：

```bash
uv pip install --system -r requirements.txt
```

## 相关仓库

| 仓库 | SSH 地址 |
|---|---|
| workspace | `git@github.com:Cyning12/ops-desk-workspace.git` |
| web | `git@github.com:Cyning12/ops-desk-web.git` |
| ios | `git@github.com:Cyning12/ops-desk-ios.git` |

## 生产部署

- **GHA（推荐）**：合入 `master` 自动部署，见 [`docs/deployment/gha-api-deploy.md`](docs/deployment/gha-api-deploy.md)
- **手动应急**：`ops-desk-workspace/deploy/deploy.sh --skip-web`
