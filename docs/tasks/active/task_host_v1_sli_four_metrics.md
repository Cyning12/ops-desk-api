# Task：Host v1.0 出口跟进 · SLI 四项定稿（定义 / 有数 / 看板）（host-v1-sli-four-metrics）

> **状态**：`active`（2026-09-24 · 00 10-task 起草 · 出口复核 G1）  
> **类型**：observability / eval follow-up（**优先 docs+聚合口径+看板；热路径埋点按实判最小 diff**）  
> **依据**：`docs/reports/host_v1_exit_review/REPORT_host_v1_exit_review_20260924_v1_zh.md` · GAP G1 · 07 §4 指标面  
> **上游**：`docs/spec/agent-infra/07_host_v1_landing_plan_v0.md` §4 · `docs/spec/agent-infra/04_eval_and_observability_plan_v0.md` · `docs/spec/agent-infra/eval/ROADMAP_eval_observability_v0.md` §3 · V1-C Cost 落点  
> **分支**：`task/host-v1-sli-four-metrics`（**禁止 master 直改 · 30 由 00 委派**）  
> **10 注**：2026-09-24 · 00 亲起（出口复核授权开最早跟进 · 承 harness-00-delegate-only「无初稿起草第一步」）

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `host-v1-sli-four-metrics` |
| **git_branch** | `task/host-v1-sli-four-metrics` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 四项 SLI 定义表可机读断言（键名/公式/成功口径）；Cost 聚合与 V1-C `cost_per_successful_task` 对拍；P99/完成率/命中率有 mock 聚合断言或导出样例；看板交付=Langfuse Dashboard 截图或 GUIDE 可复现步骤+样例查询；禁止伪造 0 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | **`none`（30 实判）**：字典/GUIDE/`evals/agent/sli` 聚合；**未**触 `app/` 热路径 |
| **graph_delta** | 无 |
| **graph_delta_note** | 30 留痕：D4=docs-only · 无一级模块/路由/表/SSE；B1 n/a |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 契约真值在本 task + 07 §4 + eval ROADMAP；GUIDE 属范围项 |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,20,30,40` |
| **invoke_retention_profile** | `default` |
| **experience_capture** | `recommended` |
| **kpi_aggregator** | `CLOSE` |
| **orchestration** | 10 → 20-task-audit → HG-AUDIT-R1 → 30（00 委派）→ 40 → PR → CLOSE；**不重开 V1-A~E** |
| **freeze_id** | 无 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | **approved** | 20-R1, 30 | 2026-09-24 · **00 代录**（维护者令原话：「生成下v1.0出口复核的00 Prompt，授权00签收过程文档」· 授权面含本复核相关 HG-TASK-DRAFT） |
| HG-AUDIT-R1 | **approved** | **30** | 2026-09-24 · **00 代录**（维护者令原话：「委派，并授权签收后续文档」）；依据：20-task-audit R1 **PASS-WITH-NITS** 零阻塞（`docs/harness/reviews/task_host_v1_sli_four_metrics_audit_R1_20260924.md`） |
| HG-GRAPH-MODULES | **approved** | **30** | 2026-09-24 · 00 代录 · 预期 `graph_change_layer=none`（真读 `01_modules` 签录至 V1-E）；若 30 触行备注 → 人签新行随交付 |
| HG-PILOT-OPSDESK-GLAYER | n/a | — | 不涉 |

---

## 背景与目标

出口复核（2026-09-24）：功能面 V1-A~E **PASS**；指标面 **PASS-WITH-GAP**——07 §4 要求四项「有定义、有数、有看板」，现状仅 **Cost per Successful Task** 有 Host 定义+单测有数且 **明确无看板**；端到端 P99 / 任务完成率 / 能力命中率停在大纲候选与 Eval E1 缺口表。

一句话：把四项升为可验收的 Host v1.0 SLI 出口面（字典钉死 + 可复现有数 + 看板或等价 GUIDE），闭合出口 GAP G1。

---

## 钉死契约

| 项 | 钉死 |
|----|------|
| **四项集合** | ① 端到端延迟 P99 ② 任务完成率 ③ 能力命中率 ④ Cost per Successful Task（承 V1-C，不另发明公式） |
| **定义落点** | 增补 `docs/spec/agent-infra/eval/` 下 v1.0 出口 SLI 表（或 ROADMAP §3 扩展节）· 键名稳定 · 与 E1 字典对齐不打架 |
| **成功任务口径** | **承 V1-C 锁死**：成功任务 = supervisor run 终态 `done` 的 run_id 集合（调用方按 `run_events` 筛后传入；与 `cost_per_successful_task` docstring 一致）；写入定义表，禁另发明 |
| **有数** | 每项至少一种：聚合纯函数单测 / 导出样例 CSV 或 JSON / Langfuse 可筛查询步骤产出样例数 |
| **看板** | Langfuse Dashboard（优先）或内部 GUIDE「三步打开看板」+ 截图/字段清单；**禁止**只写「以后再做」 |
| **Cost** | 复用 `app/llm/budget.cost_per_successful_task`；补看板/导出接线，不改估算铁律（缺单价 `unknown` 不伪造 0） |
| **E1 对齐提示** | 完成率↔`avail.success` · 命中率↔`avail.capability_ok`（metadata `ok`≠SLI）· Cost↔Host 函数（非另起 `cost.usd_est` 语义）· P99：**E1 §3.2 无现成 latency score** → D1 须扩展字典键名（禁同义异名） |
| **默认** | 新热路径 score 默认关或观察；不破既有 off 零 diff 纪律 |
| **D4→B1** | 若 D4 触发热路径/聚合码改动 → 交付前补「旧测 grep 影响面」三态（回归/新增/迁移无）；docs-only 则 n/a |

### 非范围

- ❌ 重开 / 重做 V1-A~E 功能波  
- ❌ v2.0 多服务拆分 · 自建完整可观测中台  
- ❌ 商务对账计费 / 跨租户账单  
- ❌ 改 freeze 契约 / 新 SSE 事件 / 新对外计费 API（除非定义表明确且补闸）  
- ❌ 顺手改 capability/delegation/memory 语义  

---

## 范围

- [x] **D1 · 定义表**：四项公式/标签/成功口径/数据源落盘（eval 域）  
- [x] **D2 · 有数**：Cost 对拍既有函数；其余三项 mock/导出/查询样例可断言  
- [x] **D3 · 看板**：Langfuse Dashboard 或 GUIDE 可复现步骤 + 交付物入 `docs/reports/host_v1_exit_review/` 或 `docs/guides/`  
- [x] **D4 ·（按实判）热路径最小埋点**：仅当定义依赖缺失 metadata/score 时最小 diff；否则 docs-only  
- [x] **D5 · 测试/图谱**：单测绿 · ruff 净增 0 · graph 按实判  

---

## failure_paths

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----------|----------|--------|----------|
| `HG-AUDIT-R1` 未签即 30 | **拒开工** | 是 | 是 |
| 四项缺任一「定义」行 | **拒收** | 是 | 是 |
| 看板仅口头无 GUIDE/截图/可复现步骤 | **拒收** | 是 | 是 |
| Cost 缺单价伪造 0 | **拒收** | 是 | 是 |
| 重开 V1 功能面改码 | **拒收** | 是 | 是 |
| 定义与 E1 字典同义异名冲突 | 回 10 对齐字典后重交 | 是 | 否 |
| D4 触码却未补 B1 旧测影响面 | **拒收** | 是 | 是 |
| 新 score 默认开破坏既有 off 零 diff | **拒收** | 是 | 是 |

---

## 验收标准

- [x] HG-AUDIT-R1 approved 后方可勾选下列码/文档项  
- [x] 四项均有定义表行（公式 + 标签 + 成功口径 + 数据源）  
- [x] 四项均有「有数」证据（单测或导出样例或查询步骤产出）  
- [x] 四项均有看板或等价 GUIDE（可复现）  
- [x] Cost 与 `cost_per_successful_task` 口径一致（对拍断言）  
- [x] `pytest` 触及面绿 · `ruff check` 净增 0 · `graph_change_layer` 如实  
- [ ] 出口报告 G1 可在 CLOSE 时回写为 closed  
- [x] （条件）若 D4 触码：B1 旧测影响面三态已落盘并逐条处置 · **本波 D4=docs-only → B1 n/a**  

---

## 依赖

| 依赖 | 说明 |
|------|------|
| 出口报告 | `docs/reports/host_v1_exit_review/REPORT_host_v1_exit_review_20260924_v1_zh.md` |
| 07 §4 | `docs/spec/agent-infra/07_host_v1_landing_plan_v0.md` |
| 04 / E1 | `docs/spec/agent-infra/04_eval_and_observability_plan_v0.md` · `eval/ROADMAP_eval_observability_v0.md` |
| V1-C | `docs/tasks/done/task_host_v1_llm_factory_closure.md` · `app/llm/budget.py` |
| E5 先例 | `docs/tasks/done/task_eval_token_cost_ledger.md` |
| 编码规范 | `docs/standards/CODING_BACKEND_L2_v1_zh.md`（若改 `app/`） |

---

## 给执行帽必读

1. 本 task · 出口报告 §指标面  
2. 07 §4 · eval ROADMAP §3  
3. `app/llm/budget.py` `cost_per_successful_task`（只读对齐）  
4. `FRAGMENT_30_gate_verify_v1_zh.md`（30 前闸表）  

---

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|----|------|------------|----------------------|----------------|
| R0 | 出口 GAP=指标四面未齐；Cost 半成；其余三项定义缺 | no | — | Langfuse 项目权限/现网数据是否可得 |
| R1 | HG-TASK-DRAFT approved · HG-AUDIT-R1 pending · graph 预期 none | no | — | 无 |
| R2 | 竖切 D1 定义→D2 有数→D3 看板→D4 按需埋点；优先 docs+聚合不重做 V1 | no | — | 热路径埋点爆炸半径 |
| R3 | failure_paths 八条（原六 + D4 缺 B1 / off 零 diff）；最锋利=看板空真与伪造 0 | no | — | 无 |
| R4 | 验收 8 条可勾选（含条件 B1）；对拍 Cost；pytest 触及面 | no | — | 无 |
| R5 | 可交 20；不代签 HG-AUDIT-R1 | yes | 方案唯一 · 锚点已钉 · 无功能波分叉 | 见 R0/R2 |

**actual_last_round**：R5 · **early_stop**：yes · **residual_risks**：见 R0/R2

### R0 · 问题框定

07 四项出口未闭合；跟进单只补观测面，不重开功能波。

### R1 · 开工闸

HG-TASK-DRAFT=approved（00 代录）；HG-AUDIT-R1=pending → 禁 30。

### R2 · 竖切

定义先行，再有数，再看板；埋点按实判。

### R3 · 失败语义

见 failure_paths（八条：过程闸 + 定义缺 + 看板空真 + 伪造 0 + 重开 V1 + E1 同义异名 + D4 缺 B1 + off 零 diff）。

### R4 · 可测性

定义表可断言 + Cost 对拍 + 看板 GUIDE 可复现；验收 8 条（末条条件触发）。

### R5 · 交付判定

可交 20-task-audit。

### 自检结论（执行者）

| 项 | 结果 |
|---|---|
| 分支 | `task/host-v1-sli-four-metrics`（非 master） |
| GATE_VERIFY | HG-AUDIT-R1=approved · `npx spec-wave verify --task …` = **PASS** |
| D1 | `docs/spec/agent-infra/eval/SLI_host_v1_four_metrics_v1.md` + yaml |
| D2 | `evals/agent/sli/aggregate_sli.py` + fixture；Cost 对拍 `cost_per_successful_task` |
| D3 | `GUIDE_host_v1_sli_dashboard_v1.md`（三步 + 字段清单） |
| D4 | **docs-only** · 未改 `app/` · B1 n/a · `graph_change_layer=none` |
| D5 | `pytest tests/eval/test_host_v1_sli.py` + `tests/test_llm_budget.py` → **37 passed** · `ruff check evals/agent/sli tests/eval/test_host_v1_sli.py` 净增 0 |
| 触 app/ | **否**（`git diff master -- app/` 空） |
| 40 验收 | **PASS**（2026-09-24 独立真跑）· invoke `invoke_20260924_40_host-v1-sli-four-metrics.md` |
| G1 CLOSE | **hold** · 出口报告已注「40 验收 PASS · 待 merge 后 closed」· **未**归档 |
| commit | **未**（维护者未令） |

---

## 修订记录

| 日期 | 摘要 |
|------|------|
| 2026-09-24 | 00 10-task 落稿（出口复核 G1）· HG-TASK-DRAFT 00 代录 approved · HG-AUDIT-R1 pending |
| 2026-09-24 | **00 代录 HG-AUDIT-R1=approved**（维护者令「委派，并授权签收后续文档」· 20 R1 PASS-WITH-NITS）· 委派 30 |
| 2026-09-24 | 20-task-audit R1 **PASS-WITH-NITS** 微修（不改范围实质）：成功口径承 V1-C 锁死（去「建议」）· 补 E1 对齐提示/D4→B1 钉死 · failure_paths +2 · 验收条件 B1 · R3/R4 计数同步；审查文 `docs/harness/reviews/task_host_v1_sli_four_metrics_audit_R1_20260924.md` |
| 2026-09-24 | **30**：D1–D5 交付 · docs-only · invoke `invoke_20260924_30_host-v1-sli-four-metrics.md` |
| 2026-09-24 | **40 PASS**：verify/pytest/ruff 真跑绿 · `app/` diff 空 · invoke `invoke_20260924_40_…` · G1 注待 merge 后 closed · 未 CLOSE |
