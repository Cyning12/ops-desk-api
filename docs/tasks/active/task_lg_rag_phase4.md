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
| HG-GRAPH-MODULES | pending | 30 | 随 30 更新 `lg_rag` 行备注后签 |

---

## 背景与目标

PLAN 收官阶段。Supervisor 拆解复合问题 → 分派 rag/extract/tool 专业 Agent → Aggregator 综合结构化答案。rag 子任务复用 Phase 2/3 router 图全部能力。

**完成态**：

- [ ] `LgRagState` 增 `subtasks` / `subtask_results`（后者 `add` reducer）
- [ ] `supervisor_node`：LLM 拆解 ≤4 子任务；失败/非法 → fallback 单 rag（宁退化不失败）
- [ ] `rag_subtask_node`（内部调 router 图子图，输入隔离）· `info_extract_node`（dates/versions/people JSON，非法容错）· `tool_exec_node`（Mock 注册表，未知工具容错）
- [ ] `aggregator_node`：分节结构化答案 + 来源标注；中间结果不进 messages
- [ ] dispatch 条件边：按序取子任务 → 按 type 分派 → 耗尽进 aggregate；空 subtasks 防死循环
- [ ] mock 单测全链 + 容错路径；Phase 1–3 共 21 单测不回归
- [ ] 3–5 条复合 query 实跑演示（拆分合理性 + 覆盖面人工核，记 task）
- [ ] Langfuse 单树可见子任务序；G-L1 更新 + graph-compile

---

## 范围 / 非范围

**范围**：`app/ops/lg_rag/`（子包 `multi/`：supervisor/agents/graph）· `tests/test_lg_rag_multi.py` · G-L1 备注。

**非范围**：Send 并行 fan-out · HITL/interrupt · Store 长期记忆 · 真实外部 API 工具 · SSE/Chat 接入 · 全量 73 Golden · 检索层零命中修复（已另立分析 task）。

---

## 验收标准

- [ ] 复合问题拆解 → 分派 → 综合全链走通（mock + 实跑演示）
- [ ] cap=4 截断 / 拆解失败 fallback / extract 非法 JSON / 未知 tool / 空 subtasks 防死循环（mock 覆盖）
- [ ] 三图并存：Phase 1–3 单测不回归；ruff 绿
- [ ] Langfuse 单树可见子任务序（API 实证）
- [ ] `git diff master`：chat/graph.py 与 lc_evidence_chain 零改动
- [ ] G-L1 更新 + `graph-compile.sh` exit 0

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

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-21 | 初版（AI 起草 · 待人审）：DESIGN 同步提交；三闸 pending |
| 2026-08-21 | 维护者签收并指定身份模式：父窗固定 00（编排/验收），30/40 实际执行交子 agent |
