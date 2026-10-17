# Task：host-v1-sli-dashboard（04 测评轨 · Host v1.0 SLI 四项看板落地 · Langfuse Dashboard 实证）

> **状态**：`active`（2026-10-17 维护者授权 00 代录签收（m00238「授权00签收后续文档，开始下面的任务」· 20 R1 书面审经授权豁免）· **30 已交付**（走 D5 降级路径 · 证据/invoke/task 档齐）· 待 40 核验 / PR 合并）
> **类型**：observability / eval follow-up（**docs+ops 面** · 零 `app/` 生产改动 · `graph_change_layer=none`）
> **依据**：`docs/spec/agent-infra/eval/GUIDE_host_v1_sli_dashboard_v1.md`（看板操作真值）· `docs/spec/agent-infra/eval/SLI_host_v1_four_metrics_v1.md`（定义 signed 2026-09-24）· `docs/tasks/done/task_host_v1_sli_four_metrics.md`（四指标定义/有数/GUIDE 已 done · **Dashboard 实证未交付**）
> **分支建议**：`task/host-v1-sli-dashboard`（base master 最新）

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `host_v1_sli_dashboard` |
| **git_branch** | `task/host-v1-sli-dashboard` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 看板落地实证面：Langfuse Dashboard 四项 widget（名=dict_key）截图/导出留档 + fixture 聚合命令输出断言 + 离线 `pytest tests/eval/test_host_v1_sli.py -q` 绿；无项目权限走 GUIDE 声明的 fixture 降级路径并照登「无实证」，禁伪造截图/数字 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `none`（30 实判：仅触 `docs/reports/` 与可选 `evals/agent/sli/fixtures/` 样例；不触 `app/` 热路径） |
| **graph_delta** | 无 |
| **graph_delta_note** | docs/reports 与 fixture 样例不入图谱册 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 契约真值已在 SLI 定义表 + GUIDE；本 task 只补落地证据，无 wiki 面 |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,20,30,40` |
| **invoke_retention_profile** | `default` |
| **experience_capture** | `recommended` |
| **kpi_aggregator** | `n/a` |
| **orchestration** | 10 落稿 → 20-task-audit R1 → 维护者签闸 → 30（Dashboard 落地 + 证据留档）→ 40（可复现性核验）→ PR → CLOSE |
| **freeze_id** | 无（禁动 freeze / SSE / 热路径 score） |
| **related_tasks** | `docs/tasks/done/task_host_v1_sli_four_metrics.md`（上游定义 task · done） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | approved | 20, 30 | 2026-10-17 维护者授权 00 代录（m00238） |
| HG-AUDIT-R1 | approved | 30 | 2026-10-17 维护者授权 00 代录（m00238 · 20 R1 书面审豁免） |
| HG-GRAPH-MODULES | approved | 30 | 2026-10-17 代录：全局真值 approved（docs/_tech_graph/l1/01_modules.md:63）· `graph_change_layer=none` |

---

## 背景与目标

### 已有什么 / 缺什么（10 亲读三件锚点 · 2026-10-17）

**已有（done · 勿重做）**：

- 四项 SLI 定义表 signed：`docs/spec/agent-infra/eval/SLI_host_v1_four_metrics_v1.md` + 机读副本 `sli_host_v1_four_metrics_v1.yaml`（钉死契约：成功口径承 V1-C · Cost 缺单价 `unknown` 不伪造 0 · 禁同义异名键）。
- 有数落点：`evals/agent/sli/aggregate_sli.py`（`aggregate_e2e_p99` / `aggregate_task_completion` / `aggregate_capability_hit` / Cost 对拍）+ `evals/agent/sli/fixtures/sli_sample.json`。
- 离线 CI 测试：`tests/eval/test_host_v1_sli.py`（不连网 · fixture）。
- 操作手册：`docs/spec/agent-infra/eval/GUIDE_host_v1_sli_dashboard_v1.md`（三步打开看板 + 字段清单 + 非范围）。

**缺（本 task 交付面）**：

- Langfuse 项目里**真实保存的四项 Dashboard widget**——GUIDE §步骤 3.1 仅给操作步骤且截图标注「可选」，上一棒 D3 交付到 GUIDE 即止，看板实证未落地。
- **钉死的可复现查询 / 导出样例**：真实 project 的 Traces/Scores 导出映射为 `evals/agent/sli/fixtures/` 形状的样例未入仓；`docs/reports/host_v1_exit_review/` 现仅有 2026-09-24 三件（ACCEPTANCE / BACKLOG / REPORT），无看板证据。
- 真实环境聚合输出与 fixture 的对拍留档（GUIDE §步骤 3.2 命令未跑过留证；照登：无实证）。

### SPEC 判定（钉死 · 防越权）

GUIDE 已是 v1 签收交付物，自带范围/非范围/可复现步骤，本 task 直接承接其操作面，**不降级为 10-spec 预研**。但：若 30 实判必须改热路径埋点 / 新写 score / 动 `aggregate_sli.py` 公式才能出数（即越 GUIDE §非范围），**STOP 退回 10/20，另立 SPEC 链路**——10-task 无权越权签收 SPEC，30 无权顺手扩面。

### 目标

按 GUIDE §三步在本环境 Langfuse project 落地四项看板：保存 widget（名与 `dict_key` 一致）+ 钉死可复现查询/导出 + 证据入 `docs/reports/host_v1_exit_review/`；无权限时走 GUIDE 第 6 行声明的 fixture 降级路径并诚实照登。

---

## 范围

- [x] **D1 · Dashboard 落地**（走 D5 降级路径：照登「无实证（无 Langfuse 项目权限）」· 禁伪造已遵守 · 探测证据入证据文 §2）：在本环境 Langfuse project（与 `OPS_CHAT_TRACER=langfuse` 写入同 project）保存四项 widget，名与 dict_key 一致：`latency.e2e_p99_ms` · `avail.success` · `avail.capability_ok` · `host.cost_per_successful_task`；截图入 `docs/reports/host_v1_exit_review/`（文件名含日期）。
- [x] **D2 · 可复现查询/导出钉死**（四项筛选/窗口/widget 名=dict_key 钉死于 `docs/reports/host_v1_exit_review/SLI_DASHBOARD_EVIDENCE_20261017_30.md` §3 · GUIDE 零改动）：Traces/Scores 筛选条件文档化（落 `docs/reports/host_v1_exit_review/` 或回写 GUIDE 增补节）；导出 CSV 映射为 `evals/agent/sli/fixtures/` 形状样例入仓（真实数据须脱敏，见 FP-3）。
- [x] **D3 · 聚合对拍留档**（fixture 主样例四键齐 + 新增 `sli_sample_unknown.json` unknown 语义实证；真实导出对拍照登无实证）：跑 GUIDE §步骤 3.2 命令（`aggregate_all_from_fixture`）输出四项键，连同导出样例的聚合结果贴入 30 invoke / 报告。
- [x] **D4 · 离线闸复验**（`uv run pytest tests/eval/test_host_v1_sli.py -q` → 9 passed）：`pytest tests/eval/test_host_v1_sli.py -q` 绿。
- [x] **D5 · 降级路径（已触发）**（无 Langfuse 项目权限 → fixture 聚合作有数证据 + 「照登：无实证」钉死句式）：无项目权限/无真实数据 → fixture 聚合作有数证据 + 文中钉「照登：无实证（无 Langfuse 项目权限）」，禁伪造。

## 非范围

按 GUIDE §非范围钉死，并补 Harness 面：

- ❌ 自建完整可观测中台 / 新对外计费 API
- ❌ 改 freeze / SSE / 热路径强制写 score（本波 docs-only 延续）
- ❌ `cost.usd_est` 与 Host Cost SLI 合并（SLI 定义表 §3 显式分流）
- ❌ 改 `SLI_host_v1_four_metrics_v1.md` 公式/成功口径/键名（signed 契约；改动须另走 SPEC）
- ❌ 改 `evals/agent/sli/aggregate_sli.py` 聚合逻辑（只允许新增 fixture 样例文件）
- ❌ 另起同义异名键（`e2e_latency_p99` / `success_rate` / `tool_hit_rate` 等）
- ❌ `app/` 任何改动；iOS / web / 租户面
- ❌ 本起草阶段零文件改动（仅落盘本 task）

---

## failure_paths

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----------|----------|--------|----------|
| FP-1 无 Langfuse 项目权限 / 环境不可达 | 走 D5 降级：fixture 聚合留证 + 「照登：无实证」；**禁伪造截图/数字** | 是（获权后补实证） | 报告明示降级 |
| FP-2 widget 名与 dict_key 不一致 / 同义异名 | **拒收**（违 SLI 钉死契约 §2） | 是 | 看板键名漂移 |
| FP-3 真实导出含敏感信息（用户内容/租户标识） | 脱敏后仅保留 fixture 形状字段（run_id/duration_ms/terminal_status/ok/token 计数/model）；原始 CSV 不入仓 | 是 | 数据泄露风险 |
| FP-4 出数必须改热路径/新 score/改聚合公式 | **STOP 退回 10/20**：越 GUIDE 非范围，须另立 SPEC；30 禁顺手扩面 | 是 | task 返工（合法） |
| FP-5 HG-AUDIT-R1 pending 即动手 | GATE_VERIFY **拒开工** | 是 | — |
| FP-6 Cost 缺单价伪造 0 / 缺 `ok` 伪造 0 | **拒收**；聚合必须输出 `unknown`（SLI Cost 铁律 + capability_hit 行规） | 是 | 假数入报告 |
| FP-7 把 metadata 键 `ok` 当 score 名上报 | **拒收**（GUIDE §步骤 2 明示） | 是 | 指标口径污染 |
| FP-8 证据只贴聊天未入仓（截图/导出无文件落点） | **拒收**：证据须入 `docs/reports/host_v1_exit_review/` 或 fixture 目录 | 是 | 不可复现 |

---

## 验收标准

- [x] **TC-D1（Dashboard 实证）**→ 降级路径照登成立（证据文 §2）：Langfuse Dashboard 四项 widget 已保存且名=dict_key 四键全齐；截图文件入 `docs/reports/host_v1_exit_review/`（名含日期）；或 D5 降级路径照登（无实证声明 + fixture 证据）。
- [x] **TC-D2（可复现查询钉死）**→ 证据文 §3 四项筛选表（widget 名=dict_key 逐字）：四项各自的筛选/窗口条件文档化（哪个 UI 入口、过滤什么字段、时间窗怎么选），第三者按文档可复开同视图；导出样例入 `evals/agent/sli/fixtures/`（脱敏，FP-3）。
- [x] **TC-D3（聚合对拍）**→ 证据文 §4.1/§4.2：fixture 四键齐 + unknown 实证；真实导出照登无实证：`python -c "from evals.agent.sli.aggregate_sli import aggregate_all_from_fixture; import json; print(json.dumps(aggregate_all_from_fixture(), indent=2, ensure_ascii=False))"` 输出含四键；真实导出样例聚合结果与 fixture 结果并列贴入 30 invoke；缺单价/缺 `ok` 面输出 `unknown` 而非 0（TC 断言或输出摘录）。
- [x] **TC-D4（离线闸）**→ 9 passed；零 .py 改动 ruff 净增 0：`pytest tests/eval/test_host_v1_sli.py -q` 绿；`ruff check` 触及面净增 0。
- [x] **TC-D5（零越界）**→ 证据文 §6 白名单表：`git diff --stat master...HEAD` 仅触 `docs/reports/host_v1_exit_review/`、`evals/agent/sli/fixtures/`（新增样例）、本 task、invoke 档；`app/` / `evals/agent/sli/aggregate_sli.py` / SLI 定义表零 diff。
- [x] **TC-D6（口径一致）**→ 证据文 §7 自检：证据中四项键名与 `SLI_host_v1_four_metrics_v1.md` §2 dict_key 列逐字一致；成功口径=终态 `done`（承 V1-C），无另发明公式字样。

## 依赖

- 操作真值：`docs/spec/agent-infra/eval/GUIDE_host_v1_sli_dashboard_v1.md`（三步 + 字段清单 + 非范围）
- 定义真值：`docs/spec/agent-infra/eval/SLI_host_v1_four_metrics_v1.md` + `docs/spec/agent-infra/eval/sli_host_v1_four_metrics_v1.yaml`
- 上游 task（done）：`docs/tasks/done/task_host_v1_sli_four_metrics.md`（G1 closed 于定义/有数/GUIDE 层）
- 有数落点：`evals/agent/sli/aggregate_sli.py` · `evals/agent/sli/fixtures/sli_sample.json`
- 离线闸：`tests/eval/test_host_v1_sli.py`
- Cost 口径源（只读对齐）：`app/llm/budget.py` `cost_per_successful_task`
- 出口语境：`docs/spec/agent-infra/07_host_v1_landing_plan_v0.md` §4 · `docs/spec/agent-infra/eval/ROADMAP_eval_observability_v0.md` §3
- 证据落点目录：`docs/reports/host_v1_exit_review/`（现存 2026-09-24 三件）

## 给执行帽的必读列表

1. 本 task 全文（含 SPEC 判定钉死 · FP-1 诚实纪律 · FP-4 越界 STOP）。
2. `GUIDE_host_v1_sli_dashboard_v1.md` 全文（操作真值 · 禁信转述）。
3. `SLI_host_v1_four_metrics_v1.md` §1 钉死契约 + §2 四项定义表。
4. `docs/tasks/done/task_host_v1_sli_four_metrics.md`（上一棒边界：D4=docs-only · B1 n/a）。
5. `evals/agent/sli/aggregate_sli.py`（只读 · 聚合键与 unknown 语义）。
6. `docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`（30 前闸扫描）。

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|---|---|---|---|---|
| R0 | 框定：定义/有数/GUIDE 三件套已 done；缺口=Dashboard 实证与可复现导出未落地 | false | — | Langfuse 项目权限与现网数据可得性（FP-1） |
| R1 | 证据：亲读 GUIDE/SLI/done task 三件；`docs/reports/host_v1_exit_review/` 现存三件无看板证据；fixture/test/aggregate 均在 | false | — | 照登：无实证（真实环境聚合未跑过） |
| R2 | 方案：D1 widget + D2 查询钉死 + D3 对拍 + D4 离线闸 + D5 降级路径；承接 GUIDE 不另起炉灶 | false | — | 导出脱敏边界（FP-3） |
| R3 | 反例：越 GUIDE 非范围即 STOP（FP-4）；伪造 0/截图拒收（FP-1/FP-6）；metadata `ok`≠score 名（FP-7） | false | — | 权限长期不可得时实证缺口残留 |
| R4 | 验收：TC-D1~D6 均可对文件/命令输出断言；降级路径也可验收（照登句式钉死） | false | — | 无 |
| R5 | 收口：草稿交 20；闸 pending 待维护者签；禁 30 | true | GUIDE 已承载范围/非范围 · 方案唯一 · 再轮无新锚点 | 见 R0/R3 |

**actual_last_round**：R5（early_stop）

### R0 · 问题框定

上一棒把「看板」交付到 GUIDE（操作手册）层即 CLOSE；07 §4「有看板」的出口语义还差最后一里：真实 Dashboard widget + 可复现导出证据。本 task 是落地棒，不是定义棒。

### R1 · 证据收集

2026-10-17 亲读：GUIDE（61 行 · 三步/字段清单/非范围/「无项目权限时用 fixture 聚合作有数证据」明示降级）、SLI 定义表（signed · Cost 铁律 · 禁同义异名）、done task（D3=GUIDE 交付 · D4=docs-only）；盘点 `docs/reports/host_v1_exit_review/`（3 件 · 无看板证据）、`evals/agent/sli/`（aggregate+fixture 在）、`tests/eval/`（test_host_v1_sli.py 在）。

### R2 · 方案生成

GUIDE §步骤 3 给三个留证据选项（UI 截图 / 导出映射 / 离线 CI），本 task 要求 D1+D2+D3 组合交付（截图+导出+聚合输出），D5 作为权限降级兜底；离线 CI（D4）作不变闸复验。

### R3 · 反例与边界

最锋利反例是「为了出数去改热路径或聚合公式」——这会把 docs+ops 棒拖成 SPEC 面；故 FP-4 钉 STOP 而非放行。诚实纪律：无实证就写「照登：无实证」，伪造截图/0 视同拒收。

### R4 · 验收/可测性

TC-D1/D2 对文件存在性与内容断言；TC-D3/D4 对命令输出断言；TC-D5 diff 白名单；TC-D6 逐字键名比对。降级路径下 TC-D1 以「照登句式 + fixture 证据」验收，不留主观空子。

### R5 · 收口

草稿交 20-task-audit；人工闸全 pending 待维护者签；禁 30；未 commit。

### 自检结论（执行者）

**30 帽（2026-10-17）· 交付态自检：PASS（降级路径合规）**

- GATE_VERIFY PASS：三闸 approved（维护者授权 00 代录 m00238 · R1 书面审豁免）；`npx spec-wave verify` → `VERIFY: PASS`。
- D1：FP-1 触发（env 无 Langfuse 双 key · .env.example 全注释 · localhost:3000 不可达）→ 走 D5 降级，**照登：无实证（无 Langfuse 项目权限）**，零伪造截图/数字。
- D2：四项 widget 筛选/窗口/widget 名=dict_key 钉死于 `docs/reports/host_v1_exit_review/SLI_DASHBOARD_EVIDENCE_20261017_30.md` §3。
- D3：GUIDE §3.2 命令实跑 fixture 主样例四键齐（p99=400.0 / success=0.6 / capability=0.75 / cost=0.004）；新增 `evals/agent/sli/fixtures/sli_sample_unknown.json` 实证缺 ok/缺单价输出 `unknown` 非 0；真实导出对拍照登无实证。
- D4：`uv sync --extra dev && uv run pytest tests/eval/test_host_v1_sli.py -q` → 9 passed；零 .py 改动，ruff 净增 0（存量错误零交集不修）。
- D5/D6：diff 白名单仅触证据目录/fixture 新增/task/invoke/review 档；键名逐字一致 · 成功口径承 V1-C · 无另发明公式。
- 未决残留：Langfuse 项目权限长期不可得时真实 Dashboard 实证缺口残留（FP-1 可重试：获权后按证据文 §3 补 widget + 截图）。

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-17 | 10-task 初稿落盘（帽 10 · 闸 pending 待维护者签 · 禁 30 · 未 commit） |
| 2026-10-17 | 维护者授权 00 代录三闸 approved（m00238 · 20 R1 书面审豁免）；20 R1 审查文落 `docs/harness/reviews/task_host_v1_sli_dashboard_audit_R1_20261017.md`（签收） |
| 2026-10-17 | 30 帽交付：D1 走 D5 降级照登（无 Langfuse 项目权限）· D2 查询钉死 · D3 fixture/unknown 对拍 · D4 pytest 9 passed · 证据文 `SLI_DASHBOARD_EVIDENCE_20261017_30.md` + invoke_30 落盘 |
