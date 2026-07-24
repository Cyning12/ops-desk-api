# Invoke：30 执行编码 · chat-websocket-v1（补录）

> **补录说明**：本文件为 2026-07-20 流程补录。执行时未按纪律落盘 invoke，现按 `TEMPLATE_invoke.md` 补齐，交付摘要为当时实际结果。

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 30（含 40 自检闭环） |
| task_slug | `chat-websocket` |
| freeze_id | — |
| task_paths | `docs/tasks/done/task_chat_websocket_v1_2026-07-18.md` |
| related_review_or_none | 无 |
| git_branch | `task/chat-websocket-v1` |
| worktree_root | — |
| created_utc_or_local | 2026-07-18（执行日） |
| notes | PR 待合并；用户批准：WS 暂不鉴权（首个 maintainer 作演示用户） |

---

## 可复制 Prompt 快照

```text
## 30 开工（签闸后 · 须 GATE_VERIFY）

@docs/tasks/active/task_chat_websocket_v1.md
@docs/harness/prompts/30-execute-code.md
@docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md
@docs/_tech_graph/01_struct.md

【开工前】
1. 首输出 FRAGMENT_30_gate_verify 闸扫描表（读 task 人工闸表，比对用户声称）
2. 仅当 HG-AUDIT-R1=approved（task 表）→ 可改码

【实现】
- 分支：task/chat-websocket-v1（基于 task/admin-github-sync）· 仅 task 所列路径
- 范围：chat/streaming.py 共享层抽取、WS /api/ops/chat/ws、
  演示用户解析、message/cancel 协议、单连接串行保护、测试、文档
- test_strategy: required → 先红后绿

【Verify】
- pytest tests · ruff check app tests · ./scripts/graph-compile.sh
```

---

## 交付摘要（本帽结束时填）

- **验证命令**：`pytest tests`（71 passed）· `ruff check app tests`（绿）· `./scripts/graph-compile.sh`（绿）· 冒烟（连接 → 提问 → 取消 `run.cancelled` ts_ms=1ms · DB status=cancelled → 同连接再提问 → `done`，通过）
- **变更路径**：`app/ops/chat/{streaming,ws,router,sse}.py`、`app/ops/router.py`、`tests/test_chat_ws.py`、`tests/test_chat_router.py`、`docs/ios/api-auth-chat.md`、`docs/_tech_graph/10_flow_chat.*`、`docs/_tech_graph/01_struct.md`
- **下一棒**：CLOSE（task 归档 `docs/tasks/done/task_chat_websocket_v1_2026-07-18.md`）
- **关键实现记录**：竞态取消（graph `__anext__` vs cancel Event）中断生成中节点；串行保护 1s 宽限用 `asyncio.wait`（`wait_for` 超时会 cancel pump 任务导致客户端挂起）；shielded cleanup 保持久化抗取消。

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-07-20 | 流程补录：执行时未落盘 invoke，按模板补齐 |
