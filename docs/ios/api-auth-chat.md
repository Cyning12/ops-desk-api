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

## 注意事项

- 本地开发时 cookie 的 `secure` 标志为 `false`，支持 HTTP。
- `ops_session` 为 **HttpOnly**，iOS JavaScript 无法读取，但 `URLSession` 会自动管理。
- session 默认有效期 7 天（由后端 `session_ttl_hours` 控制）。
- 若收到 401，应引导用户重新登录。
