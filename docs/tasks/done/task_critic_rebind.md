# Task：Strategy Builder S4 · Critic rebind

> **状态**：completed（2026-08-28 · 00 机械验收 PASS）  
> **类型**：feature / strategy-and-intent · S4  
> **上游规划**：`docs/spec/agent-infra/03_strategy_and_intent_plan_v0.md` §2 / §4  
> **ROADMAP**：`docs/spec/agent-infra/strategy/ROADMAP_strategy_builder_v0.md` §2 S4-a–c · §9  
> **前置**：S1 [#78](https://github.com/Cyning12/ops-desk-api/pull/78) · S2 [#80](https://github.com/Cyning12/ops-desk-api/pull/80) · S3 [#82](https://github.com/Cyning12/ops-desk-api/pull/82) MERGED  
> **分支**：`task/critic-rebind`  
> **无关**：勿与 `task_ops_sync_sender_migration` · `task_rag_answer_mixed_evidence` · `task_retrieval_longquery_analysis` 混改；禁止改 `chat/graph.py` 拓扑；禁止 Agently；禁止动态 compile；禁止把 Host 校验做成模型可选 tool；禁止无预算全图 ReAct。

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `critic-rebind` |
| **git_branch** | `task/critic-rebind` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 规则 stub + 条件边；预算熔断无死循环；mock 不连外网 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1` |
| **graph_delta** | `docs/_tech_graph/l1/01_modules.md` · `docs/_tech_graph/l1/10_flow_lg_rag.graph.yaml` |
| **graph_delta_note** | `lg_rag` 备注：supervisor 图 Critic 条件边；不新增一级模块 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 契约在 spec/agent-infra；无 coding_wiki 条文变更 |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,30` |
| **invoke_retention_profile** | `default` |
| **freeze_id** | 无 |
| **orchestration** | strategy-and-intent 第四棒 = S4 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | 2026-08-28 · **00 代签 · 维护者会话授权续 S4**（R1 pass） |
| HG-AUDIT-R1 | approved | 30 | 2026-08-28 · **00 代签** · 见 `docs/harness/reviews/task_critic_rebind_audit_R1_20260828.md` |
| HG-GRAPH-MODULES | approved | 30 | 仅 G-L1 `lg_rag` 备注 + `s_critic`；不新增一级模块 · **00 代签** |

---

## 背景与目标

S1–S3 已有 Intent → Builder → Planner → workers → aggregator → END。S4 在 aggregator 后加 **Critic 规则 stub** 与有预算条件边：同 catalog 重拆 / 回 Builder rebind / 耗尽 END。

---

## 范围 / 非范围

**范围（S4-a–c）**：

- **S4-a**：`critic_node` 规则 stub；可选 `CriticVerdict` schema（不必 LLM）
- **S4-b**：`aggregator → critic_node`；条件边 pass/end→END、retry_planner→supervisor、rebind→strategy_builder；预算 1+1
- **S4-c**：span `critic_outcome` · `inner_retry_count` · `rebinding_count`
- 回环重置：`subtasks=[]`；`subtask_results` 的 `None`=清空
- 单测无死循环 + G-L1 + graph-compile + ruff

**非范围**：

- LLM Critic / intent→② 回环  
- 无预算 ReAct；Builder 自动扩权绕过 Policy  
- 改 `chat/graph.py` / router / basic 拓扑  
- Eval · Skill 引擎 · 动态 compile  

### 00 定夺（摘 ROADMAP §9）

| 项 | 值 |
|---|---|
| 节点 | `critic_node`；state `critic_verdict` / `inner_retry_count` / `rebinding_count` |
| 预算 | `MAX_INNER_RETRIES=1` · `MAX_REBINDING=1` |
| 规则 | 无 error→pass；error+空 allowlist→rebind；error+非空→retry_planner；超预算→end |
| 落点 | `app/ops/strategy/critic.py` + `lg_rag/multi/graph.py` + `LgRagState` reducer |

---

## 验收标准

- [x] S4-a：规则 stub 写入 `critic_verdict`；无 LLM 依赖主路径
- [x] S4-b：图边 `aggregator→critic_node`；retry→supervisor；rebind→strategy_builder；pass/end→END
- [x] S4-b：强制一直 retry/rebind 时在预算内 END（无死循环单测）
- [x] S4-b：回环后 `subtasks` 空且 `subtask_results` 可被清空（reducer）
- [x] S4-c：span 字段落地
- [x] G-L1 `lg_rag` 备注 + `s_critic` + graph-compile
- [x] ruff / pytest 触及路径绿；`chat/graph.py` 零 diff；router/basic 拓扑不回归

---

## failure_paths

| 触发 | 行为 | 可重试 |
|---|---|---|
| 子任务含 error、allowlist 非空 | retry_planner（未超 inner 预算） | 至多 1 次 |
| 子任务含 error、allowlist 空 | rebind（未超 rebind 预算） | 至多 1 次 |
| 已达 MAX_* | END · `critic_outcome=end` | N |
| 无 error | pass → END | N |

---

## test_strategy

```text
required · 规则 stub · 不连外网
pytest：critic 规则 / 图边 / 预算熔断 / reducer 重置
ruff 触及路径
./scripts/graph-compile.sh
chat/graph.py 0 diff
```

---

## 自检结论

> 2026-08-28 · 00 机械复检 · **PASS**

- [x] 验收勾选 S4-a–c
- [x] pytest 绿集 **29 passed**（规则/边/reducer/预算熔断/span/intent/builder/multi 非 ainvoke）
- [x] ruff 0 · graph-compile exit 0 · `chat/graph.py` 零 diff
- [x] 本地 ainvoke 全链仍因 `langchain.debug` AttributeError 不可跑（与 S1–S3 同环境；交 CI）

**50 结论**：PASS · 策略轨 S1–S4 实现闭环；Eval 轨不自动开工

---

## CLOSE

| 项 | 内容 |
|---|---|
| 日期 | 2026-08-28 |
| 定稿 | supervisor 图 aggregator→critic_node；规则 stub；预算 1+1；reducer None=清空 |
| 归档 | `docs/tasks/done/task_critic_rebind.md` |
| PR | 待开 |

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-28 | 00 拆 S4 task · R1 pass · HG 代签 |
| 2026-08-28 | 30/40 PASS · 00 机械验收 PASS · CLOSE |
