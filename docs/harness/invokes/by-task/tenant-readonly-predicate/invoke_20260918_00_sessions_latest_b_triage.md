# invoke · 00 · tenant-readonly-predicate · sessions/latest@B 联调阻塞排查

| 项 | 内容 |
|----|------|
| **时间** | 2026-09-18 |
| **帽** | 00 |
| **分支** | `task/tenant-readonly-predicate` |
| **触发** | web 报：切 B 后 `GET /api/ops/chat/sessions/latest` → 500 → Chat 输入禁用 |

## 结论

**非** `sessions/latest` 在租户 B 下的数据面/谓词 bug。  
**真因（高置信）**：web Vite 代理打 `:8001` 时 api 进程曾断开 → `ECONNREFUSED` → **代理层对浏览器表现为 500**（头仍可被记成 `x-ops-tenant-id: ops-desk-pilot-b`）。

## 证据

| 源 | 事实 |
|----|------|
| web vite 日志 `996973` | `4:33:54` `proxy error: /api/ops/chat/sessions/latest` · `ECONNREFUSED 127.0.0.1:8001`（同窗还有 `/auth/tenant` `/auth/me`） |
| web 起的 api `996972` | `4:31:00` exit 143 关停；日志内 **零条** `sessions/latest` |
| 本仓现活 api `:8001`（4:40 起，常驻） | live HTTP：`login → latest@A → POST /tenant B → latest@B(+header)` **全 200** |
| ASGI 同路径 | 同上 **200**；`sessions/latest` **不读** tenant 头/谓词（仅 `get_current_user` + `OpsSessionChat`） |
| Docker `:8000` | openapi **无** `/api/ops/auth/tenant`（勿联调） |

## 给 web 00

1. 确认 `VITE_API_PROXY=http://127.0.0.1:8001` 且本仓 uvicorn **仍在听**（勿用 Docker `:8000`）。
2. **重试**：切 B → 进 Chat → Network 看 `sessions/latest` 应为 **200**；再发 lg-rag/stream。
3. 若再 500：请贴 **响应 body** + api 终端该请求行（区分代理 500 vs 应用 Traceback）。

## 本窗

- **未改实现码**（无应用层缺陷可修）
- api `:8001` **保持运行**供联调
- 派 30：补「切 B → latest」回归单测（防回归；非修 500）
