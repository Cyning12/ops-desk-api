# module · `lg_rag`

| 字段 | 值 |
|------|-----|
| **Wave** | **W2**（主）· W6（模块表瘦身） |
| **graph_change_layer** | `G-L1` |

---

## 1. 代码范围

`app/ops/lg_rag/**`

| 文件 | 职责 |
|------|------|
| `graph.py` | basic + router 图 · `ainvoke_*` / `astream_*` |
| `multi/graph.py` | supervisor 图 · `ainvoke_supervisor_agent` / `astream_supervisor_agent` |
| `nodes.py` | router/rag/direct/refuse/evaluate/rewrite |
| `multi/nodes.py` | supervisor / subtask / aggregator |
| `router.py` | HTTP `POST /invoke`（`lg-rag-http-v1`）· `POST /stream`（`lg-rag-sse-v1`） |
| `sse_stream.py` | SSE updates → T1 事件帧 |
| `checkpointer.py` | InMemory / AsyncPostgres saver |
| `state.py` | `LgRagState` |

---

## 2. 现状

| 资产 | 状态 |
|------|------|
| `01_modules` 行 | ✅ |
| G-L0 | ✅ 挂路由 |
| `10_flow_lg_rag` | ✅ |
| G-L2 | ✅ 分文件 `by_path_lg_rag.yaml` / `by_symbol_lg_rag.yaml` · **全** `implementedBy`（`05` §9） |

---

## 3. 目标资产

| 优先级 | 文件 | 动作 |
|--------|------|------|
| P0 | `l1/10_flow_lg_rag.graph.yaml` | **已有**；随 Spec 改节点同步 |
| P0 | `l0/00_main.graph.yaml` | lg_rag_router → flow `::triggers`（已有） |
| P1 | `l1/01_modules.md` | 短摘要 + link（持续） |
| P2 | `l2/indexes/*_lg_rag.yaml` | **已开** · 与 `05` §9 绑定 · **禁止**并入 chat indexes |

---

## 4. 三模式拓扑摘要

**HTTP**（`router.py`）：`mode` → `ainvoke_basic_agent` | `ainvoke_router_agent` | `ainvoke_supervisor_agent`

**basic**：`START → rag → END`

**router**：`START → router → direct|refuse|rag → evaluate ⇄ rewrite (≤2) → END`

**supervisor**：`START → supervisor → dispatch* → aggregator → END`

**黑盒**：`rag_node` / `rag_subtask` → `lc_evidence_chain.ainvoke_evidence_answer`（边标跨模块，不展开 LCEL）

---

## 5. 验收清单

- [ ] 新 yaml `graph_id=10_flow_lg_rag`
- [ ] HTTP 节点 anchors → `lg_rag/router.py`
- [ ] 三张拓扑在图中有分节或 POINTER 节点（basic/router/supervisor）
- [ ] `01_modules` 依赖出边 `→ lc_evidence_chain, llm` 不变
- [ ] compile 绿；graphs 总数 6

---

## 6. 依赖

- → `lc_evidence_chain` · `llm`
- ← `api`（router 注册）

---

## 7. 非范围

- 挂入 `chat/graph`
- 并行 Send / HITL（Phase 4 非范围项）
