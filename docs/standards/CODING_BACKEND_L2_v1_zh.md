# 编码规范 L2 — 后端（Python / FastAPI / SQLAlchemy · v1）

> **状态**：active  
> **栈**：Python 3.11+ · FastAPI · SQLAlchemy 2.0 async · Alembic · pytest · Ruff  
> **L1**：[`CODING_BASELINE_L1_v1_zh.md`](./CODING_BASELINE_L1_v1_zh.md)  
> **配置真值**：`app/config.py`、`.env.example`  
> **图谱**：`docs/_tech_graph/`

---

## 1. 适用范围

| 路径 | 职责 |
|---|---|
| `app/main.py` | FastAPI 入口、CORS、lifespan |
| `app/config.py` | 环境变量与配置真值 |
| `app/db/` | SQLAlchemy Base、models、session、迁移 |
| `app/ops/` | 业务路由、service、LangGraph 节点 |
| `app/llm/` | LLM Provider 工厂与实现 |
| `tests/` | pytest 测试 |

---

## 2. 条文（P-01～P-15）

| ID | 主题 | 遵循 | 本仓落地 |
|---|---|---|---|
| **P-01** | 模块边界；路由薄 | B-01 | `app/ops/*/router.py` 只负责 HTTP；业务在 `service.py` / `nodes.py` |
| **P-02** | 早返回与异常 | B-02 | handler 先校验再调用；窄捕获 `except` |
| **P-03** | 环境变量单一真值模块 | B-03 | `app/config.py` 中 `Settings` 类；外部通过 `settings.xxx` 读取 |
| **P-04** | 命名与 import 顺序 | B-04 | 模块内：stdlib → 第三方 → 本仓；业务术语与图谱一致 |
| **P-05** | 结构化错误 / HTTPException | B-05 | FastAPI 用 `HTTPException(status_code=..., detail={...})`；SSE 用 `event: error` |
| **P-06** | 分支与策略 | B-06 | Provider 工厂按 `OPS_LLM_PROVIDER` 返回实例；意图路由在 `graph.py` 显式 |
| **P-07** | 最小 diff | B-07 | 一个 PR 一个主题；禁止顺带重构无关文件 |
| **P-08** | 类型注解 / Pydantic | B-08 | 全仓 `from __future__ import annotations`；请求/响应用 Pydantic；DB model 用 Mapped/mapped_column |
| **P-09** | 重复抽取 | B-09 | `app/ops/chat/sse.py` 统一 SSE 格式化；`get_db()` 统一 session |
| **P-10** | pytest 与 marker | B-10 | `pytest tests`；async 测试用 `pytest-asyncio`；DB 测试使用 async session fixture |
| **P-11** | 安全与密钥 | B-11 | 密钥不进仓库；session cookie `HttpOnly`；invite token 校验 |
| **P-12** | 日志与 trace 字段 | B-12 | 结构化日志带 `run_id`；SSE 事件带 `seq`、`ts_ms` |
| **P-13** | 异步一致性 | — | 全链路 async；DB 用 `asyncpg` + SQLAlchemy async；禁止同步 IO 阻塞事件循环 |
| **P-14** | 数据库迁移 | — | 模型变更必须生成 Alembic migration；migration 脚本可回滚 |
| **P-15** | LangGraph 节点纯函数 | B-01 | `app/ops/chat/nodes.py` 不依赖 FastAPI；只读/写 `ChatState` |

### P-13 异步一致性

- 路由、service、节点函数均为 `async def`。
- DB 操作通过 `AsyncSession`。
- LLM 流式调用返回 async generator。
- 禁止在 async 函数中使用 `requests`、`time.sleep` 等同步阻塞调用。

### P-14 数据库迁移

```bash
alembic revision --autogenerate -m "describe_change"
alembic upgrade head
```

- 提交代码须同时提交 migration 文件。
- 不允许手动改 production DB，必须通过 migration。

### P-15 LangGraph 节点约束

- 节点函数签名：`async def xxx_node(state: ChatState) -> dict`
- 返回 dict 的 key 必须是 `ChatState` 的字段或新增字段。
- 节点内部不发起 HTTP 请求、不操作 SSE。

---

## 3. CI 对齐

| 检查 | 命令 | workflow |
|---|---|---|
| Test | `pytest tests -q --tb=short` | `.github/workflows/pytest.yml` |
| Lint | `ruff check app tests` | 待启用（当前 workflow 已注释） |
| Tech Graph | `./scripts/graph-compile.sh` | 待新增 `.github/workflows/tech-graph.yml` |

---

## 4. 修订记录

| 版本 | 日期 | 说明 |
|---|---|---|
| v1.0 | 2026-07-16 | 从 cyning-harness L2 后端模板改写为 ops-desk-api 真值 |
