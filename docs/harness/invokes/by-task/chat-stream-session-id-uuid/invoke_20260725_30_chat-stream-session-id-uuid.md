# Harness invoke 快照：chat-stream-session-id-uuid

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 10 / 22 / 30 / 40（00 统筹同会话顺次执行） |
| task_slug | `chat-stream-session-id-uuid` |
| task_paths | `docs/tasks/active/task_chat_stream_session_id_uuid.md` |
| related_review_or_none | `docs/harness/reviews/task_chat_stream_session_id_uuid_audit_R1_20260725.md` |
| git_branch | `fix/chat-stream-session-id` |
| created_utc_or_local | 2026-07-25 |
| notes | ops-desk-web Epic W7 联调发现的阻断缺陷；人闸 00 代签 |

---

## 可复制 Prompt 快照

```text
30 执行：修复 streaming.py resolve_chat_session 中 str(chat_session.user_id) != user_id
（user_id 为 UUID 对象恒不等 → 带 session_id 恒 404）。先写回归测试（真实 DB UUID-id
用户 + 既有 session → 200，修复前应红），再改 str(user_id)，pytest 全绿后重建容器实测。
```

---

## 交付摘要

- **验证命令**：回归测试修复前 `assert 404 == 200` FAIL → 修复后 PASS；`pytest tests` 85 passed；`ruff check` 通过；`harness verify` PASS
- **容器实测**：`docker compose up -d --build api` 后 latest → stream(带 session_id) → SSE 序列完整（run.start → thinking×2 → answer → done）
- **变更路径**：`app/ops/chat/streaming.py`（1 行）、`tests/test_chat_router.py`（+test_stream_existing_session_ok）
- **下一棒**：交还 00 → CLOSE（ops-desk-web W7 联调解锁）

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-07-25 | 10/22/30/40 同会话完成，落盘 invoke |
