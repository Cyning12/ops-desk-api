# invoke · 30 · R2 ASGI 断连钩补修 · lg-rag-sse-disconnect-completion

| 项 | 内容 |
|----|------|
| **时间** | 2026-10-14 |
| **帽** | 30（R2 补修 · 非首开） |
| **触发** | 00 裁定 `invoke_20261014_00_r2_dispatch_30.md` · 40 TC5 FAIL（live 未触达 settle） |
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

Starlette `StreamingResponse.__call__`：ASGI `spec_version >= (2,4)` 时**不**并行 `listen_for_disconnect`，仅 `stream_response` + `send` 抛 `OSError`→`ClientDisconnect`。主循环卡在长 `__anext__`、keepalive `send` 未失败时，生成器**永不** `aclose` → R1 的 `GeneratorExit`/`CancelledError` 沉降死角。单元 `agen.aclose()` 绿 ≠ live。

## 修法

1. `iter_lg_rag_sse` / `_iter_lg_rag_sse_core` 增可选 `is_disconnected: Callable[[], Awaitable[bool]]`
2. 等待 anext 期间按 `_DISCONNECT_POLL_S`（默认 1s）与 keepalive 独立轮询探针；True → cancel 挂起 anext → `_settle_disconnected` → return（**不** yield）
3. `router.stream_lg_rag` 挂 `is_disconnected=request.is_disconnected`
4. 保留既有 `GeneratorExit` / `CancelledError` / finally 兜底路径

## 测试

| 测 | 结果 |
|----|------|
| TC1 aclose | ✅ |
| TC2 DB 沉降 replay | ✅ |
| **新** `test_asgi_disconnect_probe_settles_without_aclose`（卡 anext · **不** aclose · 探针沉降） | ✅ |
| keepalive 回归 | ✅ |
| HITL + resume 子集 | ✅ 26+ 面含入 28 passed |
| `test_chat_history_api` | ✅ 25 passed |
| ruff 触及 | ✅ |

## 文档

- §10.3 补 ASGI≥2.4 探针句
- `01_modules.md` / `10_flow_lg_rag.*` 备注补 `is_disconnected` 轮询

## 非改

Wave B · web · `uv.lock` · HITL 状态机 · silent 新 event_type · **未 git commit**

## 交棒

→ **00** 再派 **40** 复跑 TC5 live（uvicorn 中途断连 → DB `done{disconnected}` → replay 200）

## 残留风险

- 探针依赖 ASGI server 及时投递 `http.disconnect`；极端代理缓冲仍可能延迟至约 `_DISCONNECT_POLL_S`
- FP-1 落盘失败仍可能孤儿（补偿扫描未做）
- TC5 live 仍须 40 机证
