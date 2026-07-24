# iOS v1 · Auth + Chat 接口联调文档

> **适用对象**：`ops-desk-ios` v1 Chat 模块  
> **后端版本**：`task/auth-session-db-cookie`  
> **更新日期**：2026-07-17

---

## 联调前置

1. 后端启动且数据库已迁移：
   ```bash
   alembic upgrade head
   uvicorn app.main:app --reload --port 8000
   ```
2. 创建首个 maintainer 用户与邀请密钥：
   ```bash
   python scripts/create_initial_user.py
   ```
   输出示例：
   ```json
   {"username": "admin", "invite_token": "AbCdEfGhIjKlMnOpQrStUvWxYz", "role": "maintainer"}
   ```

---

## 接口概览

| 顺序 | 方法 | 路径 | 说明 |
|---|---|---|---|
| 1 | POST | `/api/ops/auth/login` | 用户名 + 邀请密钥登录，设置 HttpOnly cookie |
| 2 | GET | `/api/ops/auth/me` | 确认登录状态 |
| 3 | GET | `/api/ops/chat/sessions/latest` | 获取最新 chat session，无则自动创建 |
| 4 | POST | `/api/ops/chat/stream` | SSE 流式对话 |
| 5 | POST | `/api/ops/auth/logout` | 登出，清除 cookie |

---

## 1. 登录

**Request**

```http
POST /api/ops/auth/login HTTP/1.1
Content-Type: application/json

{
  "username": "admin",
  "invite_token": "AbCdEfGhIjKlMnOpQrStUvWxYz"
}
```

**Response**

```json
{
  "ok": true,
  "user": {
    "id": "...",
    "username": "admin",
    "role": "maintainer"
  }
}
```

**Cookie**

- 响应会设置 `ops_session` HttpOnly Cookie。
- iOS 需使用支持 cookie 的 HTTP 客户端（如 `URLSession` 默认自动管理 cookie jar）。
- 后续请求必须携带该 cookie。

---

## 2. 获取当前用户

用于验证 session 是否有效。

```http
GET /api/ops/auth/me HTTP/1.1
Cookie: ops_session=...
```

```json
{
  "user": {
    "id": "...",
    "username": "admin",
    "role": "maintainer"
  }
}
```

---

## 3. 获取/创建最新 Chat Session

iOS v1 每次进入 Chat 页面时调用此接口：有则返回最近使用的 session，无则自动创建。

```http
GET /api/ops/chat/sessions/latest HTTP/1.1
Cookie: ops_session=...
```

```json
{
  "id": "...",
  "user_id": "...",
  "title": "New Chat",
  "created_at": "2026-07-17T01:23:45",
  "updated_at": "2026-07-17T01:23:45"
}
```

**说明**

- `id` 即后续调用 `/api/ops/chat/stream` 时所需的 `session_id`。
- 首次调用会新建 session；后续调用返回最近更新的 session。
- 若需未来支持多 session 列表，可新增 `GET /api/ops/chat/sessions`。

---

## 4. SSE 流式对话

```http
POST /api/ops/chat/stream HTTP/1.1
Content-Type: application/json
Cookie: ops_session=...

{
  "message": "你好",
  "session_id": "<从 /chat/sessions/latest 获取>",
  "model": null
}
```

**响应**：`text/event-stream`

事件类型（按顺序出现）：

| event_type | agent_role | payload 说明 |
|---|---|---|
| `run.start` | `system` | `{ "run_id": "..." }` |
| `thinking` | `intent` / `context` | 思考过程文本 |
| `answer` | `answer` | 回答文本片段 |
| `done` | `system` | `{ "latency_ms": 1234, "model": "..." }` |
| `error` | `system` | `{ "stage": "...", "message": "...", "retryable": false }` |

**iOS 消费提示**

- 使用 `URLSession` 的 `dataTask` 读取 stream。
- 按 `\n\n` 分割 SSE 帧。
- 每帧去掉 `data: ` 前缀后按 JSON 解析。
- 只处理 `event_type` 为 `answer` / `thinking` / `done` / `error` 的行。

---

## 5. 登出

```http
POST /api/ops/auth/logout HTTP/1.1
Cookie: ops_session=...
```

```json
{
  "ok": true
}
```

- 服务端会删除 DB session 并清除 cookie。
- iOS 本地也应清空 cookie jar 或相关缓存。

---

## 错误码

| 状态码 | 场景 |
|---|---|
| 200 | 成功 |
| 401 | 未登录、session 过期、invite token 无效 |
| 403 | 已登录但非 maintainer 访问 admin/sync（iOS 一般不需要） |
| 404 | chat session 不存在（ `/chat/sessions/latest` 不会返回 404，会自动创建） |

---

## iOS 调用时序

```
启动 App
  │
  ▼
POST /api/ops/auth/login
  │
  ▼
GET /api/ops/chat/sessions/latest  ──┐
  │                                  │
  ▼                                  │
POST /api/ops/chat/stream  ◄─────────┘  (用户发送消息)
  │
  ▼
消费 SSE 事件并渲染
```

---

## curl 完整示例

```bash
# 1. 创建用户并获取 token
export TOKEN=$(python scripts/create_initial_user.py | jq -r '.invite_token')

# 2. 登录（保存 cookie 到 /tmp/cookies.txt）
curl -c /tmp/cookies.txt -X POST http://localhost:8000/api/ops/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","invite_token":"'$TOKEN'"}'

# 3. 获取当前用户
curl -b /tmp/cookies.txt http://localhost:8000/api/ops/auth/me

# 4. 获取最新 chat session
export SESSION_ID=$(curl -s -b /tmp/cookies.txt http://localhost:8000/api/ops/chat/sessions/latest | jq -r '.id')

# 5. 流式对话
curl -b /tmp/cookies.txt -X POST http://localhost:8000/api/ops/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message":"你好","session_id":"'$SESSION_ID'"}'

# 6. 登出
curl -b /tmp/cookies.txt -X POST http://localhost:8000/api/ops/auth/logout
```

---

## WebSocket Chat（实验性 · 暂不鉴权）

> ⚠️ **临时方案**：`WS /api/ops/chat/ws` 当前**不做鉴权**，服务端自动以 DB 中首个 maintainer 作为演示用户。仅用于本地面试演示，iOS 暂未接入；公网部署前必须补鉴权。

### 连接

```
ws://localhost:8000/api/ops/chat/ws
```

### 客户端 → 服务端

```json
// 发起一次对话
{"type": "message", "message": "#1 是什么问题？", "session_id": null, "model": null}

// 取消进行中的 run（run_id 来自 run.start 事件）
{"type": "cancel", "run_id": "<run_id>"}
```

### 服务端 → 客户端

事件 JSON 结构与 SSE 完全一致（`run_id` / `seq` / `ts_ms` / `agent_role` / `event_type` / `payload`），以 JSON text frame 推送：

```
run.start → thinking* → tool_result* → answer* → done
                                              └─ 或 run.cancelled（取消时）
                                              └─ 或 error（失败时）
```

### 与 SSE 的差异

| 维度 | SSE `/chat/stream` | WS `/chat/ws` |
|---|---|---|
| 方向 | 单向（server→client） | 双向 |
| 取消生成 | 不支持 | `{"type":"cancel"}` |
| 鉴权 | cookie 必填 | 暂不鉴权（演示用户） |
| 并发 | 每次请求独立 run | 单连接同时最多 1 个活跃 run |
| 重连 | 浏览器自动 | 客户端自行处理 |

### 协议错误

非法 JSON / 未知 type / 活跃 run 期间重复发 message / cancel 不存在的 run，都会收到 `event_type: "error"` 的帧（`payload.stage` 分别为 `ws.protocol` / `ws.cancel`），连接保持不断开。

### websocat 调试示例

```bash
# 连接并提问
websocat ws://localhost:8000/api/ops/chat/ws
> {"type":"message","message":"你好"}
< {"run_id":"...","seq":1,"event_type":"run.start",...}
< ...
< {"event_type":"done",...}

# 取消（另起一行发送）
> {"type":"cancel","run_id":"<run_id>"}
< {"event_type":"run.cancelled",...}
```

---

## 注意事项

- 本地开发时 cookie 的 `secure` 标志为 `false`，支持 HTTP。
- `ops_session` 为 **HttpOnly**，iOS JavaScript 无法读取，但 `URLSession` 会自动管理。
- session 默认有效期 7 天（由后端 `session_ttl_hours` 控制）。
- 若收到 401，应引导用户重新登录。
