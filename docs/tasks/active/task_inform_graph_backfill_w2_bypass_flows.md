# Task：Inform 图谱补齐 · W2（旁路 G-L1 flows：lc_evidence + lg_rag）

> **状态**：active（闸已签 · 00 代签授权）  
> **类型**：图谱 / 文档（无业务 Python 改码）  
> **上游 SPEC**：`docs/spec/SPEC-inform-graph-backfill_v1.md`（HG-SPEC-SIGNOFF approved 2026-08-23）  
> **范围真值**：`docs/spec/inform-graph-backfill/01_execution_waves.md` §W2 · `modules/lc_evidence_chain.md` · `modules/lg_rag.md` · `layers/G-L1_flows.md`  
> **前置**：W1 已合并（PR #46）；kit 1.5.1 升级 + 迁移探针完成（命令面不切，normalize 保留）  
> **分支**：`task/inform-graph-backfill-w2-bypass-flows`  
> **执行模式**：00 编排/验收；30 子 agent 执行

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `inform-graph-backfill-w2-bypass-flows` |
| **git_branch** | `task/inform-graph-backfill-w2-bypass-flows` |
| **graph_change_layer** | `G-L1` |
| **graph_delta** | 新建 `docs/_tech_graph/l1/10_flow_lc_evidence.graph.yaml` · `10_flow_lg_rag.graph.yaml`；`l0/00_main.graph.yaml` 加 ::triggers；`l1/01_modules.md` 加 POINTER 并瘦身行内拓扑长文 |
| **graph_delta_note** | W2 范围锁定；不建 l2 indexes（W3）；不做 rag 摘要 flow（W4） |
| **wiki_delta** | `n/a` |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,30` |
| **test_strategy** | `required` |
| **test_strategy_note** | `./scripts/graph-compile.sh` exit 0；`git diff app/` 为空；graph.json graphs 计数 4→6 |
| **code_quality_bar** | `not_applicable` |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | 2026-08-24 00 代签（维护者指令「回到图谱完整绘制 task」+ 本窗授权签收过程文档；SPEC 已签收） |
| HG-AUDIT-R1 | approved | 30 | 2026-08-24 00 代签（纯图谱 yaml，范围锁定 W2 spec；同 W1 例） |
| HG-GRAPH-MODULES | pending | 30 | 00 复检 01_modules.md POINTER 化后签 |

---

## 范围（§W2 锁定）

1. 新建 `docs/_tech_graph/l1/10_flow_lc_evidence.graph.yaml` + 编译 md：retrieve→grade→answer 链 + gate 条件 + HTTP invoke 入口节点（真值 = `app/ops/lc_evidence_chain/`，体例对齐既有 `10_flow_chat.graph.yaml`）
2. 新建 `docs/_tech_graph/l1/10_flow_lg_rag.graph.yaml` + 编译 md：basic / router（含 evaluate/rewrite 回环）/ supervisor 三拓扑，按 spec 用**分节或子图 POINTER**；HTTP `lg-rag/invoke` 入口；真值 = `app/ops/lg_rag/`
3. `00_main.graph.yaml`：`lc_evidence_router` / `lg_rag_router` → 对应 flow 的 `::triggers` 边
4. `01_modules.md`：`lc_evidence_chain` / `lg_rag` 行增「详见 `10_flow_*`」POINTER，**删除/收敛**行内重复拓扑长文为一句摘要（注意：不改模块边界与依赖出边）
5. `./scripts/graph-compile.sh` 绿（含 normalize --check）

## 非范围

- `l2/indexes`（W3）；`10_flow_rag`（W4）；模块表全面瘦身（W6）
- `app/` 业务代码；切 graph 命令面

## 验收标准

- [ ] 两个新 flow yaml 与代码真值拓扑一致（抽读核对）
- [ ] `00_main` ::triggers 边正确
- [ ] `01_modules.md` POINTER 化（边界/出边不变）
- [ ] graph.json graphs 计数 4 → 6
- [ ] `./scripts/graph-compile.sh` exit 0；`git diff app/` 为空

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-24 | 初版（00 起草 + 代签闸 · 维护者授权）：W2 范围自 01_execution_waves.md 锁定 |
