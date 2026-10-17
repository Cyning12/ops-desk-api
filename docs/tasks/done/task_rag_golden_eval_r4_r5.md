# Task：rag-golden-eval-r4-r5（R-4 四类 golden 结案级评测 + R-5 Demo 证据表）

> **状态**：done（CLOSED 2026-10-17 · PR #262 MERGED squash e1697ad · mergedAt 2026-10-17T05:50:17Z · CLOSE 档 docs/tasks/close/close_rag_golden_eval_r4_r5_20261017.md）
> **类型**：评测 / 证据资产（检索轨 golden scenario 结案 + Demo 证据表 · **不改生产语义**）  
> **上游**：路线 `../ops-desk-workspace/docs/05-plan/04-agent-completion-roadmap_v1_zh.md` §P1-RAG（R-4 / R-5 标注「仍可能缺口 · 评测结案勿假设」）· 契约 `../ops-desk-workspace/docs/contracts/rag-knowledge-contract-v1.md`（R-P0 已定稿 2026-08-08）  
> **分支**：`task/rag-golden-eval-r4-r5`（自 master 新切）  
> **评测纪律**：自建 scenario eval，**不用 BMH**（路线 §3）

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `rag_golden_eval_r4_r5` |
| **git_branch** | `task/rag-golden-eval-r4-r5` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 汇总/断言脚本 CI 确定性（fake 报告样例喂入 · 不连真库/真 LLM）；结案级真跑与 Demo 证据采集 = 需库与 LLM 访问，钉为前置条件/人工闸项，不占 CI 绿 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `none` |
| **graph_delta** | `none` |
| **graph_delta_note** | 评测资产（evals/ + tests/ + reports/）；无新模块/无对外契约改动 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 评测口径真值在路线 §P1-RAG 与契约页；本 task 不回写 coding_wiki 正文（30 实判可改 volatile 短注） |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,20,30,40` |
| **invoke_retention_profile** | `default` |
| **experience_capture** | `recommended` |
| **kpi_aggregator** | `CLOSE` |
| **orchestration** | 10 落稿 → 20 R1 → 维护者签三闸 → 30（汇总脚本+测试+模板）→ 40/维护者真跑回填结案报告与证据表 → CLOSE |
| **freeze_id** | 无 |
| **related_tasks** | [`task_golden-query-set-v1.md`](../done/task_golden-query-set-v1.md)（金标集+runner 已闭环 · 本 task 只增量结案）· [`task_eval_goldenset_lg_rag.md`](../done/task_eval_goldenset_lg_rag.md) · [`task_memory_golden_eval.md`](../done/task_memory_golden_eval.md) |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | approved | 20, 30 | 2026-10-17 维护者授权 00 代录（m00238） |
| HG-AUDIT-R1 | approved | 30 | 2026-10-17 维护者授权 00 代录（m00238 · 20 R1 书面审豁免） |
| HG-GRAPH-MODULES | approved | 30 | 2026-10-17 代录：全局真值 approved（01_modules.md:63）· `graph_change_layer=none` |
| HG-EVAL-LIVE-RUN | pending | 40 | 待维护者签：结案级真跑需本地/生产库 + 真 LLM key 访问授权（30 交付物本身不依赖本闸） |

---

## 背景与目标

### 已覆盖什么（防重复纪律 · 禁重复立项）

| 面 | 状态 | 真值 |
|----|------|------|
| 金标查询集 v1（73 条四象限 zh2en=26 / zh2zh=20 / en2en=16 / negative=11） | **已闭环** | [`task_golden-query-set-v1`](../done/task_golden-query-set-v1.md) · `evals/golden/queries_v1.yaml` |
| R-4 runner（生产同路径 hybrid_recall → grade → decide · 卫生过滤 `hygiene_denylist.yaml`） | **已闭环** | `evals/golden/run_eval.py` · `tests/test_golden_eval_runner.py` |
| 多轮对照报告（含 qdrant 后端 / A-C 臂 / rerank 地板参数系列） | 已产出（过程稿） | `reports/r4*.yaml`（18 份 · 首跑 2026-08-11） |
| Agent 模块金标（router / strategy_builder / supervisor / e2e 确定性评估器） | **已闭环 · 非检索轨** | [`task_eval_goldenset_lg_rag`](../done/task_eval_goldenset_lg_rag.md) · `evals/agent/golden/` |
| 记忆轨金样评测（抽取/复述/supersede + 扫参） | **已闭环 · 非检索轨** | [`task_memory_golden_eval`](../done/task_memory_golden_eval.md) · `evals/memory/` |

### 缺口（本 task 只做这些增量）

1. **R-4 结案级汇总评测**：路线 R-4 要求四类 golden + recall@k 断言到文档 ID + 引用 ∈ 命中集 + 拒答正确率 + 小样本老实标 confidence。现有 `reports/r4*.yaml` 是逐案过程稿，**无一份对齐路线的结案报告**（逐象限汇总 + 门槛判定 + confidence + 观测口径），结案与否勿假设。
2. **跨语言面（zh2en ≥1/3 门槛）**：路线钉「ZH问→EN文档 跨语言 ≥1/3」；需结案报告显式给出 zh2en 象限命中率并判定达成情况。
3. **拒答正确率统计**：负样本 11 条的拒答正确率（gate_action=refuse 占比 + 误拒/误答分类）需显式汇总。
4. **R-5 Demo 证据表**：版本/输入/结果/错误（生产候选增强口径）——路线标注仍可能缺口，现仓无对应资产。
5. **观测口径对齐**：报告头部对齐 SPEC-evaluation-observation（路线 A-P1-3 称其已签 2026-08-07；**照登：无实证**——该 SPEC 真值文件在 api 仓与 workspace 仓均未检索到，以路线引用口径为准，30/40 若找到真值文件按实校正）。

### 目标

交付：结案级汇总脚本（复用 `run_eval.py` 产物，不旁路重写检索路径）+ 确定性测试 + 结案报告模板 + R-5 Demo 证据表模板；真跑回填由 40/维护者在授权环境下执行。**不改**检索/评级/拒答生产代码语义。

---

## 范围

- **E1 · 汇总脚本**：`evals/golden/summarize_r4.py`（或 30 裁定等价命名）：读 `reports/r4*.yaml` 或 runner 新跑产物 → 逐象限聚合（recall@5 命中率 / min_relevance 达成率 / citation_in_hits 达成率 / 负样本拒答正确率与误拒·误答分类）→ zh2en 象限对路线「≥1/3」门槛显式判定 → 小样本 confidence 标注（n 小即老实标，如 Wilson 区间或「n=26，置信有限」字样）→ 出结案报告 YAML + Markdown 摘要。
- **E2 · 结案报告模板**：`reports/r4_final_TEMPLATE.md`（版本/embedder/grader/语料 N/逐象限指标/门槛达成/未达成项与原因/观测口径注记）；真跑产物落 `reports/r4_final_*.md|yaml`。
- **E3 · R-5 Demo 证据表**：`evals/golden/demo_evidence_TEMPLATE.md`（版本/commit/输入 query/结果摘要/引用/错误与降级行为/复现命令）；真跑后由 40/维护者填 `reports/demo_evidence_*.md`。
- **E4 · CI 测试**：`tests/test_golden_eval_r4_summary.py`：fake 报告样例喂入 → 聚合正确性断言（含四象限分组、zh2en 门槛判定三态、拒答正确率分类、confidence 标注存在性）；不连真库/真 LLM/外网。
- **E5 · 契约核对**：30 亲读契约 `../ops-desk-workspace/docs/contracts/rag-knowledge-contract-v1.md` 对照现网实现（`app/ops/rag/`）；发现漂移 → 记入结案报告「契约漂移」节并走 failure_path FP-5 上抛，**不在本 task 改契约**。

## 非范围

- 改 `app/ops/rag/**` / `app/ops/lg_rag/**` 检索、评级、拒答、融合代码语义；改生产默认开关/env 默认值
- 改契约页 `../ops-desk-workspace/docs/contracts/rag-knowledge-contract-v1.md`（漂移上抛，修订另 task）
- 扩金标集条数 / 重写 `evals/golden/run_eval.py` / `queries_v1.yaml` 语义（本 task 复用其产物；确需勘误的个别条目经 20/维护者裁定后另记）
- 重复立项 agent 模块金标（[`task_eval_goldenset_lg_rag`](../done/task_eval_goldenset_lg_rag.md)）与记忆轨评测（[`task_memory_golden_eval`](../done/task_memory_golden_eval.md)）已闭环面
- 调参（rerank 地板/权重/HNSW）：报告只如实记录指标，「未达门槛不改默认」先例（[`task_rag_reranker_p0`](../done/task_rag_reranker_p0.md) 系）不变
- BMH 接入、LLM-as-judge 上云、Langfuse Dataset/CI 新 workflow
- 生产向量水位核查（另 task [`task_prod_vector_waterline_check.md`](./task_prod_vector_waterline_check.md)）

---

## 失败路径

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----------|----------|--------|----------|
| FP-1 HG-AUDIT-R1 pending 即 30 | GATE_VERIFY **拒开工** | 是 | — |
| FP-2 汇总脚本读到残缺/非法报告 | 显式报错非零退出（不静默跳过条目冒充全量） | 是（修/重跑报告） | 报告缺项如实可见 |
| FP-3 zh2en 未达 ≥1/3 或拒答正确率差 | 报告如实判 NOT-MET + 失败条目清单；**不改默认参数**（调参另 task） | 是 | 结案报告 |
| FP-4 真跑缺库/缺 LLM key | HG-EVAL-LIVE-RUN 未签则 40 不跑；脚本 preflight 显式失败不冒充 | 是 | 40 invoke / 报告头部 |
| FP-5 契约页与实现漂移 | 记入结案报告「契约漂移」节 + invoke 上抛 00/维护者；本 task 零改契约 | 是（另 task 修） | 报告 + 上抛记录 |
| FP-6 30 顺手改检索/拒答语义 | 零 diff 契约（`app/ops/rag/**` · `app/ops/lg_rag/**`），审查拒收 | 是 | — |
| FP-7 小样本被当「已达标」引用 | 报告头部写死样本量与 confidence；40 核验 | 否 | 报告头部 |
| FP-8 SPEC-evaluation-observation 真值文件仍不可得 | 报告按路线引用口径对齐并显式注记「SPEC 文件未检索到 · 照登：无实证」 | 是 | 报告头部注记 |

---

## 验收标准

- [x] **TC-R4-1**：`evals/golden/summarize_r4.py` 落地；对 fake 样例报告聚合断言全绿（`pytest tests/test_golden_eval_r4_summary.py -q` → 12 passed，可对命令输出断言）
- [x] **TC-R4-2**：结案报告模板 `reports/r4_final_TEMPLATE.md` 含逐象限（zh2en/zh2zh/en2en/negative）recall@5 + min_relevance + citation_in_hits + 拒答正确率（误拒/误答分类）+ zh2en「≥1/3」门槛显式判定位 + 样本量/confidence 位 + 观测口径注记位
- [x] **TC-R4-3**：R-5 Demo 证据表模板 `evals/golden/demo_evidence_TEMPLATE.md` 含版本/commit/输入/结果/引用/错误与降级/复现命令七段；真跑回填后至少 4 条（每象限 ≥1 条 · 含至少 1 条负样本拒答演示）——回填要求已写入模板纪律节
- [x] **TC-R4-4**：`app/ops/rag/**` · `app/ops/lg_rag/**` · `app/db/**` **零 diff**；`evals/golden/queries_v1.yaml` 与 `run_eval.py` 零语义 diff（30 仅新增 summarize_r4.py + 测试 + 模板）
- [ ] **TC-R4-5**：结案真跑产物 `reports/r4_final_*` 存在（40/维护者在 HG-EVAL-LIVE-RUN 授权后跑；头部写死门槛与达成情况与 confidence）；zh2en 命中数/26 与拒答正确率显式可见——**待 40/维护者（HG-EVAL-LIVE-RUN pending）**
- [x] **TC-R4-6**：契约核对结论落 invoke（**零漂移**；观察项 `Relevance.UNRATED` 内部标记非漂移；本 task 契约文件零 diff）
- [x] **TC-R4-7**：`ruff` 触及路径绿；`pytest tests/test_golden_eval_runner.py` 13 passed 零新增红；`npx --yes spec-wave task lint --file docs/tasks/active/task_rag_golden_eval_r4_r5.md` 输出含 `LINT: PASS`

## 依赖

- 路线真值：`../ops-desk-workspace/docs/05-plan/04-agent-completion-roadmap_v1_zh.md` §P1-RAG（R-4/R-5）· §3 测评纪律（自建不用 BMH）
- 契约页（只读核对 · 不改）：`../ops-desk-workspace/docs/contracts/rag-knowledge-contract-v1.md`
- 已闭环资产（复用不重写）：`evals/golden/queries_v1.yaml` · `evals/golden/run_eval.py` · `evals/golden/hygiene_denylist.yaml` · `tests/test_golden_eval_runner.py` · `reports/r4*.yaml`
- 防重复参照：[`task_golden-query-set-v1`](../done/task_golden-query-set-v1.md) · [`task_eval_goldenset_lg_rag`](../done/task_eval_goldenset_lg_rag.md) · [`task_memory_golden_eval`](../done/task_memory_golden_eval.md)（「真跑=维护者复制区」先例）
- 编码规范：`docs/standards/CODING_BACKEND_L2_v1_zh.md`
- 姊妹 task（水位核查 · 独立立项）：[`task_prod_vector_waterline_check.md`](./task_prod_vector_waterline_check.md)

## 给执行帽的必读列表

1. 本 task 全文（防重复表 · 缺口清单 · FP-5 契约纪律 · 零 diff 硬项）。
2. 路线 §P1-RAG + §3（`../ops-desk-workspace/docs/05-plan/04-agent-completion-roadmap_v1_zh.md`）。
3. `evals/golden/run_eval.py` docstring 与 `reports/r4-1.yaml` 样例结构（禁信转述）。
4. [`task_golden-query-set-v1.md`](../done/task_golden-query-set-v1.md)（金标集来历 · G67 双审教训）。
5. [`task_memory_golden_eval.md`](../done/task_memory_golden_eval.md)（评测纪律先例：显式失败不冒充 · 报告写死门槛 · 真跑隔离）。
6. `docs/standards/CODING_BACKEND_L2_v1_zh.md`。
7. `docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`。

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|---|------|------------|----------------------|----------------|
| R0 | 框定：R-4/R-5 是「结案」缺口非「从零」缺口；金标集+runner+过程报告已闭环 | false | — | 结案标准依赖路线口径 |
| R1 | 证据：73 条四象限在库 · r4 报告 18 份均为过程稿 · 无结案汇总/Demo 证据表 · SPEC-observation 文件未检索到（照登：无实证） | false | — | SPEC 真值若另有藏所 |
| R2 | 方案：汇总脚本吃既有产物 · 结案报告+证据表模板先行 · 真跑钉人工闸 | false | — | 汇总脚本与 runner 字段耦合 |
| R3 | 反例：防重复三 done task · 契约漂移只上抛 · 零生产 diff · 小样本 confidence 诚实 | false | — | 个别金标条目勘误诉求 |
| R4 | 验收：TC-R4-1..7 可对命令输出断言 · 真跑不占 CI 绿（HG-EVAL-LIVE-RUN） | false | — | 真跑环境可得性 |
| R5 | 收口：草稿交 20；三闸 pending 待维护者签；禁 30 | true | 增量边界与先例已钉死，再轮无新锚点 | 闸未签 |

**actual_last_round**：R5（early_stop）

### R0 · 问题框定

路线 R-4/R-5 标「仍可能缺口 · 结案勿假设」。精读三份 done task 后确认：缺口在**结案级汇总 + 门槛判定 + Demo 证据表**，不在金标集或 runner 本体。

### R1 · 证据收集

`queries_v1.yaml` 73 条四象限（zh2en=26/zh2zh=20/en2en=16/negative=11）定稿于 2026-08-11；`reports/` 有 r4 系列 18 份过程报告（含 qdrant 后端对照），无逐象限门槛判定的结案稿；仓内无 Demo 证据表资产；SPEC-evaluation-observation 真值文件两仓未检索到，照登无实证。

### R2 · 方案生成

不新造 runner：汇总脚本读既有 YAML 产物聚合；模板先行使真跑只填数；真跑授权独立闸（memory-golden-eval「真跑=维护者复制区」先例）。

### R3 · 反例与边界

禁重复立项已闭环面（金标集/agent 金标/记忆轨）；契约漂移只记录上抛；`app/ops/rag/**` 零 diff；「未达门槛不改默认」先例沿用。

### R4 · 验收/可测性

聚合逻辑用 fake 报告样例确定性断言（分组/门槛三态/拒答分类/confidence 存在）；真跑产物验收落 40/维护者，不绑架 CI。

### R5 · 收口

草稿交 20 R1；三闸与 HG-EVAL-LIVE-RUN 全 pending 待维护者签；闸未签禁 30。

### 自检结论（执行者）

30 自检（2026-10-17 · hat 30）：

| 命令 | 结果 | exit |
|------|------|------|
| `npx --yes spec-wave verify --target . --task docs/tasks/active/task_rag_golden_eval_r4_r5.md` | VERIFY: PASS（三闸 approved · HG-EVAL-LIVE-RUN pending 不阻 30） | 0 |
| `pytest tests/test_golden_eval_r4_summary.py -q` | 12 passed（四象限分组/门槛三态含 1/3 边界/拒答分类/confidence 标注/FP-2 显式失败/CLI 端到端确定性/r4-1.yaml 结构冒烟） | 0 |
| `pytest tests/test_golden_eval_runner.py -q` | 13 passed（既有回归零新增红） | 0 |
| `ruff check evals/golden/summarize_r4.py tests/test_golden_eval_r4_summary.py` | All checks passed! | 0 |
| `python evals/golden/summarize_r4.py --report reports/r4-1.yaml --out-* /tmp/…` | SUMMARY zh2en=19/25 gate=MET refuse=9/10（过程稿冒烟 · 结论仅作结构验证，非结案数值） | 0 |
| `npx --yes spec-wave task lint --file docs/tasks/active/task_rag_golden_eval_r4_r5.md` | 含 LINT: PASS | 0 |
| `git status`（app/ 零 diff） | `app/` 无任何改动；`queries_v1.yaml`/`run_eval.py` 零 diff | — |

**验收摘要**：TC-R4-1/2/3/4/6/7 绿；TC-R4-5 待 HG-EVAL-LIVE-RUN approved 后由 40/维护者真跑回填。

**已知未测项**：结案级真跑（需库+LLM key，闸 pending）；Demo 证据表回填；过程稿数值的结案效力（旧报告 71 条 ≠ 现金标 73 条，真跑须用现集）。

**契约核对（TC-R4-6）**：亲读契约 v1 对照 `app/ops/rag/grader.py` / `retrieve.py` / `app/ops/chat/rag_nodes.py` → **零漂移**（四级枚举/gate 决策/拒答文案逐字/引用卡字段/snippet≤400+前缀剥离/RRF 1:1 融合且分数不进 gate 全对齐）；观察项：`Relevance.UNRATED`（level=-1）为内部标记、never 出现在 grader 输出，不计漂移；SPEC-evaluation-observation 真值文件两仓未检索到（照登：无实证，FP-8 注记已入模板）。

**结论**：30 范围交付完成，可交 40/维护者。

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-17 | 10-task 落稿（R-4 结案级评测 + R-5 Demo 证据表 · 增量立项 · 三闸 pending 待维护者签 · 未 commit） |
| 2026-10-17 | 30 交付：summarize_r4.py + 12 项确定性测试 + r4_final_TEMPLATE.md + demo_evidence_TEMPLATE.md + 契约核对零漂移；TC-R4-1/2/3/4/6/7 绿，TC-R4-5 待闸 |
| 2026-10-17 | CLOSED：PR #262 MERGED squash e1697ad（2026-10-17T05:50:17Z）· 批量关账 · CLOSE 档 close_rag_golden_eval_r4_r5_20261017.md |
