# Task：lc_evidence_chain 硬化（usage 上报 + grader fail-closed + kept 排序）

> **状态**：completed（50 机械 PASS · 待 CLOSE 归档）  
> **类型**：observability / rag-debug（旁路硬化，不切 Chat 主路）  
> **上游 SPEC**：`docs/spec/SPEC-lc-evidence-chain-hardening_v1.md`（accepted · HG-SPEC-SIGNOFF=approved · 2026-08-17）  
> **对照评审**：`docs/guides/REVIEW_lc_evidence_chain_third_party_20260816.md` §3  
> **20-spec-audit**：`docs/harness/reviews/spec_lc-evidence-chain-hardening_audit_R1_20260817.md`  
> **分支**：`task/lc-evidence-chain-hardening`（相对 `origin/master`；合入走 PR，禁止直推 master）  
> **编排**：单 task · 10-task → 20-task-audit → 闸齐 → 30（可含 40）→ 00 机械核对 → 50 → CLOSE / PR  
> **无关 active**：`docs/tasks/active/task_ops_sync_sender_migration.md` **不要**混进本波、不要在本分支改它。

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `lc-evidence-chain-hardening` |
| **git_branch** | `task/lc-evidence-chain-hardening` |
| **test_strategy** | `required` |
| **test_strategy_note** | pytest mock，不连真 LLM / 真库：`complete()` 聚合后上报 usage；grader 抛错 → refuse 且 HTTP 200；`kept` 按 `relevance.level` 降序（同档稳定）；`git diff` 不改 `app/ops/chat/graph.py` 拓扑 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1` |
| **graph_delta** | `docs/_tech_graph/l1/01_modules.md` |
| **graph_delta_note** | `lc_evidence_chain` / `llm` 备注补「complete 路径上报 usage；grader 故障 refuse」；**不新增**一级模块；**不改** chat graph 边 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 不改 coding_wiki；行为以 SPEC + 本 task 为准 |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,30` |
| **invoke_retention_profile** | `default` |
| **freeze_id** | `lc-evidence-http-v1`（**保持，不升**；响应 schema 不新增必填键） |
| **orchestration** | 单 task 收 D1–D4；00 不实现 `app/`；起草 SPEC 的原窗不参与实现 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | 2026-08-17 00 代签：维护者本会话下发 `PROMPT_00_orchestrate.md` 要求跑通 10→30→CLOSE；20 R1 内容零阻塞 |
| HG-AUDIT-R1 | approved | 30 | 审查 `docs/harness/reviews/task_lc_evidence_chain_hardening_audit_R1_20260817.md`（内容 pass）· 2026-08-17 00 代签推进 30 |
| HG-GRAPH-MODULES | approved | 30 | 真值 `docs/_tech_graph/l1/01_modules.md`；本 task **不新增**一级模块，只改备注 |

---

## 背景与目标

旁路 LCEL（retrieve → grade → answer）已生产可用：HTTP `POST /api/ops/lc-evidence/invoke`、Web 调试页、Langfuse 根 span 调用树（2026-08-17 维护者 UI 确认）。三方测评原文有多处事实错误；仓内复核后仍成立的 backlog 见评审 §3。

**完成态**：在不改 graph、不升 HTTP freeze、不切 Chat 默认路径的前提下——旁路 `complete()` generation 可上报 token；grader LLM 故障 fail-closed 为拒答（HTTP 200）；传给 answer 的 `kept` 按相关档降序。

Trace 父子树已验收，本波 **不再**开 tracing task。

---

## 范围（D1–D4 · 单 task，不拆）

### D1 · `complete()` 上报 token usage

- 聚合 `complete_stream` 时识别 usage 末帧（`LlmChunk.meta["usage"]`：`prompt_tokens` / `completion_tokens`）。
- 构造 `LlmUsage`，调用 `update_current_generation_usage`。
- **不**改 `BaseProvider.complete` 返回类型（仍 `str`）。
- SiliconFlow / Bailian 两处重复循环应收成 **一处 helper**（避免只改一边）。
- 无 usage 帧：静默跳过，不抛。
- 上报点 **只在 `complete()` 聚合一处**；Chat `complete_stream` 路径已自行上报，不要双计。

### D2 · grader 异常 fail-closed

- `grade_chunk` / `_grade_chunks_llm` 捕获 `LlmProviderError` 与其它完成期异常。
- 失败：打 error 日志；返回 `grades=[]`（现有 `decide_grade` 已 refuse）。
- HTTP：仍 200 `{ok:true}` + 拒答文案 / 空 evidence；**不是** 500 `lc_evidence_failed`。
- Langfuse：可在 grade span 写 `grade_failed=true`（失败静默）；**不**新增 HTTP 必填字段。
- answer / retrieve / embed 失败仍 500（与 grader 故障分开）。

### D3 · kept 按档降序

- `decide_grade`：过滤后 `kept` 按 `grade.relevance.level` **降序**。
- 同档 **稳定排序**（不打乱召回相对序）。
- 无 grade 的条本就不会进 kept。

### D4 · 图谱一句

- `docs/_tech_graph/l1/01_modules.md`：`lc_evidence_chain` / `llm` 备注补「complete 路径上报 usage；grader 故障 refuse」。
- `./scripts/graph-compile.sh` 通过。

---

## 非范围

- 改 `app/ops/chat/graph.py` 拓扑，或把旁路挂到 `POST /api/ops/chat/stream`
- 把 httpx read timeout 改成 60s（现网 `connect=10 / read=180`）
- `build_chain` 单例化
- `@lru_cache` / Redis 检索缓存
- 用 `rerank_score` 映射 **EXACT**（禁止）；本期也不做 CE→RELEVANT 的可选降级
- SiliconFlow 指数退避 / 全链路熔断
- 句边界截断
- 接回 Graph / 抽共享 `retrieve_evidence`
- Langfuse Prompt Management / Scores / Dataset
- SSE 流式、多轮 session、独立 `POST /api/ops/rag/search`
- 升 `lc-evidence-http-v1` 或改 Web 页
- 再开 Trace 父子树 task（2026-08-17 UI 已确认）
- 改 `task_ops_sync_sender_migration.md` 或其实现

---

## 依赖

| 项 | 说明 |
|---|---|
| SPEC | `docs/spec/SPEC-lc-evidence-chain-hardening_v1.md` |
| 评审 §3 | `docs/guides/REVIEW_lc_evidence_chain_third_party_20260816.md` |
| 编码规范 | `docs/standards/CODING_BACKEND_L2_v1_zh.md` |
| 闸扫描 | `docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md` |
| Provider | `app/llm/providers/siliconflow.py` · `bailian.py` · `base.py`（重复 `complete()` 循环） |
| 旁路闸 | `app/ops/lc_evidence_chain/grader.py` |
| HTTP | `app/ops/lc_evidence_chain/router.py`（refuse 已 200；未捕获异常才 500） |
| usage 先例 | `app/ops/chat/nodes.py`（`complete_stream` 路径已上报；本波勿改拓扑） |
| tracing | `app/ops/tracing.py` · `update_current_generation_usage`（tracing 关 = no-op） |
| 既有单测 | `tests/test_lc_evidence_chain.py` · `tests/test_lc_evidence_http.py` |

---

## 实施步骤（建议 · 30）

1. **D1 helper**：在 `app/llm/providers/` 收一处聚合函数（建议挂 `BaseProviderImpl` 或同包 helper）：拼 content、若 `chunk.meta["usage"]` 存在则构造 `LlmUsage` 并 `update_current_generation_usage`（上报失败须静默，对齐 tracing.py）。两 Provider 的 `complete()` 改调该 helper；返回仍 `str`。
2. **D2**：`_grade_chunks_llm` 的 `provider.complete` 包 try/except；失败日志 + `grades=[]`；可选 span metadata `grade_failed=true`。不要在 HTTP 层把 grader 失败改成 500。
3. **D3**：`decide_grade` 在拼出 `kept` 后按 `g.relevance.level` 降序 `sorted(..., reverse=True)`（Python 稳定排序）。refuse 时 kept 仍为空。
4. **单测 mock**（不连真 LLM/真库）：usage 上报；grader `LlmProviderError` → ainvoke refuse + HTTP 200；exact 排在 relevant 前且同档保序。answer/retrieve 抛错仍 500（可复用或对照 `test_invoke_upstream_failure_envelope`）。
5. **D4**：G-L1 一句 + `./scripts/graph-compile.sh`。
6. `ruff check` 触及路径；`git diff origin/master -- app/ops/chat/graph.py` 为空。
7. 落盘 30（可含 40）invoke；回填「自检结论（执行者）」。**未**经维护者要求不要 push。

---

## 验收标准

- [x] tracing 开启 + mock stream 带 `usage`：`complete()` 后 `update_current_generation_usage` 被调用，且 `prompt_tokens` / `completion_tokens` 与末帧一致
- [x] tracing 关闭：`complete()` 仍返回拼接文本；不上报、不抛
- [x] mock grader `complete` 抛 `LlmProviderError`：`ainvoke_evidence_answer` 返回 `meta.gate_action=refuse`、空/无可用 evidence、拒答文案；HTTP 包装层 **200** 而非 500
- [x] answer / retrieve 失败：HTTP 仍 500 `{ok:false,error}`（与 D2 分开）
- [x] `decide_grade`：同时有 exact 与 relevant 时，kept 中 exact 在前；同档保持原相对序
- [x] `git diff`（相对合入基线）**不改** `app/ops/chat/graph.py` 拓扑
- [x] `ruff check` 触及路径 + 相关 pytest 绿
- [x] `docs/_tech_graph/l1/01_modules.md` 已补 usage / grader refuse 备注；`./scripts/graph-compile.sh` exit 0
- [x] HTTP freeze `lc-evidence-http-v1` 未升；响应未新增必填键
- [ ] （人工可选）Langfuse：一次旁路 invoke 的 `grade_llm` / `answer_llm` generation 可见 input/output token。**不挡机械关账**

---

## failure_paths

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

## 给执行帽必读

1. 本 task  
2. `docs/spec/SPEC-lc-evidence-chain-hardening_v1.md`  
3. `docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`  
4. `docs/standards/CODING_BACKEND_L2_v1_zh.md`  
5. `app/llm/providers/siliconflow.py` · `bailian.py` · `base.py`（`complete` 聚合）  
6. `app/ops/lc_evidence_chain/grader.py`  
7. `app/ops/lc_evidence_chain/router.py` · `app/ops/tracing.py` · `app/ops/chat/nodes.py`（usage 先例，勿改 graph）  
8. `tests/test_lc_evidence_chain.py` · `tests/test_lc_evidence_http.py`

---

## 思考轮

### 思考轮控制

| 字段 | 值 |
|---|---|
| **actual_last_round** | R5 |
| **early_stop** | no |
| **residual_risks** | `complete()` 副作用依赖「调用时已在 generation span 内」；若未来有人在 span 外调 `complete()` 则 usage 落不到树。句边界截断与检索缓存仍未做（非范围）。Langfuse token 可见性为人工可选，不挡机械关账。 |

### R0 · 问题框定

生产旁路已稳。要把三方测评经仓内复核后的真缺口做成下一波，而不是原文里那些错误 P0（timeout 60、lru_cache、按「替代 Chat 上生产」打分）。

### R1 · 范围 / 非范围

范围 = D1 usage + D2 grader refuse + D3 kept 排序 + D4 G-L1 一句。  
非范围 = 改 graph、timeout 60、缓存、单例、CE→档位、接回 Graph、升 freeze、改 Web、再开 tracing。  
Trace 树已验收，本波不重复开工。

### R2 · 方案

Token：`complete()` 副作用上报，不改返回类型；两 Provider 收成一处 helper。  
grader：异常 ≡ 空 grades ≡ refuse；HTTP 200。  
kept：同波按 level 降序、同档稳定排序。

### R3 · 边界

区分 grader 故障（定义态拒答 / 200）与 answer/retrieve 故障（仍 500）。禁止 EXACT 映射。HTTP schema 不加必填键。`grade_failed` 只写日志 + Langfuse metadata。

### R4 · 验收

三组 mock pytest + graph diff 空 + ruff + graph-compile；Langfuse token 为人工可选、不挡关账。

### R5 · 签收就绪

思考轮已闭合。闸未签前禁 30。实现交 **独立 30 子 agent**（cwd=本 worktree）；00 不改 `app/` / `tests/` 业务实现。

---

### 自检结论

> 10-task 起草自检 · 30 开工前须 HG-TASK-DRAFT + HG-AUDIT-R1=approved。

- [x] 验收 / failure_paths / 非范围 / 依赖齐全
- [x] 思考轮 R0–R5 + 控制表已写
- [x] 10-task invoke 已落档
- [x] `npx @cyning/harness task lint` PASS
- [x] HG-TASK-DRAFT approved（2026-08-17 00 代签）
- [x] HG-AUDIT-R1 approved（R1 审查文 · 2026-08-17 00 代签）

---

### 自检结论（执行者）

> 30 含 40 · 2026-08-17 · cwd=本 worktree · **未 commit / 未 push**

| 命令 | 退出码 | 摘要 |
|---|---|---|
| `npx @cyning/harness verify --target . --task docs/tasks/active/task_lc_evidence_chain_hardening.md`（开工前 + 收尾） | 0 | VERIFY: PASS；闸三项 approved |
| 主仓 `.venv/bin/ruff check` 触及路径（本 worktree 无 `.venv`） | 0 | All checks passed |
| 主仓 `.venv/bin/pytest tests/test_llm_providers.py tests/test_lc_evidence_chain.py tests/test_lc_evidence_http.py -q` | 0 | **48 passed** |
| `git diff origin/master -- app/ops/chat/graph.py` | 0 | 空 |
| `./scripts/graph-compile.sh` | 0 | OK；生成物仅 `generated_at` / tech-graph freeze stamp |
| HTTP freeze `lc-evidence-http-v1` | — | 未升；未新增响应必填键 |
| CE `rerank_score` → EXACT | — | 未做 |

已知未测：Langfuse UI 上 `grade_llm` / `answer_llm` 的 input/output token（人工可选，不挡机械关账）。

下一棒：交还 00 机械核对 → 50。

---

### 自检结论（50）

> Harness 50 · 2026-08-17 · 00 独立复检 · **PASS（机械）**

- [x] 验收表机械项已勾且与实现一致（抽读 `_complete_from_stream` / `_grade_chunks_llm` except / `decide_grade` 稳定降序 / G-L1 备注）
- [x] `git diff origin/master -- app/ops/chat/graph.py` 为空
- [x] `harness verify` PASS · ruff PASS · pytest **48 passed**
- [x] freeze `lc-evidence-http-v1` 未升；无 CE→EXACT
- [x] invoke 50 已落档
- [ ] （人工可选）Langfuse UI token — **不挡机械关账**

**50 结论：PASS（机械）· 可 CLOSE / PR**

### 经验

- `complete()` 上报必须与 Chat `complete_stream` 分路径，避免双计；helper 对 tracing 用 lazy import，以免 `llm` 模块出边变成 ops。
- grader 失败要在 `_grade_chunks_llm` 内吞成空 grades，才能让 HTTP 层继续走 200 refuse；不要在 router 再开特例。
- Wiki: n/a（本波不改 coding_wiki；行为真值在 SPEC + G-L1 备注）

### KPI

| 项 | 分 |
|---|---|
| Task_KPI% | 100 |

## CLOSE

| 项 | 内容 |
|---|---|
| 日期 | 2026-08-17 |
| 定稿 | `complete()` 聚合上报 usage；grader 故障 refuse/200；kept 按档降序；freeze 不升 |
| 归档 | `docs/tasks/done/task_lc_evidence_chain_hardening.md` |

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-17 | 10-task 首稿：承接已签 SPEC D1–D4；闸 pending |
| 2026-08-17 | 20 R1 pass；00 代签 HG-TASK-DRAFT + HG-AUDIT-R1 |
| 2026-08-17 | 30+40 PASS；00 机械核对 + 50 PASS；关账 |
