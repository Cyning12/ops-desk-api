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
| HG-GRAPH-MODULES | approved | 30 | 2026-08-25 00 签：00 统一复检过（compile 绿 · graphs 7 · coverage OK · 01_modules 仅备注列变化 diff 证据） |

---

## 范围

1. `01_modules.md`：`lg_rag` / `lc_evidence_chain` / `rag` 行备注改为短句 + link（拓扑只在 flow yaml）；**module_id / glob / 依赖出边 / 人签记录一律不动**
2. 检查其余行是否同样有拓扑长文可瘦身（`chat` 行等），同原则处理

## 非范围

- 模块边界/出边改动
- `app/` 业务代码

## 验收标准

- [x] 三行（及以上）备注短句化 + link 到对应 10_flow_*；边界零改动（diff 证据）
- [x] `./scripts/graph-compile.sh` exit 0

---

## 自检结论（30 回填 · 2026-08-25）

- **瘦身**：`rag` / `lc_evidence_chain` / `lg_rag` 三行备注删行内拓扑长文改短句 + link 到对应 `10_flow_*`；`chat` 行原已为短句，仅补 link 到 `10_flow_chat.md`（共四行处理）。
- **边界零改动证据**：`git diff docs/_tech_graph/l1/01_modules.md` 仅 4 行「负责人/备注」单元格变化；module_id / 名称 / 路径 glob / 依赖方向列逐字节不变；跨模块契约、人签记录、关联节均不在 diff hunk 中。
- **compile**：`./scripts/graph-compile.sh` exit 0（与 W5 同次运行：7 graphs · 99 nodes · 142 edges · check 全 OK）。
- **coverage 复跑**：R3「备注含 START→ 长拓扑」检查行数 1 → 0，无 warn。

### 偏差及理由

- `rag` 行删去「被 `lc_evidence_chain` 复用 `hybrid_recall`」表述：该复用关系仍由 lc 行依赖出边（→ rag）与跨模块契约 RetrievedChunk 行承载，信息无丢失，符合「拓扑/重复长文只在 flow yaml」原则。

### 遗留风险

- 无新增；拓扑真值以各 10_flow_*.graph.yaml 为准。

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-25 | 初版（00 起草 + 代签闸 · 维护者授权）：范围自 01_execution_waves.md §W6 锁定 |
| 2026-08-25 | 30 回填：四行备注短句化 + link；边界零改动 diff 证据；验收两项全勾 |
