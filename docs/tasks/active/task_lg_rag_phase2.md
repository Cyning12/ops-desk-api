# Task：LangGraph lg_rag Phase 2（Router Agent 意图路由）

> **状态**：active（draft · 待人审）  
> **类型**：feature / Agent 框架落地（LangGraph 旁路 Phase 2）  
> **总纲**：`docs/guides/PLAN-langgraph-agent-framework_v1.md` Phase 2  
> **Detailed Design**：`docs/guides/DESIGN_langgraph-lg-rag-phase2-router_v1.md`（**approved 2026-08-19 维护者签收**，本 task 的执行真值说明书）  
> **前置**：Phase 1 已完成（state / rag_node / graph / checkpointer / tracing / smoke / 单测）  
> **实现仓**：本仓（Open Folder = 本仓根）  
> **分支**：沿用 `task/lg-rag-phase1`（维护者裁定：整个 PLAN 完成后才开 PR，各 Phase 在同一分支累积）  
> **无关**：勿与 `task_ops_sync_sender_migration` 混改。

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `lg-rag-phase2` |
| **git_branch** | `task/lg-rag-phase1`（沿用 · 整 PLAN 一次 PR） |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | mock LLM 的分流/兜底单测（不连库/LLM 可绿）；router 标注集准确率脚本需真 LLM 本地手动；golden 抽样回归手动 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1` |
| **graph_delta** | `docs/_tech_graph/l1/01_modules.md` |
| **graph_delta_note** | `lg_rag` 行备注更新：router 三路拓扑（direct/rag/refuse）+ route 字段；不新增一级模块 |
| **wiki_delta** | `n/a` |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,30` |
| **orchestration** | 单 task；DESIGN 即 30 说明书 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | 2026-08-19 维护者会话签收 DESIGN（无修订），task 为其机械闸化 |
| HG-AUDIT-R1 | pending | 30 | 维护者签（或省略独立 20 轮注明理由，同 Phase 1 例） |
| HG-GRAPH-MODULES | pending | 30 | 随 30 更新 `lg_rag` 行备注后签 |

---

## 背景与目标

Phase 1 最小图（START→rag→END）已站稳。Phase 2 加意图路由：闲聊不触发检索、越界固定拒答、技术问答走原黑盒链。Track A：router 落 `lg_rag`，Chat 图冻结。

**完成态**：

- [ ] `LgRagState` 增 `route: str`（`rag|direct|refuse`；缺省 `rag`，老 checkpoint 兼容）
- [ ] `router_node`：`#\d+` 规则快路径→rag；LLM 三分类（低温度、JSON 白名单）；异常/超时/非法输出 fallback=rag + warning
- [ ] `direct_answer_node`（LLM 直答闲聊，不检索）· `refuse_node`（固定拒答文案，与 Chat `REFUSAL_TEXT` 同款）
- [ ] `build_router_agent()` / `ainvoke_router_agent()`；`build_basic_agent` 保留作对照（Phase 1 单测全绿不回归）
- [ ] 标注集 `evals/router/labeled_router_v1.yaml`（~30 条）+ 准确率脚本 ≥90%
- [ ] Langfuse 单 trace 树含 router 节点与 route/fallback metadata
- [ ] smoke `--router`；G-L1 备注更新 + graph-compile；chat/graph.py 与 lc_evidence_chain 零改动

---

## 范围（本仓）

1. `state.py`：`LgRagState` 增 `route` 字段（无 reducer，写回覆盖）。
2. `nodes.py`：`router_node` / `direct_answer_node` / `refuse_node` / `route_by_route`；router 决策写 span metadata（route 值、是否 fallback、LLM 原始输出截断）。
3. `graph.py`：`build_router_agent` + `ainvoke_router_agent`（复用 checkpointer / propagate_attributes 注入）；条件边 `route_by_route` 用 `state.get("route") or "rag"`。
4. `__init__.py` export 增补；`scripts/lg_rag_smoke.py` 加 `--router`。
5. `evals/router/labeled_router_v1.yaml`（技术 15 / 闲聊 10 / 拒答 5）+ 准确率脚本（`scripts/router_accuracy.py` 或 evals 内）。
6. mock 单测：三路分流、#快路径、LLM 异常/非法 fallback、老 checkpoint 兼容、续写不回归。
7. G-L1 `lg_rag` 行备注更新 + graph-compile。

---

## 非范围（Phase 2 明确不做）

- evaluate / rewrite 循环、`retry_count`（Phase 3）
- 挂 `POST /api/ops/chat/stream` 或任何 SSE 契约改动
- overview 专用路径（lg_rag 统一走 rag）
- Chat 规则路由（`intent_node`）任何改动（冻结）
- `retrieved_evidence` / `gate_action` 进 state（留 chain 黑盒）
- 全量 73 条 Golden 回归（另开 task）
- `build_basic_agent` 下线（保留对照，default 切换另议）

---

## 依赖

| 项 | 说明 |
|---|---|
| Detailed Design | `docs/guides/DESIGN_langgraph-lg-rag-phase2-router_v1.md`（approved） |
| Phase 1 资产 | `app/ops/lg_rag/`（state/nodes/graph/checkpointer） |
| LLM | `app.llm.factory`（与 grader 同档小模型） |
| 拒答文案 | Chat `REFUSAL_TEXT`（复用同款，防漂移） |
| tracing | `app/ops/tracing` + Phase 1 `propagate_attributes` 注入 |
| 编码规范 | `docs/standards/CODING_BACKEND_L2_v1_zh.md` |

---

## 实施步骤（建议 · 30）

按 DESIGN §9：state → nodes → graph → export/smoke → 标注集+准确率脚本 → mock 单测 → G-L1。

---

## 验收标准

- [ ] 三路分流拓扑生效；闲聊 query 不触发检索（mock 断言 `ainvoke_evidence_answer` 未被调用）
- [ ] `#\d+` 快路径直进 rag；LLM 故障/非法输出 fallback=rag（warning 日志）
- [ ] router 标注集准确率 ≥ 90%（真 LLM 本地跑，结果记入 task）
- [ ] `build_basic_agent` 不回归（Phase 1 + Phase 2 单测全绿）
- [ ] Langfuse 单 trace 树含 router 节点与 route metadata（API 实证）
- [ ] `git diff master -- app/ops/chat/graph.py` 为空；`lc_evidence_chain` 零改动
- [ ] ruff + pytest 触及路径绿；G-L1 更新 + `graph-compile.sh` exit 0

---

## failure_paths

| 触发 | 行为 | 可重试 | 用户可见 |
|---|---|---|---|
| router LLM 异常/超时 | fallback `rag` + warning | Y | 无感（走检索主路径） |
| router 输出非法 JSON/越界值 | 同上 | Y | 无感 |
| direct_answer LLM 失败 | 异常上抛（与 rag_node 同语义） | Y | 调用方异常 |
| 老 checkpoint 无 `route` 键 | 条件边缺省 `rag` | Y | 无感 |
| 误改 chat/graph 或 chain 内部 | 验收打回 | N | PR 拒绝 |

---

## 给执行帽必读（本仓）

1. 本 task + `docs/guides/DESIGN_langgraph-lg-rag-phase2-router_v1.md`（30 说明书）
2. `app/ops/lg_rag/`（Phase 1 全部）
3. `app/ops/chat/nodes.py` `intent_node` / `REFUSAL_TEXT`（语义对照 · 只读）
4. `app/ops/chat/graph.py`（冻结 · 只读）
5. `docs/standards/CODING_BACKEND_L2_v1_zh.md`

---

## 思考轮

### 思考轮控制

| 字段 | 值 |
|---|---|
| **actual_last_round** | R3 |
| **early_stop** | yes（DESIGN 已审签收，本表为机械闸化） |
| **residual_risks** | LLM 路由准确率依赖标注集代表性（30 条偏小，后续可扩）；direct/refuse 边界case 需标注集覆盖；双轨期 Chat 与 lg_rag 分类口径靠 §3 映射表锚定。 |

### R0
DESIGN 已含 Track A 决策与全部实施细节，本 task 不重复论证。

### R1
fallback=rag（宁检索勿错杀）为已定调原则；拒答文案复用 Chat 同款。

### R2
basic/router 双图并存，default 切换与 Chat 接回均另议。

### R3
闸未齐前禁 30。

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-19 | 初版（AI 起草）：DESIGN 已维护者签收；HG-TASK-DRAFT 随签收转 approved，余两闸待人审 |
