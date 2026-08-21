# Task：LangGraph lg_rag Phase 4（Multi-Agent · Supervisor 协作）

> **状态**：active（draft · 待人审）  
> **类型**：feature / Agent 框架落地（LangGraph 旁路 Phase 4 · PLAN 收官）  
> **总纲**：`docs/guides/PLAN-langgraph-agent-framework_v1.md` Phase 4  
> **Detailed Design**：`docs/guides/DESIGN_langgraph-lg-rag-phase4-multiagent_v1.md`（draft · 待签收，30 说明书）  
> **前置**：Phase 1–3 全部完成（50 PASS / 验收裁定通过）  
> **实现仓**：本仓  
> **分支**：沿用 `task/lg-rag-phase1`（整 PLAN 一次 PR）  
> **无关**：勿与 `task_ops_sync_sender_migration` / `task_retrieval_longquery_analysis` 混改。

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `lg-rag-phase4` |
| **git_branch** | `task/lg-rag-phase1`（沿用 · 整 PLAN 一次 PR） |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | mock 三处 LLM + chain 的全链单测（不连库可绿）；复合 query 实跑演示需真 LLM 本地手动 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1` |
| **graph_delta** | `docs/_tech_graph/l1/01_modules.md` |
| **graph_delta_note** | `lg_rag` 行备注更新：supervisor 多智能体拓扑 + state 新字段；不新增一级模块 |
| **wiki_delta** | `n/a` |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,30` |
| **orchestration** | 单 task；DESIGN 即 30 说明书 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | 2026-08-21 维护者会话签收 DESIGN（无修订），task 为其机械闸化 |
| HG-AUDIT-R1 | approved | 30 | 2026-08-21 维护者会话直签（「签收」+ 指定 00 编排模式）：省略独立 20 轮，DESIGN 当面审签收即视为审查通过（同前例） |
| HG-GRAPH-MODULES | approved | 30 | 2026-08-21 已更新 `lg_rag` 行（Phase 3/4 拓扑）并加人签记录 |

---

## 背景与目标

PLAN 收官阶段。Supervisor 拆解复合问题 → 分派 rag/extract/tool 专业 Agent → Aggregator 综合结构化答案。rag 子任务复用 Phase 2/3 router 图全部能力。

**完成态**：

- [x] `LgRagState` 增 `subtasks` / `subtask_results`（后者 `add` reducer）
- [x] `supervisor_node`：LLM 拆解 ≤4 子任务（cap 截断）；失败/非法 → fallback 单 rag；40 实证 fallback=false 未误触发
- [x] 三 agent 节点全部实现并经 40 实跑（Q1 rag+tool、Q3 双 tool、Q2 双 rag、Q4 单 rag）
- [x] `aggregator_node`：分节结构化答案 + 来源标注（40 实证对 mock 数据不一致还主动批判标注）；中间结果不进 messages
- [x] dispatch 条件边（len(results) 推进索引）；空 subtasks 防死循环（mock 覆盖）
- [x] mock 单测 9 个（全链/cap/fallback/容错/防死循环/异常继续/三图并存）；四文件合跑 30 passed（21 不回归）
- [x] 4 条复合 query 实跑（40 报告）：拆分类型分派全对、覆盖两侧、无异常/死循环/超时
- [x] Langfuse 单树（40+00 双重实证：supervisor→rag_subtask[嵌套 router 全链]→tool_exec→aggregator，决策 metadata 落盘）；G-L1 更新 + graph-compile exit 0

---

## 范围 / 非范围

**范围**：`app/ops/lg_rag/`（子包 `multi/`：supervisor/agents/graph）· `tests/test_lg_rag_multi.py` · G-L1 备注。

**非范围**：Send 并行 fan-out · HITL/interrupt · Store 长期记忆 · 真实外部 API 工具 · SSE/Chat 接入 · 全量 73 Golden · 检索层零命中修复（已另立分析 task）。

---

## 验收标准

- [x] 复合问题拆解 → 分派 → 综合全链走通（mock 9 个 + 40 四条实跑）
- [x] cap=4 / fallback / 非法 JSON / 未知 tool / 防死循环（mock 全覆盖）
- [x] 三图并存：30 passed 不回归；ruff 绿；全量 pytest 231 passed / 3 failed（既有环境缺表，与本改动无关）
- [x] Langfuse 单树可见子任务序（40 报告观测树 + 00 抽验 4 条 trace 均在）
- [x] `git diff master`：chat/graph.py 与 lc_evidence_chain 零改动
- [x] G-L1 更新 + `graph-compile.sh` exit 0

---

## failure_paths

| 触发 | 行为 | 可重试 |
|---|---|---|
| 拆解 LLM 失败/非法 | fallback 单 rag 子任务 | Y |
| 子任务执行异常 | 记录错误结果，继续后续 | Y |
| extract JSON 非法 | 空结构 + warning | Y |
| 未知 tool | 错误结果记录 | Y |
| aggregator LLM 失败 | 异常上抛 | Y |
| 误改 chain / chat 图 | 验收打回 | N |

---

## 思考轮

### 思考轮控制

| 字段 | 值 |
|---|---|
| **actual_last_round** | R2 |
| **early_stop** | yes（DESIGN 已详，task 为闸化） |
| **residual_risks** | 顺序 fan-out 延迟累加（每子任务一次 rag/LLM）；LLM 拆解稳定性（fallback 兜底）；演示集小（3–5 条）仅作定性验收。 |

### R0
三图并存，supervisor 不动 router/basic。

### R1
子任务结果走 subtask_results reducer，不进 messages（吸取 P3 中间答案膨胀教训）。

### R2
Mock 工具先行，真实 API 另议；并行 Send 另议。

---

## 自检结论（50 · 00 验收）

> 2026-08-21 · 00（父窗）验收：30 子 agent 实施 + 40 子 agent 真机验证，00 机械复检 · **PASS**

- [x] 30 产出 00 复检：ruff 绿 / 30 passed / 禁区零 diff / graph.py 拓扑与 tracing 复用抽读合格
- [x] 40 真机验证 PASS：4 条复合 query 拆分全对、无异常/死循环/超时；全量 231 passed 无新增失败
- [x] 00 抽验 Langfuse：p4-40-q1~q4 四条 trace 均在（name=lg-rag, env=dev）
- [x] G-L1 更新 + graph-compile exit 0
- [ ] （遗留观察，不挡）顺序 fan-out 多 rag 子任务复合 query 延迟可达 ~250s（DESIGN 既定取舍，并行 Send 另议）；mock 工具罐头数据与入参无关（mock 设计）；Q1 rag 拒答属知识库覆盖问题（与检索层分析 task 关联）

**50 结论：PASS · PLAN Phase 4 完成，四个 Phase 全部收官（Golden 73 全量回归与检索层分析各由独立 task 承接）**

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-21 | 初版（AI 起草 · 待人审）：DESIGN 同步提交；三闸 pending |
| 2026-08-21 | 维护者签收并指定身份模式：父窗固定 00（编排/验收），30/40 实际执行交子 agent |
| 2026-08-21 | 30 子 agent 实施完成（state 两字段 + multi/ 子包 + 9 mock 单测；30 passed）；00 复检过；G-L1 更新 |
| 2026-08-21 | 40 子 agent 真机验证 PASS（4 条复合 query + Langfuse 单树 + 全量回归）；00 50 验收 PASS；HG-GRAPH-MODULES 签 |
