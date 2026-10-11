---
hat: 50
task_slug: hitl-approval-consumption-loop
date: 2026-10-10
---

# invoke · 50+CLOSE · hitl-approval-consumption-loop（T1 · D1 审批消费门 + D2 unlock 空形态回填 + D4 台账/测试 · 批准→放行消费成环核心）

## 收口结论

- 链路全通：10-task（SPEC v1 signed 承接 D1/D2/D4 · 骨架先行增量落盘 · 锚点逐行实读 master `4d905e0` · R1-N1/N2 两实证扩面 · early_stop at R5）→ 20-task-audit R1（FAIL→修复→增量复核 PASS · 审查文 `docs/harness/reviews/task_hitl_approval_consumption_loop_audit_R1_20261010.md` · commit `45fec13` · 残留 NIT 计数口径回改「14 处」）→ 维护者三闸人签（HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES · 00 代录 2026-10-10 · `invoke_20261010_00_gate_signoff_t1.md` 留痕）→ 30（`f7177bf` 消费门+unlock 回填+payload 增键 · `b281d7c` B1 十四处 sync→async 随改+A4④ 设计真态段双断言改写 · `8503456` 验收 29 枚+UP017 lint 修 · `80eb872` 增强 29→34 枚（Db 双 store TTL 真读组/TA1 span 双面/TA3③ resume 成环机制段/TA4-D/TA5 台账/TA6 409 保留）· `c70a9d4` 图谱 lg_rag/hitl 行备注+在册行回写+30 invoke · `b78d814` 收尾棒增量回填）→ 40（核验七项 PASS 带偏差登记 · 独立复跑不采信自报 · TA1–TA7 全机断绿 · 全量 1713 passed 0 failed · live 六 env 组挂起→pending→decide→**resume 200** 实证 · `9080c0a`/`3a8fb3f`/`d1b0c06`）。
- 闸链：三闸全 approved（维护者签 · 00 代录 · 图谱闸表在册行 lg_rag/hitl/capability 在案 01_modules.md）。
- PR [#216](https://github.com/Cyning12/ops-desk-api/pull/216)：CI 四绿（import-linter / lint-wiki-delta / pytest / check）→ merge master `3f6a630`（2026-10-10 · Asia/Shanghai）。SPEC v1 文档此前已随 PR #214（`dd728ab`）带入 master，本 PR 不再承担带入义务。
- 归档：task → `done/`（头部状态 done · F1–F6 + 验收 TA1–TA7 勾选 · TA3 live 末段标注「resume 200 达成 · done{completed} 末段 replan 重盖章上抛 T2/SPEC v2」· 修订表 CLOSE 行）；active README 登记表补行；Hub `docs/tasks/done/README.md` engineering 域表行 + 修订记录行补登；本 CLOSE invoke 落盘。

## 交付摘要

| 项 | 内容 |
|---|---|
| **产出** | `app/ops/lg_rag/multi/nodes.py` 编排层 async 消费门（_delegation_issue_block_reason / _join_subtasks async 化 · +148 行 diff 面）+ `_persist_hitl` payload jsonb 增键 `capability_id`（零迁移）+ unlock 空形态回填（unlock=被拦 sid 自身 · 仅 delegation_issue 类形态守卫）+ `tests/test_hitl_approval_consumption.py` 34 枚新测 + B1 十四处随改（含 `scripts/acceptance/capability_step_contract_gate.py:152` 补 `await`）+ 图谱 lg_rag/hitl 行备注回写 |
| **验收** | TA1 消费放行（台账 logger+span 双面）· TA2 变异否定八组 25+ 枚（pending/rejected · 三元组/缺键/类型守卫 · TTL InMemory+Db 双 store 真读 · 读异常 · env 解析 · 归一）· TA3 unlock=sid+resume 成环机制段 + live resume 200 · TA4 反回归（registry/policy/delegation diff 空 + 消费不过 gateway/Policy 断言）· TA5 off 零触达（spy 零调用+零台账）· TA6 decide 落库不动（store/router diff 空 + prefix_touch 空 unlock 409 保留）· TA7 工程面（全量 1713 passed · ruff 触及面零新增 · graph-compile EXIT=0 · 门禁失败 0） |
| **红线** | `auto_approve_ok` 纯函数零 IO 逐字节零 diff · `registry.py::_match_filter` 与 `policy.py` 闸序段 diff 空 · decide 落库/重复 decide 409 一行不动 · router.py:404-411 409 守卫保留 · off/observe 消费零触达 · capability 包零 IO 零 diff——**消费只作用于 delegation 签发判定，不豁免 gateway/Policy 任何一层** |

## 偏差登记（40 核验「重要发现」· 上抛 T2/SPEC v2）

- **replan 重盖章使消费键失配**：live 中每次 resume 后 supervisor 走 LLM 正常重规划 → `_stamp_host_plan` 重盖 sid（:1→:2→…→:11 逐轮递增实证），消费键 (run_id, subtask_id, capability_id) 永不命中 → FP-3 再拦循环（每轮 decide+resume 均 200 但末段 `done{completed}` 不可达）。SPEC FP-3 假设「_carry_plan 沿用 id 可命中」，实读 nodes.py:1017-1054 证实 carry 只在 LLM 重规划失败/非法时触发；正常 replan 必重盖章。
- **定性**：机制段（TA3③ pytest · sid 保留形态）消费成环已证；T1 范围（手动模式 resume 200 成环机制 · D2 时代 409 已消）达成。**非本 task 回归**。live 收敛需裁定：resume 后对 approved 步骤走 carry 保号 / 或消费键放宽（(run_id, capability_id) 粒度）——留 T2/SPEC v2。

## 留痕

- 40 核验期并发窗 `.env` 被翻 enforce 致窗口性红 4 枚（capability_lookups×3+lg_rag_multi×1 · delegation no_token）；env 覆盖/复原后复绿，非代码归因；master 基线对拍钉死（主仓 master `eb8e93d` 同款 4 测本地同红 · CI 绿 → 本地环境性红 · 与 T1 零关系 · `d1b0c06` 留案）。
- graph-compile 时间戳噪音已 checkout 还原（EXIT=0 实证）；CLOSE 机械闸（task lint done/ 路径 · graph-compile）复跑结果见本 PR 留痕。
- worktree `t1-approval-consumption-loop` 与分支 `task/hitl-approval-consumption-loop` 待清理由 00 处理（active README 已登记）。

## 移交

- **T2 在途**：T2（D5 批准后自动继续可配置面 · `task_hitl_approval_consumption_auto_resume`）仍 active——base 须含 T1 merge 已达成（`3f6a630` 已入 master）；本 CLOSE 只收口 T1，**签发审批消费回路全链 CLOSE 待 T2 收口**。
- SPEC v1 D1/D2/D4 本 task 面闭合；A9/A10 存续面由 T2 承接；偏差裁定（carry 保号 vs 消费键放宽）留 T2/SPEC v2。
