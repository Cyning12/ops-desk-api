# Task：lg-rag SSE · subtask 中途可见（running 起步帧）

> **状态**：active（2026-09-07 · 维护者令「开启此任务 · subagent 执行 · 00 统筹」）  
> **类型**：传输 / 子任务过程时效  
> **上游**：[`05_lg_rag_transport_and_session_plan_v0.md`](../../spec/agent-infra/05_lg_rag_transport_and_session_plan_v0.md) **§10.7**  
> **前置**：idle-keepalive CLOSE · [#123](https://github.com/Cyning12/ops-desk-api/pull/123) / CLOSE [#124](https://github.com/Cyning12/ops-desk-api/pull/124)；web idle [#36](https://github.com/Cyning12/ops-desk-web/pull/36)  
> **分支**：`task/lg-rag-sse-subtask-live`  
> **帽子**：00 起草；**10**；**20**；**30+40**（可由 subagent 执行，00 统筹验收）  
> **无关**：子图 retrieve/grade 逐步帧 · 子任务内 token · 新 event_type · 改 idle/keepalive 数值

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `lg-rag-sse-subtask-live` |
| **git_branch** | `task/lg-rag-sse-subtask-live` |
| **implement_repo** | `ops-desk-api`（web 另 task `web-lg-rag-sse-subtask-live`） |
| **test_strategy** | `required` |
| **test_strategy_note** | mock 慢 rag_subtask：节点返回前已 yield `subtask.progress`+`status=running`；完成帧含 done；T5/keepalive 旧测不回归；不连真 LLM |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1` |
| **graph_delta** | `docs/_tech_graph/l1/01_modules.md` · `10_flow_lg_rag` 备注 |
| **graph_delta_note** | 不新增一级模块；若新增 `progress_stream.py` 符号则 G-L2 indexes 同步 |
| **wiki_delta** | `docs/coding_wiki/volatile.md` |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,00,30` |
| **invoke_retention_profile** | `default` |
| **freeze_id** | `lg-rag-sse-v1`（不新 freeze；不新 event_type；payload 增 `status`） |
| **close_pr_policy** | `required` |
| **related_pr** | （待开） |
| **kpi_aggregator** | `CLOSE` |
| **orchestration** | api-first；web 并行可消费 running 帧 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | 2026-09-07 · **00 代签 · 维护者令开启** |
| HG-AUDIT-R1 | **approved** | 30 | 2026-09-07 · **00 代签 · 维护者令开启 · subagent 执行** |
| HG-GRAPH-MODULES | approved | — | 不新增一级模块 · **00 代签** |

---

## 00 定夺

| 项 | 钉死 |
|---|---|
| **slug** | `lg-rag-sse-subtask-live` |
| **机制** | contextvar progress sink（镜像 `answer_stream`）；`rag_subtask`/`info_extract`/`tool_exec` **入口** `await emit_running(...)` |
| **帧** | `event_type=subtask.progress` · running：`status/subtask_id/type` · done：既有摘要 + `status=done` |
| **sse_stream** | 与 delta 同样竞速 `pending_frames`；running **落盘**占 seq |
| **非本波** | 子图逐步帧 · token · 新 event_type |

---

## 范围

1. 新模块（建议）`app/ops/lg_rag/progress_stream.py`：sink set/reset + `emit_subtask_running`  
2. `multi/nodes.py`：三子任务节点入口调 running  
3. `sse_stream.py`：挂 sink + 竞速 yield；`map_node_update` 完成帧补 `status=done`  
4. 单测 + 05 §10.7（已落盘）+ G-L1 备注 + volatile  

## 验收标准

- [ ] 慢 mock 子任务：`running` 帧在节点 `__anext__` 返回前可见  
- [ ] 完成帧仍为 `subtask.progress` 且含摘要；推荐 `status=done`  
- [ ] keepalive / T5 delta 测不回归  
- [ ] ruff · pytest · graph-compile（若动 yaml）  

## failure_paths

| 触发 | 行为 | 可重试 |
|---|---|---|
| 无 sink（invoke） | running 调为空操作 | — |
| sink 异常 | 打日志，不中断节点 | 是 |

## 修订记录

| 日期 | 说明 |
|---|---|
| 2026-09-07 | **00**：维护者令开启；钉 MVP=running 起步帧 + progress sink |
