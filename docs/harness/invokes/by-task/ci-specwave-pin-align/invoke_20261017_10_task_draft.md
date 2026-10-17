---
hat: 10-task
task_slug: ci_specwave_pin_align
date: 2026-10-17
---

# invoke · 10-task 起草 · ci_specwave_pin_align（仓卫生 · CI/脚本钉版对齐 3.3.0）

## 落稿摘要

- 起草帽：子 Agent 3ba49fb8（X 线 · 00 委派 · 2026-10-17 批次五方向之一）。
- 实证锚点：scripts/graph-compile.sh:28 与 .github/workflows/lint-wiki-delta.yml:35/:39 仍钉 spec-wave 3.0.1；package.json:6 / .coding-kit/manifest.json / pnpm-lock 已 3.3.0；tech-graph.yml:33 走脚本无独立钉版。
- 授权锚点：docs/tasks/close/close_specwave_330_graph_update_20261011.md 已照录不一致并建议「另立小 task」——本 task 即该另立案。
- 交付：docs/tasks/active/task_ci_specwave_pin_align.md（TC-1~6 含 CI 绿实证 + npx 缓存防假绿 · FP-1 revert 预案 · FP-5 刻意保留 3.0.1 裁定口）。
- lint：spec-wave task lint PASS（仅 W3 占位提醒照登）· lint-wiki-delta --scope active PASS。

## 留 20 审要点

- TC 断言是否机断可验 · 回滚预案可操作性 · graph_change_layer=none 判定是否成立（3.3.0 compile 若产图谱漂移须走 FP-2 不混入）。
