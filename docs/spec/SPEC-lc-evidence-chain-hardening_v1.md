# SPEC：lc_evidence_chain 硬化（观测补齐 + 闸失败兜底）（v1）

> **状态**：`accepted`（HG-SPEC-SIGNOFF=**approved** · 2026-08-17 维护者签收 v1）  
> **track**：`rag` / observability（旁路已生产可用后的 backlog）  
> **上游**：`docs/guides/REVIEW_lc_evidence_chain_third_party_20260816.md` §3（仓内复核后的采纳表）· 现网 `app/ops/lc_evidence_chain/` · v1 `docs/spec/SPEC-langchain-evidence-chain_v1.md`  
> **下游**：新 00（独立 worktree）起草 task → 20-task-audit + HG-AUDIT-R1 → 派 30。**起草 SPEC 的原窗不实现**  
> **Open Folder（实现）**：`ops-desk-api/`  
> **Bounded Context**：旁路继续 **默认不进** `chat/graph`；HTTP freeze `lc-evidence-http-v1` **不升**；不把旁路改造成「替代 Chat 的生产主路」。

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **spec_slug** | `lc-evidence-chain-hardening` |
| **invoke_slug** | `lc-evidence-chain-hardening` |
| **test_strategy** | `required` |
| **test_strategy_note** | pytest mock：`complete()` 聚合后上报 usage；grader 抛错 → refuse 而非 500；`kept` 按 `relevance.level` 降序；`git diff` 不改 `app/ops/chat/graph.py` 拓扑 |
| **Open Folder（实现）** | `ops-desk-api/` |
| **默认分支** | `task/lc-evidence-chain-hardening` |
| **graph_change_layer（建议）** | `G-L1`（`llm` complete 观测副作用；`lc_evidence_chain` 备注增量） |
| **freeze_id** | 保持 `lc-evidence-http-v1`（响应 schema 不新增必填键） |
| **对照评审** | `docs/guides/REVIEW_lc_evidence_chain_third_party_20260816.md` |

### 人工闸（SPEC 阶段）

| human_gate_id | status | 说明 |
|---|---|---|
| **HG-SPEC-SIGNOFF** | approved | 维护者 2026-08-17 签收 v1；审查 `docs/harness/reviews/spec_lc-evidence-chain-hardening_audit_R1_20260817.md` |

---

## 1. 背景与目标

### 背景

旁路 LCEL（retrieve → grade → answer）已合入生产并稳定：HTTP `POST /api/ops/lc-evidence/invoke`、Web 调试页、Langfuse 根 span 调用树（2026-08-17 维护者 UI 确认）。

2026-08-16 三方测评原文有多处事实错误（超时已有、`lru_cache` 不可用、不宜按「替代 Chat 上生产」打分）。仓内复核后 **仍成立的 backlog** 见评审 §3。生产已稳，本波把其中 **P1 + 可同波的 P2 排序** 收成可签收范围。

### 现状缺口（对照代码 · 2026-08-17）

| 缺口 | 现状 | 来源 |
|---|---|---|
| 旁路 Token 未进 Langfuse | `complete()` 聚合 `complete_stream` 时丢掉 `chunk.meta.usage`；Chat 流式路径已 `update_current_generation_usage` | 评审 §3 P1 |
| grader LLM 失败整链 500 | `grade_chunk` 无 try/except；HTTP 捕获为 `lc_evidence_failed` | 评审 §3 P1 |
| `kept` 未按档重排 | `decide_grade` 按召回原序过滤 | 评审 §3 P2 |
| Trace 父子 | **已完成**（根 span `lc-evidence-chain` + 维护者确认调用树） | 评审 §3 P1 → 本 SPEC **非范围** |

### 一句话目标

在 **不改 graph、不升 HTTP freeze、不切 Chat 默认路径** 的前提下：旁路 generation 可在 Langfuse 看到 token；grader 故障 fail-closed 为拒答；回答依据按相关档排序。

### 非目标

- 改 `app/ops/chat/graph.py` 拓扑，或把旁路挂到 `POST /api/ops/chat/stream`
- 把 httpx read timeout 改成 60s（现网 `connect=10 / read=180`，评审 A 已否）
- `build_chain` 单例化（评审 H）
- `@lru_cache` / Redis 检索缓存（评审 F；无痛点不开）
- 用 `rerank_score` 映射 **EXACT**（评审 G）；本期也不做 CE→RELEVANT 的可选降级
- SiliconFlow 指数退避 / 全链路熔断（Provider / Chat Epic）
- 句边界截断（P2 残留；须与 Chat `snippet≤400` / grader `1200` 对齐后再开）
- 接回 Graph / 抽共享 `retrieve_evidence`（IMPL「未来接回」· 另开 SPEC）
- Langfuse Prompt Management / Scores / Dataset
- SSE 流式、多轮 session、独立 `POST /api/ops/rag/search`
- 升 `lc-evidence-http-v1` 或改 Web 页

---

## 2. 方案对比（R2）

### 2.1 Token 上报

| 方案 | 描述 | 结论 |
|---|---|---|
| A · 改 `complete()` 返回 `(str, LlmUsage)` | 所有调用方要改签名 | **否决**（爆破面大） |
| B · `complete()` 聚合时副作用上报 | 仍返回 `str`；若 `chunk.meta.usage` 存在且 tracing 开，调 `update_current_generation_usage` | **采用** |
| C · 仅旁路改走 `complete_stream` | 只修 lc_evidence；Chat 非流式调用仍丢 usage | **否决**（重复实现） |

**推荐 B**：SiliconFlow / Bailian 的 `complete()` 共用同一聚合逻辑（现两处复制循环）。上报点 **只此一处**；`grade_llm` / `answer_llm` 的 `trace_span(run_type="llm")` 已包住 `complete()`，usage 会落到当前 generation。Chat `complete_stream` 路径保持现状（已自行上报，不走 `complete()`，无双计）。

tracing 关闭时 `update_current_generation_usage` 已是 no-op。

### 2.2 grader 失败

| 方案 | 描述 | 结论 |
|---|---|---|
| A · 捕获异常 → 视同空 grades → `decide_grade` refuse | 与「LLM 漏评 / 空 JSON」同语义；HTTP **200** + `gate_action=refuse` | **采用** |
| B · CE 分数映射 RELEVANT/EXACT | 尺度不同；CE 关时无分；EXACT 污染闸 | **否决**（评审 G） |
| C · 继续 500 | 评分故障被当成整链崩溃；前端 Alert，无法展示拒答 | **否决** |

**推荐 A**。answer / retrieve / embed 失败仍 500（无法在无生成或无召回时给出定义态）。`grade_failed` 只写 **日志 + Langfuse span metadata**，**不**新增 HTTP 必填字段（避免升 freeze）。

### 2.3 kept 排序

同波做：`decide_grade` 在过滤后按 `relevance.level` **降序**；同档保持原相对序（稳定排序）。列表通常 ≤5，改动面小、行为可测。

---

## 3. 范围（交付项）

### D1 · `complete()` 上报 token usage（必做）

- 聚合 `complete_stream` 时识别 usage 末帧（`LlmChunk.meta["usage"]`：`prompt_tokens` / `completion_tokens`）。
- 构造 `LlmUsage`，调用 `update_current_generation_usage`。
- **不**改 `BaseProvider.complete` 返回类型（仍 `str`）。
- 两 Provider 的重复循环应收成一处 helper（避免只改一边）。
- 无 usage 帧：静默跳过，不抛。

### D2 · grader 异常 fail-closed（必做）

- `grade_chunk`（或 `_grade_chunks_llm`）捕获 `LlmProviderError` 与其它完成期异常。
- 失败：打 error 日志；返回 `grades=[]`（现有 `decide_grade` 已 refuse）。
- HTTP：仍 200 `{ok:true}` + 拒答文案 / 空 evidence；**不是** 500 `lc_evidence_failed`。
- Langfuse：可在 grade span 写 `grade_failed=true`（失败静默，对齐 tracing 其它 metadata）。

### D3 · kept 按档降序（必做 · 原 P2 同波）

- `decide_grade`：`kept` 按 `grade.relevance.level` 降序；无 grade 的条本就不会进 kept。
- 同档稳定排序（不打乱召回相对序）。

### D4 · 图谱一句（随实现）

- `docs/_tech_graph/l1/01_modules.md`：`lc_evidence_chain` / `llm` 备注补「complete 路径上报 usage；grader 故障 refuse」。
- `./scripts/graph-compile.sh` 通过。

---

## 4. 架构约束

```text
[现网 Chat · 勿改拓扑]
  complete_stream → nodes.py 已上报 usage

[本波]
  complete() 聚合 stream
       → 拼 content（返回 str，契约不变）
       → 若有 usage 且 tracing 开 → update_current_generation_usage
  grade_chunk 异常
       → grades=[] → decide_grade refuse → answer 空证据早退
  decide_grade
       → kept 按 relevance.level 降序
```

| 约束 | 要求 |
|---|---|
| HTTP freeze | `lc-evidence-http-v1` 字段名 / 外壳不变；refuse 仍 200 |
| graph | **禁止**改 `graph.py` 节点与边 |
| 闸语义 | 仍：weak→refuse；relevant→answer_partial；exact→answer；空 grades refuse |
| 枚举 | 继续用 `app.ops.rag.grader.Relevance`，不得另起一套 |
| 检索 | 仍只调 `hybrid_recall`；禁止复制 SQL |

---

## 5. 验收标准（SPEC 级）

1. tracing 开启 + mock stream 带 `usage`：`complete()` 后 `update_current_generation_usage` 被调用，且 `prompt_tokens` / `completion_tokens` 与末帧一致。  
2. tracing 关闭：`complete()` 仍返回拼接文本；不上报、不抛。  
3. mock grader `complete` 抛 `LlmProviderError`：`ainvoke_evidence_answer` 返回 `meta.gate_action=refuse`、空/无可用 evidence、拒答文案；HTTP 包装层 **200** 而非 500。  
4. `decide_grade`：同时有 exact 与 relevant 时，kept 中 exact 在前。  
5. `git diff`（相对合入基线）**不改** `app/ops/chat/graph.py` 拓扑。  
6. `ruff check` 触及路径 + 相关 pytest 绿；若改 G-L1 则 `graph-compile.sh` exit 0。  
7. （人工可选）Langfuse：一次旁路 invoke 的 `grade_llm` / `answer_llm` generation 可见 input/output token。不挡机械关账。

---

## 6. failure_paths

| 触发 | 行为 | 可重试 | 用户可见 |
|---|---|---|---|
| 流式无 usage 帧 | 答案照常；Langfuse 无 token | — | 业务无感 |
| tracing 未开 | 不上报 | — | 无 |
| 上报 usage 失败 | 静默；业务结果仍返回 | Y | 无 |
| grader LLM 超时/4xx/解析前异常 | refuse（200） | Y（换问法 / 重试） | Meta 拒答 + 拒答文案 |
| answer LLM 失败 | 仍 500 `{ok:false,error}` | Y | Alert |
| retrieve / embed 失败 | 仍 500 | Y | Alert |
| 误改 graph / 升 freeze 字段 | 验收打回 | N | PR 拒绝 |
| CE 分数当 EXACT | 审查打回 | N | 禁止合入 |

---

## 思考轮

### 思考轮控制

| 字段 | 值 |
|---|---|
| **actual_last_round** | R5 |
| **early_stop** | no |
| **residual_risks** | `complete()` 副作用依赖「调用时已在 generation span 内」；若未来有人在 span 外调 `complete()` 则 usage 落不到树。句边界截断与检索缓存仍未做。 |

### R0 · 问题框定

生产旁路已稳。要把三方测评经仓内复核后的真缺口做成下一波，而不是原文里那些错误 P0。

### R1 · 范围 / 非范围

范围 = D1 usage + D2 grader refuse + D3 kept 排序 + G-L1 一句。  
非范围 = 改 graph、timeout 60、缓存、单例、CE→档位、接回 Graph、升 freeze。  
Trace 树已验收，本波不重复开工。

### R2 · 方案

Token：`complete()` 副作用上报，不改返回类型。  
grader：异常 ≡ 空 grades ≡ refuse。  
kept：同波按 level 降序。

### R3 · 边界

区分 grader 故障（定义态拒答）与 answer/retrieve 故障（仍 500）。禁止 EXACT 映射。HTTP schema 不加必填键。

### R4 · 验收

三组 mock pytest + graph diff 空 + ruff；Langfuse token 为人工可选。

### R5 · 签收就绪

思考轮已闭合。人签 + 20-spec-audit pass。实现交 **新 00**（worktree Prompt：`PROMPT_00_orchestrate.md`）。

---

## 下一棒

1. ~~20-spec-audit + HG-SPEC-SIGNOFF~~（已完成 · 2026-08-17）  
2. **新 00**：Open Folder = worktree `ops-desk-api-wt-lc-evidence-hardening`  
   复制 `docs/harness/invokes/by-task/lc-evidence-chain-hardening/PROMPT_00_orchestrate.md`  
3. 新 00 出 `docs/tasks/active/task_lc_evidence_chain_hardening.md`（闸未签前禁 30）

起草本 SPEC 的会话 **不** 再派 30、不改 `app/`。

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-17 | v1 draft：承接复核后 P1（Token / grader refuse）+ 同波 P2（kept 排序）；Trace 树已完成故排除 |
| 2026-08-17 | 维护者签收 · HG-SPEC-SIGNOFF=approved；20-spec-audit pass；交接新 00 worktree |
