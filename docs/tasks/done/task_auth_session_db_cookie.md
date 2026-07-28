# Task：认证鉴权体系（DB Session + HttpOnly Cookie）

> **状态**：completed  
> **类型**：功能实现  
> **关联**：`docs/_tech_graph/01_struct.md` · `app/ops/auth.py` · `app/db/models.py` · `app/deps.py`

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `auth-session-db-cookie` |
| **test_strategy** | `required` |
| **test_strategy_note** | login/session/logout/me 单元测试；admin 路由保护集成测试 |
| **code_quality_bar** | `L2_backend` |
| **orchestration** | 单 task |
| **git_branch** | `task/auth-session-db-cookie` |
| **experience_capture** | `recommended` |

| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 本仓未启用 WikiTrack |
### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| **HG-GRAPH-MODULES** | approved | **30** | 用户确认：任务含 auth/chat 模块及 iOS 接口文档，纳入 graph |
| **HG-AUDIT-R1** | approved | **30** | 用户确认：范围含 iOS 联调整体验收 |

---

## 背景与目标

当前 `app/ops/auth.py` 与 `app/deps.py` 为空壳，`ops_users` / `ops_sessions` / `ops_invite_tokens` 表已定义但无业务逻辑。本任务实现完整的 DB session 认证鉴权体系，并优先面向 iOS v1 Chat 联调提供可用接口：

1. 初始化脚本创建首个 maintainer 用户与邀请密钥。
2. `POST /api/ops/login` 校验 username + invite token，签发 `ops_session` HttpOnly Cookie。
3. `get_current_user` 依赖校验 cookie token_hash，过期拒绝。
4. `POST /api/ops/logout` 使当前 session 过期。
5. `GET /api/ops/me` 返回当前登录用户。
6. `require_maintainer` 仅允许 maintainer 访问 admin/sync 路由。
7. 提供 iOS 可提前调用的接口文档，覆盖登录 → 获取/创建最新 chat session → stream 调用链路。

**完成态**：

- [x] 初始化脚本 `scripts/create_initial_user.py`
- [x] `POST /api/ops/login` 实现
- [x] `POST /api/ops/logout` 实现
- [x] `GET /api/ops/me` 实现
- [x] `get_current_user` 依赖实现
- [x] `require_maintainer` 依赖实现
- [x] admin/sync 路由挂载保护
- [x] iOS 接口文档 `docs/ios/api-auth-chat.md`
- [x] 单元/集成测试
- [x] `docs/_tech_graph/01_struct.md` / graph yaml 更新
- [x] `./scripts/graph-compile.sh` 通过
- [x] `### 自检结论` 回填

**不做**：

- 用户注册、OAuth、JWT、RBAC 细粒度权限
- 前端/iOS 登录页面
- 邀请密钥的邮件发送

---

## 范围

- [x] `app/ops/auth.py`
- [x] `app/deps.py`
- [x] `app/ops/router.py`（挂载保护）
- [x] `app/ops/admin/sync.py`（添加 `require_maintainer`）
- [x] `scripts/create_initial_user.py`
- [x] `docs/ios/api-auth-chat.md`
- [x] `tests/test_auth.py`

## 非范围

- 登录鉴权增强（2FA、OAuth、JWT）
- 前端页面
- Admin sync 具体 upsert 逻辑（属于 Epic 4）

---

## 失败路径

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|---|---|---|---|
| username 不存在 | 返回 401，不泄露用户是否存在 | 是 | 401 Unauthorized |
| invite token 无效或已使用 | 返回 401 | 是 | 401 Unauthorized |
| session token 无效/过期 | 返回 401 | 是 | 401 Unauthorized |
| 非 maintainer 访问 admin/sync | 返回 403 | 否 | 403 Forbidden |

---

## 验收标准

- [x] `pytest tests` 通过
- [x] `ruff check app tests` 通过
- [x] `./scripts/graph-compile.sh` 通过
- [x] 本地可调用 `POST /api/ops/login` 并收到 `ops_session` HttpOnly Cookie
- [x] 携带有效 cookie 可访问 `GET /api/ops/me`
- [x] 未登录访问 `POST /api/ops/admin/sync` 返回 401
- [x] 非 maintainer 访问 `POST /api/ops/admin/sync` 返回 403
- [x] iOS 本地可完成：登录 → 获取/创建最新 chat session → `POST /api/ops/chat/stream` 收到 SSE 事件
- [x] iOS 接口文档覆盖 cookie 处理、session 获取、stream 调用示例

---

## 给执行帽的必读列表

1. `AGENTS.md`
2. `docs/standards/CODING_BACKEND_L2_v1_zh.md`
3. `docs/_tech_graph/01_struct.md`
4. `app/config.py`
5. `app/db/models.py`
6. `app/ops/router.py`

---

## 实现备忘

| 项 | 状态 | 备注 |
|---|---|---|
| 初始化脚本 | ✅ | 创建 maintainer + invite token |
| login 接口 | ✅ | 依赖初始化脚本 |
| session 校验依赖 | ✅ | 依赖 login |
| logout / me 接口 | ✅ | 依赖 session 校验 |
| maintainer 保护 | ✅ | 依赖 session 校验；在 `app/ops/router.py` 挂载 admin/sync 时应用 |
| iOS 接口文档 | ✅ | 与 iOS 端同步 cookie/session/stream 调用顺序；放在 `docs/ios/api-auth-chat.md` |

---

### 自检结论（执行者）

本地验收已通过：

- `ruff check app tests`：全部通过
- `pytest tests`：42 passed，9 skipped（skip 为 PostgreSQL 不可用时跳过）
- `./scripts/graph-compile.sh`：通过，生成 `10_flow_auth.md` 等
- 手动联调通过：
  - `POST /api/ops/auth/login` 设置 `ops_session` HttpOnly cookie
  - `GET /api/ops/auth/me` 返回当前用户
  - `GET /api/ops/chat/sessions/latest` 自动创建/返回最近 session
  - `POST /api/ops/admin/sync` 作为 maintainer 返回 202
  - `POST /api/ops/auth/logout` 清除 session，后续 `/me` 返回 401
- iOS 接口文档 `docs/ios/api-auth-chat.md` 已覆盖完整调用链

---

## 修订记录

| 日期 | 说明 |
|---|---|
| 2026-07-17 | 创建 task，匹配分支 `task/auth-session-db-cookie` |
| 2026-07-17 | 增加 iOS 联调整体验收与 `docs/ios/api-auth-chat.md` 文档 |
| 2026-07-17 | 实现完成并通过 ruff / pytest / graph-compile / 手动联调 |

