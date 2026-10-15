# invoke · 30 · R3 blocking receive disconnect · lg-rag-sse-disconnect-completion

| 项 | 内容 |
|----|------|
| **时间** | 2026-10-14 |
| **帽** | 30（R3 补修 · 非首开） |
| **触发** | 00 裁定 `invoke_20261014_00_r3_dispatch_30.md` · 40-R2 TC5 FAIL（peek 轮询 live 永 False） |
| **分支** | `task/lg-rag-sse-disconnect-completion` |
| **D1/D2** | 仍 A-only · `done{status:'disconnected'}` · **禁 Wave B** |

## GATE_VERIFY（开工）

| human_gate_id | task表status | 一致？ | blocks_30 | 30可开工？ |
|---------------|--------------|--------|-----------|------------|
| HG-TASK-DRAFT | approved | Y | Y | ✅ |
| HG-AUDIT-R1 | approved | Y | Y | ✅ |
| HG-GRAPH-MODULES | approved | Y | — | ✅ |

`npx spec-wave verify --task …` → **VERIFY: PASS**

## 根因（亲读验证）

| 项 | 值 |
|----|-----|
| **仓内版本** | **starlette 0.52.1** · **uvicorn 0.44.0**（非 40 文称 1.3.1） |
| **`Request.is_disconnected`** | 已 cancel 的 `CancelScope` 调 `_receive()` → **只偷看已入队消息，从不阻塞**等 `http.disconnect` |
| **`StreamingResponse` ASGI≥2.4** | 仍不并行 `listen_for_disconnect`；仅 `send`→`OSError`→`ClientDisconnect` |
| **R2 假绿** | 单元 mock `is_disconnected→True` 绿 · live peek 永 False · 无 settle 日志 · 图续写 seq |

## 修法（blocking receive · 非 send-path）

1. 摘掉 `is_disconnected` peek 轮询与 `_DISCONNECT_POLL_S`
2. `iter_lg_rag_sse` / core 增可选 `receive: AsgiReceive`（路由挂 **`request.receive`**，body 已由 FastAPI 读完）
3. 启动独立 Task：**阻塞** `await receive()` 直到 `type==http.disconnect` → `disconnect_event.set()`
4. 主循环 `asyncio.wait` 与 `disconnect_event.wait()` 竞速 → cancel 挂起 anext → `_settle_disconnected` → return（不 yield）
5. `finally` cancel watch Task（**receive 单消费者** · 勿再挂 peek）
6. 保留既有 `GeneratorExit` / `CancelledError` / finally 兜底

## 测试

| 测 | 结果 |
|----|------|
| TC1 aclose | ✅ |
| TC2 DB 沉降 replay | ✅ |
| **新** `test_blocking_receive_disconnect_settles_when_peek_would_miss`（peek 对照永 False · 仅 put `http.disconnect` 沉降 · **不** aclose） | ✅ |
| keepalive | ✅ |
| HITL + chat history 子集 | ✅ 36 passed（含 keepalive） |
| ruff 触及 | ✅ |
| `graph-compile` | EXIT=0 |

## 文档

- §10.3 R3：blocking `request.receive`（弃 peek）
- `01_modules.md` / `10_flow_lg_rag.*` 备注对齐

## 非改

Wave B · web · `uv.lock` · HITL 状态机 · silent 新 event_type · **未 git commit**

## 交棒

→ **00** 再派 **40** 复跑 TC5 live（uvicorn 中途断连 → DB `done{disconnected}` → replay 200；日志键 `ASGI disconnect watch settled`）

## 残留风险

- 依赖 uvicorn 在客户端断后向 `receive` 投递 `http.disconnect`（较 peek 可靠，仍须 40 机证）
- 若未来其它路径再读同一 `request.receive` → 双消费者冲突（当前 stream 独占）
- FP-1 落盘失败仍可能孤儿（补偿扫描未做）
