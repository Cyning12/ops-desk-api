# module · `lc_evidence_chain`

| 字段 | 值 |
|------|-----|
| **Wave** | **W2** |
| **graph_change_layer** | `G-L1` |

---

## 1. 代码范围

`app/ops/lc_evidence_chain/**`

| 文件 | 职责 |
|------|------|
| `chain.py` | LCEL：`retrieve → grade → answer` · `ainvoke_evidence_answer` |
| `retrieve.py` | 调 `rag.hybrid_recall` |
| `grader.py` | `grade_chunk` · `decide_grade` |
| `answer.py` | `answer_question` |
| `router.py` | HTTP `POST /api/ops/lc-evidence/invoke` · freeze `lc-evidence-http-v1` |
| `types.py` | `EvidenceItem` · `ChainResult` |

---

## 2. 现状

| 资产 | 状态 |
|------|------|
| `01_modules` 行 | ✅ 含 HTTP · Langfuse · usage |
| `task_lc_evidence_http` | 曾标 `10_flow_lc_evidence` **可选非挡** → 未建 |
| G-L0 / flow | ❌ |

---

## 3. 目标资产

| 优先级 | 文件 | 动作 |
|--------|------|------|
| P0 | `l1/10_flow_lc_evidence.graph.yaml` | **新建**（`layers/G-L1_flows.md` §3） |
| P0 | `l0/00_main.graph.yaml` | lc_evidence_router → `::triggers` |
| P1 | `l0/POINTERS_cross_repo.md` | 增 flow 行 |
| P2 | `01_modules.md` | W6 缩短备注 |

---

## 4. 拓扑真值

```text
POST /lc-evidence/invoke (cookie auth)
  → ainvoke_evidence_answer
      → retrieve_evidence (→ rag.hybrid_recall → db)
      → grade (→ llm)
      → answer (→ llm)
  → 200 {ok,data}  # gate refuse 仍 200
```

---

## 5. 验收清单

- [ ] flow 含 HTTP · chain · retrieve · grade · answer 节点
- [ ] 边标注 **不改** `chat/graph`（备注节点或边 label）
- [ ] freeze `lc-evidence-http-v1` 在 HTTP 节点 label 或 description
- [ ] compile 绿

---

## 6. 依赖

- → `rag` · `llm` · `db`
- 被 `lg_rag` 黑盒复用

---

## 7. 非范围

- 改 LCEL 业务 / prompt
- SSE / 挂 chat stream
