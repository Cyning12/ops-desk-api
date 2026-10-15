# Invoke：lg-rag-sse-run-worker · 40-verify（TC-B6 live · 2026-10-14）

| 字段 | 值 |
|------|-----|
| **hat_id** | 40（live verify） |
| **task** | `docs/tasks/active/task_lg_rag_sse_run_worker.md` |
| **分支** | `task/lg-rag-sse-run-worker` |
| **前置** | 30 B1+B2 薄 · `invoke_20261014_30_implement.md` · 00 派 `invoke_20261014_00_dispatch_40.md` |
| **对照** | 旧 disconnect TC5 ASGI 钩 live×3 FAIL；本棒按 **B 语义**（断连→worker settle→replay 补后半段）验收 |
| **live 环境** | 干净起 uvicorn `127.0.0.1:8051`（PID 18184 · 杀旧 R3 91210）· 剥离 proxy · `OPS_CHAT_TRACER=off` · 本地 PG · cookie `ops_session` |
| **结论** | **TC-B6 PASS**（主样本 httpx + curl 对照均 settle→replay 200 + 普通 `done`） |

## 人工闸扫描（GATE_VERIFY · 40 亲读 task 表）

| human_gate_id | task表status | 一致？ | blocks_30 |
|---------------|--------------|--------|-----------|
| HG-TASK-DRAFT | approved | Y | — |
| HG-AUDIT-R1 | approved | Y | — |
| HG-GRAPH-MODULES | approved | Y | — |

`npx --yes spec-wave@3.3.0 verify --task docs/tasks/active/task_lg_rag_sse_run_worker.md` → **VERIFY: PASS**

## 工程面（亲跑）

| # | 命令 | 结果 |
|---|------|------|
| 1 | 相关 pytest（run_worker / disconnect / stream / hitl / token / resume / memory / chat_history） | **92 passed** |
| 2 | `spec-wave verify --task …run_worker.md` | **VERIFY: PASS** |
| 3 | 禁区 | **未改** `app/` · **未改**旧 disconnect task · **未 commit** · 无关红测未修 |

## TC-B6 live（B 语义 · 非 ASGI 钩）

| # | 观测项 | verdict | 证据 |
|---|--------|---------|------|
| 1 | 真实 uvicorn + 中途断开（supervisor mid-stream） | ✅ | httpx break @seq3 · curl `--max-time 8` |
| 2 | 断连后 worker 继续（subscriber cancel · worker untouched） | ✅ | uvicorn：`subscriber cancelled … (worker untouched)` |
| 3 | settle 后 `POST /lg-rag/replay` **200** 含后半段 + 普通 `done` | ✅ | live_max=3 → replay_max=**445** · `done` 无 `status:disconnected` |
| 4 | 失败路径 `error{stage:lg_rag.worker_failed}` | n/a（本跑成功） | — |
| 5 | 断连前真在飞 **409 + Retry-After: 2**（TC-B4） | ✅ | `tc_b6_inflight_409.*` |
| 6 | 可选 `continue_from_run_id` 新 run | ✅ 冒烟 | 新 `run_id=2cc766d2…` · 同 `thread_id` · HTTP 200 · query 注入 `[继续回复·既…` |

**主样本 run_id**：`71d3cdfb85ae478eb75e0fa56c835300`（httpx · settle ~110s · latency_ms=111464）  
**对照样本**：`69f3723f985d4b8d829064b00a2c3fbe`（curl · 初轮 150s 窗仍 409 · late probe worker closed→200 · 更长 LLM）

### 与旧 TC5 对照

| 维度 | 旧 TC5（ASGI） | 本 TC-B6（RunWorker） |
|------|----------------|------------------------|
| 验收轴 | 同连接内 `http.disconnect` → `done{disconnected}` | HTTP 只取消 subscriber；worker 写到普通 `done` |
| live×3 | FAIL（永久 409） | **PASS**（settle 后 200 + 后半段） |

## TC-B4 保护区 live 抽检

| 观测项 | verdict | 证据 |
|--------|---------|------|
| 断连前 `POST /lg-rag/replay` → **409 + Retry-After: 2** · body `Run is still in flight…` | ✅ | `tc_b6_inflight_409.hdr` / `.body` |
| 断连后即时仍 409（worker 未 settle） | ✅ | `tc_b6_postclose_immediate.*` |

## 附件清单（`attachments/` · `tc_b6_*`）

| 文件 | 说明 |
|------|------|
| `tc_b6_disconnect_stream.hdr` / `tc_b6_disconnect_live_partial.sse` | httpx live 头 + 断连前帧（seq≤3） |
| `tc_b6_inflight_409.hdr` / `.body` | TC-B4 409+Retry-After |
| `tc_b6_postclose_immediate.hdr` / `.body` | 断连后即时仍 409 |
| `tc_b6_disconnect_replay.hdr` / `.sse` / `.body` | settle 后 replay 200（445 帧 · 普通 done） |
| `tc_b6_disconnect_summary.json` / `tc_b6_disconnect_meta.txt` | 主样本 PASS 快照 |
| `tc_b6_curl_disconnect_*` | curl max-time 对照（late settle PASS） |

## 阻塞 / 下一棒

- **无阻塞 TC-B6**。
- 仍 open（非本棒）：TC-B3 HTTP 面断言可补强 · TC-B5 补偿扫描实装 · TC-B10 与旧 disconnect task **co-CLOSE** · D3 web task 仍待另开。
- 建议 00：可签收 TC-B6 / 准备 co-CLOSE；**未 commit**。

## 修订

| 日期 | 说明 |
|------|------|
| 2026-10-14 | 40：TC-B6 live PASS · 409 抽检 PASS · pytest 92 · verify PASS · 证据 `tc_b6_*` |
