# module · `rag`

| 字段 | 值 |
|------|-----|
| **Wave** | W4（可选） |
| **graph_change_layer** | `G-L1`（若建 flow）或 `none` |

---

## 1. 代码范围

`app/ops/rag/**` — 核心：`retrieve.py`（`hybrid_recall`）· `ingest.py` · `embedder.py` · `reranker.py` · `backend.py` · `retrievers/qdrant_retriever.py`

---

## 2. 现状

| 资产 | 状态 |
|------|------|
| `01_modules` 行 | ✅ 备注较新（Qdrant · embed HTTP · shadow write） |
| 独立 flow | ❌ |
| 消费方 | `chat/rag_nodes` · `lc_evidence_chain/retrieve` |

---

## 3. 补齐策略（二选一 · W4 拍板）

### 选项 A · 独立 `10_flow_rag`（推荐若要做「改 A 影响 B」到检索层）

摘要拓扑：

```text
query → embed → hybrid_recall ─┬─ dense (Qdrant | pgvector fallback)
                               ├─ FTS/sparse (PG)
                               └─ rerank → RetrievedChunk[]
ingest → chunk → embed → store (PG + optional Qdrant shadow)
```

节点 anchors 指向 `retrieve.py` · `ingest.py` · `hybrid_recall` 入口。

### 选项 B · 仅契约边（更薄）

不建 flow；在 `10_flow_chat` / `10_flow_lc_evidence` 的 retrieve 边上标 `::triggers` → `01_modules` 的 `RetrievedChunk` 契约。

---

## 4. 目标资产（若选 A）

| 文件 | 动作 |
|------|------|
| `l1/10_flow_rag.graph.yaml` | 新建 |
| `l0/00_main.graph.yaml` | 可选 `rag_domain` external 节点 |
| `01_modules.md` | 增关联 link |

---

## 5. 验收清单

- [ ] 维护者记录选型 A/B
- [ ] 若 A：flow ≤15 节点（摘要级 · 不展开 SQL）
- [ ] compile 绿

---

## 6. 非范围

- 重画 ingest 运维脚本（`scripts/qdrant_migrate/*`）
- 对照实验 task（zhparser/sparse arm）补图
