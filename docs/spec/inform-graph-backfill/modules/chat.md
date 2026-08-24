# module · `chat`

| 字段 | 值 |
|------|-----|
| **Wave** | **W1**（G-L1 拓扑）+ **W3**（G-L2 indexes） |
| **graph_change_layer** | `mixed` |

---

## 1. 代码范围

`app/ops/chat/**` — 重点：`graph.py` · `nodes.py` · `rag_nodes.py` · `router.py` · `ws.py` · `service.py` · `streaming.py`

---

## 2. 现状

| 资产 | 状态 |
|------|------|
| `01_modules` 行 | ✅ 含 `→ rag` |
| `10_flow_chat` | ⚠️ 缺 retrieve/grade/refuse；intent 仍直连 answer |
| G-L2 indexes | ⚠️ 无 `rag_nodes.py` |
| 代码拓扑 | ✅ 含 RAG 链（2026-08-10） |

**漂移**：图谱版本冻结 `2026-07-27`，代码已演进。

---

## 3. 目标资产

| 优先级 | 文件 | 动作 |
|--------|------|------|
| P0 | `l1/10_flow_chat.graph.yaml` | 刷新 LangGraph 拓扑（见 `layers/G-L1_flows.md` §2） |
| P0 | `l1/10_flow_chat.graph.yaml` | bump `version` |
| P1 | `l2/indexes/by_path.yaml` | 追加 `rag_nodes.py` 三符号 |
| P1 | `l2/indexes/by_symbol.yaml` | 同上 |
| P2 | `10_flow_chat` | 补缺失 anchors（EVAL P0 建议） |

---

## 4. 拓扑真值（代码）

```text
START → detect_intent
  issue_qa  → load_context → generate_answer → END
  general|overview → retrieve → grade → refuse_answer | generate_answer → END
```

节点注册名：`detect_intent` / `load_context` / `generate_answer` / `retrieve` / `grade` / `refuse_answer`（`graph.py`）。

---

## 5. 节点 id 映射建议

| yaml node id | 代码节点名 | implementedBy symbol |
|--------------|------------|----------------------|
| `intent` | detect_intent | `intent_node` |
| `context` | load_context | `load_issue_context_node` |
| `answer` | generate_answer | `answer_node` |
| `retrieve` | retrieve | `retrieve_node` |
| `grade` | grade | `grade_node` |
| `refuse_answer` | refuse_answer | `refuse_node` |
| `stategraph` | (compiled) | `graph` module |

---

## 6. 验收清单

- [ ] flow 图与 `graph.py` 条件边语义一致
- [ ] `retrieve` 边指向 `rag` 或标注 `hybrid_recall` 契约
- [ ] W3：indexes 与 implementedBy 一致
- [ ] `git diff app/ops/chat/` 为空（纯图谱棒）
- [ ] `./scripts/graph-compile.sh` exit 0

---

## 7. 依赖

- → `llm` · `db` · `rag`（`hybrid_recall`）
- ← `api`（SSE/WS 路由）

---

## 8. 非范围

- 不改 Chat 业务逻辑 / prompt
- lg_rag 并入 chat graph（硬约束：旁路不进 `chat/graph`）
