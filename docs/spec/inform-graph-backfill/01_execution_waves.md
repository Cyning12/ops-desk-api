# 01 · 执行波次（W0–W6）

> **用法**：每波对应 **一个** `docs/tasks/active/task_inform_graph_backfill_w*.md`；本文件为 scope 真值。

---

## 依赖图

```text
W0 纪律
 └─► W1 G-L0 + chat flow 追平
      ├─► W2 旁路 G-L1 flows
      │    └─► W6 模块表瘦身
      ├─► W3 chat G-L2 indexes
      └─► W4 rag 摘要 flow（可与 W3 并行）
W5 auth/sync anchors + coverage warn（依赖 W1 节点 id 稳定）
```

---

## W0 · 过程纪律（无 yaml）

| 项 | 动作 |
|----|------|
| Skill | 在 `s-l1-tech-graph-ops` 增 POINTER：新 HTTP 域 → G-L0；新 Agent 图 → `10_flow_*` |
| Task 模板 | 新功能 task 的 `graph_delta` 禁止默认仅 `01_modules.md`（旁路域） |
| PR | 可选 PR 模板勾选项：「涉及路由/图拓扑 → 已更新 `_tech_graph`」 |

**验收**：维护者签收；无 `graph-compile` 义务。

---

## W1 · P0：G-L0 + chat G-L1 追平

| 字段 | 值 |
|------|-----|
| **建议 task_slug** | `inform-graph-backfill-w1-g0-chat` |
| **graph_change_layer** | `mixed` |
| **主要 spec** | `layers/G-L0_00_main.md` · `modules/chat.md` · `modules/api.md` |

**范围**：

1. `00_main.graph.yaml`：新增 `lc_evidence_router`、`lg_rag_router` 节点；`ops_router` 出边；刷新 `router.py` anchors
2. `10_flow_chat.graph.yaml`：追加 `retrieve` / `grade` / `refuse_answer` 节点与条件边；`intent` 到 `retrieve` 的 `?>` 边
3. `l0/POINTERS_cross_repo.md`：补旁路 flow 指针（占位可链到 W2 文件）
4. `./scripts/graph-compile.sh` 绿

**不在 W1**：新建 `10_flow_lg_rag`（属 W2）；lg_rag G-L2 indexes。

---

## W2 · P0：旁路 G-L1 flows

| 字段 | 值 |
|------|-----|
| **建议 task_slug** | `inform-graph-backfill-w2-bypass-flows` |
| **graph_change_layer** | `G-L1` |
| **主要 spec** | `modules/lc_evidence_chain.md` · `modules/lg_rag.md` · `layers/G-L1_flows.md` |

**范围**：

1. 新建 `l1/10_flow_lc_evidence.graph.yaml` + 编译 md
2. 新建 `l1/10_flow_lg_rag.graph.yaml`（含 basic / router / supervisor 三拓扑 **分节或子图 POINTER**）
3. `00_main`：`lc_evidence_router` / `lg_rag_router` → 对应 flow 的 `::triggers`
4. `01_modules.md`：为 `lc_evidence_chain` / `lg_rag` 行增加「详见 `10_flow_*`」POINTER；**删除**行内重复拓扑长文（或留一行摘要）

**验收**：`graph.json` graphs 计数 **4 → 6**；compile 绿。

---

## W3 · P1：chat G-L2 indexes

| 字段 | 值 |
|------|-----|
| **建议 task_slug** | `inform-graph-backfill-w3-chat-g2` |
| **graph_change_layer** | `mixed` |
| **主要 spec** | `layers/G-L2_indexes.md` · `modules/chat.md` §G-L2 |

**范围**：

1. `10_flow_chat` 为新节点补 `implementedBy`（`rag_nodes.py`）
2. 更新 `l2/indexes/by_path.yaml` / `by_symbol.yaml`
3. `l2/README.md` 注明：chat 试点已含 RAG 子链

**不在 W3**：lg_rag 的 G-L2（见层 spec P2 拍板项）。

---

## W4 · P1：RAG 摘要 flow（可选）

| 字段 | 值 |
|------|-----|
| **建议 task_slug** | `inform-graph-backfill-w4-rag-flow` |
| **graph_change_layer** | `G-L1` |
| **主要 spec** | `modules/rag.md` |

**范围**：新建 `10_flow_rag.graph.yaml` 或把 hybrid_recall 折叠进 chat/lc 的 `::triggers` 边说明（二选一 · 见模块 spec）。

**可并行 W3**（无硬依赖）。

---

## W5 · P2：anchors + coverage warn

| 字段 | 值 |
|------|-----|
| **建议 task_slug** | `inform-graph-backfill-w5-coverage` |
| **graph_change_layer** | `none` 或 `G-L1`（若只补 anchors） |
| **主要 spec** | `modules/auth.md` · `ci/coverage_check.md` |

**范围**：

1. `10_flow_auth` / `11_flow_sync_to_chat` 硬边 anchors 补全或刷新行号
2. 实现 `scripts/graph_coverage_check.py`（warn）：对比 `router.include_router` 集合 vs `00_main` 子路由节点
3. **可选** 接入 `tech-graph.yml`（warn 不 fail）

---

## W6 · P2：模块表瘦身

| 字段 | 值 |
|------|-----|
| **建议 task_slug** | `inform-graph-backfill-w6-modules-trim` |
| **graph_change_layer** | `G-L1` |
| **依赖** | W2 完成 |

**范围**：`lg_rag` / `lc_evidence_chain` / `rag` 行备注改为短句 + link；拓扑只在 flow yaml。

---

## 建议首棒 Prompt（复制用）

维护者授权 30 后，首棒建议 **W1**（收益最大、不依赖新文件命名争议）：

```text
Open Folder=ops-desk-api；读 docs/spec/inform-graph-backfill/01_execution_waves.md §W1
与 modules/chat.md、layers/G-L0_00_main.md；建 task_inform_graph_backfill_w1_g0_chat；
只改 docs/_tech_graph 下 00_main + 10_flow_chat + POINTERS；跑 graph-compile.sh。
```
