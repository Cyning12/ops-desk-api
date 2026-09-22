---
hat: 50
task_slug: memory-preference-profile
date: 2026-09-22
---

# invoke · 50+CLOSE · memory-preference-profile（M3 画像记忆 kind=preference）

## 收口结论
- 五棒全通：10-spec（signed 4a2f4d9 · 实扫发现 CHECK kind='fact' 物理锁死→alembic 义务 · 显式-only E1 通路约束合规 §1.2.4）→ 10-task（27 验收 · B1 13 行）→ 20-audit（R1 PASS 零退回 · B1 抽 5 亲跑）→ 30（D1–D5 落地 · 1975ab5+f1faf80 · 变异三态全链路真 PG 过）→ 40（PASS 27/27 · alembic 脏炸路径亲跑 · 变异③复做 · 对拍独立复核）。
- 闸链：HG-SPEC-SIGNOFF / HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES（memory 行备注级 · f90d74d 00 ratify）全 approved（维护者授权 00 代录）。
- PR [#157](https://github.com/Cyning12/ops-desk-api/pull/157)：CI 全绿 → merge master `cede506`（2026-09-22）。
- 归档：task → done/；active README / spec 索引同步（占位表下一建议序 2 = session-summary-fallback）。

## 留痕
- P-1：30 invoke collected 数字偏差（1210→1235 实为 passed 数）→ CLOSE 按 40 实测 1210→1239（+29）入账。
- 偏好挤占统一预算残余风险（span memory_preferences_injected 双计数可观测）。
- 金样判定面=注入上下文结构（不裁判模型自由文本）· 引导语双保险。
- backfill 偶发 flaky（test_reconcile_mismatch_marks_failed 随机序）基线既有，入 fix 候选清单。

## 移交
- 队列下一棒：session-summary-fallback（M5 会话真摘要 · 铁律：可回退原文）。
