---
hat: 10
task_slug: hitl-approved-replan-quality
date: 2026-10-11
---

# invoke · 10+task 起草 · hitl-approved-replan-quality（SPEC §9 序1）

## 落稿摘要

- 首棒（子 Agent 2c4b0fd5）骨架先行纪律生效——落骨架 commit 0f0ecc 后填肉卡滞 · interrupt 留痕 · **00 代笔填肉**（授权 m01606 · 文档面非实现码）。
- 锚点亲读复核（base cae745e · merge 后行号漂移校正）：真决策点 = app/ops/lg_rag/multi/nodes.py:1759 `obs["verdict"] = "replan" if approved else "settle"`（SPEC §9 旧引 router.py:328-357 系 app/ops/hitl/router.py _collect_decisions 汇总面 · task 文按真值锚）；:1156 nonce 重签发=write 重放危害论证；_stamp_host_plan def :630；保号 :747/:997 只保号不解决重放本体。
- 交付：docs/tasks/active/task_hitl_approved_replan_quality.md v1——D1 三案（A 定点重跑/B 记忆注入/C 混合倾向）· D done{completed} 倾向另立（非范围照登留裁定口）· 钉死契约 5（write 零重发核心红线）· FP-1~FP-4 · TC1-TC5（TC1 红测先行防恒绿 · TC3 live 依赖序2）· 三闸 pending。

## 留 20 审要点

- D1 三案取舍 · D「另立 vs 顺手收」裁定 · TC3 依赖序2 排期合理性 · FP-2「计划过期」反例构造可行性。
