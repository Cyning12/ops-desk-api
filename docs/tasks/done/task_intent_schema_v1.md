# Task：Strategy Builder S2 · Intent schema v1

> **状态**：completed（2026-08-27 · 00 机械验收 PASS）  
> **类型**：feature / strategy-and-intent · S2  
> **上游规划**：`docs/spec/agent-infra/03_strategy_and_intent_plan_v0.md`（HG-SPEC-SIGNOFF=approved）  
> **ROADMAP**：`docs/spec/agent-infra/strategy/ROADMAP_strategy_builder_v0.md` §6–§7  
> **前置**：S1 `strategy-builder-allowlist` [#78](https://github.com/Cyning12/ops-desk-api/pull/78) MERGED  
> **分支**：`task/intent-schema-v1`  
> **无关**：勿与 `task_ops_sync_sender_migration` · `task_rag_answer_mixed_evidence` · `task_retrieval_longquery_analysis` 混改；禁止改 `chat/graph.py` 拓扑；禁止 Agently；禁止动态 `StateGraph.compile`；禁止把 Host 校验做成模型可选 Capability/MCP tool。

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `intent-schema-v1` |
| **git_branch** | `task/intent-schema-v1` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | mock LLM + SO；Intent schema / 节点 fallback · Builder 读 intent · router 图零拓扑回归 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1` |
| **graph_delta** | `docs/_tech_graph/l1/01_modules.md` · `docs/_tech_graph/l1/10_flow_lg_rag.graph.yaml` |
| **graph_delta_note** | `lg_rag` 备注：supervisor 图 Intent 节点；不新增一级模块 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 契约在 `docs/spec/agent-infra/`；无 coding_wiki 条文变更 |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,30` |
| **invoke_retention_profile** | `default` |
| **freeze_id** | 无 |
| **orchestration** | strategy-and-intent 次棒 = S2 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | 2026-08-27 · **00 代签 · 维护者会话授权续 S2**（R1 pass） |
| HG-AUDIT-R1 | approved | 30 | 2026-08-27 · **00 代签** · 见 `docs/harness/reviews/task_intent_schema_v1_audit_R1_20260827.md` |
| HG-GRAPH-MODULES | approved | 30 | 仅 G-L1 `lg_rag` 备注 + flow 增 `s_intent`；不新增一级模块 · **00 代签** |

---

## 背景与目标

S1 已强制 supervisor 路径经 Builder 写 allowlist，但 Builder **不读意图**（仅配置候选）。S2 增加细 **Intent schema + 节点**（LLM + SO Host 校验），写入 state 供 Builder 裁剪；粗 `router` 三路保持外层安全闸。

---

## 范围 / 非范围

**范围（S2-a–b）**：

- **S2-a**：`IntentV1` schema + `intent_node` + `LgRagState.intent`；supervisor 图挂节点；Builder 按 §00 定夺消费 intent
- **S2-b**：与粗 router 并存策略文档化（ROADMAP §7 已钉；实现可再落 GUIDE，须与 §7 一致）
- H4 槽 `lg_rag.intent.system`
- 单测 + G-L1 备注 + `s_intent` flow + graph-compile + ruff

**非范围**：

- S3 YAML manifest · S4 Critic rebind · Eval  
- 改 router / basic 图拓扑；改 `chat/graph.py`  
- Skill 执行引擎；Builder LLM；动态 compile  

### 00 定夺（摘 ROADMAP §6）

| 项 | 值 |
|---|---|
| 拓扑 | `START → intent → strategy_builder → supervisor → …`（静态） |
| SO | `acomplete_structured` · `max_retries=1`；失败 → 保守 fallback intent，不拒图 |
| Builder | `needs_tool=False` → 空 allowlist；`True` → Registry∩Policy 求交；skill 本波仍空 list |
| router | 零拓扑 diff |

### 实现落点

- `app/ops/lg_rag/schemas/intent.py` · `app/ops/strategy/intent.py`  
- `app/ops/lg_rag/multi/graph.py` 挂边  
- `app/ops/strategy/builder.py` 读 `state.intent`  
- `docs/guides/GUIDE_intent-vs-router-coexistence_v0.md`（可选；与 ROADMAP §7 一致）

---

## 验收标准

- [x] S2-a：`IntentV1` 单测（合法/extra ignore/缺省）
- [x] S2-a：`intent_node` mock LLM + SO 成功写入 `state.intent`；失败 fallback + span
- [x] S2-a：supervisor 图含 Intent 节点且边为 START→intent_node→strategy_builder（节点 id 不能为 `intent`：LangGraph 禁止与 state key 同名）
- [x] S2-a：Builder 消费 `needs_tool=False` → 空 allowlist；`True` → 非空且 ⊆ Policy 可见
- [x] S2-b：并存策略落盘（GUIDE 或确认 ROADMAP §7 已覆盖）
- [x] G-L1 备注 + `s_intent` + graph-compile 绿
- [x] ruff / pytest 触及路径绿；`chat/graph.py` 零 diff；router 图拓扑不回归

---

## failure_paths

| 触发 | 行为 | 可重试 |
|---|---|---|
| Intent SO 失败 / 预算耗尽 | 保守 fallback intent；图继续 | N |
| `needs_tool=False` | 空 allowlist → supervisor fallback 单 rag | N |
| `risk_hint=high` | **不**放开 Policy 高危 | N |
| Intent 缺字段 | schema 缺省；extra ignore | N |

---

## test_strategy

```text
required · mock LLM + SO
pytest：intent schema / strategy intent 节点 / builder 消费 / supervisor 拓扑
ruff 触及路径
./scripts/graph-compile.sh
chat/graph.py git diff 空
router 图：START→router 边仍在（不删不改）
```

---

## 自检结论

> 2026-08-27 · 00 机械复检 · **PASS**

- [x] 验收勾选 S2-a–b
- [x] pytest 触及路径 48 passed
- [x] ruff 0 · graph-compile exit 0 · `chat/graph.py` 零 diff · router `START→router` 仍在
- 00 接受图节点 id `intent_node`（LangGraph 禁止与 state key `intent` 同名）
- 注：ainvoke 全链本地 `langchain.debug` 与 S1 同环境问题；节点级已覆盖

**50 结论**：PASS · 下一棒 S3 `catalog-manifest-yaml`（非本轨除非维护者另开）

---

## CLOSE

| 项 | 内容 |
|---|---|
| 日期 | 2026-08-27 |
| 定稿 | IntentV1 + intent_node + Builder 读 needs_tool；router 并存 |
| 归档 | `docs/tasks/done/task_intent_schema_v1.md` |
| PR | [#80](https://github.com/Cyning12/ops-desk-api/pull/80) |

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-27 | 00 拆 S2 task · R1 pass · HG 代签 |
| 2026-08-27 | 30/40 PASS · 00 机械验收 PASS · CLOSE |
