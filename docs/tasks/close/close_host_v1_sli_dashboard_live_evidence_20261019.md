# CLOSE：host-v1-sli-dashboard-live-evidence（TC-D1 Langfuse 实证补录 · 2026-10-19）

> 关账日期：2026-10-19 · 关账人：00（goal-eb568703）· 体例承 close_hitl_resume_async_20261015.md

## 一、任务信息

| 项 | 值 |
|---|---|
| task | [task_host_v1_sli_dashboard_live_evidence.md](../done/task_host_v1_sli_dashboard_live_evidence.md)（已归档 done/） |
| 性质 | TC-D1 实证补录（**零改码 40 轨** · 承母体 task_host_v1_sli_dashboard PR #261 开账） |
| PR | [#279](https://github.com/Cyning12/ops-desk-api/pull/279) MERGED · squash `72aebad` · CI 4/4 绿 · docs-only 7 件零 .py |
| 审查 | R1 [task_host_v1_sli_dashboard_live_evidence_audit_R1_20261019.md](../../harness/reviews/task_host_v1_sli_dashboard_live_evidence_audit_R1_20261019.md) 通过零阻塞（锚点 12/12） |
| 闸 | 三闸 approved（授权链 00 代录）· retention=minimal（10,40） |

## 二、交付清单

- `docs/reports/host_v1_exit_review/SLI_DASHBOARD_LIVE_EVIDENCE_20261019_40.md`（40 证据文十节）
- `docs/reports/host_v1_exit_review/sli_live_export_sample_20261019.json`（真实脱敏样例 · e2e_latency 84 行/capability_calls 101 行 · 原始 API JSON 不入仓 FP-L5）
- `invoke_20261019_40_live_evidence.md` + 10/20 invoke + R1 审查文随档

## 三、验收核验（TC-L1~L6）

- 凭据实判 PASS：GET jp.cloud.langfuse.com/api/public/projects（pk/sk Basic）HTTP 200 · project=Ops-desk-agent（id cmsn0e1c10012ad0j0agd32aq）· dev 1026 traces/1379 observations 全量分页实测（窗 2026-09-20→10-11）· Scores=0 · prod 50794 条全为 GET /health OTEL 埋点无关照登
- TC-L1 widget：**照登成立·不假绿**——Dashboards 公共 API 三变体（/api/public/v2|v1|/dashboards）全 HTTP 404（text/html）+ 无浏览器 UI 会话 → 四 widget（名=dict_key 逐字）保存+截图缺口延续零伪造；重试路径=持 UI 会话者按 SLI_DASHBOARD_EVIDENCE_20261017_30.md §3 表补
- TC-L2 筛选表复开：latency 字段在（393/1026）· metadata.module=e2e 无匹配照登（真实取值仅 strategy_builder/intent）· avail.success 终态 0 行照登 · capability_ok 101 行 ok（tool_exec span · True72/False29）可复现 · cost 前提不可得照登
- TC-L3 真实聚合对拍：**avail.capability_ok=0.712871…（72/101）真实出数** · **latency.e2e_p99_ms=562052.0ms（n=84 lg-rag 根 trace · nearest_rank · 真实长尾照登不修饰）** · avail.success=null（0/0 终态行 · 非 0 非编造）· cost=空行集机械 0.0 不作数+117 行非零 usage 强喂→unknown（缺单价铁律 FP-L7 真实触发 · MODEL_UNIT_PRICES 无对应档）· FP-L3 口径冲突零
- TC-L4 离线闸：pytest tests/eval/test_host_v1_sli.py 9 passed · ruff 净增 0
- TC-L5 零越界：白名单成立 · 端侧全程只读 GET · app//aggregate_sli.py/定义表/GUIDE/既有 fixtures/freeze/热路径零 diff
- TC-L6 口径一致：四键逐字一致 · unknown 非 0 · ok metadata 未当 score 上报

## 四、偏差与照登

1. widget 缺口延续（API 404+无 UI 会话 · 执行面能力缺口 · 可重试）。
2. avail.success/host.cost_per_successful_task 真实出数缺口同根因=**terminal_status 未埋 Langfuse trace metadata**（终态真源=DB 事件表 app/ops/lg_rag/history.py:254）· 修复=热路径埋点属 FP-L4 面须另立 SPEC，本棒零改码不触碰。
3. 过程异常处置：GitHub SSH（443/22 直连）被断 → HTTPS+gh credential+代理 7890 push 成功照登。
4. CLOSE 消账对照（母体 close_host_v1_sli_dashboard_20261017.md）：§四.2（真实导出对拍）**已消账** · §四.5（40 轨缺位）**已消账** · §四.1（widget）未消账延续。

## 五、遗留移交

| 项 | 去向 |
|---|---|
| widget 保存+截图 | 持 Langfuse UI 会话者按 20261017_30 §3 表补（可重试路径在案） |
| terminal_status 埋点缺口 | FP-L4 面另立 SPEC（热路径 · 非本 task） |

## 六、维护者 checklist

- [x] 凭据实判 PASS 证据文十节留档
- [x] 真实聚合两键出数（capability_ok 0.7129 · p99 562052ms）
- [x] 缺口照登不假绿（widget/success/cost 三处）
- [x] 脱敏合规（原始 JSON 不入仓）
- [x] PR 合并 · 归档 done/ · README 登记 · 50 invoke 落盘
