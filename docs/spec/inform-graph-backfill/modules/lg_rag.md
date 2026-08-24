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
| `graph.py` | basic + router 图 · `ainvoke_basic_agent` / `ainvoke_router_agent` |
| `multi/graph.py` | supervisor 图 · `ainvoke_supervisor_agent` |
| `nodes.py` | router/rag/direct/refuse/evaluate/rewrite |
| `multi/nodes.py` | supervisor / subtask / aggregator |
| `router.py` | HTTP `POST /api/ops/lg-rag/invoke` · freeze `lg-rag-http-v1` |
| `checkpointer.py` | InMemory / AsyncPostgres saver |
| `state.py` | `LgRagState` |

---

## 2. 现状

| 资产 | 状态 |
|------|------|
| `01_modules` 行 | ✅ 但 **超长备注**（Phase1–4 全文） |
| G-L0 | ❌ 未挂路由 |
| `10_flow_lg_rag` | ❌ |
| G-L2 | ❌ |

---

## 3. 目标资产

| 优先级 | 文件 | 动作 |
|--------|------|------|
| P0 | `l1/10_flow_lg_rag.graph.yaml` | **新建**（见 `layers/G-L1_flows.md` §4） |
| P0 | `l0/00_main.graph.yaml` | lg_rag_router → flow `::triggers` |
| P1 | `l1/01_modules.md` | 行改为短摘要 + link `10_flow_lg_rag.md`（W6） |
| P2 | `l2/indexes/*` | 仅当维护者拍板第二 G-L2 试点（见 `layers/G-L2_indexes.md`） |

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
