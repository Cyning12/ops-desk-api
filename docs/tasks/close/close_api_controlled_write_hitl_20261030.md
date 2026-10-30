# CLOSE：api-controlled-write-hitl（阶段 W · api 受控写 + HITL 写执行审批闸）

> 关账日期：2026-10-30 · 关账人：10（task/文档帽 CLOSE 棒）
> 体例承 [close_lg_rag_gate_produces_unfulfilled_20261030.md](close_lg_rag_gate_produces_unfulfilled_20261030.md)

## 一、任务信息

| 项 | 值 |
|---|---|
| task | [task_api_controlled_write_hitl.md](../done/task_api_controlled_write_hitl.md)（已归档 done/） |
| 性质 | feature · 阶段 W api 侧最小竖切：写类 capability 走 Policy + HITL 审批闸（无审批 fail-closed 挂起）→ decide/resume 单路径接合 auto-resume → tenant_scope 下推一致 → span `approval_id` 审计串链 |
| PR | [#303](https://github.com/Cyning12/ops-desk-api/pull/303) MERGED 2026-10-30T15:13:51Z · merge commit `09f97f4` · feat commit `227a482`（交付分支 `task/api-controlled-write-hitl-w0`） |
| CI | 4/4 绿：check / import-linter / lint-wiki-delta / pytest（run 41072479105 等 · 2026-10-30） |
| 闸 | HG-TASK-DRAFT / HG-AUDIT-R1（20-R1 PASS 零 blocker）/ HG-GRAPH-MODULES / HG-STAGE-W-DESIGN 四闸全 approved（2026-10-30 维护者签 · 00 代录） |
| 审查文 | `docs/harness/reviews/task_api_controlled_write_hitl_audit_R1_20261030.md`（20-R1 PASS · M1/N1 已闭环回填） |
| 30 invoke | `docs/harness/invokes/by-task/api-controlled-write-hitl/invoke_20261030_30_implement.md` |

## 二、交付清单（30 实录）

| 产物 | 说明 |
|---|---|
| `app/ops/lg_rag/multi/nodes.py`（+234/-62 · 唯一 app 改动） | 编排层 `tool_exec_node` 写执行审批闸：`side_effect ∈ WRITE_SIDE_EFFECTS` 且无新鲜 approved 单据 → blocked terminal（`capability_write_hitl_required`）→ `_persist_hitl` → `interrupt()`；两道闸正交（Policy 写闸不豁免 HITL 审批闸）；`_match_fresh_approved` 匹配核心单实现三调用点；D2 空 unlock 回填守卫扩类 `∈ {delegation_issue, capability_write}`；payload `write_intent` 脱敏摘要落既有 hitl `payload` jsonb（零扩表零迁移） |
| `tests/test_write_approval_gate.py`（新增 11 测） | W0–W3 红测先行 + 红线负样本（env-only 无审批仍拦 · 跨租户/缺租户不消费 ×3 · rejected 零执行）+ 恢复单路径源码钉死 |
| `docs/_tech_graph/l1/01_modules.md`（W5 薄增量 4 处） | capability / lg_rag / hitl 行备注 + HG-GRAPH-MODULES 台账 1 行；不新增一级模块 |

零改动确认：`app/ops/hitl/**` · `app/ops/capability/gateway.py`（span `approval_id` 预留启用）· SSE 事件表 · alembic。

## 三、验收核验（12/12 勾选 · 证据锚）

| 验收 | 结果 |
|---|---|
| 人工闸四件 approved | PASS · task 闸表（维护者签 · 00 代录） |
| W0 无审批不执行（负样本绿） | PASS · `test_write_approval_gate.py` 11/11 绿（30 invoke）+ CI pytest 绿 |
| W1 decide→resume 单路径全链 · resume_mode 三值 · auto_resume 语义一致 | PASS · decide/resume 零改动 + 单路径源码钉死测（30 invoke）+ CI 绿 |
| W2 tenant_scope 下推 · 跨租户写 404 · 头/session 403 回归 | PASS · 负样本 ×3 新测绿 + 全量对拍恒等（30 invoke） |
| M1 影响面逐条标注 | PASS · 30 invoke M1 表：全仓仅 TA3/TB5 两例经 tool_exec 执行写能力且均有 approved 单据 → 零破坏；行为变化声明「温和」实证确认 |
| W3 span `approval_id` 落值 · 审计串链 | PASS · `cap_ctx["approval_id"]` 注入 → gateway.py:1318 预留启用 + `capability_write_approval_consumed` 台账（30 invoke） |
| W4 首条极窄写能力端到端 | PASS · `testing.write.echo`（HG-STAGE-W-DESIGN 签收选型）端到端自动化断言（11 测） |
| `hitl-browser-decide-v1` 消费语义回归（400/404/409/422） | PASS · decide 回归测在两边失败集之外（30 invoke）· CI 绿 |
| ruff 绿 + pytest 回归绿 | PASS · CI check + pytest 绿；本地全量对拍 27F≡27F 恒等（预存失败环境性） |
| graph-compile 绿 · 不新增一级模块 | PASS · 30 invoke + CI check |
| SSE 事件表零 diff | PASS · app diff 仅 nodes.py · 事件发射面零改动（30 invoke） |
| task lint PASS | PASS · `npx spec-wave task lint --file docs/tasks/done/task_api_controlled_write_hitl.md` → LINT: PASS（2026-10-30 · 10 CLOSE 复跑） |

## 四、偏差与照登

1. **40 独立验收 invoke 未执行**：task `required_invoke_hats=10,20,30,40`，本 task 40 棒未单独跑、无 40 invoke 落盘；CLOSE 验收锚 = PR #303 CI 4/4 绿（含 pytest）+ 30 自检表（含全量对拍恒等证明零回归）+ 20-R1 审查文。照登为观察点，是否补 40 live 验收由维护者裁决。
2. **本地 `.env` 27 个预存失败**（30 invoke 未决风险 1）：环境性、与交付无关，以 CI 为准——CI pytest 绿已证。
3. **非编排直调面不过审批闸**（30 invoke 未决风险 2）：既有设计边界（审批闸在编排层），属阶段 P 平台项，task 非范围照登。
4. **`write_intent.args_summary` 为脱敏摘要**（30 invoke 未决风险 3）：审计取完整参数走 span/receipt 既有通道。

## 五、指针处置清单（改 / 不改分明）

**改（活跃指针随迁）**：
- `docs/tasks/active/task_api_controlled_write_hitl.md` → `git mv` 至 `docs/tasks/done/`（状态行 `active`→`done` · 验收 12/12 + 范围 W0–W5 勾选 · 自检结论回填 · 修订行）
- `docs/tasks/active/README.md`：关账行登记（活跃 0 件）
- `docs/discussions/2026-09-17_interview_gaps_adoption_and_landing_v0.md` §5 进度 / §8.4：陈旧「W/P 未开」按实态改注「阶段 W api 受控写竖切已合入（PR #303 · 2026-10-30）· web HITL 审批页另 task 进行中」+ 修订表行

**不改（历史实证记录 · 刻意保留快照）**：
- `docs/harness/invokes/by-task/api-controlled-write-hitl/invoke_20261030_{10_task_draft,20_task_audit,30_implement}.md` 内 `docs/tasks/active/...` 路径
- `docs/harness/reviews/task_api_controlled_write_hitl_audit_R1_20261030.md` 内 active 路径
- task 档自身 lint 验收行/自检表首行的 active 路径（历史快照 · 承 `task_tenant_readonly_predicate` 先例）
- `docs/_tech_graph/l1/01_modules.md:134` HG-GRAPH-MODULES 台账（仅名引用 · 无 active 路径）
- `tests/test_write_approval_gate.py:3`（task_slug 名引用 · 且 CLOSE 棒禁改 tests/）

## 六、维护者 checklist

- [ ] 验收锚抽验：PR #303 merge commit `09f97f4` ∈ master · CI 4/4 绿
- [ ] 观察点裁决：40 独立验收是否补跑（live 审批闸演示）
- [ ] web HITL 审批页 task（另 task 进行中）与本竖切的接合验收
- [ ] 本 CLOSE PR 合并后分支 `task/api-controlled-write-hitl-close` 清理

## 七、修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-30 | CLOSE 落稿：验收 12/12 勾选（证据锚 PR #303 / `227a482` / 30 invoke / 20-R1 / CI 4/4 绿）· 状态 done · 归档 done/ · 讨论稿 §8 联动 · README 关账行 · 指针处置清单 · 40 观察点照登 |
