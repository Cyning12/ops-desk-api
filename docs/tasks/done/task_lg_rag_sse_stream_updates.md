# Task：lg-rag T2 · SSE stream（updates）+ Obs Generation I/O

> **状态**：completed（2026-08-31 CLOSE · api PR [#97](https://github.com/Cyning12/ops-desk-api/pull/97) MERGED · web [#23](https://github.com/Cyning12/ops-desk-web/pull/23) MERGED）  
> **类型**：传输 / 观测薄层  
> **上游**：[`05_lg_rag_transport_and_session_plan_v0.md`](../../spec/agent-infra/05_lg_rag_transport_and_session_plan_v0.md) §3 P1/P2 · §4.2 T1  
> **前置**：T0 Spec 签收 · [`task_lg_rag_sse_t0_t1_spec`](../done/task_lg_rag_sse_t0_t1_spec.md)  
> **分支**：`task/lg-rag-sse-stream-updates`  
> **帽子**：00 起草闸；**30 实现**（本会话在闸齐后执行）。  
> **无关**：T3/T4 session·replay；T5 token 流；T6 弃用 chat 代码删除；改 `chat/graph.py`；E5 收尾。

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `lg-rag-sse-stream-updates` |
| **git_branch** | `task/lg-rag-sse-stream-updates` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | mock astream / 鉴权；SSE 帧序断言；tracing I/O mock；不连真 LLM/Langfuse |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1` |
| **graph_delta** | `docs/_tech_graph/l1/10_flow_lg_rag.graph.yaml` |
| **graph_delta_note** | `lg_rag` 模块备注 + flow：新增 `POST /lg-rag/stream`（freeze `lg-rag-sse-v1`）；不新增一级模块 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 传输/观测薄层；真值在 `05` + G-L1/G-L2；不晋升 coding_wiki |
| **kpi_aggregator** | `CLOSE` |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,00,30` |
| **invoke_retention_profile** | `default` |
| **freeze_id** | `lg-rag-sse-v1` |
| **close_pr_policy** | `required` |
| **related_pr** | `#97` |
| **orchestration** | T2 + Obs-I/O 同波；不单开 Obs task |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | 2026-08-30 · **00 代签 · 维护者令「开工」** |
| HG-AUDIT-R1 | approved | 30 | 2026-08-30 · **00 代签** · 见 `docs/harness/reviews/task_lg_rag_sse_stream_updates_audit_R1_20260830.md` |
| HG-GRAPH-MODULES | approved | — | 不新增一级模块 · **00 代签** · 仅 `lg_rag` 行/flow 备注 |

---

## 范围

### T2 · SSE

1. `POST /api/ops/lg-rag/stream`（cookie 鉴权同 invoke）  
2. Body：`query` · `mode`（默认 **`supervisor`**）· 可选 `thread_id`  
3. `astream(..., stream_mode="updates")` → SSE 帧：`run_id`/`seq`/`ts_ms`/`agent_role`/`event_type`/`payload`  
4. 事件映射对齐 `05` §4.2：`run.start` · `node.progress` · `subtask.progress` · `answer` · `done` / `error`  
5. 断连语义（本波钉死）：**服务端尽量跑完图**；不保证客户端收齐；**不做** cancel/replay（T4）  
6. **不**改 `/invoke` 行为；**不**挂 chat  
7. **G-L2（`05` §9）**：`by_path_lg_rag` / `by_symbol_lg_rag` 覆盖 `10_flow_lg_rag` **全部** `implementedBy`（分文件 · 不混 chat）

### Obs-I/O（同波验收 · 不单开 task）

1. `tracing`：`update_current_generation_io`（截断 + 失败 no-op）  
2. Provider `complete` 路径在 generation 上下文内写入 truncated input/output  
3. I/O 失败 **不**阻断主答

## 非范围

- Token 级流（T5）  
- Session 压缩 / cursor replay（T3/T4）  
- 删除或改路由默认到 chat  
- 全路径强制补 I/O（缺口可列文档一行）

## 验收标准

- [x] `/stream` 鉴权 401；校验 422  
- [x] mock astream：帧序含 `run.start` → 至少一进度 → `answer`（若有 aggregator）→ `done`  
- [x] tracing 关时 I/O 上报零调用；开时 mock client 收到截断 I/O  
- [x] `ruff` + 相关 pytest 绿；`./scripts/graph-compile.sh` 绿  
- [x] `05` 回写：HTTP 路径冻结为 `/api/ops/lg-rag/stream` · freeze `lg-rag-sse-v1`  
- [x] G-L2：lg_rag indexes 覆盖 flow **全部** `implementedBy`（`05` §9）  
- [x] `npx --yes dsh-coding-kit task lint-wiki-delta --target .` 通过（本波 wiki_delta=`n/a`）

## failure_paths

| 触发 | 行为 |
|---|---|
| 图异常 | SSE `error`（retryable 视异常）+ flush_traces；HTTP 仍 200 stream 内报错 |
| Generation I/O 失败 | 日志/debug；不抛业务 |
| 非法 mode | 422 |

---

## CLOSE

| 项 | 值 |
|---|---|
| PR | api [#97](https://github.com/Cyning12/ops-desk-api/pull/97) **MERGED** 2026-08-31 · web [#23](https://github.com/Cyning12/ops-desk-web/pull/23) **MERGED** 2026-08-31 |
| web task | [`ops-desk-web/docs/tasks/done/task_web_lg_rag_sse_t2.md`](../../../ops-desk-web/docs/tasks/done/task_web_lg_rag_sse_t2.md)（slug `web-lg-rag-sse-t2` · 已归档） |
| 人工 checklist | [`ops-desk-web/docs/checklists/CHECKLIST_lg_rag_sse_joint_release_v1.md`](../../../ops-desk-web/docs/checklists/CHECKLIST_lg_rag_sse_joint_release_v1.md) |
| Spec | api `05` §10–§11（T2 联调已通过；指针随本 CLOSE 改 done/） |
| 归档 | 2026-08-31 · 00 关账 · 维护者 Prompt 授权 |

### 自检结论

> 2026-08-31 · 00 关账复检 · **PASS**（实现已合入 #97；本窗不重跑业务测）

- [x] 验收标准全勾（合入前 30/40 已绿）
- [x] web T2 [#23](https://github.com/Cyning12/ops-desk-web/pull/23) MERGED · checklist 联调已勾
- [x] invoke 帽集合 10/00/30 齐全 · R1 审查文存在

### KPI

Task_KPI%: 100 · D1 范围钉死 T2+Obs-I/O · D2 联调闸已过 · D3 过程档齐 · D4 图谱 G-L1/G-L2 已随 #97 · D5 关账补登 2026-08-31
