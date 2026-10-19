---
hat: 10-task
task_slug: host_v1_sli_dashboard_live_evidence
date: 2026-10-19
---

# invoke · 10-task 起草 · host_v1_sli_dashboard_live_evidence（04 测评轨 · SLI 看板真实实证补录）

## 落稿摘要

- 起草帽：00 委派 10-task 子 Agent（2026-10-19 · 维护者会话「全做」选定推进）。
- 上游移交面：task_host_v1_sli_dashboard 已 CLOSED（PR #261 · squash 19a32d5），TC-D1 走 FP-1 降级照登「无实证（无 Langfuse 项目权限）」；CLOSE 档 §四.1/§四.2 钉死两条可重试缺口（真实 widget / 真实导出对拍），§七给获权后补实证路径。
- 凭据面勘察（本帽仅验键存在 · 不读值不判有效性）：`.env` 含 `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` / `LANGFUSE_BASE_URL` / `LANGFUSE_ENV` / `OPS_CHAT_TRACER` 五键俱在 → 存在即权限可能在，40 实判。
- SPEC 判定：承上游钉案——GUIDE + SLI 定义表 signed 已承载范围/非范围，本棒只补证据面；改定义/聚合/GUIDE/热路径任一即 FP-L4 STOP 另立 SPEC。
- 交付：`docs/tasks/active/task_host_v1_sli_dashboard_live_evidence.md`（F1 widget 落地 · F2 查询/导出钉死 · F3 真实聚合对拍 · F4 留档收口；TC-L1~L6 六条；FP-L1~L10 十条；graph_change_layer=none · review_hat=20 · required_invoke_hats=10,40 · 人工闸全 pending）。
- 30 缺位照登：零改码预判无 30 面；实判需改码即 STOP 退回另立项（正补上游 CLOSE 档 §四.5「40 轨未走」缺位）。
- 纪律：人工闸全 pending 未代签 · 零 git · 仅新增 untracked 文件（本 task + 本 invoke）。
- lint：见下「lint 结果」节（起草后自跑）。

## 实证发现（起草前亲读锚点）

- `docs/tasks/done/task_host_v1_sli_dashboard.md`：TC-D1–D6 终态全绿，D1 降级照登句式钉死「照登：无实证（无 Langfuse 项目权限）」；自检结论明示「获权后按证据文 §3 补 widget + 截图」。
- `docs/tasks/close/close_host_v1_sli_dashboard_20261017.md`：§四.1 真实 Dashboard 缺口可重试 · §四.2 真实导出对拍缺口 · §四.5 40 轨缺位照登 · §七 checklist「（获权后）D1 补实证」。
- `docs/reports/host_v1_exit_review/SLI_DASHBOARD_EVIDENCE_20261017_30.md` §3：四项 widget 名=dict_key 逐字 + UI 入口/筛选字段/时间窗/导出字段钉死表 + 导出映射脱敏约定（仅 fixture 形状字段 · 原始 CSV 不入仓）——本棒 F1/F2 操作真值。
- `GUIDE_host_v1_sli_dashboard_v1.md`：三步打开看板 + 字段清单 + 非范围；「无项目权限时用 fixture 聚合作有数证据」降级声明仍在（本棒反向走获权路径）。
- `SLI_host_v1_four_metrics_v1.md` §1/§2：成功口径承 V1-C（终态 done）· Cost 缺单价 unknown 不伪造 0 · 禁同义异名 · 四键 `latency.e2e_p99_ms` / `avail.success` / `avail.capability_ok` / `host.cost_per_successful_task`。
- `evals/agent/sli/`：`aggregate_sli.py`（DICT_KEYS 四键与定义表逐字一致 · `aggregate_all_from_fixture` 支持自定义路径）+ fixtures `sli_sample.json` / `sli_sample_unknown.json` 俱在；离线闸 `tests/eval/test_host_v1_sli.py` 在。

## lint 结果

- `npx --yes spec-wave task lint --file docs/tasks/active/task_host_v1_sli_dashboard_live_evidence.md` → **EXIT=0 · LINT: PASS**（首跑 E5 缺 ### 自检结论 节 → 补 draft 占位节后复跑 PASS）。
- `lint-wiki-delta` 本版 spec-wave 无此命令（未知命令 · EXIT=1），未跑；单 task 起草非批量拆分，`wiki_delta` 字段已在元信息表预填（`n/a` + note）。

## 留 20 审要点

- 40 轨实证棒的闸表 blocks_hats（无 30 · HG-AUDIT-R1 blocks 40）是否合规 · FP-L1/L2/L3 不假绿三连是否充分 · TC-L3 对拍断言形态（真实导出经 `aggregate_all_from_fixture` 读路径）· invoke_retention_profile=minimal（10,40）取舍。
