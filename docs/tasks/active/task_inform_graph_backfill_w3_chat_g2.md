# Task：Inform 图谱补齐 · W3（chat G-L2 indexes）

> **状态**：active（闸已签 · 00 代签授权）  
> **类型**：图谱 / 文档（无业务 Python 改码）  
> **范围真值**：`docs/spec/inform-graph-backfill/01_execution_waves.md` §W3 及对应模块/层 spec  
> **分支**：`task/inform-graph-backfill-w3-w6`（W3–W6 集成分支）  
> **执行模式**：00 编排/验收；30 子 agent 执行（与 W4 同子 agent 串行）

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `inform-graph-backfill-w3-chat-g2` |
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

1. `10_flow_chat.graph.yaml` 新 RAG 节点（retrieve/grade/refuse_answer 等 W1 追加的）补 `implementedBy`（指向 `app/ops/chat/rag_nodes.py` 等真实符号）
2. 更新 `l2/indexes/by_path.yaml` / `by_symbol.yaml`
3. `l2/README.md` 注明 chat 试点已含 RAG 子链

## 非范围

- lg_rag 的 G-L2（层 spec P2 拍板项）
- `app/` 业务代码

## 验收标准

- [x] `10_flow_chat` 新节点 implementedBy 齐全且符号真实存在（抽读核对）
- [x] by_path / by_symbol 索引与 yaml 一致（compile + 抽读）
- [x] `./scripts/graph-compile.sh` exit 0；`git diff app/` 为空

---

## 自检结论（30 · 2026-08-25）

- **implementedBy**：`10_flow_chat` 共 11 条（8+3）；RAG 三节点经抽读核对符号真实 —— `retrieve_node`（rag_nodes.py L64）/ `grade_node`（L116）/ `refuse_node`（L175），均保留 `layer_hint: G-L2`。注：三条 implementedBy 实为 W1 已追加，本波抽读验证 + bump version（2026-08-23 → 2026-08-25）。
- **indexes**：`by_path.yaml` 6→7 文件（追加 `app/ops/chat/rag_nodes.py` 三条）；`by_symbol.yaml` 追加 `retrieve_node` / `grade_node` / `refuse_node` 倒排；双向与 flow yaml `implementedBy` 集合一致（各 11 条）；version 同步 bump 至 2026-08-25（spec §3 规则 4）。
- **l2/README.md**：注明试点域 chat 已含 RAG 子链节点，并写明「拓扑变更须同步 flow yaml + indexes」。
- **compile**：`npm_config_cache=/tmp/npm-cache-lg ./scripts/graph-compile.sh` exit 0；`OK: 10_flow_chat`；normalize check 7/7。
- **POINTER**：`01_modules.md` `deeper: ../l2/indexes/by_path.yaml` 仍有效。
- **diff 纪律**：`git diff app/` 为空；未 commit。

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-25 | 初版（00 起草 + 代签闸 · 维护者授权）：范围自 01_execution_waves.md §W3 锁定 |
| 2026-08-25 | 30 执行完成：chat G-L2 追平（indexes + README + version bump）；验收三项全勾，自检结论见上 |
