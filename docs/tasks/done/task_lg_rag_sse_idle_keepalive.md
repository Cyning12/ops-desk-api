# Task：lg-rag SSE · idle 超时语义 + comment keepalive

> **状态**：completed（2026-09-07 CLOSE · PR [#123](https://github.com/Cyning12/ops-desk-api/pull/123) MERGED）  
> **类型**：传输 / SSE 保活与超时语义  
> **上游**：[`05_lg_rag_transport_and_session_plan_v0.md`](../../spec/agent-infra/05_lg_rag_transport_and_session_plan_v0.md) **§10.6**  
> **前置**：T5.1 CLOSE · [`task_lg_rag_sse_delta_realtime`](./task_lg_rag_sse_delta_realtime.md) · [#122](https://github.com/Cyning12/ops-desk-api/pull/122)  
> **分支**：`task/lg-rag-sse-idle-keepalive`  
> **帽子**：00 起草闸；**10** 补全；**20** 审；**30+40** 实现。  
> **无关**：新 event_type · 新 freeze · 改 invoke 页 axios 墙钟 · Nginx · 节点内 token 级 subagent 日志

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `lg-rag-sse-idle-keepalive` |
| **git_branch** | `task/lg-rag-sse-idle-keepalive` |
| **implement_repo** | `ops-desk-api`（api keepalive + SPEC；web idle/UI 在 `ops-desk-web` 同波） |
| **test_strategy** | `required` |
| **test_strategy_note** | mock 慢 `__anext__`：节点返回前至少一条 `: keepalive`；业务帧形状回归；不连真 LLM |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1` |
| **graph_delta** | `docs/_tech_graph/l1/01_modules.md` · `docs/_tech_graph/l1/10_flow_lg_rag.md`（备注） |
| **graph_delta_note** | 不新增一级模块；仅 `lg_rag`/flow 备注补 idle/keepalive；G-L2 indexes 不动 |
| **wiki_delta** | `docs/coding_wiki/volatile.md` |
| **wiki_delta_note** | 实现波短注；契约真值在 05 §10.6 |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,00,30` |
| **invoke_retention_profile** | `default` |
| **freeze_id** | `lg-rag-sse-v1`（**不**新 freeze；keepalive 为 SSE comment，不进 data JSON） |
| **close_pr_policy** | `required` |
| **related_pr** | `#123` |
| **kpi_aggregator** | `CLOSE` |
| **orchestration** | api keepalive + SPEC 本仓；web idle + 子任务分区 UI 跨仓并行 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | 2026-09-07 · **00 代签 · 维护者令 Implement plan** |
| HG-AUDIT-R1 | **approved** | 30 | 2026-09-07 · **00 代签 · 维护者令 Implement plan** |
| HG-GRAPH-MODULES | approved | — | 不新增一级模块 · **00 代签** · 仅备注 |

---

## 00 定夺

| 项 | 钉死 |
|---|---|
| **slug** | **`lg-rag-sse-idle-keepalive`** |
| **客户端超时** | **idle 120s**：任意 `reader.read()` 有字节即重置；**不设**整轮墙钟上限 |
| **keepalive** | 等待下一 `astream` update 期间每 **30s** yield `: keepalive\n\n`；不落盘、不占 `seq`、不冒充 progress/answer |
| **UI（web）** | `subtask.progress` → 独立「子任务过程」；`node.progress` →「编排进度」 |
| **非本波** | invoke 页 axios 300s 墙钟；Nginx；新 event_type |

---

## 范围

1. 05 §10.6 契约 + 联调项改写（去掉 ≥300s 墙钟表述）  
2. `app/ops/lg_rag/sse_stream.py` keepalive  
3. 单测：慢 update 前可见 comment  
4. G-L1 备注 + volatile 短注  
5.（跨仓）web idle + Chat 子任务分区（本 task 编排，码在 web 仓）

## 非范围

- 新 `event_type` / 新 freeze  
- 改 replay 落盘形状  
- invoke 非流式墙钟  
- Nginx / Vite proxyTimeout（除非联调证明必需）

---

## 验收标准

- [x] mock 慢 `__anext__`：节点返回前 ≥1 条 `: keepalive`  
- [x] 业务帧 `run.start`→progress→`answer`→`done` 形状不回归  
- [x] keepalive 不出现在 persist 调用（单测断言）  
- [x] 05 §10.6 落盘；§10.2 联调项改 idle 语义  
- [x] ruff · 相关 pytest · graph-compile · volatile 更新  

## failure_paths

| 触发 | 行为 | 可重试 | 用户可见 |
|---|---|---|---|
| 服务端停写且无 keepalive | web idle 120s → timeout；可 T4 续看 | 是 | 超时文案 |
| keepalive 误落盘 | 拒合入；测拦 | — | — |
| 误发业务 event 当心跳 | 拒合入 | — | UI 噪声 |

## 修订记录

| 日期 | 说明 |
|---|---|
| 2026-09-07 | **00**：维护者令 Implement plan；钉 idle 120s + comment keepalive 30s |
| 2026-09-07 | **30+40**：sse_stream keepalive + 单测；05 §10.6；PR [#123](https://github.com/Cyning12/ops-desk-api/pull/123) MERGED |
| 2026-09-07 | **00 CLOSE**：归档 done/ · Hub 补登 |

## 关账（CLOSE）

| 项 | 值 |
|---|---|
| PR | [#123](https://github.com/Cyning12/ops-desk-api/pull/123) MERGED |
| 归档 | `docs/tasks/done/task_lg_rag_sse_idle_keepalive.md` |
| Hub | 2026-09-07 补登 |
| 下一棒 | `lg-rag-sse-subtask-live`（subtask 中途 SSE） |
