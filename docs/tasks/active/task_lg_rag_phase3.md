# Task：LangGraph lg_rag Phase 3（自我纠正 evaluate/rewrite 循环）

> **状态**：active（draft · 待人审）  
> **类型**：feature / Agent 框架落地（LangGraph 旁路 Phase 3）  
> **总纲**：`docs/guides/PLAN-langgraph-agent-framework_v1.md` Phase 3  
> **Detailed Design**：`docs/guides/DESIGN_langgraph-lg-rag-phase3-selfcorrect_v1.md`（draft · 待维护者签收，30 说明书）  
> **前置**：Phase 1（basic/checkpointer/tracing）· Phase 2（router 三路，标注集 100%）  
> **实现仓**：本仓（Open Folder = 本仓根）  
> **分支**：沿用 `task/lg-rag-phase1`（整 PLAN 一次 PR）  
> **无关**：勿与 `task_ops_sync_sender_migration` 混改。

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `lg-rag-phase3` |
| **git_branch** | `task/lg-rag-phase1`（沿用 · 整 PLAN 一次 PR） |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | mock 单测（回环/熔断/失败路径，不连库可绿）；漏召回改善 eval 需真 LLM+库本地手动 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1` |
| **graph_delta** | `docs/_tech_graph/l1/01_modules.md` |
| **graph_delta_note** | `lg_rag` 行备注更新：evaluate/rewrite 回环 + state 新字段；不新增一级模块 |
| **wiki_delta** | `n/a` |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,30` |
| **orchestration** | 单 task；DESIGN 即 30 说明书 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | 2026-08-21 维护者会话签收 DESIGN（无修订），task 为其机械闸化 |
| HG-AUDIT-R1 | approved | 30 | 2026-08-21 维护者会话直签（「签收」按既定流程含执行 30+40 授权）：省略独立 20 轮，DESIGN 当面审签收即视为审查通过（同 Phase 1/2 例） |
| HG-GRAPH-MODULES | approved | 30 | 2026-08-21 已更新 `lg_rag` 行（Phase 3 回环 + state 新字段） |

---

## 背景与目标

Phase 2 三路分流已站稳。Phase 3 加自纠错：rag 路径后经 evaluate 判质量（复用 chain gate 结论，零额外 LLM），low 时 rewrite 改写重试，最多 2 次熔断。PLAN 验收：G37、G39 等漏召回 case 改善 ≥3 条。

**完成态**：

- [x] `LgRagState` 增 `retry_count` / `current_query` / `chain_meta`（老 checkpoint 兼容缺省）
- [x] `evaluate_node`（gate_action 三路映射 + 零命中 kept 缺失判 low）+ `route_by_quality`
- [x] `rewrite_node`（**关键词组合改写**；失败/空/同文→清空 current_query 顶格 retry_count 直接 END；`max_retries=2`）
- [x] `rag_node` 优先取 `current_query` 并写回 `chain_meta`
- [x] router 图回环生效（Langfuse 实证 G56：low→rewrite→rag→high 全链路与 metadata）
- [x] mock 单测 8 个（回环/熔断/失败/同文/缺 meta/direct 旁路）；lg_rag 共 21 passed
- [x] `scripts/lg_rag_retry_eval.py` 三轮实跑（候选池 18 条）；第三轮总改善 4 条
- [x] Langfuse 单树可见回环与 quality/retry/rewrite_to metadata（API 实证）；G-L1 更新 + graph-compile exit 0

---

## 范围（本仓）

`app/ops/lg_rag/`（state/nodes/graph）· `tests/test_lg_rag_retry.py` · `scripts/lg_rag_retry_eval.py` · G-L1 备注。详见 DESIGN §9。

---

## 非范围（Phase 3 明确不做）

- 多查询分解并行检索（另议）
- `retrieved_evidence` 进 state（`chain_meta` 轻量替代）
- SSE / Chat 接入；Chat 图任何改动（冻结）
- 全量 73 条 Golden 回归（另开 task）
- Multi-Agent（Phase 4）
- basic 图改动（冻结对照）

---

## 依赖

| 项 | 说明 |
|---|---|
| Detailed Design | `docs/guides/DESIGN_langgraph-lg-rag-phase3-selfcorrect_v1.md` |
| Phase 1/2 资产 | `app/ops/lg_rag/` 全部 |
| 质量信号 | `ChainResult.meta`（`gate_action/hit_count/kept_count/best_relevance/grade_count`） |
| 漏召回候选池 | `evals/golden/queries_v1.yaml`（`expect_relevance: weak` / 历史 miss，含 G37/G39） |
| LLM | `app.llm.factory`（rewrite 与 router 同档小模型） |
| 编码规范 | `docs/standards/CODING_BACKEND_L2_v1_zh.md` |

---

## 验收标准

- [x] low→rewrite→rag 回环生效；最多 2 次熔断（mock 断言调用次数）
- [x] rag_node 重试时使用改写后 query（mock 断言 chain 入参）
- [x] 漏召回 case 改善 ≥3 条：实测**总改善 4 条**（retry 驱动 2：G49/G56；grader 方差 2：G17/G63），误分流 0。注：G37 三轮均未改善——根因为检索层长句零命中（`readPullRequest` 单词命中 issue 87、整句 0 命中），属 rag 模块另案；grader LLM 方差致单跑对比有噪声
- [x] Phase 1/2 全部单测不回归（21 passed）；ruff 绿
- [x] Langfuse 单树可见回环与 quality/retry metadata（API 实证）
- [x] `git diff master`：chat/graph.py 与 lc_evidence_chain 零改动
- [x] G-L1 更新 + `graph-compile.sh` exit 0

---

## failure_paths

| 触发 | 行为 | 可重试 | 用户可见 |
|---|---|---|---|
| rewrite LLM 失败/空/同文 | 直接 END（不回环、不递增） | Y | 末次答案（可能拒答文案） |
| rag 重试仍 low | 达 2 次熔断 END | Y | 同上 |
| `chain_meta` 缺失 | 视为 high，不回环 | Y | 无感 |
| 改写语义漂移 | eval 观测 + prompt 约束 | — | 答案质量波动 |
| 误改 chain / chat 图 | 验收打回 | N | PR 拒绝 |

---

## 给执行帽必读（本仓）

1. 本 task + DESIGN（30 说明书）
2. `app/ops/lg_rag/`（Phase 1/2 全部）
3. `app/ops/lc_evidence_chain/chain.py` `_meta_span_update` / `types.py`（meta 字段真值 · 只读）
4. `evals/golden/queries_v1.yaml`（漏召回候选池）
5. `docs/standards/CODING_BACKEND_L2_v1_zh.md`

---

## 思考轮

### 思考轮控制

| 字段 | 值 |
|---|---|
| **actual_last_round** | R3 |
| **early_stop** | yes（DESIGN 已详，task 为闸化） |
| **residual_risks** | 改善 ≥3 条依赖候选池实际表现（G37/G39 为复合问，改写未必都命中）；medium 不重试可能漏掉部分可改善 case（对齐 PLAN 流程图的取舍）；中间答案留存使 messages 变长（SSE 接入时再收敛）。 |

### R0
evaluate 复用 chain gate 结论，避免第二次 grader LLM（成本/延迟/一致性三重收益）。

### R1
单查询改写优先于多查询分解（rag_node 单查询入口；分解属非范围）。

### R2
熔断双保险：次数上限 2 + rewrite 失败即终止。

### R3
闸未齐前禁 30。

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-21 | 初版（AI 起草 · 待人审）：DESIGN 同步提交；三闸 pending |
| 2026-08-21 | 维护者签收三闸；30/40 完成：回环+熔断+关键词改写；eval 三轮：首轮暴露 eval 分类 bug（direct 误分流计改善）→ router prompt 收紧 + 标注集扩 34 条 100%；二轮 2 改善（误分流 0）；三轮改关键词策略后 4 改善（retry 驱动 2）；G37 未改善=检索层长句零命中（另案）；Langfuse 实证回环 |
