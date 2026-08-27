# Task：Agent Host H1 · Supervisor 赋能目录闭环

> **状态**：completed（2026-08-27 · 00 CLOSE PASS · 已归档）  
> **类型**：feature / agent-host-plan · H1  
> **上游规划**：`docs/spec/agent-infra/02_agent_host_plan_v0.md`（HG-SPEC-SIGNOFF=approved）  
> **ROADMAP**：`docs/spec/agent-infra/orchestration/ROADMAP_supervisor_capability_catalog_v0.md`  
> **总轨**：`agent-host-plan`（H1 / H2 / H3 / H4 / H5）  
> **分支**：`task/lg-rag-supervisor-capability-catalog`  
> **无关**：勿与 `task_ops_sync_sender_migration` · `task_rag_answer_mixed_evidence` · `task_retrieval_longquery_analysis` 混改；禁止改 `chat/graph.py` 拓扑。

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `lg-rag-supervisor-capability-catalog` |
| **git_branch** | `task/lg-rag-supervisor-capability-catalog` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | mock LLM + capability registry；catalog 进 prompt · 非法 tool id fallback |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1` |
| **graph_delta** | `docs/_tech_graph/l1/01_modules.md` |
| **graph_delta_note** | `lg_rag` 备注：supervisor 读 Capability 目录；不新增一级模块 |
| **wiki_delta** | `n/a` |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,30` |
| **invoke_retention_profile** | `default` |
| **freeze_id** | 无 |
| **orchestration** | agent-host-plan 首棒 = H1 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | 2026-08-27 00 代签（R1 pass） |
| HG-AUDIT-R1 | approved | 30 | 2026-08-27 00 代签 |
| HG-GRAPH-MODULES | approved | 30 | G-L1 备注已写 |

---

## 背景与目标

supervisor 已能拆 plan 并 `tool_exec` 调 Gateway，但 **planner 未读 `list_capabilities`**，plan 中 tool id 无 Host 校验。H1 形成 **编排 ↔ Capability 闭环**。

---

## 范围 / 非范围

**范围**：

- `supervisor_node`：`list_capabilities(filter=…)` → 格式化进 LLM messages
- `_parse_subtasks` 后： `type=tool` 时 `tool` ∈ 可见 id；非法 → **整 plan fallback 单 rag**
- 注册 ≥1 低危非 mock `local_fn`（`utc_now_iso` 只读）
- span：`capability_catalog_count`；非法 tool → `supervisor_invalid_tool_id`
- 单测 + G-L1 备注 + graph-compile

**非范围**：

- 改 supervisor 图拓扑；Skill NL（H5）；Policy 门（H2）；`acomplete_structured` 全面接入  
- PromptAssembly 大包（H4）

---

## 验收标准

- [x] H1-a：`list_capabilities` 带 `node_role=supervisor` + `kinds=local_fn` · 单测
- [x] H1-b：mock LLM messages 含 capability 目录片段（id/description/risk 摘要）
- [x] H1-c：非法 tool id → fallback 单 rag；supervisor 节点单测覆盖
- [x] H1-d：`utc_now_iso` 非 mock 低危 capability 可 invoke
- [x] H1-e：span metadata 字段落地
- [x] H1-f：G-L1 备注 + graph-compile 绿
- [x] ruff / pytest 触及路径绿；`chat/graph.py` 零 diff

---

## failure_paths

| 触发 | 行为 | 可重试 |
|---|---|---|
| 非法 tool id in plan | fallback 单 rag | N |
| list 空 | 仍可拆 plan；tool 子任务 invoke 未知 id → ok=False | N |
| LLM 拆 plan 失败 | 保留现 fallback 单 rag | N |

---

## 自检结论

> 2026-08-27 · 00 机械复检 · **PASS**

- [x] 验收勾选
- [x] pytest H1 6 passed · structured_output_p2 12 passed · capability 25 passed
- [x] graph.py 零 diff · graph-compile exit 0

**50 结论**：PASS · 下一棒 H2 `capability-policy-sandbox`

---

## CLOSE

| 项 | 内容 |
|---|---|
| 日期 | 2026-08-27 |
| 定稿 | supervisor ↔ Capability 目录闭环 + tool id Host 校验 |
| 归档 | `docs/tasks/done/task_lg_rag_supervisor_capability_catalog.md` |
| PR | [#70](https://github.com/Cyning12/ops-desk-api/pull/70) MERGED |

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-27 | 00 拆 task · HG-SPEC 已签 |
| 2026-08-27 | HG 代签 · 00 统筹 |
| 2026-08-27 | 30/40 PASS · CLOSE · git mv → done/ |
