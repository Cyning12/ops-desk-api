# Task：Inform 图谱补齐 · W4（RAG 摘要 flow · 选项 A）

> **状态**：completed（闸已签 · 00 代签授权；2026-08-25 随 PR #49 关账归档）  
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
| HG-GRAPH-MODULES | approved | 30 | 2026-08-25 00 签：00 统一复检过（compile 绿 · graphs 7 · coverage OK · 01_modules 仅备注列变化 diff 证据） |

---

## 范围

1. 新建 `docs/_tech_graph/l1/10_flow_rag.graph.yaml`（**选项 A 独立 flow**，spec 推荐）：query → embed → hybrid_recall → dense（Qdrant | pgvector fallback）/ FTS 融合 → rerank → hydrate；anchors 指向 `retrieve.py` / `embedder.py` / `reranker.py` / `backend.py`
2. 编译 md 随 graph-compile 产出

## 非范围

- 折叠进 chat/lc ::triggers（选项 B，本波不取）
- `app/` 业务代码；ingest 侧详细展开（摘要 flow 粒度）

## 验收标准

- [x] `10_flow_rag` 拓扑与 `app/ops/rag/` 代码真值一致（抽读）
- [x] graph.json graphs 6 → 7
- [x] `./scripts/graph-compile.sh` exit 0；`git diff app/` 为空

---

## 自检结论（30 · 2026-08-25）

- **新建** `docs/_tech_graph/l1/10_flow_rag.graph.yaml`（选项 A 独立 flow）：15 节点（≤15 上限）/ 20 边；链 query → embed → hybrid_recall → dense（Qdrant 默认 \| pgvector 即时降级）/ FTS·sparse 第二路 → RRF k=60 融合 →（可选）CE rerank → RetrievedChunk[] top-5；含 Qdrant 命中 PG hydrate 回表粒度；ingest 侧不展开（摘要粒度）。
- **拓扑抽读核对**：dense 默认 Qdrant（backend.py L57-78，再试 1 次即时降级 pgvector）；FTS 默认 plainto_tsquery、`RAG_SECOND_PATH=sparse` C 臂（retrieve.py L204-214）；RRF k=60 两路等权（retrieve.py L25/L134-149）；rerank 默认关、顶分地板+相对顶分过滤、fail-closed 回退粗排（reranker.py L221-298）；hydrate 禁从 Qdrant 读正文（qdrant_retriever.py L18/L113）。anchors 全部指向真实文件行/符号。
- **graph.json**：graphs 6 → 7（新增 `10_flow_rag`；99 nodes / 142 edges）。
- **compile**：exit 0；`OK: 10_flow_rag`；normalize check 7/7；产物 `l1/10_flow_rag.md` 由编译生成（未手写）。
- **diff 纪律**：`git diff app/` 为空；未 commit。
- **遗留**：`01_modules.md` 增关联 link（spec §4 可选项）属 W6 主体改动范围，本波未动。

---

## CLOSE

| 项 | 内容 |
|---|---|
| 日期 | 2026-08-25 |
| 定稿 | W4 10_flow_rag（graphs 6→7） |
| 归档 | `docs/tasks/done/task_inform_graph_backfill_w4_rag_flow.md` |
| PR | [#49](https://github.com/Cyning12/ops-desk-api/pull/49) MERGED |

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-25 | 初版（00 起草 + 代签闸 · 维护者授权）：范围自 01_execution_waves.md §W4 锁定 |
| 2026-08-25 | 30 执行完成：新建 `10_flow_rag`（选项 A）；验收三项全勾，自检结论见上 |
| 2026-08-25 | 归档（task_task_closeout_hygiene）：CLOSE 节补录 · 状态→completed · git mv 至 docs/tasks/done/（合并日 2026-08-25 · PR #49） |
