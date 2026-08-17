# Task Audit R1：lc-evidence-chain-hardening

> **hat_id**：20-task-audit  
> **task**：`docs/tasks/active/task_lc_evidence_chain_hardening.md`  
> **对照 SPEC**：`docs/spec/SPEC-lc-evidence-chain-hardening_v1.md`（accepted · HG-SPEC-SIGNOFF=approved）  
> **对照评审**：`docs/guides/REVIEW_lc_evidence_chain_third_party_20260816.md` §3  
> **日期**：2026-08-17  
> **分支**：`task/lc-evidence-chain-hardening`  
> **审查**：00 书面审 · **不**改 `app/` · **不**代签 `HG-AUDIT-R1`  
> **结论**：内容 **`pass`** · 流程闸起草时 **`pending`** · 建议签 `HG-TASK-DRAFT` + `HG-AUDIT-R1=approved`

---

## 结论摘要

| 维度 | 判定 | 说明 |
| --- | --- | --- |
| **内容可执行** | **pass** | 范围 D1–D4 / 非范围 / 验收 / failure_paths / test_strategy / 必读齐全；现网插入点清晰 |
| **流程闸 `HG-AUDIT-R1`** | 起草时 **pending** | 真值在 task 人工闸表；本审仅建议，审查当时 **禁止**改表 |
| **思考轮审查** | **pass** | 控制表闭合（R5 / early_stop=no）；residual_risks 齐全 |
| **与 SPEC v1** | **无冲突** | 方案 B（complete 副作用上报）/ 方案 A（空 grades → refuse）/ 同档稳定排序 |
| **是否退回 10-task** | **否** | 无内容阻塞 |
| **建议代签** | **是** | 内容零阻塞；00/维护者可将 `HG-TASK-DRAFT` 与 `HG-AUDIT-R1` 改为 approved |

---

## 元信息核对

| 字段 | task 值 | 审阅 |
| --- | --- | --- |
| `task_slug` | `lc-evidence-chain-hardening` | OK |
| `git_branch` | `task/lc-evidence-chain-hardening` | OK（与当前分支一致） |
| `test_strategy` | `required` | OK |
| `test_strategy_note` | mock；不连真 LLM/真库；三组断言 + graph diff | OK；可执行 |
| `code_quality_bar` | `L2_backend` | OK |
| `graph_change_layer` | `G-L1` | OK：备注增量，不新增一级模块 |
| `graph_delta` | `docs/_tech_graph/l1/01_modules.md` | OK |
| `wiki_delta` | `n/a` | OK + note |
| `review_hat` | `20` | OK |
| `required_invoke_hats` | `10,30` | OK（不含 20；本审不强制 20 invoke） |
| `invoke_retention_profile` | `default` | OK |
| `freeze_id` | `lc-evidence-http-v1` 保持不升 | OK |
| `HG-TASK-DRAFT` | pending（起草） | 正确；blocks 22-R1 |
| `HG-AUDIT-R1` | pending（起草） | 正确；blocks 30 |
| `HG-GRAPH-MODULES` | approved | OK；不新增一级模块 |
| 上游 SPEC | accepted · 人签 2026-08-17 | OK |
| 无关 active | `task_ops_sync_sender_migration.md` 已声明勿混 | OK |

`npx @cyning/harness task lint --file docs/tasks/active/task_lc_evidence_chain_hardening.md` → **PASS**。

---

## 核对表

### 1 · 范围（对照 SPEC D1–D4）

| SPEC / task 项 | 审阅 | 说明 |
| --- | --- | --- |
| D1 `complete()` 聚合上报 usage；仍返回 `str`；两 Provider 一处 helper | **pass** | 现 `siliconflow.py` / `bailian.py` 的 `complete()` 均为复制循环、丢弃 `chunk.meta`；Chat `nodes.py` 已在 `complete_stream` 上报。helper 应收到 `app/llm/providers/`（`BaseProviderImpl` 或同包），上报点只此一处 |
| D2 grader 异常 → `grades=[]` → refuse；HTTP 200 不是 500 | **pass** | `_grade_chunks_llm` 现无 try/except；`decide_grade` 空 grades 已 refuse；router 仅在 `ainvoke` **抛错**时 500。只要 ainvoke 正常返回 refuse，HTTP 已是 200（`test_invoke_refuse_is_200`） |
| D3 `kept` 按 `relevance.level` 降序；同档稳定排序 | **pass** | 现 `decide_grade` 按召回原序 append；Python `sorted` 稳定即可 |
| D4 G-L1 一句 + `graph-compile.sh` | **pass** | 改 `lc_evidence_chain` / `llm` 备注，不增模块 |

### 2 · 非范围

| 非范围项 | 审阅 |
| --- | --- |
| 改 `graph.py` / 接回 Chat stream | **pass** |
| timeout 改 60 | **pass**（评审 A 已否） |
| `build_chain` 单例 | **pass** |
| lru_cache / Redis 缓存 | **pass** |
| CE `rerank_score` → EXACT（及本期 CE→RELEVANT） | **pass**（评审 G） |
| 句边界截断 / 改 Web / 升 freeze | **pass** |
| 再开 Trace 父子 task | **pass**（2026-08-17 UI 已确认） |
| 混入 `task_ops_sync_sender_migration` | **pass** |

### 3 · 验收标准

| 验收 | 审阅 | 说明 |
| --- | --- | --- |
| tracing 开 + mock usage 帧 → `update_current_generation_usage` 参数一致 | **pass** | 可 patch tracing 函数；断言 tokens |
| tracing 关：仍返回 str、不上报、不抛 | **pass** | `update_current_generation_usage` 已 no-op；单测仍应断言未被业务路径误调或允许 no-op |
| grader `LlmProviderError` → refuse + HTTP 200 | **pass** | 链级 + HTTP 级各一测；勿只测 decide 空 grades（那是既有行为） |
| answer/retrieve 失败仍 500 | **pass** | 与 D2 分开；可对照 `test_invoke_upstream_failure_envelope` |
| exact 在 relevant 前；同档保序 | **pass** | 纯 `decide_grade` 单测即可 |
| 不改 `graph.py`；ruff；graph-compile；freeze 不升 | **pass** |
| Langfuse token 人工可选、不挡关账 | **pass** | 与 SPEC §5.7 一致 |

### 4 · failure_paths

| 触发 | task 行为 | 审阅 |
| --- | --- | --- |
| 无 usage 帧 / tracing 关 / 上报失败 | 业务照常；静默 | **pass** |
| grader 超时/4xx/解析前异常 | refuse 200 | **pass** |
| answer / retrieve 失败 | 仍 500 | **pass** · 与 grader 已拆开 |
| 误改 graph / 升 freeze / CE→EXACT | 打回 | **pass** |

### 5 · test_strategy

| 项 | 审阅 |
| --- | --- |
| `required` + mock，不连真 LLM/真库 | **pass** |
| 覆盖 usage / grader refuse+200 / kept 排序 | **pass** |
| 既有 `tests/test_lc_evidence_chain.py` / `test_lc_evidence_http.py` | **pass**：增补，勿拆掉 refuse-is-200 与 upstream-500 |

### 6 · 给执行帽必读

SPEC、GATE_VERIFY fragment、L2、两 Provider `complete`、`grader.py`、router/tracing/nodes 先例、既有单测 —— **齐全**，无必读空洞。

### 7 · 思考轮审查（阶段 C）

| 字段 | 值 | 审阅 |
| --- | --- | --- |
| `actual_last_round` | R5 | OK |
| `early_stop` | no | OK |
| `residual_risks` | span 外调 `complete()` usage 落不到树；截断/缓存非范围；Langfuse 人工不挡关账 | **闭合** |
| R0–R5 | 问题→范围→方案→边界→验收→禁 30 | **闭合** |

**思考轮结论**：通过；不退回 10-task。

---

## 现实现可执行性（只读 · 不改码）

- D1：两 Provider `complete()` 逐 chunk 拼 `content` 后 `return "".join(parts)`，usage 末帧被丢。Chat 流式路径已解析 `chunk.meta["usage"]`。30 抽 helper 即可，**不要**改 `complete` 签名、**不要**在 `grade_llm`/`answer_llm` 再报一次（双计）。
- D2：`_grade_chunks_llm` 在 `trace_span("grade_llm")` 内直接 `await provider.complete`。捕获后返回 `[]` 即可落入既有 `decide_grade` refuse；HTTP 层无需为 grader 失败新增分支。
- D3：`kept` 现按 `evidence` 原序过滤；`Relevance.level` 已是 int 档位。
- D4：`01_modules.md` 已有 `lc_evidence_chain` 行（含 HTTP freeze 与 Langfuse tags）；本波只加一句备注。

---

## 内容阻塞清单

**无。** 不退回 10-task。审查落盘时 **不**附 30 Prompt（闸尚未 approved）。

---

## 非阻塞提醒（30 时注意 · 不挡签闸）

1. usage 上报失败必须静默（对齐 `tracing.py`）；无 usage 帧不抛。
2. helper 聚合时跳过纯 meta 帧（usage / 可能的 `model.fallback`），不要把空 content 当正文问题，但也不要把 usage 帧的 content 误拼（现 Chat 对 usage 帧 `continue`）。
3. grader 捕获范围：完成期异常（含 `LlmProviderError`）；不要把 retrieve/answer 失败吞成 refuse。
4. 禁止 `rerank_score` → EXACT。
5. 单测 mock，不连真 LLM/真库。
6. 维护者未说 commit 则不要擅自 push。

---

## 签收 / 关闭（本轮为 20 终轮）

- 20 R1 **内容通过**（`pass`）。
- 流程闸起草时 **pending**：30 在 `HG-AUDIT-R1=approved` 之前必须拒开工。
- 下一棒：维护者（或本 00 会话明确授权代签）签闸后，再 `verify` 并下发 30。

---

## 维护者签闸（20 后 · 30 前）

- [x] 已读 R1 审查结论（内容 `pass` · 无退回 10）
- [x] 在 task 人工闸表将 `HG-TASK-DRAFT` 与 `HG-AUDIT-R1` 改为 approved（00 代签 · 2026-08-17；授权依据：维护者本会话 `PROMPT_00_orchestrate.md` 要求跑通 10→30→CLOSE）
- [ ] commit task 文档或确认已签（维护者未要求 00 commit 文档；实现子 agent 未授权则不 push）
- [x] 再下发 Harness 30 Prompt（闸表已 approved 后）

30 Agent 将以 task 表为准。

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-17 | 20 R1 首审 pass · 闸当时 pending |
