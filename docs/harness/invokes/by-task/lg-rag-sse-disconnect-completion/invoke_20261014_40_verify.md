# Invoke：lg-rag-sse-disconnect-completion · 40-verify（2026-10-14）

| 字段 | 值 |
|------|-----|
| **hat_id** | 40-verify |
| **task** | `docs/tasks/active/task_lg_rag_sse_disconnect_completion.md` |
| **分支** | `task/lg-rag-sse-disconnect-completion` |
| **核验范围** | TC5 live（真实 uvicorn + 中途断开 → 收尾 → replay 200）+ TC3 保护区 live 抽检（真在飞 409）+ 工程面复核（disconnect/resume/hitl pytest 子集 + verify） |
| **live 环境** | 本机 uvicorn `127.0.0.1:8051`（8050 占用）· 剥离 proxy · `OPS_CHAT_TRACER=off` · 本地 PG · cookie 登录 admin/maintainer（`scripts/create_initial_user.py`） |
| **结论** | **TC5 FAIL / BLOCKED→00**（单元 aclose 绿 · live ASGI 断连未沉降） |

## GATE / 工程面（40 亲跑）

| # | 命令 | 结果 |
|---|------|------|
| 1 | `npx --yes spec-wave@3.3.0 verify --task docs/tasks/active/task_lg_rag_sse_disconnect_completion.md` | **VERIFY: PASS** |
| 2 | `uv run pytest tests/test_lg_rag_sse_disconnect_completion.py tests/test_chat_history_api.py -q` | **27 passed** |
| 3 | `uv run pytest tests/test_lg_rag_sse_resume.py tests/test_lg_rag_sse_hitl.py tests/test_lg_rag_sse_disconnect_completion.py -q` | **26 passed** |
| 4 | 码面抽检 | `_settle_disconnected` / `GeneratorExit` / `CancelledError` 在 `sse_stream.py` 存在（30 交付在册） |

## TC5 live 对照

| # | 观测项 | verdict | 证据 |
|---|--------|---------|------|
| 1 | 真实 uvicorn + 客户端中途断开 | ✅ 复现 | supervisor 长跑 · kill curl 于 `run.start` 后（`tc5_disconnect_live_partial.sse`） |
| 2 | DB 收尾帧 `done{status:'disconnected'}` | ❌ | `event_store` 快照仅 `seq1 run.start` · **无 done**（`tc5_disconnect_summary.json`） |
| 3 | `run_stream_closed` 真 | ❌ | **false**（同 summary） |
| 4 | 断连后 `POST /lg-rag/replay` 200 含收尾 | ❌ | 断连后轮询 **120s 仍 409**；终态复打仍 409（`tc5_disconnect_replay.hdr` / `.body`） |
| 5 | 对照修复前联调（web `jc_tc4_network.json` reload→409） | ⚠ 未消解 | live 断连后形态仍等同孤儿永久 409 |

**主样本 run_id**：`5c5b4cf0187b4184a9c4be7307a4eab5`（thread `63d1842e9f864780888e7094f3fceda2`）

### 另试路径（均未拿到 disconnected 收尾）

| 方法 | 结果 |
|------|------|
| `mode=basic` + 空证据 | ~1.5s 正常 `done`（无 status）· 无法构成 mid-stream 断连窗（`tc5_curl_disconnect_*`） |
| httpx `stream` 早关 | race：persist 前关连 → 瞬时 500/`connection is closed` → 随后 404 |
| raw socket + SO_LINGER RST | 同 race → 404；未见 settle 日志（`tc5_sock_disconnect_*`） |

## TC3 保护区 live 抽检

| 观测项 | verdict | 证据 |
|--------|---------|------|
| 真在飞窗口 `POST /lg-rag/replay` → **409 + Retry-After: 2** | ✅ | 同 run `5c5b4cf0…` 断连前打点（`tc5_inflight_409.hdr` / `.body`）· body=`Run is still in flight; retry after it settles.` |

## 根因假设（报 00 · 禁 40 擅自扩 Wave B）

1. **单元 vs live 钩差**：TC1/TC2 对 `agen.aclose()` 直调 → `GeneratorExit` → `_settle_disconnected` **绿**；live 依赖 Starlette `StreamingResponse` 在客户端断开后取消/aclose 生成器。
2. **Starlette 1.3.1 / ASGI≥2.4**：`listen_for_disconnect` **不再并行监听**；仅当后续 `send` 抛 `OSError` 才走 `ClientDisconnect`。若生成器卡在长时间 `__anext__`（LLM/图）且 keepalive `send` 未失败，则 **永不进入** `_settle_disconnected`。
3. 本样本：断连后仅见 embedding 日志 · **无** `disconnect settle failed` · 120s+ 仍 `run_stream_closed=false` → 与「未 aclose / 未触达 settle」一致。
4. **非范围守界**：未改 Wave B / web / HITL / `uv.lock`；未 git commit。

## 附件清单（`attachments/`）

| 文件 | 说明 |
|------|------|
| `tc5_disconnect_stream.hdr` | live stream 响应头（含 run_id） |
| `tc5_disconnect_live_partial.sse` | 断连前客户端已收帧（仅 run.start） |
| `tc5_inflight_409.hdr` / `.body` | 真在飞 409+Retry-After |
| `tc5_disconnect_replay.hdr` / `.body` | 断连后终态仍 409 |
| `tc5_disconnect_summary.json` / `tc5_disconnect_meta.txt` | run 快照 + FAIL 结论 |
| `tc5_curl_disconnect_*` | basic 过快完成对照（正常 done 无 status） |
| `tc5_sock_disconnect_*` / `tc5_postclose_immediate.*` | 早关 race 对照 |

## 结论

**TC5 FAIL · BLOCKED 报 00**：Wave A 单测沉降路径成立，但 **真实 uvicorn 客户端中途断开未落到 `done{status:'disconnected'}`**，replay 仍永久 409（与修复前联调 TC4 / F-OBS-2 孤儿面同构）。建议 00 裁定：是否派 30 补 ASGI 断连钩（如 `request.is_disconnected` 竞态 / 缩短 keepalive 探测 / 显式 cancel）——**仍属 Wave A 收尾可达性**，勿静默扩 Wave B worker。

TC3 保护区 live 抽检 **PASS**（409+Retry-After 仍在）。pytest 子集与 verify **PASS**。未 commit / push。

## 修订

| 日期 | 说明 |
|------|------|
| 2026-10-14 | 40 落稿：TC5 live FAIL 证据齐 · 409 保护区 PASS · verify/pytest 子集绿 · BLOCKED→00 |
