# Task：Inform 图谱补齐 · W1（G-L0 + chat G-L1 追平）

> **状态**：active  
> **类型**：图谱 / 文档（无业务 Python 改码）  
> **上游 SPEC**：`docs/spec/SPEC-inform-graph-backfill_v1.md`（HG-SPEC-SIGNOFF approved · 2026-08-23）  
> **执行 spec**：`docs/spec/inform-graph-backfill/modules/chat.md` · `layers/G-L0_00_main.md`  
> **建议分支**：`task/inform-graph-backfill-w1-g0-chat`

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `inform-graph-backfill-w1-g0-chat` |
| **git_branch** | `task/inform-graph-backfill-w1-g0-chat` |
| **graph_change_layer** | `mixed` |
| **graph_delta** | `docs/_tech_graph/l0/00_main.graph.yaml` · `docs/_tech_graph/l1/10_flow_chat.graph.yaml` · `docs/_tech_graph/l0/POINTERS_cross_repo.md` |
| **graph_delta_note** | W1：G-L0 挂 lc/lg 路由并刷新 router anchors；`10_flow_chat` 追平 retrieve→grade→refuse 拓扑；**不新增**一级模块；**不建** `10_flow_lg_rag`（W2） |
| **wiki_delta** | `n/a` |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,30` |
| **test_strategy** | `required` |
| **test_strategy_note** | `./scripts/graph-compile.sh` exit 0；`git diff app/` 为空 |
| **code_quality_bar** | `not_applicable` |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | 维护者 2026-08-23：签收 SPEC 后开 W1 |
| HG-AUDIT-R1 | approved | 30 | 纯图谱 yaml；范围锁定 W1 spec |
| HG-GRAPH-MODULES | approved | 30 | 不新增一级模块；不改 `01_modules` 边界 |

---

## 范围

1. `docs/_tech_graph/l0/00_main.graph.yaml`：新增 `lc_evidence_router` · `lg_rag_router`；刷新 `ops_router` anchors
2. `docs/_tech_graph/l1/10_flow_chat.graph.yaml`：追加 RAG 链节点/边；bump `version`
3. `docs/_tech_graph/l0/POINTERS_cross_repo.md`：旁路 flow 占位（W2 填实）
4. `./scripts/graph-compile.sh` 绿

## 非范围

- `l2/indexes`（W3）
- 新建 `10_flow_lc_evidence` / `10_flow_lg_rag`（W2）
- `app/` 业务代码

---

## 验收标准

- [x] `00_main` 含 lc/lg 路由节点与正确 anchors
- [x] `10_flow_chat` 与 `app/ops/chat/graph.py` 拓扑一致
- [x] `./scripts/graph-compile.sh` exit 0
- [x] `git diff app/` 为空

---

## 关联

- `docs/spec/inform-graph-backfill/01_execution_waves.md` §W1
- `docs/harness/evidence/EVAL_tech_graph_third_party_20260730.md`
