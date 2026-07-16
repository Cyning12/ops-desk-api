# 编码基线 L1 — ops-desk-api（Python · FastAPI · v1）

> **状态**：active  
> **版本**：v1.0  
> **日期**：2026-07-16  
> **维护**：本仓 `docs/standards/`  
> **L2**：[`CODING_BACKEND_L2_v1_zh.md`](./CODING_BACKEND_L2_v1_zh.md)

---

## 1. 适用范围

| 适用 | 不适用 |
|---|---|
| 本仓业务代码新增/修改 | 纯文档 task（无代码） |
| Agent 与人类 PR | 第三方 vendored |
| `app/`、`tests/`、`alembic/` | 依赖包内部 |

**优先级**：task + `_tech_graph` + `AGENTS.md` > 本 L1 > L2 > 外部参考 > 个人习惯。

---

## 2. 条文（B-01～B-12）

| ID | 原则 | 本仓落地 |
|---|---|---|
| **B-01** | 单一职责；函数/模块只做一件事 | 路由层薄，handler 只解析请求/调用 service；业务逻辑下沉到 `app/ops/*/service.py` 与节点函数 |
| **B-02** | 早返回；嵌套 ≤2 | `if not x: return` 优先；避免深层 if/try 嵌套 |
| **B-03** | 配置外置；禁止硬编码 URL/密钥 | `app/config.py` 为唯一环境变量真值；`.env.example` 文档化变量名 |
| **B-04** | 命名即文档；与图谱/API 术语一致 | 函数/变量名与 `docs/_tech_graph/`、API schema 术语一致；issue_qa / overview / general 等意图名统一 |
| **B-05** | 错误可结构化 | 路由层返回 `{"error": "code", "message": "..."}`；内部异常不泄露 traceback；SSE error 事件格式统一 |
| **B-06** | 扩展点显式；表驱动优于 if-else 链 | LLM Provider 使用工厂模式；LangGraph 条件路由显式在 `graph.py` 声明 |
| **B-07** | 最小 diff；禁止范围外重构 | 一个 task 只改相关模块；图谱与代码同步更新 |
| **B-08** | 类型与契约优先 | 全仓类型注解；Pydantic 校验请求/响应；禁止裸 `dict` 传业务数据 |
| **B-09** | 重复 ≥3 处须抽取 | SSE 事件格式化、DB session 获取、配置读取等已抽为公共函数 |
| **B-10** | 测试与行为绑定 | `pytest tests` 绿；新增路由/节点须补测试；`test_strategy: required` 先测后码 |
| **B-11** | 安全与密钥；输入校验 | 密钥只进 env；invite token / session cookie 校验；SQL 注入通过 SQLAlchemy 参数化防御 |
| **B-12** | 可观测钩子；禁止静默失败 | 异常必须记录或返回 error 事件；SSE 流必须发送 `done` 或 `error` 终止 |

---

## 3. 反模式速查

| ID | 反模式 | 改法 | 条文 |
|---|---|---|---|
| AP-01 | 魔法字符串 API 路径 | 使用 router prefix 常量 / 由 FastAPI 生成 | B-03, B-04 |
| AP-02 | 路由层堆业务+SQL | 下沉 service / repository | B-01 |
| AP-03 | 深层嵌套 try/except | 早 return；窄捕获 | B-02 |
| AP-04 | `except Exception: pass` | 结构化错误 + 日志 | B-05, B-12 |
| AP-05 | 在节点函数里操作 HTTP/SSE | 节点函数只读/写 `ChatState` | B-01 |
| AP-06 | 直接改 `site-packages` | fork + editable install 或适配层 | B-06, B-07 |

---

## 4. PR / 审查自检

- [ ] 无新增硬编码 URL/魔法数/密钥（B-03, B-11）
- [ ] 无范围外文件改动（B-07）
- [ ] 新增/修改路由、表、事件、LangGraph 节点已同步更新 `docs/_tech_graph/*.graph.yaml`
- [ ] `./scripts/graph-compile.sh` 通过
- [ ] `ruff check app tests` 通过
- [ ] `pytest tests` 通过（B-10）

---

## 5. 与 L2 的关系

| 层级 | 路径 | 职责 |
|---|---|---|
| **L1** | 本文件 | 语言无关原则与条文 ID |
| **L2 后端** | `CODING_BACKEND_L2_v1_zh.md` | Python / FastAPI / SQLAlchemy / pytest 具体规则 |
| **L3** | `AGENTS.md`、`.cursor/rules` | ≤15 行摘要 + 链至 L1/L2 |

---

## 6. 修订记录

| 版本 | 日期 | 说明 |
|---|---|---|
| v1.0 | 2026-07-16 | 从 cyning-harness L1 模板改写为 ops-desk-api 真值 |
