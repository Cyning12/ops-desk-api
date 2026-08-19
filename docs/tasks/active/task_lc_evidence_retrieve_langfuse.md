# Task：lc_evidence retrieve 内 embed/rerank 补 Langfuse generation

> **状态**：active（闸已签 · 交子 agent 30+40）  
> **类型**：observability / bugfix  
> **上游**：`docs/tasks/done/task_lc_evidence_langfuse_tracing.md`（旁路根 span + grade/answer generation 已合入）  
> **关联实现**：`app/ops/lc_evidence_chain/retrieve.py` · `app/ops/tracing.py` · 先例 `answer.py` / `grader.py` 的 `trace_span(..., run_type="llm")`  
> **分支**：`task/lc-evidence-retrieve-langfuse`  
> **编排**：闸齐 → 子 agent 30+40 → 父窗验收 → CLOSE / PR / merge master  
> **无关**：勿与 active `ops-sync-sender-migration`、暂存的 `lg_rag` WIP、Langfuse SDK v4 迁移（`PRIORITY_DEFERRED` DEF-001）混改。

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `lc-evidence-retrieve-langfuse` |
| **git_branch** | `task/lc-evidence-retrieve-langfuse` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | pytest：mock `trace_span`，断言 `retrieve_evidence` 在 embed（及开启 rerank 时）进入 generation 包裹；tracing 关闭时行为不变、不强制真连 Langfuse |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `none` |
| **graph_delta** | `none` |
| **graph_delta_note** | 不新增一级模块；观测语义仍落在既有 `lc_evidence_chain` / tracing；若维护者要求可顺手 G-L1 半句（非本波硬门槛） |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 不改 coding_wiki；行为真值在代码 + 本 task 验收 |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,30` |
| **invoke_retention_profile** | `default` |
| **thinking_profile** | `shortest` |
| **orchestration** | 轻量 bugfix · 对齐 grade/answer 手工 generation 先例 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | 2026-08-19 维护者「签收」：范围锁定仅旁路 `retrieve.py`；**不同步** Chat `rag_nodes.py` |
| HG-AUDIT-R1 | approved | 30 | 审查 `docs/harness/reviews/task_lc_evidence_retrieve_langfuse_audit_R1_20260819.md` · 维护者签收授权 00 代签推进 |
| HG-GRAPH-MODULES | approved | 30 | 真值 `docs/_tech_graph/l1/01_modules.md`；本 task 不新增一级模块 |

---

## 背景与目标

旁路 Langfuse 已在 `chain.py` 包根 span，并对 `grade_llm` / `answer_llm` 用 `trace_span(..., run_type="llm")` 产出 **generation**。  
但 `retrieve_evidence` 内的两类**模型/HTTP 调用**仍未被 Langfuse 识别为 generation：

1. **查询嵌入**：`embedder.embed([query])`（默认 SiliconFlow `ApiEmbedder` → `POST /embeddings`）  
2. **精排**（`RAG_RERANK_ENABLED=true`）：`rerank_chunks(...)`（默认 SiliconFlow `POST /rerank`）

外层仅有 `chain._retrieve_step` 的 `trace_span("retrieve", run_type="retriever")`，属于 retriever observation；**内部模型调用无子 generation**，UI 像「retrieve 没打模型」。

**完成态**：开启 `OPS_CHAT_TRACER=langfuse` 且 keys 具备时，一次旁路 invoke 的调用树在 `retrieve` 下可见 embed（及可选 rerank）generation；关闭 tracing 时零成本、行为与现网一致。

---

## 范围

1. 在 `app/ops/lc_evidence_chain/retrieve.py` 引入 `app.ops.tracing.trace_span`（及必要时 `update_current_span_metadata`）。  
2. 包裹查询 embed：建议名 `query_embed`（或等价清晰名），`run_type="llm"`，`model=` 使用 `embedder.name`（或当前后端模型 env）。  
3. 当 `rerank_enabled()` 为真时，包裹 `rerank_chunks`：建议名 `rerank`，`run_type="llm"`，`model=` 使用 `rerank_model_name()`（从 `app.ops.rag.reranker` 导入）。  
4. 复用既有开关：`tracing_enabled()` / `trace_span` no-op；**不**新造第二套 tracer；**不**改 CallbackHandler 主路径。  
5. 单测：mock `trace_span`（或 tracing 模块），断言进入 retrieve 时对 embed（及 enabled rerank）发起带 `run_type="llm"` 的包裹；关闭 tracing 路径不回归业务。  
6. `ruff check` 相关路径 + 既有 `tests/test_lc_evidence_chain.py` / 本 task 新增测绿。

---

## 非范围

- 修改 `hybrid_recall` SQL / Qdrant / 闸逻辑 / grade·answer 提示词  
- Langfuse SDK v3→v4 升包（见 `docs/spec/SPEC-langfuse-sdk-v4-migration_v1.md` · DEF-001）  
- 改 Chat `app/ops/chat/rag_nodes.py` 同构缺口（**默认同缺口保留**；若维护者在 `HG-TASK-DRAFT` 明示「Chat 一并修」，30 可扩一行，否则另开 task）  
- 改 `app/ops/chat/graph.py` 拓扑或 SSE 契约  
- 强制生产默认开 tracing  
- Token usage 精确回填（embed/rerank 若无 usage 字段可不写 `update_current_generation_usage`）

---

## 依赖

| 项 | 说明 |
|---|---|
| 旁路 retrieve | `app/ops/lc_evidence_chain/retrieve.py` |
| tracing 封装 | `app/ops/tracing.py`（`run_type=llm` → `as_type=generation`） |
| 先例 | `app/ops/lc_evidence_chain/answer.py` · `grader.py` |
| 嵌入 / 精排 | `app/ops/rag/embedder.py` · `reranker.py` |
| 上游观测 task | `docs/tasks/done/task_lc_evidence_langfuse_tracing.md` |
| 编码规范 | `docs/standards/CODING_BACKEND_L2_v1_zh.md` |

---

## 实施步骤（建议 · 30）

1. 切分支 `task/lc-evidence-retrieve-langfuse`（勿在 `main` / 勿叠无关 `lg_rag` 脏树）。  
2. `retrieve.py`：`from app.ops.tracing import trace_span`；embed / 条件 rerank 各包一层 generation。  
3. metadata（可选）：`backend`、候选数等写 `update_current_span_metadata`，失败静默。  
4. 单测 mock + ruff。  
5. 本机 keys 下 `scripts/lc_evidence_smoke.py` → Langfuse UI：`retrieve` 下见 `query_embed` /（可选）`rerank` generation（人工项）。

---

## 验收标准

- [x] `retrieve.py` 对 embed 调用使用 `trace_span(..., run_type="llm", model=...)`  
- [x] `RAG_RERANK_ENABLED=true` 时 rerank 同样为 generation；`false` 时不进入 rerank span  
- [x] tracing 关闭：业务结果与改前一致；无 Langfuse 强依赖  
- [x] pytest：至少覆盖「tracing 开时 embed 被包裹」；rerank 开/关各一路径（mock）  
- [x] `ruff check` 相关路径 + 相关 pytest 绿  
- [x] `git diff` **不改** `app/ops/chat/graph.py`  
- [ ] （人工）本机 keys + `LANGFUSE_ENV` 与 UI Environment 一致时，旁路 trace 可见 retrieve 子 generation

---

## failure_paths

| 触发 | 行为 | 可重试 | 用户可见 |
|---|---|---|---|
| tracing 未配置 / SDK ImportError | 透传现网；span no-op | Y（配 keys / 装依赖） | 业务无感 |
| 上报/网络失败 | 业务仍返回；埋点静默（对齐 `tracing.py`） | Y | 业务无感 |
| embed/rerank HTTP 失败 | 保持现网失败/回退语义；span 记录错误后仍抛/回退 | Y | 与改前一致 |
| 仅外层 retrieve、仍无子 generation | 验收打回 | N | PR 拒绝 |
| 误改 Chat / graph 拓扑 | 验收打回（除非闸明示扩 scope） | N | PR 拒绝 |

---

## 给执行帽必读

1. 本 task  
2. `app/ops/lc_evidence_chain/retrieve.py` · `chain.py`（外层 retrieve span）  
3. `app/ops/tracing.py` · `answer.py` / `grader.py`（generation 先例）  
4. `app/ops/rag/embedder.py` · `reranker.py`（model 名来源）  
5. `docs/standards/CODING_BACKEND_L2_v1_zh.md`

---

## 思考轮

### 思考轮控制

| 字段 | 值 |
|---|---|
| **actual_last_round** | R5 |
| **early_stop** | yes |
| **early_stop_reason** | 范围极窄：单文件补 generation 包裹，对齐既有 grade/answer 模式 |
| **residual_risks** | Chat `rag_nodes.py` 同构缺口若不同步，UI 对照 Chat vs 旁路仍不一致；本机 UI 抽检依赖 keys |

### R0
旁路 retrieve 内 embed/rerank 模型调用在 Langfuse 不可见，需补 generation 级观测。

### R1
范围锁定 `retrieve.py` + 单测；非范围含 SDK v4、默认改 Chat、改检索业务。

### R2
方案：复用 `trace_span(..., run_type="llm", model=...)`，与 answer/grader 一致；不新开关。

### R3
失败路径一律不得阻断答问；验收含 mock + 可选本机 UI。

### R4
pytest mock 绿；本机 keys 下 UI 可见 retrieve 子 generation。

### R5
闸未签前禁 30。

---

### 自检结论

> 10-task 起草自检 · 30 开工前须 `HG-TASK-DRAFT` + `HG-AUDIT-R1=approved`。

- [x] 验收 / failure_paths / 非范围 / 依赖齐全  
- [x] 思考轮 R0–R5 + 控制表（early_stop=yes）已写  
- [x] 10-task invoke 已落档  
- [x] HG-TASK-DRAFT approved（维护者签收 2026-08-19 · 仅旁路）  
- [x] HG-AUDIT-R1 approved（R1 审查文 · 维护者授权代签）  

---

### 自检结论（执行者）

> 30 实现 + 40 自检 · 2026-08-19 · 分支 `task/lc-evidence-retrieve-langfuse`

- [x] GATE_VERIFY + `harness verify` PASS（闸表均为 approved）
- [x] `retrieve.py`：`query_embed` / 条件 `rerank` 用 `trace_span(run_type="llm", model=...)`
- [x] 单测：embed 包裹 + rerank 开/关路径（mock `trace_span`，19 passed）
- [x] `git diff origin/master -- app/ops/chat/graph.py` 为空
- [x] ruff + pytest 绿
- [x] （人工遗留）本机 Langfuse UI 真连冒烟（维护者 keys）
- [x] 30/40 invoke 已落盘；**未** task close / 开 PR

**40 结论：PASS**（机械项全绿；人工 UI 项留给维护者）

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-19 | 10-task 初版：维护者反馈 Langfuse 未检测 retrieve 内模型调用 |
| 2026-08-19 | 维护者签收：闸齐；Chat 不同步；交子 agent 30+40；父窗验收后 CLOSE/PR/merge |
| 2026-08-19 | 30+40：retrieve embed/rerank generation + 单测；人工 UI 未做 |
