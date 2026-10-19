---
hat: 40-verify
task_slug: host_v1_sli_dashboard_live_evidence
date: 2026-10-19
---

# invoke · 40 实证补录 · host_v1_sli_dashboard_live_evidence（TC-D1 Langfuse 实证补录 · 零改码 40 轨）

## 执行摘要

- 执行帽：40（实证补录棒 · 维护者「全做」授权 + 授权链 m00238/m01101 00 代录 · 三闸 approved）。
- GATE_VERIFY：`npx spec-wave verify --target . --task docs/tasks/active/task_host_v1_sli_dashboard_live_evidence.md` → **VERIFY: PASS**（HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 三闸全 approved）。
- 证据文落盘：`docs/reports/host_v1_exit_review/SLI_DASHBOARD_LIVE_EVIDENCE_20261019_40.md`（本 invoke 不重复全文，逐项结论如下）。

## 凭据实判（只读探针）

- `.env` 五键俱在；`GET https://jp.cloud.langfuse.com/api/public/projects`（pk/sk Basic auth）→ **HTTP 200**，project=`Ops-desk-agent`（id `cmsn0e1c10012ad0j0agd32aq`）· `LANGFUSE_ENV=dev` · `OPS_CHAT_TRACER=langfuse` 同 project 确认。
- 数据面：dev 环境 **1026 traces / 1379 observations**（全量分页实测 · 窗口 2026-09-20T09:42Z→2026-10-11T09:30Z）· Scores totalItems=0。
- Dashboards API：`/api/public/v2/dashboards`（GET/POST）、`/api/public/dashboards`、`/api/public/v1/dashboards` → **全部 404（text/html）**。

## TC 逐项

| TC | 结果 | 证据 |
|---|---|---|
| TC-L1 Dashboard 实证 | **照登成立（不假绿）**：凭据有效项目有数据，但 widget 写入面不可达（Dashboards API 404 + 本执行面无浏览器 UI 会话）→ 四 widget（名=dict_key 逐字）保存+截图缺口延续，零伪造 | 证据文 §2/§3 探测表 |
| TC-L2 查询/导出钉死复开 | **完成（API 等价面）**：§3 四行逐条复开——latency 字段在（393/1026）· `module=e2e` 可选筛无匹配照登 · avail.success 终态 0 行照登 · capability_ok 101 行 `ok` 可复现 · cost 成功过滤前提不可得照登；脱敏样例 `sli_live_export_sample_20261019.json` 入仓（原始 JSON 不入仓） | 证据文 §4 |
| TC-L3 真实聚合对拍 | **完成**：真实样例经 `aggregate_all_from_fixture` 输出四键与 fixture 主样例并列；`avail.capability_ok`=0.7129（72/101）· `latency.e2e_p99_ms`=562052.0ms（n=84）**真实出数**；`avail.success`=null（0 终态行 · 非 0 非编造）；`host.cost_per_successful_task` 空行集机械 0.0 不作数照登 + 117 真实 usage 行强喂演示 → `unknown`（缺单价铁律真实触发）；**口径冲突零（无 FP-L3）** | 证据文 §5 |
| TC-L4 离线闸 | **绿**：`uv sync --extra dev && uv run pytest tests/eval/test_host_v1_sli.py -q` → 9 passed in 0.07s；零 `.py` 改动 ruff 净增 0 | 证据文 §6 |
| TC-L5 零越界 | **成立**：diff 仅触 `docs/reports/host_v1_exit_review/`（证据文+样例）+ 本 task + 本 invoke；`app/`/aggregate_sli.py/定义表/GUIDE/既有 fixtures 零 diff；Langfuse 端全程只读 | 证据文 §7 |
| TC-L6 口径一致 | **成立**：四键逐字一致 · 成功口径=终态 `done`（V1-C）· unknown 非 0 · 无另发明公式 | 证据文 §8 |

## widget 实证 / 照登结论（明示）

- **照登：无 widget 实证（widget 写入面不可达）**——非 FP-L1（凭据有效）非 FP-L2（项目有数据），系执行面能力缺口：Dashboards 公共 API 于本部署 404（GET/POST 三变体实测）+ headless 执行面无浏览器 UI 会话。按 FP-L1 纪律禁伪造截图，如实挂账；CLOSE 档 §四.1 缺口未消账，重试路径=持 Langfuse UI 会话者按 `SLI_DASHBOARD_EVIDENCE_20261017_30.md` §3 表保存四 widget + 截图入仓即消账。
- CLOSE 档 §四.2（真实导出对拍）**已消账**；§四.5（40 轨缺位）**已消账**（本 invoke）。

## 偏差与残留（照登）

1. widget 保存/截图缺口延续（上文 · 可重试）。
2. `avail.success` / `host.cost_per_successful_task` 真实出数缺口同根因：终态 `terminal_status` 未埋 Langfuse trace metadata（终态真源=DB 事件表 `app/ops/lg_rag/history.py:254`）——修复=热路径埋点，属 FP-L4 面须另立 SPEC，本棒零改码不触碰。
3. `metadata.module=e2e` 可选筛选真实数据无匹配（module 仅 `strategy_builder`/`intent`），如实记。
4. 真实 latency P99=562052ms 系 dev 窗内真实长尾（含早期挂起 run），数值本身照登不修饰。

## 边界声明

本棒零 `.py` 改动 · 零图谱改动（`graph_change_layer=none`）· Langfuse 端零写入（全程只读 GET；一次空 body POST 仅探测路由存在性 · 404 无副作用）· `.env` 值仅在子进程内用于认证未落盘 · 原始 API 响应不入仓（FP-L5）。
