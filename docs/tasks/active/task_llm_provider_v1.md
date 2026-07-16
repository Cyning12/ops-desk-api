# Task：LLM Provider 与 Chat 回答生成

> **状态**：in_progress  
> **类型**：功能实现  
> **关联**：`docs/_tech_graph/10_flow_chat.md` · `app/llm/` · `app/ops/chat/nodes.py`

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `llm-provider-and-chat-answer` |
| **test_strategy** | `required` |
| **test_strategy_note** | 新增 provider 工厂与节点单元测试；SSE 集成测试可选 |
| **code_quality_bar** | `L2_backend` |
| **orchestration** | 单 task |
| **git_branch** | `task/llm-provider-and-chat-answer` |
| **experience_capture** | `recommended` |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| **HG-GRAPH-MODULES** | approved | **30** | `01_struct` 一级模块表已覆盖 |
| **HG-AUDIT-R1** | approved | **30** | 本 task 范围明确，直接 approved |

---

## 背景与目标

当前 `app/ops/chat/nodes.py` 中 `answer_node` 为 TODO，`app/llm/` 下 Provider 为空壳。本任务实现：

1. LLM Provider 工厂与 SiliconFlow、百炼实现。
2. `answer_node` 调用 Provider 流式生成回答。
3. `run_chat_stream` 将 LangGraph 事件映射为 SSE 事件。
4. 持久化 `ops_runs` 与 `ops_run_events`。

**完成态**：

- [ ] `app/llm/factory.py` 工厂
- [ ] `app/llm/siliconflow.py` 实现
- [ ] `app/llm/bailian.py` 实现
- [ ] `answer_node` 接入 Provider
- [ ] SSE 事件映射（`thinking` / `answer` / `done` / `error`）
- [ ] `ops_runs` / `ops_run_events` 持久化
- [ ] 单元测试
- [ ] `docs/_tech_graph/10_flow_chat.graph.yaml` 更新锚点
- [ ] `./scripts/graph-compile.sh` 通过
- [ ] `### 自检结论` 回填

**不做**：

- 前端/iOS 改动
- 多轮对话上下文压缩
- 复杂 tool calling

---

## 范围

- [x] `app/llm/`
- [x] `app/ops/chat/nodes.py`
- [x] `app/ops/chat/service.py`
- [x] `app/ops/chat/router.py`
- [x] `app/db/models.py`（如需要新增字段）

## 非范围

- 登录鉴权增强
- 前端页面
- Admin 同步改造

---

## 失败路径

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|---|---|---|---|
| LLM API 不可用 | fallback 到百炼；都失败则 SSE `error` | 是 | error 事件 |
| 流式解析失败 | 关闭流并返回 error | 是 | error 事件 |
| DB 写入失败 | 流继续，但事件不持久化；日志记录 | 否 | 无（后台失败） |

---

## 验收标准

- [ ] `pytest tests` 通过
- [ ] `ruff check app tests` 通过
- [ ] `./scripts/graph-compile.sh` 通过
- [ ] 本地可发起 `POST /api/ops/chat/stream` 并收到 SSE 事件
- [ ] `ops_runs` 表有记录，`ops_run_events` 表有事件归档

---

## 给执行帽的必读列表

1. `AGENTS.md`
2. `docs/standards/CODING_BACKEND_L2_v1_zh.md`
3. `docs/_tech_graph/10_flow_chat.md`
4. `app/config.py`
5. `app/ops/chat/nodes.py`

---

## 实现备忘

| 项 | 状态 | 备注 |
|---|---|---|
| SiliconFlow 实现 | ⏳ | 任务 6.1；可并行 6.2 |
| 百炼 fallback | ⏳ | 任务 6.2；可并行 6.1 |
| Provider 工厂 | ⏳ | 任务 6.3；依赖 6.1、6.2 |
| load_context_node | ⏳ | 任务 6.4；可并行 6.5 |
| answer_node 接入 | ⏳ | 任务 6.5；依赖 6.3、6.4 |
| SSE 事件映射 | ⏳ | 任务 6.6；依赖 6.5；建议用 `stream_mode="updates"` |
| 持久化 | ⏳ | 任务 6.7；依赖 6.6；session 生命周期与 generator 解耦 |

---

### 自检结论（执行者）

（30/40 回填）

---

## 修订记录

| 日期 | 说明 |
|---|---|
| 2026-07-16 | 创建 task，匹配分支 `task/llm-provider-and-chat-answer` |
