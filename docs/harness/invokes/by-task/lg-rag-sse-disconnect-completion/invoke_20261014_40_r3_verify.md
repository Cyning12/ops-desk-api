# Invoke：lg-rag-sse-disconnect-completion · 40-verify R3（2026-10-14）

| 字段 | 值 |
|------|-----|
| **hat_id** | 40-verify（R3 复跑 TC5 · blocking receive） |
| **task** | `docs/tasks/active/task_lg_rag_sse_disconnect_completion.md` |
| **分支** | `task/lg-rag-sse-disconnect-completion` |
| **前置** | 30-R3 blocking `request.receive` · `invoke_20261014_30_r3_blocking_disconnect.md` |
| **对照 FAIL** | R1 `invoke_20261014_40_verify.md` · R2 `invoke_20261014_40_r2_verify.md`（peek 未翻转） |
| **live 环境** | 干净起 uvicorn `127.0.0.1:8051`（PID 91210 · 杀旧 87188）· 剥离 proxy · `OPS_CHAT_TRACER=off` · 本地 PG · cookie `ops_session` |
| **结论** | **TC5 FAIL / BLOCKED→00 · 停派升级维护者**（码面 blocking watch 在册 · 单元绿 · live 仍无 `http.disconnect` 沉降） |

## GATE / 工程面（40-R3 亲跑）

| # | 命令 | 结果 |
|---|------|------|
| 1 | 码面亲读 `sse_stream.py` / `router.py` | ✅ `router` 挂 `receive=request.receive`；`_watch_http_disconnect` 阻塞等 `http.disconnect`；**无** `_DISCONNECT_POLL_S` / peek 主路径；日志键 `ASGI disconnect watch settled` |
| 2 | `npx --yes spec-wave@3.3.0 verify --task docs/tasks/active/task_lg_rag_sse_disconnect_completion.md` | **VERIFY: PASS** |
| 3 | `uv run pytest tests/test_lg_rag_sse_disconnect_completion.py tests/test_chat_history_api.py tests/test_lg_rag_sse_resume.py tests/test_lg_rag_sse_hitl.py -q` | **52 passed** |

## TC5 live 对照（R3）

| # | 观测项 | verdict | 证据 |
|---|--------|---------|------|
| 1 | 真实 uvicorn + 中途断开（supervisor 长跑 · mid-stream 窗） | ✅ 复现 | httpx break · curl `--max-time 8` |
| 2 | DB `done{status:'disconnected'}` | ❌ | 两 run 均无 done（止于 `subtask.progress running` seq6） |
| 3 | `run_stream_closed` 真 | ❌ | false |
| 4 | 断连后 replay 200 | ❌ | httpx 48s / curl 20s+ late 仍 **409** |
| 5 | uvicorn settle 日志 | ❌ | uvicorn **无** `ASGI disconnect watch settled`（全日志无 disconnect/settle） |

**主样本 run_id**：`426b0a70e37d452aaeb649c2e091e79d`（httpx mid-stream kill · thread `ba67aea1…`）  
**对照样本**：`eea35bd94a274067a4e66e3712ff254a`（curl `--max-time 8` · 同 FAIL）

### 路径对照

| 方法 | 结果 |
|------|------|
| httpx `stream` 收齐 mid-stream 帧后 break | 48s+ 409 · DB 6 帧 · **无** disconnected · **无** settle 日志 |
| curl `--max-time 8` supervisor | 20s+ 409 · 同构 · **无** disconnected |
| 单元 `test_blocking_receive_disconnect_settles_when_peek_would_miss` | **GREEN**（mock put `http.disconnect`） |

## TC3 保护区 live 抽检

| 观测项 | verdict | 证据 |
|--------|---------|------|
| 同窗断连前 `POST /lg-rag/replay` → **409 + Retry-After: 2** | ✅ | run `426b0a70…` · `tc5_r3_inflight_409.hdr` / `.body` |

## 根因假设（报 00 · 禁 40 改码 / 禁 Wave B · **停派**）

1. **码面接线成立**：`router`→`request.receive`；blocking watch Task + `disconnect_event` 竞速 + `_settle_disconnected` 存在；app 无 `_DISCONNECT_POLL_S`。
2. **live 仍不沉降**：客户端 TCP 已断（无 ESTABLISHED）后 20–48s+，uvicorn **未**打 settle 日志 → `await receive()` **未**收到 `http.disconnect`（或未唤醒 watch）。
3. **与 R1/R2 同构产品面**：孤儿 in-flight · replay 永久 409 · 图可继续烧 LLM；与 peek 假绿不同机理，**同一验收缺口**。
4. **00 纪律**：本轮再 FAIL → **如实 BLOCKED · 停派升级维护者**（禁再派 30 同套路微调）。
5. **非范围守界**：未改 `app/` / Wave B / web · 未 commit。

## 附件清单（`attachments/` · `tc5_r3_*` 前缀 · 不覆盖 R1/R2）

| 文件 | 说明 |
|------|------|
| `tc5_r3_disconnect_stream.hdr` / `tc5_r3_disconnect_live_partial.sse` | httpx live 头 + 断连前帧 |
| `tc5_r3_inflight_409.hdr` / `.body` | TC3 409+Retry-After |
| `tc5_r3_disconnect_replay.hdr` / `.body` | 断连后仍 409 |
| `tc5_r3_postclose_immediate.hdr` / `.body` | 断连后即时 replay 仍 409 |
| `tc5_r3_disconnect_summary.json` / `tc5_r3_disconnect_meta.txt` | 主样本 FAIL 快照 |
| `tc5_r3_curl_disconnect_*` | curl max-time 对照 FAIL |

## 结论

**TC5 FAIL · BLOCKED→00 · 停派升级维护者**：30-R3 blocking receive 码面与单元绿，但 **真实 uvicorn 客户端中途断开仍不落 `done{disconnected}`**，replay 永久 409；uvicorn 无 `ASGI disconnect watch settled`。按 00 R3 纪律：**禁止再派 30 同面微调**；须维护者裁定下一路径（例如 send 失败路径强制 aclose、ASGI 层其它钩、或 Wave B 解耦）。

TC3 live 抽检 **PASS**。pytest 子集 / verify **PASS**。未 commit / push。

## 修订

| 日期 | 说明 |
|------|------|
| 2026-10-14 | 40-R3：TC5 live 仍 FAIL · blocking receive 未 live 沉降 · 409 保护区 PASS · **停派升级** · 证据 `tc5_r3_*` |
