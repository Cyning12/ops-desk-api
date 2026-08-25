# Task：Inform 图谱补齐 · W6（模块表瘦身）

> **状态**：active（闸已签 · 00 代签授权）  
> **类型**：图谱 / 文档（无业务 Python 改码）  
> **范围真值**：`docs/spec/inform-graph-backfill/01_execution_waves.md` §W6 及对应模块/层 spec  
> **分支**：`task/inform-graph-backfill-w3-w6`（W3–W6 集成分支）  
> **执行模式**：00 编排/验收；30 子 agent 执行（与 W5 同子 agent 串行）

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `inform-graph-backfill-w6-modules-trim` |
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

1. `01_modules.md`：`lg_rag` / `lc_evidence_chain` / `rag` 行备注改为短句 + link（拓扑只在 flow yaml）；**module_id / glob / 依赖出边 / 人签记录一律不动**
2. 检查其余行是否同样有拓扑长文可瘦身（`chat` 行等），同原则处理

## 非范围

- 模块边界/出边改动
- `app/` 业务代码

## 验收标准

- [ ] 三行（及以上）备注短句化 + link 到对应 10_flow_*；边界零改动（diff 证据）
- [ ] `./scripts/graph-compile.sh` exit 0

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-25 | 初版（00 起草 + 代签闸 · 维护者授权）：范围自 01_execution_waves.md §W6 锁定 |
