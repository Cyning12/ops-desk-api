---
hat: 50
task_slug: hitl-approval-consumption-strategy-env
date: 2026-10-10
---

# invoke · 50+CLOSE · hitl-approval-consumption-strategy-env（T3 · strategy 候选 map env 追加口 OPS_STRATEGY_EXTRA_CANDIDATE_CAPABILITY_IDS）

## 收口结论

- 链路全通：10-task（SPEC v1 signed 承接 D3 · 骨架先行增量落盘 · 锚点实读 config.py:1-45 / builder.py:177-182 · early_stop at R5）→ 20-task-audit R1（PASS · nit×3 非阻塞留 30/40 · 审查文 `docs/harness/reviews/task_hitl_approval_consumption_strategy_env_audit_R1_20261010.md`）→ 维护者三闸人签（HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES · 00 代录 2026-10-10）→ 30（`cd253f0` config.py env 追加口 +49 行 · `3c1c9d1` 18 枚新测 · `86f7cde` 图谱 lg_rag 行备注回写 + 30 invoke · 钉死契约七行逐条落地）→ 40（核验七项全绿 PASS · 独立复跑不采信自报 · TC1–TC3 全机断绿 · B1 八文件 114 passed · 全量 1679 passed · nit×3 吸收复核通过 · `invoke_20261010_40_verify_hitl-approval-consumption-strategy-env.md`）。
- 闸链：三闸全 approved（维护者签 · 00 代录 · `invoke_20261010_00_gate_signoff_t3.md` 留痕 · 图谱闸表 00 代录行在案 01_modules.md 行 114）。
- PR [#213](https://github.com/Cyning12/ops-desk-api/pull/213)：CI 四绿 → merge master `7853334`（2026-10-10 · Asia/Shanghai）· 随 PR 一并带入 T1/T2/T3 三 task 文档链与全部审查/签录（SPEC 文档仍在 `spec/hitl-approval-consumption` 分支 · 带入 master 留后续裁定）。
- 归档：task → `done/`（头部状态 done · F1–F4 + 验收 TC1–TC3 勾选 · 修订表 CLOSE 行）；active README 登记表补行；Hub `docs/tasks/done/README.md` engineering 域表行 + 修订记录行补登；本 CLOSE invoke 落盘。

## 交付摘要

| 项 | 内容 |
|---|---|
| **产出** | `app/ops/strategy/config.py` env 追加口 `OPS_STRATEGY_EXTRA_CANDIDATE_CAPABILITY_IDS`（+49 行 · 逗号分隔/strip/去空去重/调用点读取/台账设则记未设不记）+ `tests/test_strategy_env_extra_candidates.py` 18 枚新测 + 图谱 lg_rag 行 strategy 归属段备注回写（七要素在案） |
| **验收** | TC1 不设 env 逐字节零 diff 对拍（supervisor 五枚/default/未知 key 三例 + 全空白=不设）· 追加语义（map 命中/未知 key 两例 · 覆盖口隔离）· 解析四例；TC2 FP-5 三层裁剪断言（层1 真实 builder 路径选型 40 裁定充分）+ registry/policy/builder 对 master diff 空；TC3 全量 1679 passed · ruff 触及路径零新增 · graph-compile EXIT=0 · 台账双向断言 |
| **红线** | 静态 map 成员零改（supervisor 五枚 + default 一行不动）· `CANDIDATE_CAPABILITY_IDS` 覆盖口分支一行不动（测试钩子纯净 · env 不混入）· 下游 ∩visible/deny 判序/Policy 写闸全链零 diff——**env 只抬候选层，不是放行口** |

## 留痕

- 40 核验期复跑统一用主 checkout 解释器（worktree 无 .venv · rootdir 为 worktree · 码面以 worktree 为准）；全量 pytest 带 `SILICONFLOW_API_KEY=dummy-probe` 直绿 1679 passed · 三连反证口径无需启用。
- ruff 全量基线 55 errors 全部归属既有文件（config.py 与新测试文件零命中 · 触及路径零新增成立 · 为 master 既有基线噪音非本 task 引入）。
- graph-compile 时间戳噪音已 checkout 还原（EXIT=0 实证）；CLOSE 机械闸（task lint done/ 路径 · verify · graph-compile）复跑结果见本 PR CI 前本地留痕。
- worktree `task-hitl-approval-consumption` 与分支 `task/hitl-approval-consumption` 清理留维护者裁决（active README 已登记 · T1 已切 `task/hitl-approval-consumption-loop` 自立 · T2 后续自 master 新切）。

## 移交

- **T1/T2 在途**：T1（消费门/unlock 回填 · `task_hitl_approval_consumption_loop`）与 T2（自动 resume · `task_hitl_approval_consumption_auto_resume`）仍为 active task——本 CLOSE 只收口 T3，**签发审批消费回路全链 CLOSE 待后续 task 收口**。
- SPEC v1 D3/Q4/FP-5/A4 本 task 面闭合；A5/A8 存续面由 T1/T2 承接；SPEC 文档带入 master 的时机留 00/维护者随 T1/T2 首个实现 PR 裁定。
