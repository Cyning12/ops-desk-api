# G-L1 · Flow 图补齐规格

> **Wave**：W1（chat 刷新）· W2（新建旁路）· W4（rag 可选）  
> **协议**：`docs/_tech_graph/shared/99_mermaid_protocol.md`

---

## 1. 现有 flow 清单

| graph_id | 源 yaml | 状态 | Wave |
|----------|---------|------|------|
| `10_flow_auth` | `l1/10_flow_auth.graph.yaml` | 可用 · anchors 可加强 | W5 |
| `10_flow_chat` | `l1/10_flow_chat.graph.yaml` | **拓扑滞后** | **W1** |
| `11_flow_sync_to_chat` | `l1/11_flow_sync_to_chat.graph.yaml` | 可用 | W5 |
| `10_flow_lc_evidence` | **待建** | 缺失 | **W2** |
| `10_flow_lg_rag` | **待建** | 缺失 | **W2** |
| `10_flow_rag` | **待建（可选）** | 缺失 | W4 |

---

## 2. `10_flow_chat` 刷新要点（W1）

**代码真值**：`app/ops/chat/graph.py`

目标拓扑（节点 id 建议与 LangGraph 注册名对齐）：

```text
START → detect_intent
  ├─ [issue_qa] → load_context → generate_answer → END
  └─ [general|overview] → retrieve → grade ─┬─ refuse → refuse_answer → END
                                            └─ generate_answer → END
```

### 2.1 新增节点

| node id | label | implementedBy |
|---------|-------|---------------|
| `retrieve` | `hybrid_recall` | `app/ops/chat/rag_nodes.py` · `retrieve_node` |
| `grade` | `grade_chunks + gate` | `app/ops/chat/rag_nodes.py` · `grade_node` |
| `refuse_answer` | `refuse on low relevance` | `app/ops/chat/rag_nodes.py` · `refuse_node` |

### 2.2 边变更

- 删除或改写：`intent` 直连 `answer` 的 `[overview|general]` 边 → 改为 `intent --?>` → `retrieve`
- 新增：`retrieve` → `grade`；`grade` 条件到 `refuse_answer` / `generate_answer`
- 条件边建议 `mark: "?>"` 或 `label` 带 `[issue_qa]` / `[refuse]`（协议 §1.1）

### 2.3 跨模块边

- `retrieve` → `db`（查询向量/FTS）
- `retrieve` → `rag`（external 或 `::triggers` 到 `hybrid_recall` · 勿展开 SQL）
- `grade` / `generate_answer` → `llm`

### 2.4 保留

- SSE/WS 入口链：`chat_stream` / `chat_ws` / `event_gen` / `chat_service` / `stategraph`
- `admin_sync` 侧链（若仍准确）

---

## 3. `10_flow_lc_evidence` 新建（W2）

**建议文件**：`docs/_tech_graph/l1/10_flow_lc_evidence.graph.yaml`

| 字段 | 值 |
|------|-----|
| `graph_id` | `10_flow_lc_evidence` |
| `layer` | `G-L1` |
| `depth` | `module` |

**拓扑**（LCEL · 代码 `lc_evidence_chain/chain.py`）：

```text
client → POST /api/ops/lc-evidence/invoke
  → ainvoke_evidence_answer
    → retrieve_evidence → grade_chunk/decide → answer_question
  → {ok,data} JSON
```

**节点建议**：

| id | label | anchors / implementedBy |
|----|-------|-------------------------|
| `lc_invoke` | `POST .../lc-evidence/invoke` | `lc_evidence_chain/router.py` |
| `chain` | `LCEL chain` | `chain.py` · `build_chain` 或 `ainvoke_evidence_answer` |
| `retrieve` | `retrieve_evidence` | `retrieve.py` |
| `grade` | `grade + decide` | `grader.py` |
| `answer` | `answer_question` | `answer.py` |

**依赖外部**：`rag`（hybrid_recall）· `llm` · `db`

**freeze**：响应外壳 `lc-evidence-http-v1`（备注边 label 即可，不画 JSON schema）

---

## 4. `10_flow_lg_rag` 新建（W2）

**建议文件**：`docs/_tech_graph/l1/10_flow_lg_rag.graph.yaml`

| 字段 | 值 |
|------|-----|
| `graph_id` | `10_flow_lg_rag` |
| `layer` | `G-L1` |

一张图内用 **文档分节** 或 **里程碑节点** 表达三模式（避免单图 >20 节点时可拆 `10_flow_lg_rag_router` 子 id · 维护者 W2 拍板）：

### 4.1 HTTP 入口（共用）

`POST /api/ops/lg-rag/invoke` · `mode=basic|router|supervisor`  
→ `lg_rag/router.py` 分派 `ainvoke_*`

### 4.2 basic（Phase 1）

`START → rag → END` · `lg_rag/graph.py` · `build_basic_agent`

### 4.3 router（Phase 2–3）

`START → router → direct|refuse|rag → evaluate ⇄ rewrite → END`  
真值：`lg_rag/graph.py` · `build_router_agent`

### 4.4 supervisor（Phase 4）

`START → supervisor → dispatch(rag_subtask|info_extract|tool_exec)* → aggregator → END`  
真值：`lg_rag/multi/graph.py` · `build_supervisor_agent`

### 4.5 黑盒依赖

`rag` 子路径 **复用** `ainvoke_evidence_answer` / router 子图 → 边标 `::triggers` 到 `10_flow_lc_evidence` 或 `lc_evidence_chain` 模块，**禁止**复制 LCEL 内部。

---

## 5. `10_flow_rag` 可选（W4）

**二选一**（见 `modules/rag.md`）：

- **A**：独立摘要图：`ingest` · `hybrid_recall` · `rerank` · Qdrant Flag 降级
- **B**：仅在 chat/lc flow 上用 `rag` external 节点 + 模块表契约（更薄）

---

## 6. 编译与检查

每改/新建 yaml：

```bash
./scripts/graph-compile.sh
```

期望 `shared/graph.json`：

- W1 后：仍 4 graphs，chat edges 增加
- W2 后：**6 graphs**

---

## 7. 验收清单（G-L1 包级）

- [ ] `10_flow_chat` 含 retrieve/grade/refuse 与代码一致
- [ ] `10_flow_lc_evidence` / `10_flow_lg_rag` 存在且 md 已生成
- [ ] 新 flow 在 `01_modules.md` 关联节有 link
- [ ] 无手写 `.md` flowchart（仅 yaml 源）
