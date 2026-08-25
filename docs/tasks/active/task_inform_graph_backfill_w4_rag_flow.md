# Task：Inform 图谱补齐 · W4（RAG 摘要 flow · 选项 A）

> **状态**：active（闸已签 · 00 代签授权）  
> **类型**：图谱 / 文档（无业务 Python 改码）  
> **范围真值**：`docs/spec/inform-graph-backfill/01_execution_waves.md` §W4 及对应模块/层 spec  
> **分支**：`task/inform-graph-backfill-w3-w6`（W3–W6 集成分支）  
> **执行模式**：00 编排/验收；30 子 agent 执行（与 W3 同子 agent 串行）

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `inform-graph-backfill-w4-rag-flow` |
| **git_branch** | `task/inform-graph-backfill-w3-w6` |
| **graph_change_layer** | `mixed` |
| **wiki_delta** | `n/a` |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,30` |
| **test_strategy** | `required` |
| **test_strategy_note** | `./scripts/graph-compile.sh` exit 0；`git diff app/` 为空（W5 新增 coverage 脚本除外，其为 scripts/ 工具非 app/） |
| **code_quality_bar** | `not_applicable` |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | 2026-08-25 00 代签（维护者指令「开启图谱 W3–W6」+ 本窗授权；SPEC 已签收） |
| HG-AUDIT-R1 | approved | 30 | 2026-08-25 00 代签（纯图谱/文档，范围锁定对应 wave spec；同 W1/W2 例） |
| HG-GRAPH-MODULES | pending | 30 | 00 复检后签（W6 为 01_modules 主体改动，重点核边界不变） |

---

## 范围

1. 新建 `docs/_tech_graph/l1/10_flow_rag.graph.yaml`（**选项 A 独立 flow**，spec 推荐）：query → embed → hybrid_recall → dense（Qdrant | pgvector fallback）/ FTS 融合 → rerank → hydrate；anchors 指向 `retrieve.py` / `embedder.py` / `reranker.py` / `backend.py`
2. 编译 md 随 graph-compile 产出

## 非范围

- 折叠进 chat/lc ::triggers（选项 B，本波不取）
- `app/` 业务代码；ingest 侧详细展开（摘要 flow 粒度）

## 验收标准

- [ ] `10_flow_rag` 拓扑与 `app/ops/rag/` 代码真值一致（抽读）
- [ ] graph.json graphs 6 → 7
- [ ] `./scripts/graph-compile.sh` exit 0；`git diff app/` 为空

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-25 | 初版（00 起草 + 代签闸 · 维护者授权）：范围自 01_execution_waves.md §W4 锁定 |
