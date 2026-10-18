---
hat: 40-cleanup-executor
task_slug: local_qdrant_orphan_points_cleanup
date: 2026-10-18
---

# invoke · 40 处置执行 · local_qdrant_orphan_points_cleanup（本地 Qdrant 8574 孤儿点清理 · 含写动作）

> **授权链**：维护者 2026-10-18 授权 00 代录三闸 approved（m01000 · 承 m00238 总授权）· 落码裁定=零落码 curl。
> **口径 disclaimer（FP-7）**：本 invoke 全链为**本地/compose 开发库口径，不得外推生产**；HG-PROD-READONLY-ACCESS 仍 pending，本处置不涉生产、也不消解该闸。

## GATE_VERIFY（开工首出 · task 人工闸表真值）

| human_gate_id | status | blocks_hats | 裁定 |
|---|---|---|---|
| HG-TASK-DRAFT | approved（m01000 代录） | 20,40 | 放行 |
| HG-AUDIT-R1 | approved（m01000） | 40 | 放行 |
| HG-GRAPH-MODULES | approved（m01000 · 零落码 curl） | 40 | 放行 |
| HG-PROD-READONLY-ACCESS | pending（关联闸照登 · 本 task 零涉生产） | — | n/a |

三闸全 approved → 开工；开工前真读 task 全文 + R1 审查文 + 10/20 invoke + 上游证据 e00/e04 + check_vector_waterline.py scroll 形态。

## 执行实录（F1–F5 · 命令全文见 evidence/e00_commands.md）

- **F1 备份硬闸 PASS**：docker inspect 双容器 healthy 留证（e01）→ POST snapshots 建快照 `ops_knowledge-7885642805251913-2026-10-18-00-53-20.snapshot`（e02/e03）→ 下载拷出 host 钉死路径 `backups/local_qdrant_orphan_cleanup_20261018T005320Z/`（untracked 留本机）→ size 82,857,984 双端一致 · sha256 `270b02bd419d1e4a1a94664bc576844467639b65f3bc4838934d567838692e7f` 双端一致 · tar -tf 可读（e04/e05 · R1 N2 已执行）。
- **F2 dry-run PASS**：只读 scroll 9 页得 8574 唯一 int id（min=1 max=8593）· 与上游 e04 基准**逐集相等**（双向 diff 均空集）· |S|==8574（e06/e07）。
- **F3 白名单删除 PASS**：points/delete?wait=true 显式 id 9 批（8×1000+574 · operation_id 41–49 · 全 status=ok）· 批次并集==S · 零 filter/零 delete collection/零 truncate · 他 collection 前后清单零变化（e08/e09/e10）。
- **F4 删后核验 PASS**：points_count=0（e11）· 水位脚本复跑 `reports/vector_waterline_local_20261018T005534Z.yaml`：pg=0 · qdrant=0 · count_diff=0 · verdict=match · dlq empty · degraded=false · EXIT=0。计数对照 8574/0/-8574 → 0/0/0。
- **F5 留档**：处置报告 `reports/local_qdrant_orphan_points_cleanup_20261018T005320Z.md`（含回滚预案 PUT snapshots/recover 预写）+ 证据 e00–e11 + 本 invoke + task 档 TC 勾选/自检结论/修订记录回填。

## 偏差如实记录（不假绿）

- 首次水位复跑（00:54:44Z）未注入 DATABASE_URL（worktree 无 .env）→ degraded · PG 面无实证；**未冒充**，注入主仓 .env 同值 DATABASE_URL 后复跑全绿；降级报告 20261018T005444Z 一并留档。

## TC-OC-1..6 逐项

| TC | 结果 | 实证 |
|----|------|------|
| TC-OC-1 备份硬闸 | PASS | e01–e05 · sha256 双端一致 · tar 可读 |
| TC-OC-2 dry-run 一致 | PASS | e06/e07 · 逐集相等 diff 空集 |
| TC-OC-3 白名单删除 | PASS | e08–e10 · 9 批显式 id · 并集==S · 他集合零触碰 |
| TC-OC-4 删后核验 | PASS | e11 · 水位报告六字段全中 · 处置报告落盘 |
| TC-OC-5 不假绿+可回滚 | PASS | 判定-证据全回溯 · recover 预案预写 · 降级偏差如实留档 · disclaimer 双落 |
| TC-OC-6 零越界 | PASS | git status 仅白名单 untracked · pytest 13 passed · task lint PASS |

## 零越界声明

零落码（curl + python3 stdin 一次性脚本）· `scripts//app//alembic//docker-compose.yml` 零 diff · 写动作仅 F3 ops_knowledge 显式 id 白名单 · 零 filter/truncate/delete collection · PG 仅水位脚本既有只读 SELECT · 生产零访问。
