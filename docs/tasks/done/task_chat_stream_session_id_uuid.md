# Task：修复 chat stream 带 session_id 恒 404（str vs UUID 比较）

> **状态**：completed  
> **类型**：缺陷修复  
> **关联**：ops-desk-web Epic W7 联调阻断 · `app/ops/chat/streaming.py`

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `chat-stream-session-id-uuid` |
| **test_strategy** | `required` |
| **test_strategy_note** | 回归测试：真实 DB 用户（UUID id）+ 既有 chat session 调 /chat/stream 应 200 |
| **code_quality_bar** | `L2_backend` |
| **orchestration** | 单 task（ops-desk-web Epic 联调发现的阻断缺陷） |
| **git_branch** | `fix/chat-stream-session-id` |
| **experience_capture** | `recommended` |

| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 本仓未启用 WikiTrack |
### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| **HG-GRAPH-MODULES** | approved | **30** | 00统筹签：单行修复，不改模块边界 |
| **HG-AUDIT-R1** | approved | **30** | 00统筹签（用户授权人闸给 00 统筹）：修复 `resolve_chat_session` 中 `str(chat_session.user_id) != user_id` 的类型比较缺陷 |

---

## 背景与目标

ops-desk-web W7 联调实证：`GET /chat/sessions/latest` 返回的 session_id 再调 `POST /chat/stream` 恒 404「Chat session not found」；不传 session_id 则正常流式。

根因：`streaming.py::resolve_chat_session` 中 `str(chat_session.user_id) != user_id`——`user_id` 实参为真实鉴权加载的 `OpsUser.id`（`UUID(as_uuid=True)` → `uuid.UUID` 对象），str 与 UUID 对象比较恒不等。既有测试因 `override_auth` 用 str id 构造 OpsUser 而漏网。

**完成态**：

- [x] `streaming.py` 修复为 `str(user_id)` 比较
- [x] 回归测试：真实 DB 用户（UUID id）+ 既有 session → 200 SSE；修复前红、修复后绿
- [x] `pytest tests/test_chat_router.py` 通过
- [x] docker compose 重建 api 后实测：latest → stream(带 session_id) → SSE 200

**不做**：WS 端点同构检查（如同款缺陷另开 task）；其他端点。

## 范围

- `app/ops/chat/streaming.py`（1 行）
- `tests/test_chat_router.py`（+1 回归测试）

## 非范围

- 前端改动
- WS transport

## 失败路径

| 触发条件 | 系统行为 | 用户可见 |
|---|---|---|
| session 不存在/非本人 | 404（保持不变） | 404 |

## 验收标准

- [x] 回归测试修复前 FAIL、修复后 PASS
- [x] `pytest tests/test_chat_router.py` 全绿
- [x] 容器重建后 curl 实测带 session_id 流式 200

---

### 自检结论（执行者）

- 回归测试 `test_stream_existing_session_ok` 修复前 FAIL（`assert 404 == 200`，复现 str vs UUID 比较缺陷），修复后 PASS。
- `pytest tests` 85 passed；`ruff check` 通过。
- 容器 `docker compose up -d --build api` 重建后实测：`GET /chat/sessions/latest` → `POST /chat/stream`（带 session_id）SSE 序列完整（run.start → thinking×2 → answer → done）。
- 修复仅 1 行（`str(user_id)`），对既有 str-id 测试向后兼容（test_stream_invalid_session 404 语义不变）。
- **遗留**：WS transport（ws.py）是否同款比较缺陷未查，建议后端另开 task 排查。

---

## 修订记录

| 日期 | 说明 |
|---|---|
| 2026-07-25 | 00统筹起草（web Epic W7 联调发现）；双闸代签 approved |
| 2026-07-25 | 22 R1 零阻塞签收；30 修复 + 回归测试先红后绿；85 passed；容器实测 SSE 200 |
