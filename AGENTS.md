# ops-desk-api · Agent 导航

> **角色**：Ops Desk Kimi Code 的 FastAPI + LangGraph 后端。  
> **范围**：REST API、SSE Chat、数据库模型、LLM Provider、sync 接入。  
> **边界**：不实现前端页面、不实现 iOS UI。

## Open Folder 说明

在 Claude Code / Cursor 中，**应将本目录 `ops-desk-api/` 作为 Open Folder 根目录**。  
跨仓文档与统筹见 `../ops-desk-workspace/docs/`。

---

## 必读（按顺序）

1. **本文件 `AGENTS.md`** — Agent 导航与约束
2. **`docs/tasks/active/task_*.md`** — 当前进行中任务与人工闸表（**每次新会话必须先读**）
3. **`docs/coding_wiki/README.md`** — WikiTrack 读序入口（正文真值仍在 standards / 图谱 / 部署等原路径）
4. **`docs/_tech_graph/README.md`** + **`LAYER_README.md`** — 图谱物理分层（G-L0/G-L1/G-L2；目录 `l0`≡G-L0）
5. **`docs/skills/`** — Skill 真值（S-L0/S-L1；IDE 仅拷贝）
6. **`docs/standards/CODING_BACKEND_L2_v1_zh.md`** — 后端编码规范
7. **`README.md`** — 本仓说明
8. **`../ops-desk-workspace/docs/01-scope/00-project-brief.md`** — 项目范围与决策
9. **`../ops-desk-workspace/docs/02-backend-analysis/00-current-state.md`** — 后端现状与改造方向
10. **`../ops-desk-workspace/docs/02-backend-analysis/01-sse-chat-design.md`** — SSE Chat 详细设计
11. **`../ops-desk-workspace/docs/05-plan/00-migration-roadmap.md`** — 阶段计划

---

## 新会话启动纪律（自动加载 harness 流程）

每次新窗口/新会话启动时，**必须先完成以下步骤，再改业务代码**：

1. **扫描 active task**
   ```bash
   ls docs/tasks/active/
   ```
   - 有 `task_*.md`：读取其范围、验收标准、`failure_paths`、人工闸表。
   - 无 active task：停止改码，先走 `10-task` 创建 task。

2. **核验人工闸**
   | 闸 | 阻塞 | 真值位置 |
   |---|---|---|
   | `HG-GRAPH-MODULES` | 30 改码 | `docs/_tech_graph/l1/01_modules.md` |
   | `HG-PILOT-OPSDESK-GLAYER` | 物理分层试点改码 | `docs/tasks/active/task_*.md` 人工闸表 |
   | `HG-AUDIT-R1` | 30 开工 | `docs/tasks/active/task_*.md` 人工闸表 |

3. **确认分支正确**
   - 当前分支应为 `task/<short-description>` 或 `fix/<description>`。
   - 若在 `main`/`master`，禁止直接改码；先切任务分支。

4. **首输出闸扫描**
   - 30 改码前必须输出 GATE_VERIFY 表（见 `docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`）。
   - 任一 blocks 30 的闸为 `pending` → **拒开工**。

5. **无 task 不改码**
   - 文档/图谱维护类改动也须先有 task 或变更请求。
   - 紧急修复走 `fix/` 分支，但仍需补 task 与 invoke。

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
- 每次新增路由/表/事件类型必须同步更新 `docs/_tech_graph/`（物理分层：`l0`/`l1`/`l2`/`shared`）
- task 生产字段须含 `graph_change_layer` 与 `review_hat`（默认 `20`）；正文写 G-L\*/S-L\*，禁止裸「L0」作架构义
- Skill 只改 `docs/skills/`，再拷贝到 IDE skills 目录
- **分支与提交流程：禁止直接在 `main`/`master` 改码，必须通过任务分支 + PR 合并**
 - 新任务：`git checkout -b task/<short-description>`
 - 所有代码改动在任务分支完成并提交
 - 完成后通过 GitHub Pull Request 合并到 `main`
 - PR 合并前必须 `./scripts/graph-compile.sh` 通过且 CI 绿
 - 紧急修复也使用 `fix/<description>` 分支，不走 `main` 直推

<!-- cyning-harness:begin -->
# Harness Starter（业务仓 · 通用 Agent）

> **单源真值**：`docs/coding_wiki/` 读序 + `docs/standards/` + 本文件其余业务约定。  
> **本片段**：摘要 + **POINTER**；Harness 条文真值在 `docs/harness/prompts/`。  
> **仓内定制（v2.22+）**：写在本产品块 **外** 的 `<!-- cyning-harness-local:begin/end -->`；勿改本 begin/end 内文（upgrade 会整块替换）。G-L 布局见 profile `graph_modules_path`。

## 执行 task 前

1. Open Folder = **本仓根**
2. 读 `docs/tasks/active/task_*.md`：`test_strategy` · `failure_paths` · **人工闸**表
3. **30 改码前** GATE_VERIFY（真值在 task **人工闸表**，**非**聊天 / invoke 字面 `approved`）：
   - 运行 `npx spec-wave verify --target . --task docs/tasks/active/task_*.md`
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

<!-- cyning-harness-local:begin -->
## Ops-desk-api · Harness 仓内定制（upgrade 不改写本块）

- **pre-30 invoke 缺失**（v2.14+ · default 须有 10 等）→ **拒改码**；用户「开工」≠ 闸
- 关键词补充：`HG-PILOT-OPSDESK-GLAYER`、`G-L0`
- 图谱闸路径：`HG-GRAPH-MODULES` → `docs/_tech_graph/l1/01_modules.md`（profile `graph_modules_path`）
- **仓规条款一**（2026-10-30 · task_api_legacy_reviews_backfill S2）：升级/流程类 task 禁用 `--allow-no-review`，一律走 20-R1 审查文
- **仓规条款二**（2026-10-30 · task_api_legacy_reviews_backfill S2）：`docs/harness/legacy-gate-exempt.yaml` 扩列须带截止条件或回填义务（在四字段纪律之上 · 截止条件/回填义务写入 reason 字段）；语义面人审非机断——截止条件/回填义务由人审核对，spec-wave 四字段校验为机械面，语义面不机判（R1 审查 O2）
<!-- cyning-harness-local:end -->
