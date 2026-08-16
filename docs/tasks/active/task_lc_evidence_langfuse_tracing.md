# Task：lc_evidence_chain · Langfuse tracing 监控

> **状态**：active（闸已签 · 30/40 执行中）  
> **类型**：observability / rag-debug  
> **上游**：`docs/tasks/done/task_langchain_evidence_chain.md`（旁路 LCEL 已关账 · PR #33 已合入 master）  
> **关联实现**：`app/ops/lc_evidence_chain/` · 现网 Chat 埋点 `app/ops/tracing.py` + `app/ops/chat/service.py`  
> **分支**：`task/lc-evidence-langfuse-tracing`  
> **编排**：闸齐 → 子 agent 30+40 → **本窗 50** → **等维护者确认**再 CLOSE/合入

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `lc-evidence-langfuse-tracing` |
| **git_branch** | `task/lc-evidence-langfuse-tracing` |
| **test_strategy** | `required` |
| **test_strategy_note** | pytest：tracing 关闭时零回调；开启时 mock CallbackHandler/config 注入；不强制 CI 真连 Langfuse |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1` |
| **graph_delta** | `docs/_tech_graph/l1/01_modules.md` |
| **graph_delta_note** | `lc_evidence_chain` 备注补「可选 Langfuse · tags=`lc-evidence-chain`」；**不改** chat graph 边 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 不改 coding_wiki；冒烟说明可落 CLI / IMPL 短节 |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,30` |
| **invoke_retention_profile** | `default` |
| **orchestration** | 单 task · 复用现网 tracing 开关 · 与 Chat 轨迹可区分 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | 维护者 2026-08-16 会话「签收」· 范围锁定：仅旁路埋点 |
| HG-AUDIT-R1 | approved | 30 | 审查 `docs/harness/reviews/task_lc_evidence_langfuse_tracing_audit_R1_20260816.md` · 维护者授权 00 代签推进 |
| HG-GRAPH-MODULES | approved | 30 | 真值 `docs/_tech_graph/l1/01_modules.md`；本 task 仅增量备注 |

---

## 背景与目标

旁路 `lc_evidence_chain`（retrieve → grade → answer）已可库级/`scripts/lc_evidence_smoke.py` 调用，但**未**挂 Langfuse；Chat 路径已有 `OPS_CHAT_TRACER=langfuse` + `langfuse.langchain.CallbackHandler`。  
维护者需要在 Langfuse UI 中按 **独立 tag/run_name** 观察旁路耗时、检索/打分/生成层级与 `gate_action` 等元数据，便于与 Chat（`ops-chat`）对照。

**完成态**：开启 tracing 时，一次 `ainvoke_evidence_answer`（及 CLI 冒烟）在 Langfuse 产生可筛选轨迹；关闭时行为与现网一致（零依赖、零上报）。

---

## 范围

1. 在 `ainvoke_evidence_answer` / `build_chain().ainvoke` 路径接入 Langfuse（优先官方 **LangChain CallbackHandler**，对齐 `app/ops/chat/service.py` 模式）。  
2. Trace 约定（freeze 草案 · `freeze_id`: `lc-evidence-langfuse-v1`）：  
   - `run_name`：`lc-evidence-chain`  
   - `langfuse_tags`：至少含 `lc-evidence-chain`（可与 `ops-chat` 并存过滤）  
   - 层级可见：retrieve / grade / answer（LCEL 子 runnable 或等价 span；LLM 调用应为 **generation**）  
   - metadata 建议：`gate_action`、`hit_count`、`kept_count`、`best_relevance`（有则写；失败静默）  
3. **复用** `app/ops/tracing.py` 的 `tracing_enabled()` / `flush_traces()`；**不**另造第二套主开关（仍 `OPS_CHAT_TRACER=langfuse` + keys；文档注明旁路共用开关）。  
4. CLI：`scripts/lc_evidence_smoke.py` 在 tracing 开启时结束前 `flush_traces()`；stdout 可打印「tracing on/off」。  
5. 单测：关闭路径无 CallbackHandler；开启路径 config 含 callbacks/metadata（mock，不连云）。  
6. G-L1：`01_modules.md` 中 `lc_evidence_chain` 行补观测说明（若旁路模块行尚未合入 master，则与上游 task 一并保证存在）。

---

## 非范围

- 新增 `POST /api/ops/lc-evidence/*` HTTP（见 web SPEC / 另开 api task）  
- 修改 `app/ops/chat/graph.py` 拓扑或 Chat 默认埋点语义  
- 强制生产默认开启 Langfuse  
- Langfuse Prompt Management / Scores / Dataset 实验平台化  
- 改 grade/answer 业务逻辑或提示词正文  

---

## 依赖

| 项 | 说明 |
|---|---|
| 旁路包 | `app/ops/lc_evidence_chain/`（已合入 master · PR #33 · 2026-08-16） |
| 现网 tracing | `app/ops/tracing.py` · Chat 参考 `app/ops/chat/service.py` |
| SDK | `langfuse`（`pyproject.toml` 已列）；dotenv **先于** langfuse import（与 `scripts/trace_smoke.py` 一致） |
| 编码规范 | `docs/standards/CODING_BACKEND_L2_v1_zh.md` |
| 技能基线 | Langfuse instrumentation：优先框架集成；trace 须有清晰命名、层级、generation 类型 |

---

## 实施步骤（建议 · 30）

1. 抽小函数 `_trace_config()`（旁路专用 tags/`run_name`），`tracing_enabled()` 为 false 时返回 `None`。  
2. `ainvoke_evidence_answer`：`ainvoke(..., config=...)`；必要时对 LLM 步补 `@traceable`/`trace_span`（仅当 CallbackHandler 抓不到时，对齐 chat `nodes.py` 先例）。  
3. 在 answer/grade 完成后 `update_current_span_metadata` 写入 gate 等（失败静默）。  
4. CLI flush + 单测 + G-L1 一行。  
5. 本机（keys 具备时）跑 smoke → Langfuse UI 确认 tag=`lc-evidence-chain`（验收勾选手动项）。

---

## 验收标准

- [x] `OPS_CHAT_TRACER` 未开 / keys 缺失：`ainvoke_evidence_answer` 行为与改前一致；pytest 断言无 CallbackHandler 注入  
- [x] 开启 tracing：`ainvoke` config 含 `callbacks` + `metadata.langfuse_tags` 含 `lc-evidence-chain` + `run_name=lc-evidence-chain`（单测 mock）  
- [x] LLM 相关 observation 类型为 generation（代码路径：`trace_span(..., run_type="llm")` → as_type=generation；本机 UI 抽检见人工项）  
- [x] CLI 结束调用 `flush_traces()`（tracing 开时）  
- [x] `git diff`（相对合入基线）**不改** `app/ops/chat/graph.py` 拓扑  
- [x] `ruff check` 相关路径 + `pytest tests/test_lc_evidence_chain.py`（及本 task 新增测）绿  
- [x] `docs/_tech_graph/l1/01_modules.md` 已注明旁路可选 Langfuse  
- [ ] （人工）本机 keys 下 smoke 后 Langfuse Traces 可见且可用 tag 过滤  

---

## failure_paths

| 触发 | 行为 | 可重试 | 用户可见 |
|---|---|---|---|
| tracing 未配置 | 旁路照常跑，不上报 | — | CLI 可提示 tracing off |
| Langfuse SDK ImportError | 等同未开启，透传 | Y（装依赖） | 无 |
| 上报/网络失败 | 业务结果仍返回；埋点失败静默（对齐 tracing.py） | Y | 业务无感 |
| CallbackHandler 抓不到某次 LLM | 补 `@traceable`/`trace_span`；不可丢业务 | Y | — |
| 与 Chat trace 混淆 | 验收打回（缺独立 tag/run_name） | N | PR 拒绝 |
| 旁路包未合入 | 30 拒开工 / 叠分支 | Y | task 依赖 |

---

## 给执行帽必读

1. 本 task  
2. `app/ops/tracing.py` · `app/ops/chat/service.py`（CallbackHandler 模式）  
3. `app/ops/lc_evidence_chain/chain.py` · `answer.py` · `grader.py`  
4. `scripts/trace_smoke.py` · `scripts/lc_evidence_smoke.py`（dotenv 顺序）  
5. `docs/standards/CODING_BACKEND_L2_v1_zh.md`

---

## 思考轮

### 思考轮控制

| 字段 | 值 |
|---|---|
| **actual_last_round** | R5 |
| **early_stop** | no |
| **residual_risks** | RunnableLambda 可能削弱自动 span 粒度，须补手工 span；本机 UI 抽检依赖 keys |

### R0
为当前 LangChain evidence 旁路补齐 Langfuse 监控，与 Chat 轨迹可区分。

### R1
范围=ainvoke/CLI/单测/G-L1 备注；非范围=HTTP、改 graph、Prompt/Score 平台。

### R2
复用 `tracing_enabled` + LangChain CallbackHandler；独立 `run_name`/tags；必要时手工 span。

### R3
未配置/SDK 缺失/上报失败均不得阻断答问；禁与 ops-chat 混名。

### R4
pytest mock 开关路径；本机 smoke+UI 抽检为人工项；ruff/pytest 绿。

### R5
闸签后 30；合入依赖旁路包已在基线。

---

### 自检结论

> 10-task 起草自检 · 30 开工前须 HG-TASK-DRAFT + HG-AUDIT-R1=approved。

- [x] 验收 / failure_paths / 非范围 / 依赖齐全
- [x] 思考轮 R0–R5 + 控制表已写
- [x] 10-task invoke 已落档
- [x] HG-TASK-DRAFT approved（维护者签收 2026-08-16）
- [x] HG-AUDIT-R1 approved（R1 审查文 · 维护者授权代签）
- [x] 旁路包已合入 master（PR #33）

---

### 自检结论（执行者）

> 30 实现 + 40 自检 · 2026-08-16 · 分支 `task/lc-evidence-langfuse-tracing`

- [x] GATE_VERIFY + `harness verify` PASS（闸表均为 approved）
- [x] `_trace_config` + `ainvoke` config 注入；grade/answer LLM 用 `trace_span(run_type="llm")` 保证 generation
- [x] CLI：`tracing on/off` 打印 + 开启时 `flush_traces()`
- [x] 单测：关闭无 config；开启含 callbacks/tags/`run_name`（14 passed）
- [x] G-L1 `01_modules.md` 已补可选 Langfuse · tags=`lc-evidence-chain`
- [x] `git diff origin/master -- app/ops/chat/graph.py` 为空
- [x] ruff + pytest 绿
- [ ] （人工遗留）本机 Langfuse UI 真连冒烟（维护者 keys）
- [x] 30/40 invoke 已落盘；**未** task close / 开 PR

**40 结论：PASS**（机械项全绿；人工 UI 项留给维护者）

---

### 自检结论（50）

> Harness 50 · 2026-08-16 · 父窗独立复检 · **PASS（机械）** · **等维护者确认再 CLOSE**

- [x] 验收表机械项已勾且与实现一致（抽读 chain/grader/answer/CLI/G-L1）
- [x] `git diff origin/master -- app/ops/chat/graph.py` 为空
- [x] `harness verify` PASS · ruff PASS · pytest **14 passed**
- [x] freeze：`run_name` / tags = `lc-evidence-chain`；LLM 用 `trace_span(run_type="llm")`
- [x] invoke 50 已落档
- [ ] （人工）本机 Langfuse UI 按 tag 过滤 — **留给维护者**
- [ ] CLOSE / PR — **等维护者进一步确认**

**50 结论：PASS（机械）· 阻塞 CLOSE 仅人工 UI（可选）+ 维护者确认。**

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-16 | 首稿：旁路 Langfuse tracing · HG-TASK-DRAFT/HG-AUDIT-R1=pending |
| 2026-08-16 | 维护者签收 · R1 留痕 · 派 30+40；50 后等确认再 CLOSE |
| 2026-08-16 | 30+40 完成：CallbackHandler + generation span · 单测/ruff 绿 · UI 人工项待确认 |
| 2026-08-16 | 50 PASS（机械）· 等维护者确认再 CLOSE/合入 |
