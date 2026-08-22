# Task：lg_rag 对外 HTTP API（POST /api/ops/lg-rag/invoke）

> **状态**：active（闸已签 · 00 代签授权）  
> **类型**：feature / lg_rag 旁路 HTTP 化  
> **先例**：`task_lc_evidence_http`（`POST /api/ops/lc-evidence/invoke` · cookie 鉴权 · `{ok,data}` 外壳 · freeze 契约）  
> **实现仓**：本仓  
> **分支**：沿用 `task/lg-rag-phase1`  
> **执行模式**：00 编排/验收；30/40 子 agent 执行

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `lg-rag-http` |
| **git_branch** | `task/lg-rag-phase1`（沿用 · 整 PLAN 一次 PR） |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | httpx AsyncClient + mock 图调用（对齐 test_lc_evidence_http 体例）：鉴权、校验、envelope、mode 分派、失败路径；不连真库/LLM 可绿 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1` |
| **graph_delta** | `docs/_tech_graph/l1/01_modules.md` |
| **graph_delta_note** | `lg_rag` 行补 HTTP 端点与 freeze 契约名；`api` 行不改（路由注册在 lg_rag 包内 router.py） |
| **wiki_delta** | `n/a` |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,30` |
| **orchestration** | 单 task；契约 freeze `lg-rag-http-v1` |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | 2026-08-21 00 代签（维护者授权「作为00签收过程文档」） |
| HG-AUDIT-R1 | approved | 30 | 2026-08-21 00 代签（同上授权；契约完全沿用 lc-evidence-http 先例，风险面小） |
| HG-GRAPH-MODULES | approved | 30 | 2026-08-22 00 签：G-L1 lg_rag 行已补 HTTP 端点与 freeze 契约名 |

---

## 契约（freeze `lg-rag-http-v1`）

`POST /api/ops/lg-rag/invoke` · cookie session 鉴权（`CurrentUser`，同 lc-evidence）

**请求**：

```json
{
  "query": "string, 1..8000",
  "mode": "router | basic | supervisor（缺省 router）",
  "thread_id": "string 可选，≤255（超长 422 显式拒绝，与 web SPEC 对齐）；缺省由服务端生成"
}
```

**响应**（200）：

```json
{
  "ok": true,
  "data": {
    "answer": "string（末条 AIMessage）",
    "mode": "router",
    "thread_id": "string（回显，供续写）",
    "route": "rag | direct | refuse | ""（basic 模式无 router，空串）",
    "retry_count": 0,
    "chain_meta": {"gate_action": "", "hit_count": 0, "kept_count": 0, "best_relevance": "", "grade_count": 0},
    "subtasks": [],
    "subtask_results": []
  }
}
```

- `subtasks` / `subtask_results` 仅 supervisor 模式非空；`chain_meta` 仅走过 rag 路径时非空。
- **失败**：图内异常 → 500 `{"ok": false, "error": {"code": "lg_rag_failed", "message": "旁路调用失败"}}`（同 lc 先例语义）；`mode` 非法 → 422（Pydantic Literal 校验）。
- **Checkpointer**：v1 默认 InMemorySaver（进程内同 thread_id 续写；重启即丢，与 lc 无状态先例的差异点已告知）；env `LG_RAG_HTTP_CHECKPOINTER=postgres` 时走 `apostgres_saver(setup=True)`（每请求构建，幂等建表；性能影响记入备注，生产默认不開）。
- tracing：沿用图内 `propagate_attributes`（trace_name=lg-rag，session=thread_id）；响应前后 `flush_traces`（同 lc 先例）。
- 非流式 v1；SSE 流式（对齐 Chat 契约）另开 task。

---

## 范围（本仓）

1. `app/ops/lg_rag/router.py`：上述契约；mode→`ainvoke_basic_agent/ainvoke_router_agent/ainvoke_supervisor_agent` 分派。
2. `app/ops/router.py`：注册 lg_rag router（对齐 lc-evidence 注册行）。
3. `tests/test_lg_rag_http.py`：mock 三个 ainvoke 入口；鉴权 401/403、query 空/超长 422、mode 非法 422、三 mode 分派与 envelope、异常 500 外壳、thread_id 回显。
4. G-L1 `lg_rag` 行补端点与 freeze 契约名 + graph-compile。

## 非范围

- SSE / WebSocket 流式（另开 task）
- 挂 Chat 图或改 `chat/graph.py`（冻结延续）
- supervisor 并行化、真实工具（沿 Phase 4 非范围）
- 生产默认开 PG checkpointer（v1 默认 InMemory）

## failure_paths

| 触发 | 行为 | 可重试 |
|---|---|---|
| 图内异常（db/LLM） | 500 外壳 + 日志 + flush_traces | Y |
| mode 非法 / query 空 | 422 | Y |
| 未登录 | 401/403（复用 deps） | Y |
| InMemory 进程重启 | 历史 thread 丢，客户端需重发 | — |

---

## 验收标准

- [x] 契约三项一致；freeze 名写入 router.py docstring 与 G-L1；00 修正 thread_id 超长 422（与 web SPEC 对齐）
- [x] 三 mode 分派正确（mock 断言 + 40 真机 curl 三 mode 全 200）
- [x] 11 例全绿（401/422×5/分派/envelope/500 外壳/thread_id 生成回显）；lg_rag 30 + lc http 8 不回归（合跑 49 passed）
- [x] 40 真机（uvicorn+真 PG/Qdrant/LLM）：三 mode + 续写 + 401/422 全 PASS；chain_meta 有值；supervisor 拆出 rag+tool
- [x] `git diff master`：chat/graph.py 与 lc_evidence_chain 零改动
- [x] G-L1 更新 + graph-compile exit 0；ruff 绿

---

## 自检结论（50 · 00 验收）

> 2026-08-22 · 00（父窗）：30/40 子 agent 执行，00 复检 · **PASS**

- [x] 30 产出复检：router.py 抽读合格；ruff/11 例全绿；禁区零 diff
- [x] 契约对齐修正：thread_id 超长由静默截断改为 422（对齐 web SPEC）
- [x] 40 真机验证 PASS（三 mode + 续写 + 鉴权/校验 + Langfuse + 回归 242 passed 无新增失败）
- [x] 00 抽验 Langfuse：verify40-* traces 在案（name=lg-rag, session=thread_id）
- [ ] （观察，不挡）PG checkpointer 支路无单测（env-gated 默认不开）；续写 query 过简致 0 命中属检索质量范畴

**50 结论：PASS（机械）· 可 CLOSE**

## CLOSE

| 项 | 内容 |
|---|---|
| 日期 | 2026-08-22 |
| 定稿 | lg_rag 对外 HTTP：POST /api/ops/lg-rag/invoke（freeze lg-rag-http-v1；三 mode；cookie 鉴权；InMemory 默认 / env 可切 PG） |
| 归档 | `docs/tasks/done/task_lg_rag_http.md` |
| 下游 | ops-desk-web `docs/spec/SPEC-web-lg-rag-page_v1.md` + `task_web_lg_rag_page`（draft 待 web 维护者审） |

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-21 | 初版（00 起草 + 代签闸 · 维护者授权）：契约沿用 lc-evidence-http 先例；执行交子 agent |
| 2026-08-22 | 30 子 agent 实施（router.py + 注册 + 10 例）；00 复检 + thread_id 422 契约修正（11 例） |
| 2026-08-22 | 40 子 agent 真机验证全项 PASS；00 50 验收 PASS；CLOSE 归档 |
