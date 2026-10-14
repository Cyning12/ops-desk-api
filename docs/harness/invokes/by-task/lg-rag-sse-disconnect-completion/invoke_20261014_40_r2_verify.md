# Invoke：lg-rag-sse-disconnect-completion · 40-verify R2（2026-10-14）

| 字段 | 值 |
|------|-----|
| **hat_id** | 40-verify（R2 复跑 TC5） |
| **task** | `docs/tasks/active/task_lg_rag_sse_disconnect_completion.md` |
| **分支** | `task/lg-rag-sse-disconnect-completion` |
| **前置** | 30-R2 ASGI `is_disconnected` 轮询 · `invoke_20261014_30_r2_asgi_disconnect.md` · 00 派单 `invoke_20261014_00_dispatch_40_r2.md` |
| **对照 FAIL** | 40 R1 · run `5c5b4cf0…` · `invoke_20261014_40_verify.md` |
| **live 环境** | 干净起 uvicorn `127.0.0.1:8051`（PID 87188 · 非旧进程）· 剥离 proxy · `OPS_CHAT_TRACER=off` · 本地 PG · cookie `ops_session` |
| **结论** | **TC5 FAIL / BLOCKED→00**（码面探针在册 · 单元 mock 绿 · live `request.is_disconnected` 未沉降） |

## GATE / 工程面（40-R2 亲跑）

| # | 命令 | 结果 |
|---|------|------|
| 1 | 码面亲读 `sse_stream.py` / `router.py` | ✅ `router` 挂 `is_disconnected=request.is_disconnected`；主循环 `_DISCONNECT_POLL_S=1.0` 轮询 → `_settle_disconnected` |
| 2 | `npx --yes spec-wave@3.3.0 verify --task docs/tasks/active/task_lg_rag_sse_disconnect_completion.md` | **VERIFY: PASS** |
| 3 | `uv run pytest tests/test_lg_rag_sse_disconnect_completion.py tests/test_chat_history_api.py tests/test_lg_rag_sse_resume.py tests/test_lg_rag_sse_hitl.py -q` | **52 passed** |

## TC5 live 对照（R2）

| # | 观测项 | verdict | 证据 |
|---|--------|---------|------|
| 1 | 真实 uvicorn + 中途断开（supervisor 长跑 · mid-stream 窗） | ✅ 复现 | httpx break · curl `--max-time 8` |
| 2 | DB `done{status:'disconnected'}` | ❌ | 两 run 均无 done |
| 3 | `run_stream_closed` 真 | ❌ | false |
| 4 | 断连后 replay 200 | ❌ | 30s / 20s 轮询仍 **409**；late 复打仍 409 |
| 5 | uvicorn settle 日志 | ❌ | uvicorn **无** `ASGI disconnect probe settled` |

**主样本 run_id**：`f6a9cdd567ae41cc91c8ce3938712083`（httpx mid-stream kill · thread `2048d3b3…`）  
**对照样本**：`b16d704c9895435db7c69e88a9bdc380`（curl `--max-time 8` · 同 FAIL）

### 路径对照

| 方法 | 结果 |
|------|------|
| httpx `stream` 收齐 mid-stream 帧后 break | 30s+ 409 · DB 续写 progress/step · **无** disconnected |
| curl `--max-time 8` supervisor | 20s 409 · 仅至 `subtask.progress running` · **无** disconnected |
| 单元 `test_asgi_disconnect_probe_settles_without_aclose` | **GREEN**（mock probe→True） |

## TC3 保护区 live 抽检

| 观测项 | verdict | 证据 |
|--------|---------|------|
| 同窗断连前 `POST /lg-rag/replay` → **409 + Retry-After: 2** | ✅ | run `f6a9cdd5…` · `tc5_r2_inflight_409.hdr` / `.body` |

## 根因假设（报 00 · 禁 40 改码 / 禁 Wave B）

1. **码面接线成立**：`router`→`request.is_disconnected`；轮询与 `_settle_disconnected` 存在；单测 mock 探针绿。
2. **live 探针未翻转**：断连后图仍 persist（主样本续写 seq7–8）· **无** settle 日志 → `await is_disconnected()` 持续 False，未进沉降。
3. **Starlette 1.3.1** `Request.is_disconnected` 用 cancelled `CancelScope` 非阻塞 `_receive()`；若 uvicorn 未把 `http.disconnect` 提前入队，轮询读不到断连（与 30-R2 假设「轮询即可」在 live 上未兑现）。
4. **非范围守界**：未改 `app/` / Wave B / web · 未 commit。

## 附件清单（`attachments/` · `tc5_r2_*` 前缀 · 不覆盖 R1）

| 文件 | 说明 |
|------|------|
| `tc5_r2_disconnect_stream.hdr` / `tc5_r2_disconnect_live_partial.sse` | httpx live 头 + 断连前帧 |
| `tc5_r2_inflight_409.hdr` / `.body` | TC3 409+Retry-After |
| `tc5_r2_disconnect_replay.hdr` / `.body` | 断连后仍 409 |
| `tc5_r2_disconnect_summary.json` / `tc5_r2_disconnect_meta.txt` | 主样本 FAIL 快照 |
| `tc5_r2_curl_disconnect_*` | curl max-time 对照 FAIL |

## 结论

**TC5 FAIL · BLOCKED→00**：30-R2 探针码面与单元绿，但 **真实 uvicorn 客户端中途断开仍不落 `done{disconnected}`**，replay 永久 409（与 R1 / 联调 TC4 孤儿面同构）。建议 00 裁定是否再派 30：换更可靠的 ASGI 断连侦测（或确认 uvicorn receive 语义）——**仍属 Wave A 收尾可达性**，勿静默扩 Wave B。

TC3 live 抽检 **PASS**。pytest 子集 / verify **PASS**。未 commit / push。

## 修订

| 日期 | 说明 |
|------|------|
| 2026-10-14 | 40-R2：TC5 live 仍 FAIL · 409 保护区 PASS · 证据 `tc5_r2_*` · BLOCKED→00 |
