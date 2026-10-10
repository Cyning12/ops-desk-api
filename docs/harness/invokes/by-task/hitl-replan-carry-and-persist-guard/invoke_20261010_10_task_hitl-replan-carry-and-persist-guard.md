---
hat: 10
task_slug: hitl-replan-carry-and-persist-guard
date: 2026-10-10
---

# Invoke：10 起草 hitl-replan-carry-and-persist-guard（replan 保号 + persist 建单前检查）

> **帽**：Harness 10-task（起草） · **task**：`docs/tasks/active/task_hitl_replan_carry_and_persist_guard.md`
> **分支**：`task/hitl-carry-and-persist-guard`（worktree t-hitl-carry-and-persist-guard · base master `bdd45f9` · 消费回路全链 T1/T2 已 merge）
> **纪律**：骨架先行增量落盘 · 禁改实现码 · 三人工闸 pending 不代签

## 过程留痕

- 2026-10-10 10 骨架先行落盘（本文件 + task 节头占位骨架）→ 增量填充九节（元信息/人工闸/背景/锚点/契约/范围/failure_paths/B1/验收/依赖/必读/R0–R5/测试策略）。
- lint 首跑 FAIL（E3 验收节无勾选项 + W6 思考轮表头）→ 按 T2 模板形态改写为 `- [ ]` 勾选清单与 `| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |` 表 → 复跑 **LINT: PASS · exit 0**（`npx --yes spec-wave task lint --file docs/tasks/active/task_hitl_replan_carry_and_persist_guard.md`）。

## 依据输入（10 已逐行实读 · 实证锚点）

- **T1 40 重要发现**：`docs/harness/invokes/by-task/hitl-approval-consumption-loop/invoke_20261010_40_verify_hitl-approval-consumption-loop.md` :31-40——replan 重盖章 sid :1→:11 递增 · 消费键三元组永不命中 → FP-3 再拦循环 · `_carry_plan` 仅 LLM 重规划失败时触发（nodes.py:1017-1054）。
- **T2 40 live+附带观察**：`docs/harness/invokes/by-task/hitl-approval-consumption-auto-resume/invoke_20261010_40_verify_hitl-approval-consumption-auto-resume.md` :48（run dbc0fc74 · sid :1→:2 · 零 `delegation_approval_consumed` · done 不可达）· :55-57（孤儿 pending `hitl_5cefb116` · `_persist_hitl` nodes.py:1727 先于 `interrupt()` :1736 返回）。
- **维护者裁定（2026-10-10 · 逐字录入 task 背景节）**：① replan 保号 approved/unlocked 步骤使消费键可命中 · live done{completed} 可达；② `_persist_hitl` 建单前查新鲜 approved 单据 · 有则跳过建单。
- **nodes.py 逐行实读锚点**（全部写进 task 现状锚点表）：`_stamp_host_plan` :630-673（:642-649 盖章= sid 递增机械来源）· `_locked_prefix` :676-693（:688 unlocked 摘出前缀）· `_unresolved_suffix` :696-715 · `_carry_plan` :718-734 · replan 三路径 :960-1054 · `_apply_hitl_decision` :1644-1701（:1687-1689 剪旧结果 ⇒ approved 必未解决）· TTL :268-278 · 归一 :281-301 · 消费门 :318-372（:347/:356-357）· `_persist_hitl` :1523-1611（:1544-1555 去重读失败 fail-open 先例 · :1579-1585 capability 真源 :1583 · :1601 acreate=guard 挂点）· `observe_node` :1704-1744。
- **SPEC v1**：`docs/spec/hitl-approval-consumption/SPEC-hitl-approval-consumption_v1.md` :77（三元组+缺键 fail-closed）· :193（FP-3 原裁定覆盖假设已被 live 推翻 · 本 task=修正落地）。
- **格式模板**：`docs/tasks/done/task_hitl_approval_consumption_auto_resume.md`（256 行 · 验收勾选/思考轮表/修订形态）+ `docs/harness/templates/TASK_TEMPLATE.md`。

## 裁定摘要

- **R2 保号机制**：复用 `_carry_plan`「原行带回不重新签发」语义（:721 既有载体）· 保号集合 P=`hitl_unlocked_ids`∩未解决 · 拼装位置 locked 之后 LLM 新后缀之前 · `plan_prefix_ids`/`recoverable_point` 不变。否「回填 locked 前缀」（FP-2 重跑保护扩散）· 否「LLM 提示词保号」（不可机断 · 属非范围）。
- **R2 fail-open 建单**：检查读异常 → 照建单 + `hitl_persist_guard_read_failed` warning 台账（维护者建议「fail-safe 建单+warning」采纳）。理由：漏建单=人干等不存在的审批（:1526-1529 红线）重于孤儿 pending 污染；:1554-1555 去重读失败「退回 state 不崩」同向先例。
- **R2 旧单据交互**：缺 `capability_id` 键 approved 单据 → guard 不匹配（fail-open 照建）· 与消费门缺键 fail-closed（:356-357）同构 · 不扩面不 Backfill · 退化为既有再挂起形态。
- **failure_paths**：FP-1~FP-8 八条（保号误用/前缀语义漂移/旧单据交互/读异常静默/空 allowlist 交互/语义漂移/T1·T2 断言冲突面/终态残留）· FP-1/3/4/5 各有 TB 断言落点。

## 留给 20 审查要点

1. **钉死契约一/二（保号集合与三路径覆盖）**：P=`hitl_unlocked_ids`∩未解决的操作定义是否足够严（FP-1 授权面静默扩大风险）· 三路径全覆盖 vs 空 allowlist 短路（:963-977 locked 即全计划）的交互（FP-5）是否钉死。
2. **钉死契约五（fail-open 裁定）**：维护者建议采纳记录是否准确 · `hitl_persist_guard_read_failed` 台账键命名与「记动作不记内容」纪律是否合 delegation 台账先例。
3. **钉死契约四（guard 镜像消费门）**：复用 `_approval_consumption_ttl_seconds`/`_decided_at_ts` 同一实现 vs 抽共享助手的边界（禁第二份实现是否过强/过弱 · FP-6 语义漂移面）。
4. **B1 冲突面预期**：「resume 重放重建 pending」假设断言与「replan id 递增」假设断言的清点面是否齐全（30 基线对拍是否足以兜住未知冲突）。
5. **验收 TB4 逐字节对拍**：空 unlocked 零 diff 的对拍实现形态（同输入双实现跑批 vs snapshot）留 30 裁定是否过宽。
6. **人工闸三 pending**：HG-TASK-DRAFT/HG-AUDIT-R1/HG-GRAPH-MODULES 全 pending · 10 未代签 · 20 R1 审查后维护者签。

## 修订

| 日期 | 说明 |
|------|------|
| 2026-10-10 | 10 骨架先行落盘 → 增量填充完成 · lint 首跑 FAIL（E3/W6）按 T2 形态改写 → 复跑 PASS exit 0 · 裁定摘要与 20 审查要点回填 |
