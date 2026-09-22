---
hat: 50
task_slug: multi-replica-verify
date: 2026-09-22
---

# invoke · 50+CLOSE · multi-replica-verify（C3 · L0 多副本验证 · 占位队列末棒）

## 收口结论
- 五棒全通：10-spec（signed 8236747 · 实扫 8 条目进程内状态边界 · HITL 跨实例结构天然成立 · F1 双轨+P1 subprocess 裁定）→ 10-task（26 验收 · B1 10 行 · 双进程基建风险对策）→ 20-audit（R1 PASS 零退回 · 变异相容性核验成立）→ 30（D1–D4 落地 · 4 commit · app/alembic 零 diff · 变异×3 必挂实证 · 实做坑 6 条留痕）→ 40（PASS 26/26 亲核 · 双进程亲跑 9/9×2 · 变异①复做）。
- 闸链：HG-SPEC-SIGNOFF / HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 全 approved（维护者授权 00 代录 · 本 task 零图谱新签义务按实判成立）。
- 合并插曲：master 前进（#150/#146 维护者并入）→ SPEC add/add 冲突（占位原件 vs signed 版）→ 取 signed 版解决（44e2ee0）→ verify 复跑 PASS。
- PR [#165](https://github.com/Cyning12/ops-desk-api/pull/165)：CI 全绿 → merge master `7541102`（2026-09-22）。
- 归档：task → done/；active README / spec 索引同步（含 master 侧重复占位段清理——#150 带入双段，CLOSE 一并归并为「队列清零」段）。

## 移交
- Eureka 条目未覆盖待补（外部 Java 网关在仓外，需跨仓实测）。
- runbook 轨结论有时效（代码漂移后须复跑，入口在 reports/multi_replica_verify/）。
- test_reconcile_mismatch_marks_failed 既有 flaky（时序竞态 embedded==2 实得 3）建议 fix task 加固；边界清单锚点 1 处偏 2 行（gateway.py:81→:79）下波顺手修。
- 清单处置建议是建议非承诺；budget 配额按实例数放大为最重失真项（硬限额化须外置另案）。

## 队列终态
占位 SPEC 队列 **9/9 清零**（llm-layer-hardening · memory-embedding-backfill · continuity-dedup · prompt-asset-roadmap-p1 · memory-preference-profile · session-summary-fallback · security-hardening-W1 · memory-compliance-delete · multi-replica-verify）。prompt-asset-roadmap 阶段二三与 security-hardening W2–W4 为已签收全景 SPEC 的后续波次，不在本队列。
