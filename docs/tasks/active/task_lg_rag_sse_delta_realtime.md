# Task：lg-rag T5.1 · 终答 delta 实时投递（pacing / anti-buffer）

> **状态**：active（2026-09-01 · 维护者令「开工」）  
> **类型**：传输 / SSE 投递时效  
> **上游**：[`05_lg_rag_transport_and_session_plan_v0.md`](../../spec/agent-infra/05_lg_rag_transport_and_session_plan_v0.md) **§10.4.1**（**HG-SPEC-SIGNOFF approved**）  
> **前置**：docs-only [`task_lg_rag_sse_delta_realtime_spec`](./task_lg_rag_sse_delta_realtime_spec.md) 已签收；T5 [`task_lg_rag_sse_token_stream`](../done/task_lg_rag_sse_token_stream.md) · [#105](https://github.com/Cyning12/ops-desk-api/pull/105)  
> **分支**：`task/lg-rag-sse-delta-realtime`  
> **帽子**：00 起草闸；**10** 补全；**20** 审；**30+40** 实现。  
> **无关**：新 event_type · 新 freeze · web/iOS 假打字机 · 改 replay/thread_id/cursor 键语义 · token 化 progress

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `lg-rag-sse-delta-realtime` |
| **git_branch** | `task/lg-rag-sse-delta-realtime` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | mock 慢 chunk +（可选）慢 persist：断言节点未结束前已 yield delta；T5 旧测不回归；不连真 LLM；replay 形状不变 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1` |
| **graph_delta** | `docs/_tech_graph/l1/01_modules.md` · `docs/_tech_graph/l1/10_flow_lg_rag.md`（备注） |
| **graph_delta_note** | 不新增一级模块；仅 `lg_rag` / flow 备注补 T5.1 投递时效；若 stream 符号未增删则 G-L2 indexes 可不动（自检写明） |
| **wiki_delta** | `docs/coding_wiki/volatile.md` |
| **wiki_delta_note** | 实现波短注；契约真值仍在 05 §10.4.1 |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,00,30` |
| **invoke_retention_profile** | `default` |
| **freeze_id** | `lg-rag-sse-v1`（**不**新 freeze；不新 event_type；不改 delta/content/final 键） |
| **close_pr_policy** | `required` |
| **related_pr** | （待开） |
| **kpi_aggregator** | `CLOSE` |
| **orchestration** | api-only 先合；web **不**挡；SPEC 已签收 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | 2026-09-01 · **00 代签 · 维护者令「开工」** |
| HG-AUDIT-R1 | **approved** | 30 | 2026-09-01 · **00 代签 · 维护者令「开工」** · 见 `docs/harness/reviews/task_lg_rag_sse_delta_realtime_audit_R1_20260901.md`（R1 pass · 内容零阻塞） |
| HG-GRAPH-MODULES | approved | — | 不新增一级模块 · **00 代签** · 仅 `lg_rag`/flow 备注 |

---

## 00 定夺（草案 · 人可后签）

| 项 | 钉死 |
|---|---|
| **slug** | **`lg-rag-sse-delta-realtime`** |
| **契约** | 落实 05 **§10.4.1**：chunk → sink → emit → **尽快 yield**；禁止默认「节点结束后批量 flush 全部 delta」 |
| **主修复点** | `emit` / sink 路径上 **落盘不得阻塞 SSE yield**（现网：`await persist_run_event` 每帧 commit 串在入队前）。落盘仍尽量完成；失败仍不阻断已发 SSE（T4 语义） |
| **攒批** | **默认不人为攒批**；不新增应用层「攒满 N 帧再 write」 |
| **协议** | 不改 `event_type` / `delta` / `content` / `final` / `cursor` / `thread_id` |
| **验收锚** | mock 慢 chunk：节点 updates 到达前客户端/测试侧已能取到 ≥1 帧 delta；T5 帧序/拼接/降级/replay 不回归 |
| **非本波** | 改 Vite/nginx 现网配置（SPEC 检查清单已文档化）；web 假打字机；新 freeze |
| **合入** | 可 api-only 先合 |

---

## 范围

1. `app/ops/lg_rag/sse_stream.py`（及必要的 `event_store` 调用方式）：投递路径与 persist 解耦，保证 delta **尽快 yield**  
2. 单测：慢 chunk（及必要时慢 persist）证明节点结束前可见 delta；T5 旧测绿  
3. 05 §10.4.1「应然 vs 实然」回写实现句；G-L1 备注  
4. ruff · 相关 pytest · graph-compile（若动 yaml）· lint-wiki-delta  

## 非范围

- 新 `event_type` / 新 freeze / 改帧键语义  
- web / iOS 代码 · 前端假打字机  
- 改 Vite / 生产 nginx（仅文档已列检查项）  
- token 化 `node.progress` / `subtask.progress`  
- 改 replay 协议形状 · cancel 语义 · chat 图  
- 处理 RAG DB 业务错误（与投递正交）  

---

## 验收标准

- [x] mock 卡 persist：persist 未完成时 delta 已可见（`test_delta_yields_before_persist_completes`）  
- [x] 慢 chunk：多枚 delta 均在 final 前（`test_slow_chunks_visible_before_aggregator_update`）  
- [x] 落盘失败仍不阻断已发 SSE；done/`finally` 前 `_drain_persist` 收尾（seq 仍在 emit 同步递增）  
- [x] T5 旧测全绿 + stream/resume 回归（29 passed）  
- [x] 无新 event_type；freeze 仍 `lg-rag-sse-v1`  
- [x] `app/ops/chat/graph.py` 零 diff；`lg_rag` 不新增对 chat/session import  
- [x] 05 §10.4.1 实然/实现句回写；G-L1 备注（indexes 无新符号 · 不动）  
- [x] ruff 触及路径绿；相关 pytest 绿；`./scripts/graph-compile.sh` exit 0  
- [x] `lint-wiki-delta` PASS  

## failure_paths

| 触发 | 行为 | 可重试 | 用户可见 |
|---|---|---|---|
| persist 慢 / 失败 | SSE 仍尽快吐出；失败打日志；replay 可能缺帧（同 T4） | 是 | 打字机仍可见；续看可能缺 |
| provider 极快喷完 | 允许密帧；验收靠慢 mock 证非「节点结束后 flush」 | — | 可能仍密 |
| 背景 persist 未收尾即断连 | finally 尽量 gather；不保证断连后落盘（T2/T4 已知） | replay | 可能缺帧 |
| 误改协议键 | 拒合入；20/PR 拦 | — | — |

---

## 给执行帽的必读列表

1. 本 task（00 定夺）  
2. 05 §10.4.1（含应然 vs 实然 · 实现候选触点）  
3. `app/ops/lg_rag/sse_stream.py` · `answer_stream.py` · `event_store.py`  
4. `tests/test_lg_rag_sse_token_stream.py`  

---

### 自检结论

> **10-task** · 2026-09-01 · 闸齐后 **30+40** 已落地

- [x] slug / 范围 / 非范围 / failure_paths / 验收 / wiki_delta / graph_delta 齐  
- [x] 00 定夺：persist 不阻塞 yield · 不攒批 · 协议零变  
- [x] `emit` → `create_task(persist)` + `_drain_persist`；2 新测  
- [x] verify / ruff / pytest 29 / graph-compile / lint-wiki-delta PASS  
- 下一棒：开 PR → merge → CLOSE（须维护者令）

## 修订记录

| 日期 | 说明 |
|---|---|
| 2026-09-01 | **00**：维护者令「开工」起草实现 task；钉 slug=`lg-rag-sse-delta-realtime`；主修 persist 不阻塞 yield |
| 2026-09-01 | **10-task**：结构补全 · 自检 · 交 20 |
| 2026-09-01 | **20** pass · **HG-AUDIT-R1=approved**（00 代签 · 维护者令「开工」）→ 派 30 |
| 2026-09-01 | **30+40**：emit 后台 persist；2 新测 + 回归绿；05/G-L1 回写 |
