# Task：Chat WebSocket 端点（面试演示向）

> **状态**：completed  
> **类型**：功能实现  
> **关联**：`docs/_tech_graph/01_struct.md` · `app/ops/chat/router.py` · `app/ops/chat/service.py` · `app/ops/deps.py`

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `chat-websocket-v1` |
| **test_strategy** | `required` |
| **test_strategy_note** | WS 握手鉴权、消息流事件序列、cancel 语义集成测试 |
| **code_quality_bar** | `L2_backend` |
| **orchestration** | 单 task |
| **git_branch** | `task/chat-websocket-v1`（基于 `task/admin-github-sync`，含未合并的 Task A/B） |
| **experience_capture** | `recommended` |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| **HG-GRAPH-MODULES** | approved | **30** | 用户确认：chat 模块新增 WS 传输层纳入 graph |
| **HG-AUDIT-R1** | approved | **30** | 用户确认：WS 暂不鉴权（iOS 未接入），首个 maintainer 作演示用户 |

---

## 背景与目标

当前 Chat 仅支持 SSE（`POST /api/ops/chat/stream`，单向 server→client）。为面试演示补充 WebSocket 传输层，展示双向实时通信能力，并与 SSE 形成可讲解的技术取舍对比。

目标：

1. 新增 `WS /api/ops/chat/ws`，复用现有 `run_chat_stream` 事件管线，事件 JSON 结构与 SSE 事件一致。
2. **暂不鉴权**（iOS 端未接入 WS，面试演示临时方案）：WS 端点不做 cookie/token 校验，直接使用 DB 中首个 maintainer 作为演示用户；不存在时推送 `error` 事件。鉴权补齐留待后续 task。
3. 支持客户端主动消息：
   - `{"type":"message","message":"...","session_id":null,"model":null}` → 启动一次 chat run，流式推回事件。
   - `{"type":"cancel","run_id":"..."}` → 取消当前进行中的 run（SSE 做不到的核心卖点）。
4. 取消语义：cancel 后推送 `run.cancelled` 事件，`ops_runs.status` 置为 `cancelled`（String 字段，无需 migration）。
5. 抽取 SSE 路由中的事件缓冲/持久化逻辑为共享 helper，SSE 与 WS 双传输复用，避免复制粘贴。
6. 单连接串行：同一 WS 连接同一时刻最多一个活跃 run；新 message 到来时若已有活跃 run，返回 `error`（`retryable: false`），不并发执行。

**完成态**：

- [x] 共享流式持久化 helper 抽取（`app/ops/chat/streaming.py` 或同级）
- [x] `WS /api/ops/chat/ws` 端点实现
- [x] 演示用户解析（首个 maintainer；不鉴权，临时方案）
- [x] message → run 流式推送（事件结构与 SSE 一致）
- [x] cancel → `run.cancelled` 事件 + run 状态落库
- [x] 单连接串行保护
- [x] 单元/集成测试
- [x] iOS/调试接口文档更新（`docs/ios/api-auth-chat.md` 或新增 ws 章节）
- [x] `docs/_tech_graph/01_struct.md` / graph yaml 更新
- [x] `./scripts/graph-compile.sh` 通过
- [x] `### 自检结论` 回填

**不做**：

- **WS 鉴权**（cookie / token 校验）—— iOS 未接入，留待后续 task
- 多连接广播 / 房间模型
- 断线重连与事件重放（WS 连接断开即终止 run 推送，事件已持久化可后续查询）
- 心跳保活基础设施（依赖 uvicorn 默认 ping 即可）
- 移除或改动现有 SSE 端点行为（仅做内部重构，外部契约不变）

---

## 范围

- [ ] `app/ops/chat/ws.py`（新增）
- [ ] `app/ops/chat/streaming.py`（新增，共享 helper）
- [ ] `app/ops/chat/router.py`（重构复用 helper，外部契约不变）
- [ ] `app/ops/router.py`（挂载 ws 路由）
- [ ] `tests/test_chat_ws.py`（新增）
- [ ] `docs/ios/api-auth-chat.md`
- [ ] `docs/_tech_graph/`

## 非范围

- 前端/iOS WebSocket 客户端实现
- Chat 回答生成逻辑改动
- Redis pub/sub、多实例 WS 水平扩展

---

## 失败路径

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|---|---|---|---|
| DB 中无 maintainer 演示用户 | 推送 `error` 事件（`stage: "ws.user"`）后关闭连接 | 是（先初始化用户） | error 事件 |
| 收到非法 JSON / 未知 type | 推送 `error` 事件（`stage: "ws.protocol"`），连接保持 | 是 | error 事件 |
| run 执行中 LLM 异常 | 推送 `error` 事件，run 落库 status=error，连接保持 | 是 | error 事件 |
| 活跃 run 期间收到新 message | 推送 `error` 事件（`message: "run already active"`） | 是（先 cancel 或等 done） | error 事件 |
| cancel 不存在的 run_id | 推送 `error` 事件（`stage: "ws.cancel"`） | 是 | error 事件 |
| 客户端断开连接 | 取消活跃 run 任务，剩余事件落库，run 状态按已发生事件收尾 | — | — |

---

## 验收标准

- [x] `pytest tests` 通过
- [x] `ruff check app tests` 通过
- [x] `./scripts/graph-compile.sh` 通过
- [x] 无凭证即可建立 WS 连接（临时演示方案），用户解析为首个 maintainer
- [x] 发送 message 后按序收到 `run.start` → （`thinking`/`tool_result`/`answer`）→ `done`，字段与 SSE 事件一致
- [x] run 进行中发送 cancel，收到 `run.cancelled` 且 DB 中 run.status == `cancelled`
- [x] 事件持久化与 SSE 路径一致（`ops_run_events` 完整）
- [x] 现有 SSE 测试不回归（外部契约不变）
- [x] 本地可用 websocat/脚本完成「连接 → 提问 → 取消 → 再提问」演示链路

---

## 给执行帽的必读列表

1. `AGENTS.md`
2. `docs/standards/CODING_BACKEND_L2_v1_zh.md`
3. `docs/_tech_graph/01_struct.md`
4. `app/ops/chat/router.py`（SSE 现有实现与持久化逻辑）
5. `app/ops/chat/service.py` / `app/ops/chat/sse.py`
6. `app/ops/deps.py`（cookie 鉴权逻辑）

---

## 实现备忘

| 项 | 状态 | 备注 |
|---|---|---|
| 共享 streaming helper | ✅ | `app/ops/chat/streaming.py`：ChatEventStreamer + 持久化函数，SSE/WS 复用 |
| WS 端点 | ✅ | `app/ops/chat/ws.py`，挂载于 `/api/ops/chat/ws` |
| 演示用户解析 | ✅ | 首个 maintainer；不鉴权（iOS 未接入，临时方案） |
| cancel 语义 | ✅ | 竞态取消（event vs graph anext 竞速），可中断 LLM 生成中节点；`run.cancelled` + 状态落库 |
| 测试 | ✅ | `tests/test_chat_ws.py` 5 个用例（TestClient portal + to_thread） |
| 文档 | ✅ | `docs/ios/api-auth-chat.md` WS 章节 + tech graph 10_flow_chat |

---

### 自检结论（执行者）

- `pytest tests` 全绿（71 passed），`ruff check app tests` 通过，`./scripts/graph-compile.sh` 通过。
- 冒烟验证（真实 LLM）：连接 → 提问 → run.start 后立即取消 → `run.cancelled`（ts_ms=1ms，真实中断 LLM 请求，DB status=cancelled）→ 同连接再提问 → 正常回答 → `done`。
- 实现要点：
  - `ChatEventStreamer` 从 SSE 路由抽取，事件 dict 为唯一中间表示，SSE 加 `make_sse_event` 外壳、WS 直接 `send_json`。
  - cancel 采用「graph `__anext__` task vs cancel Event」竞速：LangGraph 节点缓冲事件到完成才返回，逐事件轮询无法中断生成中的节点；竞态取消可直接中止 in-flight LLM 请求。
  - 串行保护带 1s 宽限期（`asyncio.wait`，非 `wait_for`——后者超时**会 cancel 任务**，曾导致客户端永远等不到终态事件的挂起 bug）。
  - 持久化在 shielded cleanup task 中完成，抗外层任务取消。
- 已知限制（非本任务范围）：
  - 节点内事件缓冲：`answer_node` 收完 LLM 全部 chunk 才一次性吐出，answer 事件是「批量到达」而非逐 token；逐 token 推送需改 Epic 6 管线（如自定义事件通道）。
  - WS 不鉴权，仅限本地演示；公网部署前必须补鉴权 task。

---

## 修订记录

| 日期 | 说明 |
|---|---|
| 2026-07-18 | 创建 task，匹配分支 `task/chat-websocket-v1`（基于 `task/admin-github-sync`） |
| 2026-07-18 | 按用户意见调整：WS 暂不鉴权（iOS 未接入），使用首个 maintainer 作为演示用户 |
