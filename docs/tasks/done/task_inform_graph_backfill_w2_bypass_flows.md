# Task：Inform 图谱补齐 · W2（旁路 G-L1 flows：lc_evidence + lg_rag）

> **状态**：completed（闸已签 · 00 代签授权；2026-08-24 随 PR #47 关账归档）  
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
| HG-GRAPH-MODULES | approved | 30 | 2026-08-24 00 签：01_modules 两行仅备注列收敛 + POINTER，module_id/glob/依赖出边/人签记录零改动（diff 证据在目） |

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

- [x] 两个新 flow yaml 与代码真值拓扑一致（抽读核对）
- [x] `00_main` ::triggers 边正确
- [x] `01_modules.md` POINTER 化（边界/出边不变）
- [x] graph.json graphs 计数 4 → 6
- [x] `./scripts/graph-compile.sh` exit 0；`git diff app/` 为空

---

## 自检结论（30 执行 · 2026-08-24）

- **compile**：`npm_config_cache=/tmp/npm-cache-lg ./scripts/graph-compile.sh` exit 0；check 6/6 OK；normalize --check 6 md 通过。
- **graph.json**：`shared/graph.json` graphs = 6（`00_main` / `10_flow_auth` / `10_flow_chat` / `10_flow_lc_evidence` / `10_flow_lg_rag` / `11_flow_sync_to_chat`），4 → 6 达标。
- **app/ 零改动**：`git diff app/` 为空（0 行）。
- **拓扑核对（yaml ↔ 代码真值）**：
  - `10_flow_lc_evidence`：chain.py L118 `retrieve | grade | answer`；节点 ↔ `retrieve_evidence`（retrieve.py L24）/ `grade_chunk+decide_grade`（grader.py L27/L32）/ `answer_question`（answer.py L90）；HTTP 节点 ↔ router.py L117/L124/L138；freeze `lc-evidence-http-v1` 在 HTTP 节点 label；「不进入 chat/graph」在 chain 节点 label 与 description。
  - `10_flow_lg_rag`：basic ↔ graph.py L57-59（START→rag→END）；router ↔ graph.py L66-100（add_node×6 / 三路条件边 L73-81 / rag→evaluate L82 / evaluate⇄rewrite 回环 L83-98 / direct·refuse→END L99-100）；supervisor ↔ multi/graph.py L47-56（add_node×5 / START→supervisor L52 / dispatch 条件边 L53-55 / aggregator→END L56）；黑盒边 `::triggers` → lc chain（nodes.py L160）与 router 子图复用（multi/nodes.py L266），未展开 LCEL。
- **00_main**：`lc_evidence_router → lc_evidence_flow`、`lg_rag_router → lg_rag_flow` 两条 `::triggers` 边，体例对齐 `chat_router → chat_flow`。
- **01_modules**：`lc_evidence_chain` / `lg_rag` 两行备注收敛为一句摘要 + 「详见 10_flow_*」POINTER；module_id / 路径 glob / 依赖出边未动；人签记录行未动；关联节增两条 flow link。
- **附带**：`l0/POINTERS_cross_repo.md` 两行 W1 占位（W2 待建 · TBD）落为正式指针。
- **偏差**：①lg_rag 三拓扑采「同图分节（节点 id 前缀 b_/r_/s_）」而非拆子 graph_id——spec §4 允许分节，且避免新增 graph_id 争议；②supervisor 的 dispatch 以 `route_next_subtask` 显式节点表达回环（代码中它是条件边函数而非节点），比 12 条全连接边更可读；③`10_flow_auth/chat/sync_to_chat` 三个既有 md 仅 `generated_at` 时间戳再生成，无内容变化。
- **遗留**：`HG-GRAPH-MODULES` 仍 pending（约定由 00 复检 01_modules POINTER 化后签）；mermaid 全角括号标签未加引号（normalize --check 通过，IDE 渲染风险低）。

---

## CLOSE

| 项 | 内容 |
|---|---|
| 日期 | 2026-08-24 |
| 定稿 | 图谱 W2（旁路 flows，graphs 4→6） |
| 归档 | `docs/tasks/done/task_inform_graph_backfill_w2_bypass_flows.md` |
| PR | [#47](https://github.com/Cyning12/ops-desk-api/pull/47) MERGED |

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-24 | 初版（00 起草 + 代签闸 · 维护者授权）：W2 范围自 01_execution_waves.md 锁定 |
| 2026-08-24 | 30 执行完成：新建 10_flow_lc_evidence / 10_flow_lg_rag（三拓扑同图分节）+ 编译 md；00_main 两条 ::triggers；01_modules 两行 POINTER 化；compile 绿、graph.json 4→6、app/ 零 diff；验收五项全勾，自检结论见上 |
| 2026-08-25 | 归档（task_task_closeout_hygiene）：CLOSE 节补录 · 状态→completed · git mv 至 docs/tasks/done/（合并日 2026-08-24 · PR #47） |
