---
hat: 10-task
task_slug: hitl_ops_runbook
date: 2026-10-17
---

# invoke · 10-task 起草 · hitl_ops_runbook（HITL 生产使用流程手册 + 残留收口）

## 落稿摘要

- 起草帽：子 Agent 45e5a4a5（Y 线 · 00 委派）。
- 关键实证修正：阶段 5 重启持久化曾于 20261010 验收项 5 在 master 1117286 PASS；经 PR #250/#248/#252 三连架构合并后，F2 框为「现行 master（579d283）compose 全链复走」而非首验，TC-4 断言对齐新契约（resume 200 携 replay.cursor → 终帧 done{status:resumed, latency_ms, 无 model 键}）。
- 证据锚点：docs/acceptance/20261009_chat-history-hitl-ux_local_acceptance.md · docs/acceptance/20261010_hitl-consumption-loop_local_acceptance.md · close_hitl_resume_replay_contract_20261017.md（FP-1 model 不补钉案）· close_lg_rag_sse_run_worker_co_disconnect_20261017.md · SPEC-chat-history-hitl-ux_v0.md（Q4：F1/F2 前端移交 ops-desk-web）。
- 交付：docs/tasks/active/task_hitl_ops_runbook.md（F1–F4 / TC-1–TC-9 / FP-1–FP-7 · runbook 落 docs/guides/RUNBOOK_hitl_ops_v1_zh.md · test_strategy=人工 checklist 型 · graph_change_layer=none）。
- lint：task lint PASS（W3 照登）。E6 合规：20261010 便签本机路径仅溯源引用未照抄。

## 留 20 审要点

- 复走 TC 断言与三连合并后契约一致性 · runbook 节名断言可机断性 · 非范围「复走暴露缺口→FP-7 停派不顺手修」是否钉死。
