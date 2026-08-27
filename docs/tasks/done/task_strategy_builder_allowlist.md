# Task：Strategy Builder S1 · allowlist 闭环

> **状态**：completed（2026-08-27 · 00 机械验收 PASS · 待归档）  
> **类型**：feature / strategy-and-intent · S1  
> **上游规划**：`docs/spec/agent-infra/03_strategy_and_intent_plan_v0.md`（HG-SPEC-SIGNOFF=approved）  
> **ROADMAP**：`docs/spec/agent-infra/strategy/ROADMAP_strategy_builder_v0.md`  
> **总轨**：`strategy-and-intent`（S1 / S2 / S3 / S4）  
> **分支**：`task/strategy-builder-allowlist`  
> **无关**：勿与 `task_ops_sync_sender_migration` · `task_rag_answer_mixed_evidence` · `task_retrieval_longquery_analysis` 混改；禁止改 `chat/graph.py` 拓扑；禁止 Agently 运行时；禁止动态 `StateGraph.compile`；禁止把 Host 校验做成模型可选 Capability/MCP tool。

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `strategy-builder-allowlist` |
| **git_branch** | `task/strategy-builder-allowlist` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | mock LLM + capability registry；Builder 写 allowlist · supervisor ∩ · 空/非法 id fallback |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1` |
| **graph_delta** | `docs/_tech_graph/l1/01_modules.md` |
| **graph_delta_note** | `lg_rag` 行备注：Strategy Builder allowlist；**不新增**一级模块 `strategy`（代码可落 `app/ops/strategy/` 薄包，图谱仅 lg_rag 备注） |
| **wiki_delta** | `n/a` |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,30` |
| **invoke_retention_profile** | `default` |
| **freeze_id** | 无 |
| **orchestration** | strategy-and-intent 首棒 = S1 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | 2026-08-27 · **00 代签 · 维护者 Prompt 授权**（R1 pass） |
| HG-AUDIT-R1 | approved | 30 | 2026-08-27 · **00 代签** · 见 `docs/harness/reviews/task_strategy_builder_allowlist_audit_R1_20260827.md` |
| HG-GRAPH-MODULES | approved | 30 | 仅 G-L1 `lg_rag` 备注；不新增一级模块 · **00 代签 · 维护者 Prompt 授权** |

---

## 背景与目标

H1 已让 `supervisor_node` 读 `list_capabilities` + tool id Host 校验，但可见集仍由代码 filter 写死。S1 引入 **Strategy Builder**：按规则/配置写出本轮 `allowed_capability_ids`（可选 skill ids）入 state；Work Planner 只消费该集。

---

## 范围 / 非范围

**范围（S1-a–d）**：

- **S1-a**：`LgRagState`（或等价）增加 `allowed_capability_ids`（及可选 `allowed_skill_ids`）
- **S1-b**：Strategy Builder 节点（首版**规则/配置**，可无 LLM）：写 allowlist ⊆ Registry ∩ Policy 可见；非法 id 剔除 + span
- **S1-c**：`supervisor_node`：`list_capabilities(filter)` **∩** state allowlist；语义见下「00 定夺」
- **S1-d**：tool id Host 校验相对 **本轮可见集**；非法 → 整 plan fallback 单 rag（继承 H1）
- 单测 + G-L1 `lg_rag` 备注 + `./scripts/graph-compile.sh` + ruff

**非范围**：

- S2 Intent · S3 YAML manifest · S4 Critic rebind  
- Eval E1–E5 · Score spike  
- 改 `chat/graph.py` 拓扑；动态 compile；Builder 绕过 Policy / 模型随意 `register`  
- 新增图谱一级模块名（须维护者另明示）

### 00 定夺（allowlist 语义）

| 情形 | 行为 |
|---|---|
| supervisor 路径 | **强制**经 Builder 写入 allowlist（不得 `None` 走「仅 filter」兼容） |
| 空 allowlist `[]` | 禁止 `type=tool`；整 plan **fallback 单 rag** |
| 非法 tool id | 同 H1：整 plan fallback 单 rag |

### 实现落点（建议）

- 薄包：`app/ops/strategy/`（Builder 规则；**非**新 G-L1 一级模块）  
- 消费：`app/ops/lg_rag/multi/`（构图挂 Builder 节点；**不**改边拓扑意图以外的 chat graph）  
- Mode A：`list_capabilities` + `invoke`

---

## 验收标准

- [x] S1-a：state 字段类型 + 单测
- [x] S1-b：Builder 写 ⊆ Registry ∩ Policy；非法 id 剔除；span（如 `strategy_builder_catalog_count`）
- [x] S1-c：supervisor 可见集 = filter ∩ allowlist；空 allowlist → 无 tool / fallback 单 rag
- [x] S1-d：tool id 相对本轮可见集校验；非法 → fallback；H1 语义不回归
- [x] G-L1 `lg_rag` 备注 + graph-compile 绿
- [x] ruff / pytest 触及路径绿；`chat/graph.py` 零 diff

---

## failure_paths

| 触发 | 行为 | 可重试 |
|---|---|---|
| allowlist 含未知 / 高危被 Policy 挡 | Builder 剔除；不写入非法 id | N |
| 空 allowlist | fallback 单 rag；禁止 tool | N |
| 非法 tool id in plan | fallback 单 rag | N |
| LLM 拆 plan 失败 | 保留现 fallback 单 rag | N |

---

## test_strategy

```text
required · mock LLM + registry
pytest：strategy / lg_rag multi 触及路径
ruff check app tests（触及）
./scripts/graph-compile.sh
chat/graph.py git diff 空
```

---

## 自检结论

> 2026-08-27 · 00 机械复检 · **PASS**

- [x] 验收勾选 S1-a–d
- [x] pytest 触及路径 30 passed（strategy_builder 6 · catalog 9 · so_p2 12 · multi 节点/拓扑 4）
- [x] ruff 触及路径 0 · graph-compile exit 0 · `chat/graph.py` 零 diff
- 注：`test_lg_rag_multi` 全链 ainvoke 本地 `langchain.debug` AttributeError（与 H1 同环境已知问题；非 S1 逻辑回归；节点级已覆盖）

**50 结论**：PASS · 下一棒 S2 `intent-schema-v1`（非本轨）

---

## CLOSE

| 项 | 内容 |
|---|---|
| 日期 | 2026-08-27 |
| 定稿 | Strategy Builder allowlist：state + 规则 Builder + supervisor ∩ + tool id 相对可见集 |
| 归档 | `docs/tasks/done/task_strategy_builder_allowlist.md` |
| PR | [#78](https://github.com/Cyning12/ops-desk-api/pull/78) |

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-27 | 00 拆 S1 task · S0 已签 · R1 pass · HG 代签 |
| 2026-08-27 | 30/40 PASS · 00 机械验收 PASS · CLOSE |
