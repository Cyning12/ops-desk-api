# Task：lg-rag SSE · subtask 里程碑 step + LLM 真流式

> **状态**：completed（2026-09-08 CLOSE · PR [#127](https://github.com/Cyning12/ops-desk-api/pull/127) MERGED · 归档 done）  
> **类型**：传输 / 子任务过程时效 + provider 流式  
> **上游**：[`05_lg_rag_transport_and_session_plan_v0.md`](../../spec/agent-infra/05_lg_rag_transport_and_session_plan_v0.md) **§10.7**（step 增补）  
> **前置**：`lg-rag-sse-subtask-live`（running/done MVP）已归档 done  
> **分支**：`task/lg-rag-sse-subtask-steps`  
> **帽子**：00 · 10 · 30+40  
> **无关**：子任务内 token 打字机 · 新 event_type · web 假打字机 · 改 idle/keepalive 数值

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `lg-rag-sse-subtask-steps` |
| **git_branch** | `task/lg-rag-sse-subtask-steps` |
| **implement_repo** | `ops-desk-api`（api-first；web 另开若需适配 step） |
| **test_strategy** | `required` |
| **test_strategy_note** | mock 慢 chain：running 后、节点返回前至少一帧 `status=step`；aread 误调不得吞 chunk；T5/keepalive/running 旧测不回归；不连真 LLM |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1` |
| **graph_delta** | `docs/_tech_graph/l1/01_modules.md` · `10_flow_lg_rag` 备注 |
| **graph_delta_note** | 不新增一级模块；`emit_subtask_step` 进 G-L2 indexes；lc_evidence step_hook 不反向依赖 lg_rag |
| **wiki_delta** | `docs/coding_wiki/volatile.md` |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,00,30` |
| **invoke_retention_profile** | `default` |
| **freeze_id** | `lg-rag-sse-v1`（不新 freeze；不新 event_type；payload 增 `status=step`/`step`/`detail`） |
| **close_pr_policy** | `required` |
| **related_pr** | `#127` |
| **kpi_aggregator** | `CLOSE` |
| **orchestration** | api-first |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | 2026-09-08 · **00 代签 · 维护者确认 Implement plan** |
| HG-AUDIT-R1 | **approved** | 30 | 2026-09-08 · **00 代签 · 维护者确认 Implement plan** |
| HG-GRAPH-MODULES | approved | — | 不新增一级模块 · **00 代签** |

---

## 00 定夺

| 项 | 钉死 |
|---|---|
| **slug** | `lg-rag-sse-subtask-steps` |
| **中途帧** | `subtask.progress` · `status=step` · `step` · 可选 `detail` |
| **里程碑** | router 子图节点边界 + evidence retrieve/grade/answer 起止 |
| **终答** | 删除 provider `aread()` 假缓冲 |
| **机制** | progress sink + lc_evidence `step_hook` ContextVar（避免 chain→lg_rag 反向边） |

## 范围

1. `app/llm/providers/base.py`：删流式 `aread()`  
2. `progress_stream.py`：`emit_subtask_step`  
3. `lc_evidence_chain/step_hook.py` + `chain.py` 里程碑  
4. `multi/nodes.py`：`astream_router_agent` + step 发射 + 挂 hook  
5. 单测 + 05 §10.7 + G-L1 + volatile  

## 验收标准

- [x] 慢 mock：`running` 后、节点结束前可见 `status=step`（至少 retrieve 或 router 节点）  
- [x] provider：误调 `aread` 不得导致 chunk 丢失（回归测）  
- [x] keepalive / T5 / running 旧测不回归  
- [x] ruff · 相关 pytest · graph-compile（若动 yaml）  

## failure_paths

| 触发 | 行为 | 可重试 |
|---|---|---|
| 无 sink / 无 hook | step 空操作 | — |
| sink/hook 异常 | 打日志，不中断节点 | 是 |

### 自检结论（执行者）

> **帽**：30+40 · **日期**：2026-09-08 · **分支**：`task/lg-rag-sse-subtask-steps`（已合）  
> **invoke**：`docs/harness/invokes/by-task/lg-rag-sse-subtask-steps/invoke_20260908_30_40_lg-rag-sse-subtask-steps.md`

- 慢 mock：`running` 后、节点返回前可见 `status=step`（retrieve / router 节点）——pass
- provider：误调 `aread` 不吞 chunk（回归测）——pass
- keepalive / T5 delta / running 旧测不回归——pass
- `ruff check app tests` · 相关 `pytest` · `graph-compile`——全绿（PR #127 CI）

### KPI（00）

Task_KPI%: 100 · D1 范围钉死（step 里程碑 + aread 真流式 · 不新 event_type/freeze）· D2 闸齐（HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 00 代签落盘）· D3 过程档齐（invoke 10/00/30+40 + CLOSE invoke）· D4 图谱 G-L1 备注随 #127 · D5 关账补登 2026-09-08（Hub + active README + subtask_live #125 漏行同波补）

## 修订记录

| 日期 | 说明 |
|---|---|
| 2026-09-08 | **00**：维护者确认 Implement plan；钉 step 里程碑 + aread 修复 |
| 2026-09-08 | **00 CLOSE**：PR [#127](https://github.com/Cyning12/ops-desk-api/pull/127) MERGED；验收 4/4 全绿；归档 done/ · Hub 补登 · CLOSE invoke 留档 |

---

## 关账（CLOSE）

| 项 | 值 |
|---|---|
| PR | [#127](https://github.com/Cyning12/ops-desk-api/pull/127) MERGED（2026-09-08） |
| 验收 | running 后节点返回前可见 `status=step` · aread 误调不吞 chunk · keepalive/T5/running 旧测不回归 · ruff/pytest/graph-compile 绿 |
| 归档 | `docs/tasks/done/task_lg_rag_sse_subtask_steps.md` |
| Hub | 2026-09-08 补登（含 subtask_live #125 漏行同波补登） |
| 下一棒 | `lg-rag-sse-subtask-message`（subtask.progress 可读 `message`） |
