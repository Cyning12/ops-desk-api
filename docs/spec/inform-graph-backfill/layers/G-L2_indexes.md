# G-L2 · Indexes 补齐规格

> **Wave**：W3（chat 追平）· P2 拍板（第二试点）  
> **试点真值**：`docs/_tech_graph/l2/README.md`（当前仅 chat）

---

## 1. 现状

| 文件 | 覆盖 |
|------|------|
| `l2/indexes/by_path.yaml` | 6 个 chat 文件 · **无** `rag_nodes.py` |
| `l2/indexes/by_symbol.yaml` | 9 个符号 · **无** retrieve/grade/refuse |
| `10_flow_chat.graph.yaml` | 8 个 `implementedBy` · 缺 RAG 三节点 |

**注释**：「手维启动；后续可 `--check`」— 本包 W5 可选实现 check，**不进** harness 默认 check。

---

## 2. W3 目标（chat 试点追平）

### 2.1 `10_flow_chat` 新增 implementedBy

| node_id | path | symbol | kind |
|---------|------|--------|------|
| `retrieve` | `app/ops/chat/rag_nodes.py` | `retrieve_node` | method |
| `grade` | `app/ops/chat/rag_nodes.py` | `grade_node` | method |
| `refuse_answer` | `app/ops/chat/rag_nodes.py` | `refuse_node` | method |

每个节点保留 `layer_hint: G-L2`。

### 2.2 更新 indexes

**by_path.yaml** 追加：

```yaml
"app/ops/chat/rag_nodes.py":
  - node_id: retrieve
    symbol: retrieve_node
    kind: method
  - node_id: grade
    symbol: grade_node
    kind: method
  - node_id: refuse_answer
    symbol: refuse_node
    kind: method
```

**by_symbol.yaml** 追加对应倒排（与现有 chat 条目格式一致）。

### 2.3 `l2/README.md`

更新为：

- 试点域：`chat`（含 RAG 子链节点）
- 拓扑变更须同步 **flow yaml + indexes**

---

## 3. 一致性规则（手维）

1. `implementedBy` 集合 ⊆ indexes 集合（双向一致）
2. 同一 `(path, symbol)` 不映射到多个 node_id
3. `graph_id` 字段保持 `10_flow_chat`
4. bump `version` 与 flow yaml 同日

---

## 4. P2 拍板：第二 G-L2 试点域

| 选项 | 优点 | 缺点 |
|------|------|------|
| **A · 继续只 chat** | 成本低 | lg_rag 仍无法 path 倒排 |
| **B · lg_rag** | Supervisor/路由改动可追踪 | 多图模式 · 节点多 |
| **C · lc_evidence** | 链短 | HTTP 已 freeze · 变更少 |

**建议**：W3 只做 chat；**W2 完成后**维护者选 B 或 C 再开 `task_inform_graph_backfill_w3b-g2-lg-rag`。

若选 B：新建 `l2/indexes/by_path_lg_rag.yaml` 或扩展 by_path 加 `graph_id` 分区（避免与 chat 混排 · 需在 yaml 顶注释约定）。

---

## 5. 验收清单（W3）

- [ ] `10_flow_chat` 共 11 个 implementedBy 节点（8+3）
- [ ] `by_path` / `by_symbol` 含 `rag_nodes.py` 三条
- [ ] `01_modules.md` 的 `deeper:` POINTER 仍有效
- [ ] `./scripts/graph-compile.sh` exit 0
- [ ] **未**要求 CI 自动校验 indexes（W5 可选）

---

## 6. 非范围

- 全仓每个 `app/ops/**/*.py` 进 indexes
- AST 自动生成 indexes
- lg_rag multi 节点 G-L2（除非拍板选 B）
