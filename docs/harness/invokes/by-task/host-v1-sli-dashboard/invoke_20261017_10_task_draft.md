---
hat: 10-task
task_slug: host_v1_sli_dashboard
date: 2026-10-17
---

# invoke · 10-task 起草 · host_v1_sli_dashboard（04 测评轨 · SLI 四项看板落地）

## 落稿摘要

- 起草帽：子 Agent 3ba49fb8（X 线 · 00 委派）。
- 已有/缺口实证：SLI 定义表（signed 2026-09-24）+ aggregate_sli.py + fixture + tests/eval/test_host_v1_sli.py + GUIDE 已 done；缺=真实 Langfuse Dashboard widget + 可复现导出样例 + 真实环境聚合对拍留档（docs/reports/host_v1_exit_review/ 现仅 2026-09-24 三件）。
- SPEC 判定：GUIDE_host_v1_sli_dashboard_v1.md 已承载范围/非范围 → 无需降级 10-spec 预研（文中钉死 · 热路径埋点越界即 STOP 退回另立 SPEC）。
- 交付：docs/tasks/active/task_host_v1_sli_dashboard.md（widget 名=dict_key · 无权限降级「照登：无实证」禁伪造截图 · 证据入 docs/reports/host_v1_exit_review/）。
- lint：task lint PASS · lint-wiki-delta active PASS。

## 留 20 审要点

- Langfuse 权限前置是否写清 · fixture 降级路径与 GUIDE 一致性 ·  widget 命名=dict_key 断言形态。
