---
hat: 10-task
task_slug: vector_waterline_local_rerun
date: 2026-10-17
---

# invoke · 10-task 起草 · vector_waterline_local_rerun（TC-WL-5 开账 · 本地/compose 亲跑实证）

## 落稿摘要

- 起因：母体 task prod-vector-waterline-check 已 CLOSE（PR #263 squash ea65d3d），唯 TC-WL-5「40 轨本地/compose 亲跑出真实报告」关账照登未走（close_prod_vector_waterline_check_20261017.md §四.1 + §七 checklist），移交维护者开账；维护者 2026-10-17 选定先推此件（「先 WL-5」）。
- 实证锚点（全部亲读复核）：scripts/check_vector_waterline.py（366 行 · 只读硬约束 :55-59 · 降级三态 :307-332 · 双侧不可达 exit 2 零报告 :325-332）· RUNBOOK_prod_vector_waterline_v1_zh.md（§1 env 表 :22-27 · §2 local 命令 :39-43）· reports/vector_waterline_TEMPLATE.yaml（61 行键集）· 母体 done 档（TC-WL-5 :108 · 30 口径 :190）· CLOSE 档 · docker-compose.yml（qdrant:v1.19.0 :22-39）。
- 起草时环境实证：docker ps → ops-desk-api-qdrant-1 Up 29h (healthy) 0.0.0.0:6333-6334 映射 · ops-desk-api-db-1 Up 29h (healthy) 0.0.0.0:5432 映射 —— 亲跑前置现实满足；tests/test_check_vector_waterline.py 在库（13 桩测先例）；当前分支 master 零改动。
- 范围设计：F1 runbook 命令逐字亲跑 exit 0 · F2 真实报告 reports/vector_waterline_local_<UTCts>.yaml 对模板逐键核验 · F3 40 invoke+勾选+修订记录回填 · F4 三门复跑（ruff/pytest 13 绿/spec-wave verify）。零改码 · 40 单棒 · 零涉生产（HG-PROD-READONLY-ACCESS 仍 pending 不涉）。
- 闸设计：HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 全 pending 未代签（阻塞面 = 40 亲跑；本 task 无 30 棒）。graph_change_layer=none · review_hat=20 · required_invoke_hats=10,40。
- 交付：docs/tasks/active/task_vector_waterline_local_rerun.md（173 行）· npx --yes spec-wave task lint → EXIT=0 · LINT: PASS 一次过。

## 留 20 审要点

- 降级照登不假绿纪律是否钉死（FP-2/3/4 + TC-LR-4 真实性核验）· 禁手改报告冒充与「须改码即 STOP 另立」边界（FP-5/非范围）· 空库如实记 0（FP-6）· 本地报告防误当生产证据（FP-8 + disclaimer）· 闸阻塞面从 30 改为 40 的口径是否认可。
