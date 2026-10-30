# invoke · 10 CLOSE（api-controlled-write-hitl 归档关账）

| 项 | 值 |
|---|---|
| hat | 10（task/文档帽 · CLOSE 棒） |
| task_slug | api-controlled-write-hitl |
| task 文件 | `docs/tasks/done/task_api_controlled_write_hitl.md`（本棒自 `docs/tasks/active/` 归档迁入） |
| 分支 | `task/api-controlled-write-hitl-close`（起点 = master merge `09f97f4` · 干净） |
| 指令来源 | 棒次参数（00 委派 · 2026-10-30）：CLOSE 清单 8 条 · 只改文档/台账 · 禁改 app/ 与 tests/ |
| 前序 invoke | `invoke_20261030_10_task_draft.md` · `invoke_20261030_20_task_audit.md` · `invoke_20261030_30_implement.md` |

## 一、验收勾选（12/12 · 逐条证据核后勾选）

证据锚：**PR #303 MERGED 2026-10-30T15:13:51Z · merge commit `09f97f4` · feat commit `227a482`**（`gh pr view 303` 实证）· **CI 4/4 绿**：check / import-linter / lint-wiki-delta / pytest（`gh pr checks 303` 实证 · run 41072479105 等）· **30 invoke**（W0–W5 落地 + M1 影响面表 + 质量门 + 全量对拍 27F≡27F 恒等）· **20-R1 审查文**（PASS 零 blocker · M1/N1 闭环）· task 闸表四闸 approved（维护者签 · 00 代录）。

| # | 验收项 | 判定 | 核心证据 |
|---|---|---|---|
| 1 | 人工闸四件 approved | ✅ 勾 | task 闸表（HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES / HG-STAGE-W-DESIGN 全 approved） |
| 2 | W0 无审批不执行（负样本绿） | ✅ 勾 | 30 invoke：`test_write_approval_gate.py` 11/11 绿（红测先行）+ CI pytest 绿 |
| 3 | W1 decide→resume 单路径 · resume_mode 三值 · auto_resume 语义一致 | ✅ 勾 | 30 invoke：decide/resume 零改动 + `_execute_decided_resume` 单路径源码钉死测 + CI 绿 |
| 4 | W2 tenant_scope 下推 · 跨租户 404 · 头/session 403 回归 | ✅ 勾 | 30 invoke：跨租户/缺租户不消费负样本 ×3 绿 + 全量对拍恒等（既有 403 回归在绿集） |
| 5 | M1 影响面逐条标注 | ✅ 勾 | 30 invoke M1 表：全仓仅 TA3/TB5 两例经 tool_exec 执行写能力且均有 approved 单据 → 零破坏；「温和」实证确认 |
| 6 | W3 span `approval_id` 落值 · 审计串链 | ✅ 勾 | 30 invoke：`cap_ctx["approval_id"]` 注入 → gateway.py:1318 预留启用 + `capability_write_approval_consumed` 台账（span + logger） |
| 7 | W4 首条极窄写能力端到端 | ✅ 勾 | `testing.write.echo`（HG-STAGE-W-DESIGN 签收选型）intent→Policy→HITL→resume→执行→审计端到端自动化断言（11 测含全链） |
| 8 | `hitl-browser-decide-v1` 消费语义回归（400/404/409/422） | ✅ 勾 | 30 invoke：`test_hitl_pending_decide.py` 等 decide 回归测在两边失败集之外（绿）· CI pytest 绿 |
| 9 | ruff 绿 + pytest 回归绿 | ✅ 勾 | CI check（ruff）+ pytest 绿；本地全量对拍 27F≡27F 恒等（预存失败系 `.env` 环境性 · CI 无该 .env） |
| 10 | graph-compile 绿 · 不新增 G-L1 一级模块 | ✅ 勾 | 30 invoke（graph-compile OK · W5 薄备注 4 处）+ CI check 绿 |
| 11 | SSE 事件表零 diff | ✅ 勾 | 30 invoke：app diff 仅 `nodes.py` · 事件发射面零改动 + 挂起载荷形态测试钉死 |
| 12 | task lint PASS | ✅ 勾 | `npx spec-wave task lint --file docs/tasks/done/task_api_controlled_write_hitl.md` → `LINT: PASS` EXIT=0（2026-10-30 · 本帽归档后复跑） |

范围节 W0–W5 六项同步勾选（交付实录见 30 invoke 改动清单与设计要点）。

## 二、状态行 / 归档

- 状态行：`active` → `done`（2026-10-30 · PR #303 合入 · CI 4/4 绿 · 验收 12/12）。
- `git mv docs/tasks/active/task_api_controlled_write_hitl.md docs/tasks/done/task_api_controlled_write_hitl.md`（rename 保留历史）。
- 自检结论节回填（hat 30 交付实录 + hat 40 未执行照登）+ 修订表 CLOSE 行。

## 三、指针处置清单（改 / 不改分明）

**改（活跃指针随迁）**：
1. task 档自身：归档 done/ + 状态行 + 勾选 + 自检结论 + 修订行。
2. `docs/tasks/active/README.md`：关账行登记（活跃 0 件 · 承既有表体例）。
3. `docs/discussions/2026-09-17_interview_gaps_adoption_and_landing_v0.md`：§5 进度行「W/P 未开」陈旧表述按实态改注（~~W/P 未开~~ → 阶段 W api 受控写竖切已合入 PR #303 · 2026-10-30 · web HITL 审批页另 task 进行中；P 未开）+ §8.4 修订注记（其二）+ 修订表 2026-10-30 行。该文件确含「W 未开」行（§8.1 表格为阶段定义非进度、不动；§8.2/§8.3 为论证、不动）。

**不改（历史实证记录 · 刻意保留快照）**：
1. `docs/harness/invokes/by-task/api-controlled-write-hitl/invoke_20261030_10_task_draft.md`（:7 · :49 active 路径）
2. `docs/harness/invokes/by-task/api-controlled-write-hitl/invoke_20261030_20_task_audit.md`（:7 active 路径）
3. `docs/harness/invokes/by-task/api-controlled-write-hitl/invoke_20261030_30_implement.md`（:7 · :21 active 路径）
4. `docs/harness/reviews/task_api_controlled_write_hitl_audit_R1_20261030.md`（:3 · :21 · :72 active 路径）
5. task 档自身 lint 验收行 / 自检表首行的 `docs/tasks/active/...`（历史快照 · 承 `docs/tasks/done/task_tenant_readonly_predicate.md` 先例——其归档后 lint 行仍保 active 路径原文）
6. `docs/_tech_graph/l1/01_modules.md:134` HG-GRAPH-MODULES 台账行（仅 task_slug 名引用 · 无 active 路径）
7. `tests/test_write_approval_gate.py:3`（task_slug 名引用 · 且本棒禁改 tests/）

全仓 grep `task_api_controlled_write_hitl` 15 命中逐条核对，无其他 active 指针；仓根 `README.md` 无引用。

## 四、lint 结论

```
npx spec-wave task lint --file docs/tasks/done/task_api_controlled_write_hitl.md
→ LINT: PASS · task_api_controlled_write_hitl.md（EXIT=0 · 2026-10-30 · 归档后复跑）
```

## 五、未闭项 / 观察点（照登）

1. **40 独立验收 invoke 未执行**：task `required_invoke_hats=10,20,30,40`，本 task 无 40 棒、无 40 invoke 落盘；CLOSE 验收锚 = CI 4/4 绿（含 pytest）+ 30 自检表（含全量对拍恒等）+ 20-R1 审查文。是否补 40 live 验收（审批闸 live 演示）移交维护者裁决——非本 CLOSE 棒可补。
2. **web HITL 审批页另 task 进行中**（task 非范围项 · 本 task 仅保 `hitl-browser-decide-v1` 消费语义稳定）。
3. 30 invoke 未决风险三条照登（本地 `.env` 27 预存失败环境性 · 非编排直调面不过审批闸属阶段 P · `write_intent.args_summary` 脱敏摘要），不阻塞 CLOSE。

## 六、CLOSE 档

`docs/tasks/close/close_api_controlled_write_hitl_20261030.md`（体例承 `close_lg_rag_gate_produces_unfulfilled_20261030.md`）。

## 七、禁区确认

本棒零改 `app/` · 零改 `tests/`（diff 仅 docs/ 文档/台账）。
