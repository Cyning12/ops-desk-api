# invoke · 10-task · D1 chat_ws 复现

> hat=10 · task=test-baseline-reds · 2026-09-22 · 分支 fix/test-baseline-reds

## 命令与结果

| 命令 | 结果 |
|------|------|
| `pytest tests/test_chat_ws.py -x -q` | 1 failed（test_ws_message_streams_events）|
| `pytest tests/test_chat_ws.py -q` | **2 failed, 4 passed**：`test_ws_message_streams_events` + `test_ws_second_message_while_active_rejected` |

## 实得现象

- 断言 diff：实得事件流 index 2 为 `error`（期望 `thinking`）；完整实得 ≈ `[run.start, thinking, error]`
- teardown 噪音：`RuntimeError: Task ... attached to a different loop` / `Event loop is closed`（pytest_asyncio asyncgen fixture finalizer）
- 直跑 WS 探针（TestClient 直连）拿到 error 载荷：`stage=graph, message="Invalid port: ':1]'"`（conftest 条件）/ `"Please install langchain..."`（裸 .env 条件 · OPS_CHAT_TRACER=langfuse 而 venv 无 langchain 伞包）

## 结论

2 红稳定复现（非 flaky）。错误载荷随环境层变化 → 多根因叠加，转根因定位 invoke。
