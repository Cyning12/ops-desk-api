# SLI Dashboard 真实 Langfuse 实证补录（40 帽 · 2026-10-19）

> **task**：`docs/tasks/active/task_host_v1_sli_dashboard_live_evidence.md`（task_slug=`host_v1_sli_dashboard_live_evidence` · retention=minimal 10,40）
> **承接**：`SLI_DASHBOARD_EVIDENCE_20261017_30.md` §3（操作真值零新发明）· CLOSE 档 `close_host_v1_sli_dashboard_20261017.md` §四.1/§四.2（两条降级缺口消账面）
> **操作真值**：`docs/spec/agent-infra/eval/GUIDE_host_v1_sli_dashboard_v1.md` · **定义真值**：`SLI_host_v1_four_metrics_v1.md`（signed 2026-09-24）
> **结论速览**：凭据实判 **PASS**（project `Ops-desk-agent` 可达 · dev 环境 1026 traces / 1379 observations 真实数据在）；**TC-L1 widget 面照登不假绿**（Dashboards API 于本部署 404 + 本执行面无浏览器 UI 会话 → widget 保存/截图缺口延续，探测证据齐全）；**TC-L2/L3 真实导出对拍落地**：`avail.capability_ok`=0.7129（72/101 真实出数）· `latency.e2e_p99_ms`=562052.0ms（n=84 真实出数）· `avail.success`=null（终态未埋 Langfuse · 照登不伪造）· `host.cost_per_successful_task` 成功过滤前提不可得照登 + 缺单价铁律真实触发 `unknown` 实证；**TC-L4 pytest 9 passed**；口径冲突零（无 FP-L3）。

---

## 1. GATE_VERIFY（40 开工前闸扫描）

命令：`npx spec-wave verify --target . --task docs/tasks/active/task_host_v1_sli_dashboard_live_evidence.md`

| human_gate_id | status | blocks_hats | 40 影响 |
|---------------|--------|-------------|---------|
| HG-TASK-DRAFT | approved | 20, 40 | — |
| HG-AUDIT-R1 | approved | 40 | ✅ 可 40 |
| HG-GRAPH-MODULES | approved | 40（`graph_change_layer=none`） | ✅ |

VERIFY: PASS（输出原句：`VERIFY: PASS · task_host_v1_sli_dashboard_live_evidence.md`）。分支 `task/host-v1-sli-dashboard-live-evidence`（base origin/master `4a5e755`）。

## 2. 凭据实判与环境探测（只读探针 · 2026-10-19 11:1x–11:4x +08:00）

| 探测 | 命令 / 方式 | 结果 |
|---|---|---|
| 键存在 | `grep -c '^KEY=.' .env` ×5 | `LANGFUSE_PUBLIC_KEY`/`LANGFUSE_SECRET_KEY`/`LANGFUSE_BASE_URL`/`LANGFUSE_ENV`/`OPS_CHAT_TRACER` 各=1 |
| 键有效性 | `GET {BASE}/api/public/projects`（Basic auth = pk/sk） | **HTTP 200** · project `Ops-desk-agent`（id `cmsn0e1c10012ad0j0agd32aq` · org "Cyning's Organization"） |
| 环境定位 | `LANGFUSE_BASE_URL`=`https://jp.cloud.langfuse.com` · `LANGFUSE_ENV`=`dev` · `OPS_CHAT_TRACER`=`langfuse` | 与 `app/ops/tracing.py` 写入面同 project 确认 |
| 数据可得性（dev） | `GET /api/public/traces?environment=dev&limit=50` 全量分页 | **1026 traces**（meta.totalItems）· 窗口 2026-09-20T09:42:05Z → 2026-10-11T09:30:47Z |
| 观测面（dev） | `GET /api/public/observations?environment=dev&limit=50` 全量分页 | **1379 observations**（SPAN/GENERATION/EVENT 混合 · GENERATION 232） |
| Scores | `GET /api/public/scores?limit=5` | totalItems=**0**（`avail.success`/`avail.capability_ok` score 均未打 · §3 表「若已打」前提不成立照登） |
| Dashboards API | `GET/POST /api/public/v2/dashboards` · `GET /api/public/dashboards` · `GET /api/public/v1/dashboards` | **全部 HTTP 404（text/html · Next.js 404 页）**——本部署/套餐不暴露 Dashboards 公共 API |

非 dev 环境：prod 环境 50,794 traces 几乎全为 OTEL HTTP 自动埋点（`GET /health` 等），与 SLI 四项数据源无关；实证以 dev 环境（LangGraph pipeline trace）为准。

## 3. TC-L1 · Dashboard widget 实证 → 照登（不假绿 · 禁伪造截图）

**照登：无 widget 实证（widget 写入面不可达）。** 凭据有效、项目可达、数据在（§2），但四项 widget（`latency.e2e_p99_ms` / `avail.success` / `avail.capability_ok` / `host.cost_per_successful_task`）的新建保存+截图未能落地，根因两条并列：

1. **Dashboards 公共 API 于本部署全部 404**（§2 末行 · GET/POST 三路径变体同）——程序化建 widget 无 API 通道；
2. **本执行面无浏览器 UI 会话能力**（无 UI 登录凭据 · 无浏览器工具）——GUIDE §步骤 1/3.1 的 UI 路径（Dashboards → 新 widget → 截图）无法由 40 棒在 headless 环境完成。

纪律声明：按 FP-L1「禁伪造截图/数字」不产出任何伪截图；本照登非 FP-L1（凭据有效）亦非 FP-L2（项目有数据），系**执行面能力缺口**，如实挂账。CLOSE 档 §四.1「真实 Dashboard 缺口」**未消账**，延续可重试：任一持有 Langfuse UI 会话者按 `SLI_DASHBOARD_EVIDENCE_20261017_30.md` §3 四项筛选表保存 widget（名=dict_key 逐字）+ 截图入本目录即消账。

## 4. TC-L2 · §3 四项筛选表逐条复开核验（API 等价面）

UI 入口不可达（§3），以只读 API 等价复开筛选条件；原始 API JSON 不入仓（FP-L5），脱敏映射样例见 §5。

| widget 名（=dict_key 逐字） | §3 筛选条件 | 真实复开结果（dev 环境全量扫描） | 裁定 |
|---|---|---|---|
| `latency.e2e_p99_ms` | 根/e2e span · 可选 `metadata.module=e2e` | trace `latency` 字段在（393/1026 条有值）；`metadata.module` 真实取值仅 `strategy_builder`(96)/`intent`(58)，**无 `e2e`** → 该可选筛选无匹配照登；替代口径=根 trace 名 `lg-rag`（87 条 · 观测面含完整 pipeline 子 span · 84 条有 latency） | 一致（可选筛无匹配如实记） |
| `avail.success` | Score `avail.success`（若已打）；或按终态 `done` 聚 | Scores totalItems=0（未打）；`terminal_status` metadata 全量 1379 observations = **0 行**（终态真源=DB 事件表 `app/ops/lg_rag/history.py:254`，未埋 Langfuse trace metadata） | 偏差照登（终态面无 Langfuse 数据） |
| `avail.capability_ok` | capability/tool span metadata `ok` | **101 行 `ok` 全在 `tool_exec` span**（True 72 / False 29）· `capability_id` 101/101 齐（`testing.write.echo`/`mock_get_deploy_info`/`no_such_tool`/`mock_get_issue_status`/`test_delegation_read_cap`/`get_issue_by_number`/`utc_now_iso`） | ✅ 一致可复现 |
| `host.cost_per_successful_task` | 仅成功 `done` run 的 usage 行 × 单价 | GENERATION 232（usage>0 者 117）；**成功 run 过滤前提不可得**（同上行根因：终态未埋点）→ 口径前提不满足不强喂 | 偏差照登（前提缺 · 同根因） |

导出映射脱敏约定（FP-L5）执行：样例仅保留 fixture 形状字段（`run_id`/`duration_ms`/`capability_id`/`ok`），无用户内容/会话标识/输入输出；原始 API 响应不入仓。

## 5. TC-L3 · 真实导出样例聚合对拍

真实脱敏样例：`docs/reports/host_v1_exit_review/sli_live_export_sample_20261019.json`（fixture 形状四节：`e2e_latency` 84 行 / `task_terminals` 0 行 / `capability_calls` 101 行 / `cost_rows` 0 行——空节=真实面无对应数据照登，不编造）。

命令（读路径 · 零改码）：

```bash
uv run python -c "from pathlib import Path; from evals.agent.sli.aggregate_sli import aggregate_all_from_fixture; import json; print(json.dumps(aggregate_all_from_fixture(Path('docs/reports/host_v1_exit_review/sli_live_export_sample_20261019.json')), indent=2, ensure_ascii=False))"
```

真实样例 vs fixture 主样例（`evals/agent/sli/fixtures/sli_sample.json`）并列：

| dict_key（逐字一致） | 真实样例（dev · 2026-09-20→10-11 窗） | fixture 主样例 | 口径裁定 |
|---|---|---|---|
| `latency.e2e_p99_ms` | value=**562052.0** ms · sample_size=84 · nearest_rank_p99 | value=400.0 · n=10 · 同法 | ✅ 口径一致（数值差异=数据不同，属预期；键名/unit/method 逐字一致） |
| `avail.success` | value=**null** · successful=0/total=0 · done_over_terminal_runs | value=0.6 · 3/5 | 一致语义下的**数据缺口照登**：真实面 0 终态行 → 聚合按定义输出 null（非 0 非编造）；缺口根因=终态未埋 Langfuse（FP-L4 面 · 另立 SPEC，本棒不动热路径） |
| `avail.capability_ok` | value=**0.712871…** · hits=72/calls=101 · mean_metadata_ok | value=0.75 · 3/4 | ✅ 口径一致 · **真实出数** |
| `host.cost_per_successful_task` | value=0.0 · successful=0 · total_cost=0.0（**空行集机械输出 · 分母 0 守卫返回值，非真实口径**） | value=0.004 · 2 任务 | **缺口照登**：成功 run 集在 Langfuse 面不可得 → 口径前提不满足，空样例输出不作数；unknown 铁律实证见下 |

缺单价铁律真实数据实证（辅助演示 · 非口径内 · 仅验证 FP-L7 在真实 usage 行上触发）：将 dev 环境 117 行非零 usage GENERATION 行（未按成功 run 过滤 · model 分布 None×114/test-model×3）强喂 `aggregate_cost` → `value="unknown"` · `total_cost="unknown"` · basis=`estimate_only_not_billing`——缺单价（`MODEL_UNIT_PRICES` 无对应档）→ **unknown 非 0**，铁律 PASS。

**FP-L3 裁定：无口径冲突。** 四键键名/字段形状/unknown 语义与定义表 §2 逐字一致；两条数据面缺口（终态、成功过滤）同根因=终态未埋 Langfuse trace metadata，修复需热路径埋点改动 → FP-L4 面（另立 SPEC 链路），本棒零改码不触碰。

## 6. TC-L4 · 离线闸

```bash
uv sync --extra dev   # 本 worktree 建环境（承上游坑留痕）
uv run pytest tests/eval/test_host_v1_sli.py -q
```

输出摘录：`......... [100%] 9 passed in 0.07s`（exit 0 · 不连网 · fixture）。本棒**零 `.py` 改动** → ruff 触及面净增 0（存量错误与本棒 diff 零交集，不修 · 承上游零扩面纪律）。

## 7. TC-L5 · 零越界 diff 白名单

本棒触及面（含 untracked 新增）：

| 路径 | 性质 | 白名单 |
|---|---|---|
| `docs/reports/host_v1_exit_review/SLI_DASHBOARD_LIVE_EVIDENCE_20261019_40.md` | 新增（本件） | ✅ 证据目录 |
| `docs/reports/host_v1_exit_review/sli_live_export_sample_20261019.json` | 新增脱敏样例 | ✅ 证据目录（原始 API JSON 不入仓） |
| `docs/tasks/active/task_host_v1_sli_dashboard_live_evidence.md` | task 档回填（自检结论/修订记录） | ✅ 本 task |
| `docs/harness/invokes/by-task/host-v1-sli-dashboard-live-evidence/invoke_20261019_40_live_evidence.md` | 40 invoke | ✅ invoke 档 |

零触及：`app/` · `evals/agent/sli/aggregate_sli.py` · `evals/agent/sli/fixtures/` 既有样例 · `SLI_host_v1_four_metrics_v1.md`（+ yaml）· `GUIDE_host_v1_sli_dashboard_v1.md` · freeze/SSE/热路径 · Langfuse 端零写入（全程只读 GET；POST 仅一次空 body 路由存在性探测 · 404 无副作用）。

## 8. TC-L6 · 口径一致自检

- 证据中四键仅 `latency.e2e_p99_ms` / `avail.success` / `avail.capability_ok` / `host.cost_per_successful_task`，与定义表 §2 dict_key 列逐字一致；无 `e2e_latency_p99`/`success_rate`/`tool_hit_rate` 等同义异名（FP-L6 PASS）。
- 成功口径=终态 `done`（承 V1-C）：聚合输出 basis=`done_over_terminal_runs`；无另发明公式字样。
- 缺单价/缺 `ok` → `unknown` 非 0（FP-L7 PASS · §5 真实数据实证）；metadata `ok` 未当 score 名上报（FP-L8 PASS · 本棒零写入）。
- 证据全入仓有文件落点（FP-L9 PASS · 本件 + 脱敏样例 + 40 invoke）。

## 9. failure_paths 合规声明

| FP | 处置 |
|---|---|
| FP-L1 不假绿 | ✅ 未触发凭据失效；widget 面照登非凭据根因，附探测证据，零伪造截图/数字 |
| FP-L2 空项目 | ✅ 未触发（1026 traces 有数据）；`module=e2e` 可选筛无匹配如实记 |
| FP-L3 口径冲突 | ✅ 未触发（四键形状/unknown 语义与定义表一致） |
| FP-L4 越界出数 | ✅ 守住：终态/成功过滤缺口=埋点面，需改热路径 → 不动，留另立 SPEC |
| FP-L5 导出脱敏 | ✅ 样例仅 fixture 形状字段；原始 API JSON/CSV 不入仓 |
| FP-L6 键名漂移 | ✅ 四键逐字（§8） |
| FP-L7 伪造 0 | ✅ null/unknown 如实（§5） |
| FP-L8 ok≠score | ✅ 明示区分 |
| FP-L9 证据入仓 | ✅ 本件 + 样例 JSON |
| FP-L10 闸扫描 | ✅ §1 GATE_VERIFY PASS 后开工 |

## 10. CLOSE 档缺口消账对照

| 上游缺口（`close_host_v1_sli_dashboard_20261017.md`） | 本棒消账情况 |
|---|---|
| §四.1 真实 Dashboard widget 实证（可重试） | **未消账 · 延续照登**：凭据根因已消（键有效），新根因=Dashboards API 404 + 无 UI 会话（§3）；重试路径=持 UI 会话者按 §3 表补 widget+截图 |
| §四.2 真实导出对拍无实证 | **已消账**：真实导出脱敏样例入仓（`sli_live_export_sample_20261019.json`）+ 四键对拍并列（§5）· 两键真实出数、一键 null 照登、一键前提缺口照登+unknown 铁律实证 |
| §四.5 40 轨缺位 | **已消账**：本棒=40 实证轨，invoke 落盘 |

## 修订记录

| 日期 | 说明 |
|---|---|
| 2026-10-19 | 40 帽真实实证补录：凭据实判 PASS · widget 面照登（API 404 + 无 UI 会话）· 四项筛选表 API 复开 · 真实脱敏样例入仓 + 四键对拍（capability_ok/latency 真实出数 · avail.success null 照登 · cost 前提缺口 + unknown 铁律实证）· pytest 9 passed · 零改码零越界 |
