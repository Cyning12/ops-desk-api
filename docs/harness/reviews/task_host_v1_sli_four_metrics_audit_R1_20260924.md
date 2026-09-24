# 审查文：task_host_v1_sli_four_metrics · 20-task-audit R1（2026-09-24）

> **hat_id**：20-task-audit（R1 轮 · 书面审查 · 不改 task 范围实质 · 不动 app/ · 不签发 human_gate）  
> **审查对象**：`docs/tasks/active/task_host_v1_sli_four_metrics.md`（active · 2026-09-24 00 10-task 落稿 · 出口复核 G1）  
> **对照真值**：出口报告 §7 指标面 · `07_host_v1_landing_plan_v0.md` §4 · `eval/ROADMAP_eval_observability_v0.md` §3 · `app/llm/budget.py:cost_per_successful_task`  
> **复核方式**：全部锚点本帽真读亲跑（2026-09-24 · 工作目录 ops-desk-api/）

---

## 结论摘要

| 维度 | 结论 |
|------|------|
| **内容** | **PASS-WITH-NITS**——阻塞项为零；3 条非阻塞 nit 已微修留痕（成功口径锁死 / E1 对齐+D4→B1 / FP+验收计数同步） |
| **流程闸 HG-AUDIT-R1** | **pending**（闸表如实 · 本审查不落 30 Prompt · 维护者签闸清单见文末） |

**总评**：task 与出口 G1 / 07 §4 四项集合一致；Cost 锚点与 V1-C 纯函数对拍纪律正确；非范围锁死不重开 V1；主交付面为 docs+聚合+看板，**不属**「改默认值/校验/策略门/fallback」硬行为变更类，故缺完整 B1 实扫表可接受——以条件条款覆盖 D4 触码场景即可。lint PASS。

---

## 逐面证据（带行号）

### 1 · 闸表四行诚实（task 人工闸表）

| 闸 | task 记载 | 本帽复核 |
|----|-----------|----------|
| HG-TASK-DRAFT | **approved** · 00 代录 · 维护者令原话留痕 | 与 `invoke_20260924_00_host-v1-sli-four-metrics.md` 同令一致 ✓ |
| HG-AUDIT-R1 | **pending** · blocks 30 | **pending 属实** ✓（本帽不代签） |
| HG-GRAPH-MODULES | **approved** · 预期 `graph_change_layer=none` · 签录至 V1-E | 真读 `01_modules.md` L110 = 2026-09-24 V1-E（splittability）签录行 ✓；预期 none + 偏离回炉（task `graph_delta_note`）诚实 ✓ |
| HG-PILOT-OPSDESK-GLAYER | n/a | 不涉物理分层试点 ✓ |

### 2 · 对照真值一致性（四项集合 / G1 / E1）

| 源 | 声称 | 复核 |
|----|------|------|
| 07 §4 指标行 | 端到端 P99 / 任务完成率 / 能力命中率 / Cost per Successful Task · 有定义、有数、有看板 | task 钉死契约四项集合逐字对齐 ✓ |
| 出口报告 §7 | PASS-WITH-GAP · Cost 有定义+有数无看板；其余三项定义/有数/看板皆缺 | task 背景段与 G1 建议 slug 一致 ✓ |
| 出口 G1 | 钉死定义 + 数据落点 + Langfuse/导出看板 | 范围 D1–D3 + 条件 D4 覆盖 ✓ |
| ROADMAP §3 | `avail.success` / `avail.capability_ok` score=缺口；metadata `ok`≠命中率 SLI；**无** latency/P99 score 名 | 原 task「与 E1 对齐」成立但未点名 P99 须扩字典 → **N2**（已微修「E1 对齐提示」） |
| `cost_per_successful_task` | Σ成功 run cost / 成功任务数；成功=done run_id（调用方筛）；缺单价 → `unknown` 不伪造 0 | 真读 `app/llm/budget.py` L307-335 docstring+实现一致；task Cost 钉死「复用函数 · 不改估算铁律」✓ |

### 3 · 范围 / 非范围 / failure_paths / 验收

- **范围 D1–D5**：定义→有数→看板→按需埋点→测试/图谱，竖切与 R2 一致；D4 按实判 docs-only 优先，与类型「observability follow-up」自洽 ✓  
- **非范围**：五条覆盖重开 V1 / v2 拆分 / 对账计费 / freeze·SSE·计费 API / 顺手改其它语义 —— 与出口「明确不做」对齐 ✓  
- **failure_paths**（微修后八条）：闸未签拒开工 · 缺定义拒收 · 看板空真拒收 · 伪造 0 拒收 · 重开 V1 拒收 · E1 同义异名回 10 · D4 缺 B1 拒收 · off 零 diff 拒收 ✓  
- **验收**（微修后 8 条）：人工闸 1 + 四项×3 面（定义/有数/看板压成勾选）+ Cost 对拍 + pytest/ruff/graph + G1 closed + 条件 B1；均可否定性/可机验或可复现 GUIDE，无「以后再做」空真 ✓  
- **图谱义务**：预期 none；触 tracing/llm 行备注则补签 —— 与 `graph_change_layer` 字段一致 ✓

### 4 · B1 旧测影响面（K7 · 行为变更类必查）

**裁定：本 task 主面非行为变更类**（不改既有默认值/校验/策略门/fallback；Cost 只复用；新 score「默认关或观察」）。  
缺「完整 B1 实扫表」**不退回 10**。  
条件覆盖：钉死「D4→B1」+ failure_path + 条件验收（微修 N2）——若 30 触热路径须补三态后再交。

相关旧测锚点（供 30 按需扫，**非**本轮强制清单）：`tests/test_llm_budget.py`（含 Cost 对拍）· `test_ops_tracing.py` · `test_llm_usage*.py` · `test_admin_capability_observability.py`。

### 5 · 思考轮 R0–R5

控制表六轮齐全 · `actual_last_round=R5` · `early_stop=yes`（方案唯一 · 锚点已钉 · 无功能波分叉）理由充分；残余风险 R0（Langfuse 权限/现网数据）与 R2（埋点爆炸半径）携带至 R5 ✓。  
微修后 R3/R4 与 FP 八条、验收 8 条计数同步（原 R3「六条」与修订前一致，属过程计数 · **N3**）。

### 6 · 机械闸

- `npx spec-wave task lint --file docs/tasks/active/task_host_v1_sli_four_metrics.md` → **LINT: PASS**（仓钉 spec-wave **3.0.1**）  
- `required_invoke_hats` 含 `20` → 本 invoke 强制落盘 ✓

---

## 阻塞清单（内容）

**无。**

## 非阻塞 nit（3 条 · 本帽已微修 · 不改范围实质）

- **N1 · 成功任务口径偏软**：原文「须钉死（建议：…）」易被 30 另发明；V1-C/`cost_per_successful_task` 已锁死 done/`run_events`。→ 已改为「承 V1-C 锁死」并写禁另发明。  
- **N2 · E1 对齐与 D4→B1 欠显式**：P99 在 E1 §3.2 无现成 score；D4 触码时缺 B1 条件闸。→ 已补「E1 对齐提示」「D4→B1」钉死行 + FP/条件验收。  
- **N3 · 思考轮计数滞后**：R3「六条」/R4 未点名验收条数。→ 已同步为 FP 八条、验收 8 条。

## 观察（不要求处置）

- O1：本帽复核时 `git branch --show-current` = `master`；task 声明分支 `task/host-v1-sli-four-metrics`。30/00 须先切任务分支，禁 master 直改（非 task 内容阻塞）。  
- O2：出口 G2（dualproc `REGRESSION_*`）未纳入本 task；非范围亦未禁 docs 微修——00 可另窗或同窗 docs-only，不属本审查收口义务。

---

## 维护者签闸（20 后 · 30 前）

- [ ] 已读 R1 审查结论（PASS-WITH-NITS · 阻塞项为零 · nit N1–N3 已微修留痕）
- [ ] 在 task 人工闸表将 HG-AUDIT-R1 改为 approved（维护者/00 代录 · 日期）
- [ ] commit task 文档或确认已签
- [ ] 再下发 Harness 30 Prompt

30 Agent 将以 task 表为准；pending 时必须拒开工（见 TEMPLATE_30_gate_stop.md）。

---

## 修订记录

| 日期 | 摘要 |
|------|------|
| 2026-09-24 | 20-task-audit R1 落盘：结论 PASS-WITH-NITS（阻塞项为零 · nit×3 已微修）· lint PASS · 对照 §7/07§4/ROADMAP§3/budget Cost 锚点一致 · B1 裁定为条件覆盖非硬退回 · HG-AUDIT-R1 仍 pending 待维护者签 |
| 2026-09-24 | 30 开工前软修结论节措辞：「不构成退回」→「可接受」（避免机读 `退回` 否定守卫误伤 · 内容结论未变） |
