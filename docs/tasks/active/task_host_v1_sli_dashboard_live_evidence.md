# Task：host-v1-sli-dashboard-live-evidence（04 测评轨 · Host v1.0 SLI 看板真实 Langfuse 实证补录）

> **状态**：approved 待 40（三闸 approved · 维护者「全做」授权 + 授权链 m00238/m01101 00 代录 2026-10-19 · R1 签收 nit 知悉照登 · 零改码 40 轨 · 未 commit）
> **类型**：observability / eval follow-up（**40 轨实证补录** · 外部系统访问面 · 零改码预判 · `graph_change_layer=none`）
> **依据**：`docs/tasks/close/close_host_v1_sli_dashboard_20261017.md` §四.1/§七（FP-1 降级钉案 + 获权后补实证路径指引）· `docs/tasks/done/task_host_v1_sli_dashboard.md`（TC-D1 移交口径）· `docs/reports/host_v1_exit_review/SLI_DASHBOARD_EVIDENCE_20261017_30.md` §3（补实证操作真值）· `docs/spec/agent-infra/eval/GUIDE_host_v1_sli_dashboard_v1.md`（看板操作真值）· `docs/spec/agent-infra/eval/SLI_host_v1_four_metrics_v1.md`（定义 signed 2026-09-24）
> **维护者选定**：2026-10-19 会话「全做」——凭据面已勘察（`.env` 含 `LANGFUSE_PUBLIC_KEY`/`LANGFUSE_SECRET_KEY`/`LANGFUSE_BASE_URL`/`LANGFUSE_ENV`，存在即权限可能在，40 实判有效性）→ 推进真实实证补录
> **分支建议**：`task/host-v1-sli-dashboard-live-evidence`（base master 最新 · 本起草阶段零 git）

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `host_v1_sli_dashboard_live_evidence` |
| **git_branch** | `task/host-v1-sli-dashboard-live-evidence` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 实证补录面：真实 Langfuse project 四项 widget 落地截图/导出留档 + 真实聚合 vs fixture 口径对拍 + 离线 `pytest tests/eval/test_host_v1_sli.py -q` 绿；key 失效/项目无数据走照登路径（禁伪造截图/数字 · 如实记零数据面板 · 口径冲突上抛不擅改定义） |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `none`（预判：仅触 `docs/reports/host_v1_exit_review/` 与 invoke/task 档；不触 `app/` 热路径；若实判需改码即 STOP，见 FP-L4） |
| **graph_delta** | 无 |
| **graph_delta_note** | docs/reports 证据与 invoke 档不入图谱册 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 契约真值已在 SLI 定义表 + GUIDE；本 task 只补真实落地证据，无 wiki 面 |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,40` |
| **invoke_retention_profile** | `minimal`（实证补录棒：10 起草 + 40 实证两档；30 缺位照登——零改码预判无 30 面，若实判需改码即 STOP 退回另立项） |
| **experience_capture** | `recommended` |
| **kpi_aggregator** | `n/a` |
| **orchestration** | 10 落稿 → 20-task-audit R1 → 维护者签闸 → 40（真实 Langfuse 实证：widget 落地 + 查询/导出钉死 + 聚合对拍 + 留档收口）→ PR → CLOSE |
| **freeze_id** | 无（禁动 freeze / SSE / 热路径 score） |
| **related_tasks** | `docs/tasks/done/task_host_v1_sli_dashboard.md`（上游实证 task · CLOSED · TC-D1 走 FP-1 降级照登移交）· `docs/tasks/done/task_host_v1_sli_four_metrics.md`（定义 task · done） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | approved | 20, 40 | 2026-10-19 维护者「全做」授权 + 授权链（m00238/m01101）00 代录 · R1 task_host_v1_sli_dashboard_live_evidence_audit_R1_20261019.md 通过 |
| HG-AUDIT-R1 | approved | 40 | 2026-10-19 维护者「全做」授权 + 授权链 00 代录 · 20 R1 通过（零阻塞 nit×3 知悉照登） |
| HG-GRAPH-MODULES | approved | 40 | 授权链 00 代录 · 全局真值 approved · `graph_change_layer=none` 零图谱改动 |

---

## 背景与目标

### 已有什么 / 缺什么（10 亲读锚点 · 2026-10-19）

**已有（done · 勿重做）**：

- 上游 task `task_host_v1_sli_dashboard` 已 CLOSED（PR #261 MERGED squash 19a32d5 · 2026-10-17）：D2 四项筛选表钉死、D3 fixture 四键齐 + unknown 语义实证、D4 离线 pytest 9 passed、D5/D6 白名单与口径自检全绿。
- 补实证操作真值：`docs/reports/host_v1_exit_review/SLI_DASHBOARD_EVIDENCE_20261017_30.md` §3（四项 widget 名=dict_key 逐字 · UI 入口/筛选字段/时间窗/导出字段钉死 · 导出映射脱敏约定）。
- 定义/有数/离线闸三件套：SLI 定义表 signed + `evals/agent/sli/aggregate_sli.py` + fixtures（`sli_sample.json` + `sli_sample_unknown.json`）+ `tests/eval/test_host_v1_sli.py`。
- 凭据面（2026-10-19 勘察 · 本帽仅验键存在不读值）：`.env` 含 `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` / `LANGFUSE_BASE_URL` / `LANGFUSE_ENV` / `OPS_CHAT_TRACER` 键——存在即权限可能在，有效性与数据可得性 40 实判。

**缺（本 task 交付面 · 承 CLOSE 档 §四.1/§四.2 两条降级缺口）**：

- 真实 Langfuse project 里**实际保存的四项 Dashboard widget**（名=dict_key 逐字）与截图证据——上游 D1 走 FP-1 降级「照登：无实证（无 Langfuse 项目权限）」，获权后补实证即本棒。
- 真实 Traces/Scores 导出映射 fixture 形状的脱敏样例 + **真实环境聚合与 fixture 口径一致性对拍**留档——上游 D3 真实导出对拍同样照登无实证。

### SPEC 判定（钉死 · 防越权）

承上游 task SPEC 判定钉案：GUIDE 与 SLI 定义表均 signed，本 task 只补**证据面**，不降级 10-spec 预研；若 40 实判出数必须改热路径埋点 / 新写 score / 动 `aggregate_sli.py` 公式 / 改 SLI 定义或 GUIDE（即越非范围），**STOP 退回 10/20 另立 SPEC 链路**——40 无权顺手扩面。

### 目标

用 `.env` 已有凭据按 GUIDE §三步落地真实实证：F1 四项 widget 保存（名=dict_key 逐字）+ 截图留档 → F2 可复现查询/导出钉死 → F3 真实聚合 vs fixture 口径对拍 → F4 留档收口；任何一环不成立即照登不假绿。

---

## 范围

- [ ] **F1 · Dashboard 真实落地**：按 `docs/spec/agent-infra/eval/GUIDE_host_v1_sli_dashboard_v1.md` 三步，在与 `OPS_CHAT_TRACER=langfuse` 写入同 project 的真实 Langfuse 环境保存四项 widget，widget 名与 `docs/spec/agent-infra/eval/SLI_host_v1_four_metrics_v1.md` §2（:26-29）dict_key 列逐字一致：`latency.e2e_p99_ms` · `avail.success` · `avail.capability_ok` · `host.cost_per_successful_task`；截图入 `docs/reports/host_v1_exit_review/`（文件名含日期）。
- [ ] **F2 · 可复现查询/导出钉死**：承证据文 `SLI_DASHBOARD_EVIDENCE_20261017_30.md` §3 四项筛选表逐条复开核验（UI 入口/筛选字段/时间窗/导出字段）；真实 Traces/Scores 导出按 §3 脱敏约定映射为 fixture 形状样例留档 `docs/reports/host_v1_exit_review/`（原始 CSV 不入仓，FP-L5）。
- [ ] **F3 · 真实环境聚合对拍留档**：真实导出样例跑 `aggregate_all_from_fixture(<真实样例路径>)` 输出四键，与 fixture 主样例结果并列贴入 40 invoke / 新证据文；口径一致性核验（键名/成功口径/unknown 语义），冲突上抛不擅改定义（FP-L3）。
- [ ] **F4 · 留档收口**：新证据文落 `docs/reports/host_v1_exit_review/`（承接 20261017_30 件 · 文件名含日期）；上游 CLOSE 档 §四.1/§四.2 两条降级缺口的消账情况在证据文中明示；40 invoke 落盘。

## 非范围

承 GUIDE §非范围与上游 task 钉案，并补 Harness 面：

- ❌ 改 `SLI_host_v1_four_metrics_v1.md`（+ yaml）公式/成功口径/键名（signed 契约；改动须另走 SPEC）
- ❌ 改 `evals/agent/sli/aggregate_sli.py` 聚合逻辑（真实对拍只允许读路径调用；新增真实导出样例文件只入 `docs/reports/host_v1_exit_review/`，不动 `evals/agent/sli/fixtures/` 既有样例）
- ❌ 改 `GUIDE_host_v1_sli_dashboard_v1.md`（回写增补须另案）
- ❌ 热路径埋点 / 新写 score / 改 freeze / SSE（越界即 STOP 另立 SPEC，承上游 task SPEC 判定钉案）
- ❌ Langfuse 配置面改动超出 widget 新建（不改 project 设置 / 不建 score 定义 / 不动既有 dashboard 之外的资源）
- ❌ 自建完整可观测中台 / 新对外计费 API；`cost.usd_est` 与 Host Cost SLI 合并（定义表 §3 显式分流）
- ❌ 另起同义异名键（`e2e_latency_p99` / `success_rate` / `tool_hit_rate` 等）
- ❌ `app/` 任何改动；iOS / web / 租户面
- ❌ 本起草阶段零文件改动、零 git（仅落盘本 task + 10 invoke）

---

## failure_paths

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----------|----------|--------|----------|
| FP-L1 key 失效 / 项目不可达 / 无权限（不假绿） | 照登「无实证（凭据无效或无项目权限）」并附探测证据；**禁伪造截图/数字** | 是（换有效凭据后重跑） | 报告明示降级 |
| FP-L2 项目存在但数据为空 | 如实记零数据面板（widget 可保存 · 截图标注窗口内零数据）；不编造样本 | 是（有数据后补对拍） | 零数据面板如实可见 |
| FP-L3 真实数据与 fixture 口径冲突（聚合结果/字段形状不符定义表） | **上抛**：记录冲突明细并 STOP 该子项；**不擅改定义/聚合公式/fixture** | 是（另立 SPEC 后重跑） | 口径冲突上抛可见 |
| FP-L4 出数必须改热路径/新 score/改聚合公式/GUIDE/SLI 定义 | **STOP 退回 10/20**：越非范围，须另立 SPEC；40 禁顺手扩面 | 是 | task 返工（合法） |
| FP-L5 真实导出含敏感信息（用户内容/租户标识） | 承证据文 §3 脱敏约定：仅保留 fixture 形状字段；原始 CSV 不入仓 | 是 | 数据泄露风险 |
| FP-L6 widget 名与 dict_key 不一致 / 同义异名 | **拒收**（违 SLI 钉死契约 §2） | 是 | 看板键名漂移 |
| FP-L7 Cost 缺单价伪造 0 / 缺 `ok` 伪造 0 | **拒收**；聚合必须输出 `unknown`（Cost 铁律 + capability_hit 行规） | 是 | 假数入报告 |
| FP-L8 把 metadata 键 `ok` 当 score 名上报 | **拒收**（GUIDE §步骤 2 明示） | 是 | 指标口径污染 |
| FP-L9 证据只贴聊天未入仓（截图/导出无文件落点） | **拒收**：证据须入 `docs/reports/host_v1_exit_review/` | 是 | 不可复现 |
| FP-L10 HG-AUDIT-R1 pending 即动手 | GATE_VERIFY **拒开工** | 是 | — |

---

## 验收标准

- [ ] **TC-L1（Dashboard 实证）**：真实 Langfuse project 四项 widget 已保存且名=dict_key 四键逐字全齐；截图文件入 `docs/reports/host_v1_exit_review/`（名含日期）；或 FP-L1/FP-L2 照登成立（探测证据 + 不假绿句式 / 零数据面板如实截图）。
- [ ] **TC-L2（可复现查询/导出钉死）**：按证据文 `SLI_DASHBOARD_EVIDENCE_20261017_30.md` §3 四项筛选表逐条复开，结果（一致/偏差）留档；真实导出样例脱敏后入 `docs/reports/host_v1_exit_review/`（FP-L5）；第三者按文档可复开同视图。
- [ ] **TC-L3（真实聚合对拍）**：真实导出样例经 `aggregate_all_from_fixture` 输出四键（键名与 dict_key 逐字一致），与 fixture 主样例结果并列贴入 40 invoke / 证据文；口径一致性结论明示（一致 / FP-L3 上抛）；缺单价/缺 `ok` 面输出 `unknown` 而非 0。
- [ ] **TC-L4（离线闸）**：`pytest tests/eval/test_host_v1_sli.py -q` 绿（环境承上游坑留痕：先 `uv sync --extra dev` 再 `uv run pytest`）；零 `.py` 改动 ruff 触及面净增 0。
- [ ] **TC-L5（零越界）**：diff 白名单仅触 `docs/reports/host_v1_exit_review/`、本 task、invoke 档（+ 可选 20 审查文）；`app/` / `evals/agent/sli/aggregate_sli.py` / SLI 定义表（+ yaml）/ GUIDE / `evals/agent/sli/fixtures/` 既有样例零 diff。
- [ ] **TC-L6（口径一致）**：证据中四项键名与 `SLI_host_v1_four_metrics_v1.md` §2 dict_key 列逐字一致；成功口径=终态 `done`（承 V1-C）；无另发明公式字样。

## 依赖

- 补实证操作真值：`docs/reports/host_v1_exit_review/SLI_DASHBOARD_EVIDENCE_20261017_30.md` §3（四项筛选表 + 导出映射脱敏约定）
- 操作真值：`docs/spec/agent-infra/eval/GUIDE_host_v1_sli_dashboard_v1.md`（三步 + 字段清单 + 非范围）
- 定义真值：`docs/spec/agent-infra/eval/SLI_host_v1_four_metrics_v1.md` + `sli_host_v1_four_metrics_v1.yaml`
- 上游移交：`docs/tasks/done/task_host_v1_sli_dashboard.md`（TC-D1 移交口径）· `docs/tasks/close/close_host_v1_sli_dashboard_20261017.md`（FP-1 降级钉案 §四.1/§四.2 + 获权补实证指引 §七）
- 有数落点（只读）：`evals/agent/sli/aggregate_sli.py` · fixtures `sli_sample.json` / `sli_sample_unknown.json`
- 离线闸：`tests/eval/test_host_v1_sli.py`
- 凭据面（40 实判）：`.env` `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` / `LANGFUSE_BASE_URL` / `LANGFUSE_ENV` / `OPS_CHAT_TRACER`
- 证据落点目录：`docs/reports/host_v1_exit_review/`（现存 2026-09-24 三件 + 2026-10-17 证据文）

## 给执行帽的必读列表

1. 本 task 全文（含 SPEC 判定钉死 · FP-L1 不假绿纪律 · FP-L4 越界 STOP）。
2. `docs/reports/host_v1_exit_review/SLI_DASHBOARD_EVIDENCE_20261017_30.md` 全文（§3 = 补实证操作真值 · §2 探测句式样板）。
3. `GUIDE_host_v1_sli_dashboard_v1.md` 全文（操作真值 · 禁信转述）。
4. `SLI_host_v1_four_metrics_v1.md` §1 钉死契约 + §2 四项定义表。
5. `docs/tasks/close/close_host_v1_sli_dashboard_20261017.md` §四（偏差照登）+ §七（获权补实证路径）。
6. `evals/agent/sli/aggregate_sli.py`（只读 · 聚合键与 unknown 语义）。
7. `docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`（40 开工前闸扫描同样适用）。

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|---|---|---|---|---|
| R0 | 框定：上游 D1/D3-真实两件走 FP-1 降级照登；凭据面已勘察键在 → 补实证窗口开启；本棒=40 轨证据补录非定义非改码 | false | — | 键存在 ≠ 有效/有数据（FP-L1/L2 · 40 实判） |
| R1 | 证据：亲读 done task / CLOSE 档 / 证据文 §3 / GUIDE / SLI 定义表 / aggregate_sli.py 头 / fixtures 目录 / `.env` 键存在性（不读值） | false | — | 真实数据与 fixture 口径未验（FP-L3） |
| R2 | 方案：F1 widget 落地 + F2 查询/导出钉死 + F3 聚合对拍 + F4 留档收口；全承 §3 钉死表不另发明 | false | — | 导出脱敏边界（FP-L5） |
| R3 | 反例：不假绿（FP-L1 禁伪造）· 零数据如实记（FP-L2）· 口径冲突上抛不擅改（FP-L3）· 越界即 STOP（FP-L4）；30 缺位照登——零改码预判无 30 面 | false | — | 权限仍不可得时缺口延续（照登即可，不重开降级 task） |
| R4 | 验收：TC-L1~L6 均可对文件存在性/命令输出/diff 白名单断言；照登路径也可验收 | false | — | 无 |
| R5 | 收口：草稿交 20；闸全 pending 待维护者签；禁 40 | true | §3 操作真值已钉死 · 方案唯一 · 再轮无新锚点 | 见 R0/R1 |

**actual_last_round**：R5（early_stop）

### R0 · 问题框定

上游 task 把看板交付到「降级照登 + 操作钉死」层即 CLOSE，CLOSE 档 §四.1/§四.2 明示两条可重试缺口（真实 widget / 真实导出对拍）同根因=无项目权限。2026-10-19 凭据面勘察发现 `.env` 四键 + `OPS_CHAT_TRACER` 俱在，维护者选定推进——本 task 是**获权后的实证补录棒**，承接既有钉死条件，不重开定义/操作面。

### R1 · 证据收集

2026-10-19 亲读：done task（TC-D1–D6 终态 · D1 降级照登）、CLOSE 档（FP-1 钉案 + §七补实证指引 + 40 轨缺位照登——本棒 `required_invoke_hats=10,40` 正补此位）、证据文全文（§2 探测句式 / §3 四项筛选表 / §4 对拍样板）、GUIDE（三步/非范围）、SLI 定义表（钉死契约/禁同义异名）、`evals/agent/sli/`（aggregate + 两 fixture 在）；`.env` 仅 grep 键名存在（5 键俱在），值与有效性不判（40 实判）。

### R2 · 方案生成

F1–F4 全部承证据文 §3 钉死条件：widget 名=dict_key 逐字、UI 入口/筛选/时间窗照表复开、导出映射脱敏约定照旧、聚合对拍用既有 `aggregate_all_from_fixture` 读路径——零新发明，方案唯一。

### R3 · 反例与边界

最锋利反例是「凭据在手就为出数顺手改面」——改 GUIDE/定义/聚合/热路径任一即 FP-L4 STOP。诚实纪律三连：key 失效照登不假绿（FP-L1）、空项目如实记零数据（FP-L2）、口径冲突上抛不擅改（FP-L3）。30 缺位非漏配：零改码预判下无 30 面，实判需改码即退回另立项。

### R4 · 验收/可测性

TC-L1/L2 对文件存在性与截图/样例断言；TC-L3/L4 对命令输出断言；TC-L5 diff 白名单；TC-L6 逐字键名比对。照登路径（FP-L1/L2）下 TC-L1 以「探测证据 + 照登句式 / 零数据截图」验收，不留主观空子。

### R5 · 收口

草稿交 20-task-audit；人工闸全 pending 待维护者签；禁 40；未 commit、零 git。

### 自检结论（执行者 · 40 回填 2026-10-19）

- **闸扫描**：`npx spec-wave verify --target . --task docs/tasks/active/task_host_v1_sli_dashboard_live_evidence.md` → VERIFY: PASS（HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 全 approved 后开工）。
- **F1 widget 落地**：**照登（不假绿）**——凭据实判有效（`GET /api/public/projects` HTTP 200 · project `Ops-desk-agent` · dev 1026 traces/1379 observations），但 widget 写入面不可达：Dashboards 公共 API（`/api/public/v2/dashboards` GET/POST · `/api/public/dashboards` · `/api/public/v1/dashboards`）全部 HTTP 404，且本执行面无浏览器 UI 会话；零伪造截图/数字，缺口延续可重试。
- **F2 查询/导出钉死复开**：API 等价面复开完成——latency 字段在（393/1026）· `module=e2e` 可选筛无匹配照登 · `avail.success` 终态 0 行照登 · `ok` 101 行（tool_exec span · 72/29）可复现 · cost 成功过滤前提不可得照登；脱敏样例 `sli_live_export_sample_20261019.json` 入仓（仅 fixture 形状字段 · 原始 API JSON 不入仓）。
- **F3 聚合对拍**：真实样例经 `aggregate_all_from_fixture` 输出四键与 fixture 主样例并列——`avail.capability_ok`=0.7129（72/101）· `latency.e2e_p99_ms`=562052.0ms（n=84）真实出数；`avail.success`=null（0 终态行 · 非 0 非编造）；`host.cost_per_successful_task` 空行集机械 0.0 不作数照登 + 117 真实 usage 行强喂演示 → `unknown`（缺单价铁律真实触发）；口径冲突零（无 FP-L3）。
- **F4 留档**：证据文 `SLI_DASHBOARD_LIVE_EVIDENCE_20261019_40.md` + 40 invoke `invoke_20261019_40_live_evidence.md` + 本回填。
- **TC-L1~L6**：L1 照登成立（非 FP-L1/L2 · 执行面能力缺口）· L2/L3 落地 · L4 pytest 9 passed · L5 白名单零越界（app//aggregate/fixtures/定义表/GUIDE 零 diff · Langfuse 端只读）· L6 四键逐字一致。
- **残留缺口照登**：① widget 保存/截图（重试路径=持 Langfuse UI 会话者按 20261017_30 §3 表补 widget+截图）；② `avail.success`/`host.cost_per_successful_task` 真实出数缺口同根因=终态未埋 Langfuse trace metadata（终态真源=DB `app/ops/lg_rag/history.py:254`），修复属 FP-L4 面须另立 SPEC；③ `metadata.module=e2e` 真实数据无匹配如实记。
- **CLOSE 档缺口消账对照**：§四.1（真实 Dashboard）未消账延续 · §四.2（真实导出对拍）已消账 · §四.5（40 轨缺位）已消账。

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-19 | 10-task 初稿落盘（帽 10 · 闸全 pending 待维护者签 · 禁 40 · 零 git · 仅新增 untracked 文件） |
| 2026-10-19 | 20-task-audit R1 落盘 + 维护者签三闸 approved（HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES）· 40 开工许可到位 |
| 2026-10-19 | 40 实证补录交付：凭据实判 PASS · widget 面照登（Dashboards API 404 + 无 UI 会话 · 不假绿）· 四项筛选表 API 复开 · 真实脱敏样例入仓 + 四键对拍（capability_ok/latency 真实出数 · avail.success null 照登 · cost 前提缺口 + unknown 铁律实证）· pytest 9 passed · 零改码零越界（证据文 `SLI_DASHBOARD_LIVE_EVIDENCE_20261019_40.md` · 40 invoke · 样例 `sli_live_export_sample_20261019.json`） |
