# Invoke：lg-rag-sse-disconnect-completion · 30-implement（2026-10-14）

| 字段 | 值 |
|------|-----|
| **hat_id** | 30-implement |
| **task** | `docs/tasks/active/task_lg_rag_sse_disconnect_completion.md` |
| **分支** | `task/lg-rag-sse-disconnect-completion` |
| **波次** | **D1=A-only**（禁 Wave B）· **D2=`done{status:'disconnected'}`** · **D3=api-only** |
| **commit** | 未提交（维护者另令） |

## GATE_VERIFY（开工前）

| human_gate_id | task表status | blocks_30 | 30可开工？ |
|---------------|--------------|-----------|------------|
| HG-TASK-DRAFT | approved | Y | Y |
| HG-AUDIT-R1 | approved | Y | Y |
| HG-GRAPH-MODULES | approved | Y | Y |

- `npx --yes spec-wave@3.3.0 verify --target . --task docs/tasks/active/task_lg_rag_sse_disconnect_completion.md` → **VERIFY: PASS**
- reviews：`task_lg_rag_sse_disconnect_completion_audit_R1_20261013.md` 存在（PASS-WITH-NITS）
- pre-30 invoke：10 / 20 / 00_gate_signoff / 00_dispatch_30 齐套
- **结论：可开工**

## 实现摘要

- `sse_stream._iter_lg_rag_sse_core`：`stream_settled` + `_settle_disconnected()`；`GeneratorExit` / `asyncio.CancelledError` → 落盘 `done{status:'disconnected'}`（**不 yield**）+ drain persist；done/error/waiting_approval 路径标 settled；finally 兜底 + ContextVar reset suppress。
- `event_store` / `router`：**零 diff**（任意 `done` 已使 `run_stream_closed` 真）。
- `history.run_terminal_status`：既有透传 status 字符串 → TC 钉 `disconnected` 变体。
- 文档：`05` §10.3 实然回写；`01_modules.md` + `10_flow_lg_rag.*`；`graph-compile` EXIT=0。
- **FP-1 补偿扫描：本棒未薄做**（仅 settle 失败打 exception 日志）。

## 红→绿

| 阶段 | 结果 |
|------|------|
| RED（仅测、改码前） | `test_tc1_…` AssertionError：`done_list` 空（「断连后无 done 收尾帧」） |
| GREEN | TC1+TC2 绿；保护区 27 项 + 相关面 73 passed |

## 验收命令

| # | 命令 | exit | 结果 |
|---|------|------|------|
| 1 | `uv run ruff check app/ops/lg_rag/sse_stream.py tests/test_lg_rag_sse_disconnect_completion.py tests/test_chat_history_api.py` | 0 | All checks passed |
| 2 | `uv run pytest`（disconnect + resume + hitl + history variants） | 0 | **27 passed** |
| 3 | `uv run pytest`（上列 + sse_stream + token_stream + chat_history_api 全文件） | 0 | **73 passed** |
| 4 | `./scripts/graph-compile.sh` | 0 | EXIT=0 |
| 5 | 全量 `uv run pytest tests/ -q` | 1 | **1803 passed, 1 skipped, 7 failed**（capability_lookups×3 / hitl db_store / lg_rag_multi unknown_tool / multi_replica×2 · 与本改无关环境性既有红形态；本 task 新测未入失败列表） |

## 40 自检（轻）

- TC5 live 断连对照：**待 40**（真实 uvicorn + 客户端中途断开 → DB 收尾 → replay 200）。
- 保护区：真在飞 409 / waiting_approval / completed 既有测全绿。
- 未做：Wave B · web 假续看文案 · 历史孤儿补偿扫描。

## 改动文件

| 文件 | 说明 |
|------|------|
| `app/ops/lg_rag/sse_stream.py` | 断连沉降 |
| `tests/test_lg_rag_sse_disconnect_completion.py` | TC1/TC2 新测 |
| `tests/test_chat_history_api.py` | `disconnected` terminal 变体 |
| `docs/spec/agent-infra/05_lg_rag_transport_and_session_plan_v0.md` | §10.3 |
| `docs/_tech_graph/l1/01_modules.md` | 备注 + 闸表行 |
| `docs/_tech_graph/l1/10_flow_lg_rag.graph.yaml` / `.md` | description（compile 再生） |
| `docs/tasks/active/task_lg_rag_sse_disconnect_completion.md` | 自检回填 |
| 本 invoke | 过程留痕 |

## 非范围照登

Wave B worker · replay≡resume · HITL 状态机 · ops-desk-web · `uv.lock` · silent 新 event_type · 历史孤儿补偿扫描。
