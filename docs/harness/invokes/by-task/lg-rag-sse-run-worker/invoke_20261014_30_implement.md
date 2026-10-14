# invoke · 30 · Wave B RunWorker 实现（B1 + 薄 B2）

| 项 | 内容 |
|----|------|
| **时间** | 2026-10-14 |
| **帽** | 30（execute-code） |
| **分支** | `task/lg-rag-sse-run-worker` |
| **task** | `docs/tasks/active/task_lg_rag_sse_run_worker.md` |
| **GATE** | `VERIFY: PASS`（`npx --yes spec-wave@3.3.0 verify --task …`）· HG-TASK-DRAFT/AUDIT-R1/GRAPH-MODULES = approved |

## 人工闸扫描（GATE_VERIFY）

| human_gate_id | task表status | 一致？ | 30可开工？ |
|---------------|--------------|--------|------------|
| HG-TASK-DRAFT | approved | Y | ✅ |
| HG-AUDIT-R1 | approved | Y | ✅ |
| HG-GRAPH-MODULES | approved | Y | ✅ |

## 交付摘要

### B1（必做 · 完成）

1. **`app/ops/lg_rag/run_worker.py`**：进程内 `asyncio.Task` + `run_id` 单飞；持有 astream → emit/persist + fanout；不看 HTTP disconnect。
2. **`app/ops/lg_rag/sse_subscribe.py`**：订阅 fanout；aclose 只 unsubscribe。
3. **`router.py` `/stream`**：先 `start_run_worker` 再 `StreamingResponse(subscribe)`；去掉 `request.receive` 断连钩。
4. **TC-B1 / TC-B4**：`tests/test_lg_rag_sse_run_worker.py` 红测绿。
5. **图谱**：`01_modules.md` 入册 RunWorker；`10_flow_lg_rag.*` 备注；`graph-compile` EXIT=0。
6. **`05` §10.3 / §4.2**：断连尽量跑完以 worker 为准；`error.stage=lg_rag.worker_failed`；补偿可 `disconnected`。

### B2（薄 · 完成）

- worker 异常 → `error{stage:lg_rag.worker_failed}`（TC-B2）。
- 可选 body `continue_from_run_id`：读旧 run partial 拼进 query 草稿（新 `run_id`；禁 HITL resume）。

### A（薄）

- `scan_orphan_runs_for_compensation()` TODO 占位；worker cancel 路径仍可落 `done{disconnected}`。
- **不赌** ASGI disconnect。

## 测试

```text
pytest tests/test_lg_rag_sse_run_worker.py \
  tests/test_lg_rag_sse_disconnect_completion.py \
  tests/test_lg_rag_sse_stream.py \
  tests/test_lg_rag_sse_hitl.py \
  tests/test_lg_rag_sse_token_stream.py \
  tests/test_lg_rag_sse_resume.py \
  tests/test_memory_extract_p1.py
→ 67 passed
ruff check（触及路径）→ All checks passed
./scripts/graph-compile.sh → EXIT=0
```

## 禁区遵守

- **未改** `docs/tasks/active/task_lg_rag_sse_disconnect_completion.md`
- 未 silent 新 `event_type`；未扩多副本队列；未动 `uv.lock` / web
- **未 commit**

## D3 提示（TC-B9）

**请 00/维护者同步开 web task**：部分回复展示 +「继续回复」CTA（api 已供 `terminal_status` / `continue_from_run_id`）。

## 建议下一棒

- **40**：live TC-B6（uvicorn 中途断开 → settle → replay 补后半段）
- TC-B5 补偿扫描实装可另薄棒；TC-B3 可补 HTTP 面断言 continue_from 零 resume
- co-CLOSE：与旧 disconnect task 同批

## 风险

- MVP 单进程 fanout；多副本双 worker 仍 FP-3（另立租约）。
- 断连后默认仍烧满 LLM（FP-4 · F7 env 未做）。
- keepalive 改由 subscriber 发；既有 stream 单测已绿。
