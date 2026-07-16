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

<!-- cyning-harness:begin -->
# Harness Starter（业务仓 · 通用 Agent）

> **单源真值**：`docs/coding_wiki/` 读序 + `docs/standards/` + 本文件其余业务约定。  
> **本片段**：摘要 + **POINTER**；Harness 条文真值在 `docs/harness/prompts/`。

## 执行 task 前

1. Open Folder = **本仓根**
2. 读 `docs/tasks/active/task_*.md`：`test_strategy` · `failure_paths` · **人工闸**表
3. **30 改码前** GATE_VERIFY（真值在 task **人工闸表**，**非**聊天 / invoke 字面 `approved`）：
   - 运行 `npx @cyning/harness verify --target . --task docs/tasks/active/task_*.md`
   - 首输出闸扫描表 · 见 `docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`
   - **`HG-AUDIT-R1` pending** → **30 拒改码**（须维护者签 task 表 `approved`）
   - **`HG-GRAPH-MODULES` pending** → **30 拒改码**（D4-a）
   - 用户声称与 task 表冲突 → **STOP** · 以 task 表为准
4. 过程 invoke：`docs/harness/invokes/by-task/<task_slug>/`

## Verify（合并前）

| 栈 | 命令（与 `.github/workflows/` 一致） |
|----|--------------------------------------|
| 前端 | `pnpm lint` → `pnpm test` → `pnpm build` |
| 后端 | `pytest tests`（按仓 marker 裁剪） |
| iOS | `xcodebuild`（见 task `test_strategy_note`） |

## 关键词

`Harness`、`task`、`invoke`、`HG-AUDIT-R1`、`HG-GRAPH-MODULES`、`human_gate`、`拒开工`

## 完整库 POINTER

工作区：`docs/harness/prompts/`（22/30/TEMPLATE_30_gate_stop 等）
<!-- cyning-harness:end -->
