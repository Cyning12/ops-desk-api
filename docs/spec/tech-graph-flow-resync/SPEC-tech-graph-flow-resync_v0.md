# SPEC：lg_rag 图谱 flow/l2 索引重生成（v0 · supervisor-first 对拍）

> **状态**：`draft`（HG-SPEC-SIGNOFF=pending）
> **track**：`docs`（图谱与注释重同步；唯一代码面改动是 `multi/__init__.py` docstring 修正，注释-only）
> **上游**：2026-10-19 supervisor 全流程审核「图谱对拍」节：15 项一致 + 5 项差异，最大差异是 `l1/10_flow_lg_rag.md`（version 2026-10-14）仍画 `START → intent_node`，与代码（PR #282 supervisor-first）和 `01_modules.md:35` 行末备注（2026-10-19「去前置 Intent」）**自相矛盾**
> **建议序**：**5/5**（最后做——等前四项修复落定、拓扑稳定后一次重生成，避免刚同步又漂移）
> **现状锚点**（对拍差异清单）：
> 1. `docs/_tech_graph/l1/10_flow_lg_rag.md`：mermaid `START → intent_node`（:106, :259）、`s_intent` 节点（:209）、intent→strategy_builder 边（:260）、intent LLM/SO 边（:286-287）——代码已 `START → strategy_builder → supervisor`（`app/ops/lg_rag/multi/graph.py:96-104`）；
> 2. flow 行号锚点普遍漂移：sup 边锚 `multi/graph.py#L73-80`（实际 :96-104）、`s_rag` 锚 `multi/nodes.py#L266`（实际 `rag_subtask_node` :1391）、`s_supervisor` complete 锚 `:L200`（实际 :1163-1170）；
> 3. l2 indexes（`by_path_lg_rag.yaml` / `by_symbol_lg_rag.yaml`，version 2026-08-31）覆盖率有意冻结：缺 Wave B 新文件 `run_worker.py`/`sse_subscribe.py`，缺 `observe_node`/`_join_subtasks`/`_persist_hitl`/`_issue_plan`，缺 hitl 模块与 strategy/critic 之外的后期符号；
> 4. `intent_node` 仍挂 l2 索引 `s_intent`（指向 `app/ops/strategy/intent.py:52`），代码保留但 lg_rag 图全不挂载——图谱未标 dormant/未挂载状态；
> 5. 代码内 docstring 自相矛盾：`app/ops/lg_rag/multi/__init__.py:5` 仍写「拓扑：START → intent_node → strategy_builder → supervisor」，与同包 `graph.py:82` 注释直接冲突。
> **下游**：20-spec-audit / HG-SPEC-SIGNOFF → 00 出 task → 20-task-audit → HG-AUDIT-R1 → 30
> **Open Folder（实现）**：`ops-desk-api/`

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **spec_slug** | `tech-graph-flow-resync` |
| **invoke_slug** | `tech-graph-flow-resync` |
| **test_strategy** | `required`（图谱校验） |
| **test_strategy_note** | `./scripts/graph-compile.sh` 必过 · 重生成后 flow 文档与代码拓扑逐边对拍（checklist 落 invoke）· 行号锚点抽查（每条边锚点指向符号实际位置 ±10 行内）· dormant 标记存在性断言 |
| **默认分支** | `task/tech-graph-flow-resync` |
| **graph_change_layer** | `G-L1 + G-L2`（本 SPEC **就是**图谱变更：l1 flow 重生成 + l2 索引处置决策 + l1 modules 行备注对拍） |
| **freeze_id** | 图谱 freeze 契约 `lg-rag-http-v1` / `lg-rag-sse-v1` 描述不变（代码没变，是图谱追上代码） |

### 人工闸（SPEC 阶段）

| human_gate_id | status | 说明 |
|---|---|---|
| **HG-SPEC-SIGNOFF** | **pending** | 待 20-spec-audit 或维护者人签；l2 索引扩/冻裁定在签收时一并做（见 D2） |

---

## 1. 背景与目标

supervisor-first（PR #282，2026-10-19 合入）改了图拓扑，`01_modules.md:35` 行末备注当天已更新，但 flow 文档与 l2 索引没跟上——l1 层内部自相矛盾（行备注说「去前置 Intent」，flow 文档还在画 intent_node）。图谱是 HG-GRAPH-MODULES 闸的真值，也是 SpecWave issue #40 提议的「全帽工作地图」——**自相矛盾的地图比没有地图更危险**（照着走会走错）。

### 一句话目标

lg_rag 图谱与 supervisor-first 代码全面对拍：flow 文档重生成、行号锚点修正、intent_node 标 dormant、`multi/__init__.py` docstring 修正；l2 索引「扩 or 继续冻」由维护者签收时裁定（本 SPEC 预写两分支）。

---

## 2. 范围

单 task。**前置依赖**：建议序 1–4（query-coref-rewrite / memory-injection-consumer / scenario-stage-rewire / delegation-naming-boundary）落定后再启动——它们都会再动拓扑相关代码，图谱最后同步一次最省。

### D1 · flow 文档重生成（必做）

| 项 | 约定 |
|---|---|
| 拓扑 | `START → strategy_builder → supervisor → subtask_join →（Send 工人 / observe）→ aggregator → critic_node`，含 route_next_subtask / route_after_react / route_after_critic 条件边（真值 `multi/graph.py:96-104`、`_DISPATCH_MAP :53-60`、`_REACT_MAP :63-66`、`_CRITIC_MAP :69-74`） |
| intent_node | 从 flow 图摘除；保留一段「IntentV1 保留未挂载（dormant）」说明，指向 `app/ops/strategy/intent.py` |
| 锚点 | 全部行号锚点按重生成时点的代码重核（±10 行精度） |
| version | flow 文档 version 日期更新为重生成日 |

### D2 · l2 索引处置（二选一，签收时裁定）

| 分支 | 内容 | 适用判断 |
|---|---|---|
| **D2-a 继续冻** | 维持 2026-08-31 冻结，但在索引文件头加显式冻结声明（冻结日期 + 覆盖边界 + 「引用时须知止步于此」），并把 `s_intent` 标 dormant | 索引维护成本高、审核引用少时 |
| **D2-b 扩** | 补 Wave B 新文件（`run_worker.py`/`sse_subscribe.py`）与关键后期符号（`observe_node`/`_join_subtasks`/`_persist_hitl`/`_issue_plan` 等），version 更新 | SpecWave #40「图谱先读」纪律落地后索引成高频入口时 |

### D3 · 代码注释修正（注释-only）

| 项 | 约定 |
|---|---|
| `multi/__init__.py:5` | docstring 拓扑改为 supervisor-first 实际拓扑（注释-only，零行为变更） |
| 全仓扫 | grep 其他仍写 `START → intent_node` 的注释/文档（含 docs/ 目录），一并修正或标注历史版本归属 |

---

## 3. 非范围

- ❌ 改图谱分层结构（G-L0/L1/L2 物理分层不动）
- ❌ 改 HG-GRAPH-MODULES 闸语义与签署流程
- ❌ 除 `multi/__init__.py` docstring 外的任何 `app/` 代码改动
- ❌ 概念总图（concepts 层）补齐 delegation 9 项缺口——那是 delegation-echo worktree 走读文档线的收尾，另案
- ❌ 图谱↔代码自动同步工具（SpecWave #40 §5-3 仅提议 warning 级漂移检查，自动同步是更大题目）
- ❌ 在前四项修复落定前启动本 task（建议序钉死 5/5 最后）

---

## 4. 方案对比（R2 落盘）

| 方案 | 内容 | 裁定 |
|---|---|---|
| A 立即全量重生成（含 l2 扩） | 一次把图谱追到最新 | **弃**。前四项修复还会再动代码，现在全量追必然再漂移一次 |
| B 本 SPEC：建议序最后做 + l2 二选一 | flow 必做；l2 扩/冻签收时裁定 | **采纳** |
| C 只修 docstring 不动图谱 | 最小动作 | **弃**。l1 自相矛盾是闸真值层的伤，不能留 |

---

## 5. failure_paths

| ID | 路径 | 期望 |
|---|---|---|
| FP-1 | 重生成后 flow ↔ 代码对拍 | 每条边/节点在代码中找到对应（checklist 全勾落 invoke） |
| FP-2 | 行号锚点抽查 | 每条锚点指向符号实际位置 ±10 行内；抽样 ≥10 条 |
| FP-3 | `graph-compile.sh` | 通过（既有校验零回归） |
| FP-4 | intent_node | flow 图无 intent 节点；dormant 说明存在；l2 `s_intent` 有 dormant/未挂载标记 |
| FP-5 | D2-a 分支 | 索引文件头冻结声明存在（日期+边界） |
| FP-6 | D2-b 分支 | `run_worker.py`/`sse_subscribe.py` 与点名符号全部入索引 |
| FP-7 | `multi/__init__.py` docstring | 与 `graph.py:96-104` 实际拓扑一致；grep 无残留旧拓扑描述 |

---

## 6. 验收

- [ ] flow 文档重生成，拓扑=supervisor-first 实际，version 日期更新
- [ ] 行号锚点抽查 FP-2 全过
- [ ] intent_node dormant 三处（flow 说明 / l2 标记 / __init__ docstring）一致
- [ ] l2 分支裁定有维护者签收记录；按分支完成 FP-5 或 FP-6
- [ ] `graph-compile.sh` 通过；CI 绿
- [ ] invoke 落「重生成时点 commit hash」，供下次漂移判定基准

---

## 7. 风险

| 风险 | 缓解 |
|---|---|
| 重生成后不久又漂移 | 建议序钉最后做；invoke 记基准 commit；SpecWave #40 §5-3 漂移检查落地后机器兜底 |
| l2 扩面失控（索引进全量符号） | D2-b 只补点名清单；20-task-audit 核对 diff 面 |
| 重生成引入新错误 | FP-1/FP-2 对拍 checklist 强制 |

回滚：图谱文档 git revert；docstring 注释 revert。

---

## 8. 思考轮控制

| 轮 | 结论 | early_stop | reason | residual_risks |
|---|---|---|---|---|
| R0 | 对拍发现 l1 自相矛盾 + l2 冻结 + docstring 冲突 | no | | |
| R1 | 范围=flow 重生成 + l2 二选一 + docstring；概念总图/自动同步/分层结构非范围 | no | | |
| R2 | 采纳 B（最后做 + l2 裁定）；弃立即全量、弃只修注释 | no | | |
| R3 | 前置依赖：建议序 1–4 落定后启动 | no | | 1–4 延期则本项顺延（接受） |
| R4 | 对拍 checklist + 锚点抽查可机器化大半 | no | | |
| R5 | draft 可交 20-spec-audit；**签收时必须一并裁定 D2 分支** | no | 人签未发生 | HG-SPEC-SIGNOFF=pending |

`actual_last_round`：R5

### R0
审核会话「图谱对拍」节 5 项差异逐条落盘（见文首现状锚点）。

### R1
成功=图谱恢复可信地图地位；失败=闸真值层继续自相矛盾。

### R2
见 §4。时机选择是本 SPEC 的核心判断。

### R3
不碰闸语义；唯一代码面是注释。

### R4
`test_strategy=required`（graph-compile + 对拍 checklist）。

### R5
本文件不授权改 `app/`（含 docstring——需 task + 闸）。下一棒：20-spec-audit 或维护者人签（**签收时裁定 D2-a/D2-b**）→ 00 起草 task。

---

## 9. 修订记录

| 日期 | 说明 |
|---|---|
| 2026-10-19 | v0 draft：图谱对拍 5 项差异落盘（flow 重生成 + l2 扩/冻裁定 + docstring 修正 · 建议序 5/5 最后做） |
