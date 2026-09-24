# Agent Host v1.0 · 出口复核报告（07 §4 八面）

> **日期**：2026-09-24  
> **帽**：00（统筹 · 复核棒 · **未改** `app/`）  
> **维护者令（原话留痕）**：「生成下v1.0出口复核的00 Prompt，授权00签收过程文档」  
> **规划真值**：`docs/spec/agent-infra/07_host_v1_landing_plan_v0.md` §4  
> **过程真值**：`docs/harness/invokes/by-task/host-v1-exit-review/invoke_20260924_00_host-v1-exit-review.md`  
> **扫盘前提**：`docs/tasks/active/` 无 `task_*.md` · 分支 `master`（无已改 tracked；仅未跟踪 invoke/events）· V1-A~E + dualproc fix 均在 `docs/tasks/done/`

---

## 总裁定

| 项 | 值 |
|---|---|
| **EXIT** | **PASS-WITH-GAP** |
| **含义** | V1-A~E 功能/工程出口可签收；**不重开**已 CLOSE 波；缺口仅开 follow-up |
| **主 GAP** | **指标面**（07 §4 四项「有定义 / 有数 / 有看板」未齐） |
| **次 GAP** | 工程面：V1-E 回归报告仍记 BLOCKED；#190 后绿有 KPI/CI，**缺更新版 REGRESSION 落盘** |
| **跟进 task** | `host-v1-sli-four-metrics`（本窗 00 起草 · HG-TASK-DRAFT 代录 · HG-AUDIT-R1 待 20） |

---

## 扫盘快照（首输出核对）

| 检查项 | 结果 |
|---|---|
| active task | **空**（仅 `README.md`） |
| 分支 | `master` · tracking `origin/master` · 无已修改 tracked 文件 |
| V1-A done | `task_host_v1_delegation_token.md` · PR [#179](https://github.com/Cyning12/ops-desk-api/pull/179) |
| V1-B done | `task_host_v1_visibility_scenario_policy.md` · PR [#181](https://github.com/Cyning12/ops-desk-api/pull/181) |
| V1-C done | `task_host_v1_llm_factory_closure.md` · PR [#183](https://github.com/Cyning12/ops-desk-api/pull/183) |
| V1-D done | `task_host_v1_episodic_memory_feedback.md` · PR [#184](https://github.com/Cyning12/ops-desk-api/pull/184) |
| V1-E done | `task_host_v1_splittability_hardening.md` · PR [#187](https://github.com/Cyning12/ops-desk-api/pull/187) |
| dualproc fix | `task_multi_replica_dualproc_tenant_session.md` · PR [#190](https://github.com/Cyning12/ops-desk-api/pull/190) · CLOSE docs [#192](https://github.com/Cyning12/ops-desk-api/pull/192) |
| 本棒性质 | **复核棒 · 非实现 30**（无 GATE_VERIFY 改码闸；`graph_change_layer` 本复核预期 none） |

---

## 八面结论表

| # | 面 | 结论 | 一句话 |
|---|---|---|---|
| 1 | 委派链路 | **PASS** | 六类拒+全链路+审批留痕断言化 · PR #179 |
| 2 | 可见集 | **PASS** | 两阶段裁剪+安全默认+剔除台账 · PR #181 |
| 3 | manifest | **PASS** | 四字段 schema/加载校验/缺失→HITL · 同 #181 |
| 4 | LLM 工厂 | **PASS** | 预算闸+degraded+缓存可观测+声明式降级 · PR #183 |
| 5 | 记忆 | **PASS** | episode 零互写+聚类脚本/断言 · PR #184 |
| 6 | 工程 | **PASS-WITH-GAP** | import-linter CI 绿 + registry 可替换；双进程 **#190 后 9 passed**（禁止借 V1-E CLOSE 假绿）· 缺更新 REGRESSION 报告 |
| 7 | 指标 | **PASS-WITH-GAP** | 仅 Cost 有 Host 定义+单测有数；P99/完成率/命中率缺钉死定义/聚合/看板 |
| 8 | 图谱 | **PASS** | `01_modules` V1-A~E 行备注 + HG-GRAPH-MODULES 签录链至 V1-E |

---

## 分面证据

### 1 · 委派链路 · PASS

| 判据（07 §4） | 证据 |
|---|---|
| supervisor→工人全链路携令牌 | `task_host_v1_delegation_token` 验收 D3「全链路携令牌」勾选；`tests/test_lg_rag_delegation_wiring.py` + `tests/test_capability_delegation.py` 在仓 |
| 无令牌/越权/过期→拒绝且断言化 | 验收 D3 六类 R-a~R-f；PR #179 MERGED |
| 签发审批留痕 | 验收 D2：只读自动 / 写能力 HITL · `token_issue_hitl_required` 台账 |
| 图谱 | `01_modules` 签录行 105（V1-A） |

### 2 · 可见集 · PASS

| 判据 | 证据 |
|---|---|
| 两阶段裁剪上线 | V1-B：基线→`scenario_trim`→有效可见集；`tests/test_strategy_scenario.py` |
| 安全默认生效 | S1 fallback→∅ · 畸形 intent 收紧；验收 D2 勾选 |
| 剔除项进审计台账可查 | logger+span 双通道；验收 D3；PR #181 |

### 3 · manifest · PASS

| 判据 | 证据 |
|---|---|
| 可撤销性四字段 schema 化 | `CapabilitySpec`：`reversible`/`execution_type`/`max_reversal_latency`/`requires_stop_support` |
| 缺失→默认 HITL | `OPS_CAPABILITY_REVERSIBILITY_MODE` 三档；`tests/test_capability_reversibility.py` |
| 加载期强制校验 | 非法/矛盾/process-无-stop → ManifestError；builtin 全覆盖断言；同 PR #181 |

### 4 · LLM 工厂 · PASS

| 判据 | 证据 |
|---|---|
| 预算硬闸生效 | `app/llm/budget.py` · 三档 off/observe/enforce；`tests/test_llm_budget.py` |
| 耗尽降级必带 `degraded` | 验收 D2；防假降级铁律 |
| 缓存命中率可观测 | `infer_cache` + span；`tests/test_llm_infer_cache.py`（在仓 · V1-C） |
| 降级链声明式 | `TASK_TIER_FALLBACKS` + `resolve_fallback_chain`；PR #183 |
| Cost 指标（本面附带） | `cost_per_successful_task()` · 单测有数；**产出面=span 聚合 · 明确不建新看板**（task D5） |

### 5 · 记忆 · PASS

| 判据 | 证据 |
|---|---|
| 情景记忆独立闸/库 | `ops_memory_episodes` + `episode_gate`/`episode_service`；PR #184 |
| 零事实记忆污染断言 | 双向表计数对拍 + import 守护；`tests/test_memory_episode_gate.py` |
| 失败模式聚类报告产出 | `scripts/episode_pattern_mine.py` + `tests/test_episode_pattern_mine.py`（字段族/频次/可重放/建议零生效） |
| 注 | 默认关；本复核未见 `reports/episode_patterns/` 生产样例——能力由脚本+单测覆盖，不判 FAIL |

### 6 · 工程 · PASS-WITH-GAP

| 判据 | 证据 | 诚实口径 |
|---|---|---|
| import 机械闸 CI 绿 | `.importlinter` 在仓 · `.github/workflows/import-linter.yml` · V1-E KPI「12 kept」· #190 checks `import-linter` pass | **PASS** |
| registry 接口可替换 | `RegistryReader`/`RegistryWriter` + `set_registry`（`registry.py`/`gateway.py`）· 图谱签录行 110 | **PASS** |
| 双进程共享 PG 验证报告全绿 | **禁止**因 V1-E CLOSE 写全绿 | V1-E 报告 `reports/multi_replica_verify/REGRESSION_host_v1_splittability_hardening_20260924.md` = **BLOCKED-ENV**（9 ERROR · tenant_id）· FINDINGS #1 |
| #190 后复跑 | `task_multi_replica_dualproc_tenant_session` KPI：**9 passed** · FINDINGS #1 **closed** · PR #190 CI `pytest` pass · fixture INSERT 含 `tenant_id` | **功能面 PASS** |
| GAP | 无更新版 `REGRESSION_*` 把 result 从 BLOCKED 改为 PASS（证据散落在 task KPI / CI，未回写报告文件） | **PASS-WITH-GAP（文档）** |

### 7 · 指标 · PASS-WITH-GAP

07 §4 四项须 **有定义、有数、有看板**：

| SLI 候选 | 定义 | 有数 | 看板 | 证据锚点 |
|---|---|---|---|---|
| 端到端 P99 | **缺口**（大纲/07 候选名；无 Host 钉死公式/标签） | 无专项聚合 | 无 | `04`/`eval/ROADMAP` 有延迟观测雏形 · `avail.*` score 热路径多为缺口 |
| 任务完成率 | **缺口**（无 Host 钉死「成功任务」出口口径进 SLI 字典） | 无 | 无 | E1 `avail.success` 状态=缺口 |
| 能力命中率 | **缺口**（metadata `ok`/`capability_id` 已埋 ≠ 命中率 SLI） | 无聚合指标 | 无 | E1 `avail.capability_ok` score=缺口 |
| Cost per Successful Task | **有**（V1-C：Σ成功 run cost / 成功任务数） | **有**（纯函数+单测） | **无**（V1-C 明示「不建新看板」） | `app/llm/budget.py:cost_per_successful_task` · `tests/test_llm_budget.py::TestCostPerSuccessfulTask` |

对照：`docs/spec/agent-infra/04_eval_and_observability_plan_v0.md` + `eval/ROADMAP_eval_observability_v0.md` §3 —— Eval E0–E5 已 CLOSE，但 **未**把 07 四项升为「有看板」的 v1.0 出口面。

### 8 · 图谱 · PASS

| 判据 | 证据 |
|---|---|
| `01_modules` 全回写 | capability/lg_rag（A/B）· llm（C）· memory/db（D）· capability Registry（E）行备注均在 |
| HG-GRAPH-MODULES 签录链完整 | 签录表行 **105→110**（V1-A→V1-E，含 V1-C/D）；00 代录 + 维护者令原话留痕 |
| 本复核 | `graph_change_layer=none` · **不**新增签录行 |

---

## GAP 清单（可执行下一棒）

| ID | 面 | 缺口 | 建议 slug | 优先级 |
|---|---|---|---|---|
| G1 | 指标 | 四项 SLI：钉死定义 + 数据落点 + Langfuse/导出看板（Cost 补看板；其余三项从零） | **`host-v1-sli-four-metrics`** | **closed** · PR [#193](https://github.com/Cyning12/ops-desk-api/pull/193) MERGED · 40 PASS |
| G2 | 工程 | 补写 post-#190 dualproc `REGRESSION_*`（result=PASS · 引 git sha / recorded_at） | 可并入 G1 非范围外的 docs 微修，或随 G1 同窗 docs-only | P2 |

**明确不做**：重开 V1-A~E · 开 v2.0 拆分 · 本窗改 `app/`。

---

## 签收位（00 代录）

| 产物 | status | 留痕 |
|---|---|---|
| 本报告 | **signed** | 2026-09-24 · 00 代录 · 维护者令原话：「生成下v1.0出口复核的00 Prompt，授权00签收过程文档」 |
| invoke 修订 | 见 invoke 修订表 | 同令 |
| follow-up HG-TASK-DRAFT | **approved**（00 代录） | 同令 + 日期；见 `docs/tasks/active/task_host_v1_sli_four_metrics.md` |
| follow-up HG-AUDIT-R1 | **pending** | 须 20-task-audit 后；本窗不代签实现闸 |

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-09-24 | 00 首版出口复核 · EXIT=PASS-WITH-GAP · 开 G1 task |
| 2026-09-24 | 40 验收 `host-v1-sli-four-metrics` **PASS** · G1 注「待 merge 后 closed」· 未提前 CLOSE |
| 2026-09-24 | **G1 closed**：PR #193 MERGED（CI 四绿 · b2896c6）· task 归档 done/ |
