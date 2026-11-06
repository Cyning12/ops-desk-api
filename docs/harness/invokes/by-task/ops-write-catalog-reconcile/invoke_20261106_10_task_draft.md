# invoke · 10 起草 · ops-write-catalog-reconcile（2026-11-06）

| 项 | 值 |
|----|----|
| hat | `10`（task 起草 · 承 issue #336 维护者令） |
| task_slug | `ops-write-catalog-reconcile` |
| task 文件 | `docs/tasks/active/task_ops_write_catalog_reconcile.md` |
| 分支 | 落稿 `agent/catalog-reconcile-task-e848e9dbbf56`（部署绑定末段=工单名）；30 执行分支预登记 `fix/ops-write-catalog-reconcile`（base `master` · 待闸签收后另行授权） |
| 指令来源 | issue #336 维护者 comment [`6678466745`](https://github.com/Cyning12/ops-desk-api/issues/336#issuecomment-6678466745)（2026-11-06 06:14）：「请按 Harness 流程起草 fix task 文档（10 帽活：只产 docs/tasks/active/ task 档 + lint PASS + PR；30 改码待闸签收后另行授权）」四要求（设计闸决策点=覆盖形态 / 红测先行入 test_strategy / 三红线入 failure_paths / lint PASS 出货）· 补发受理 comment [`6679927635`](https://github.com/Cyning12/ops-desk-api/issues/336#issuecomment-6679927635)（2026-11-06 07:46 · 上一条通知丢失未入轮询 S3b 判例）：内容不变 + 明确设计闸双口径（intent 准入 vs spec 目录）与「A1 锚点语义见 task 档」· 受理依据 = 维护者 2026-11-06 13:40 授权（lead 代行签收与验收） |

## 输入真值（已读）

- issue #336 正文（backlog：SPEC v0.1 注册的 ops.write.* 三能力无专属测试面 · 机制面 · 要求=补测试覆盖纯测试面 · 红线=不改实现 · 来源 #323 40 invoke 增强/收尾清单）。
- 维护者 comment `6678466745`（题面 = `ops.write.run_note` 未覆盖——capability_catalog 有、manifest v1.0 三读全绿，但「能力声明↔manifest 一致性」和端到端实跑都没有覆盖到它 · 四要求）+ 补发令 `6679927635`（四要求重述 + 双口径 + A1 锚点语义入 task 档）。
- 10 档实扫（2026-11-06 · 只读）：仓内 `ops.write.*` 唯一注册能力 = `ops.write.run_note`（`app/ops/capability/manifests/ops.write.v1.yaml` 单枚 · 全仓 grep 无其他 ops.write.* id）——校正 #336 正文「三能力」字面；既有测试面 = `tests/test_stage_w_write_expand.py` 16 枚（A1 机制全链/V13/FP-4/A3/A2/A5 · 建设期竖切测试）+ worker-state/planner-args 两族；stage-w 40 invoke 八段实录为一次性 live 核验非常驻覆盖。

## R 轮结论摘要

| 轮 | 结论 |
|----|------|
| R0 | 缺陷 = 能力目录对账覆盖缺口（测试面非码面）：run_note 目录声明全绿但声明↔行为无常驻对账；实扫校正「三能力」= 仓内唯一 ops.write.* 能力（residual_risk 照登） |
| R1 | 范围 = 对账测试面（按签认形态）+ 旧测影响面实扫 + 偏差基线登记；非范围九条（形态自裁/实现改动/SSE/manifest 本体/新能力注册/断言放宽/spec-wave 上游/web·iOS） |
| R2 | 设计闸三案：**案①一致性机检**（声明↔manifest↔注册规格逐字段 · 快稳全机断 · 偏 A1 口径②）/ **案②端到端实跑**（正负样本真实闸链驱动 · 行为面实证最强 · DB 环境依赖）/ **案③两者**（机检打底+端到端补强 · 双口径权重留裁决）；10 档不预断 |
| R3 | FP-1~FP-10：四闸拒开工 / 三红线（fail-closed FP-2 · SSE FP-3 · 改码面 FP-4）/ 决策点属闸 FP-5 / A1 专属闸（口头断言 FP-6 · 直造状态 FP-7 · 单口径 FP-8 · 基准污染 FP-9）/ 闸表契约 FP-10 |
| R4 | 红测先行 + 负样本端到端：漂移构造（声明有·行为无 / 行为有·声明无）经真实闸链驱动 · 先红=现状无对账面必红 · 40 反向实证防恒绿假对账 |
| R5 | 落稿 · A1 锚点语义专节钉死 · 四闸 pending · NO-GO 20/30 · lint PASS 出货待审 · 30 待闸签收后另行授权 |

**actual_last_round**：R5 · **early_stop**：no · **residual_risks**：①「三能力」字面与实扫一枚之差（设计闸可澄清）；②三案双口径权重待 HG-OPS-WRITE-COVERAGE-DESIGN 裁决

## task_slug 说明

`ops-write-catalog-reconcile`（fix/测试面类 · 承载面 = ops.write.* 能力目录对账覆盖）；task 文件 / 30 分支 `fix/ops-write-catalog-reconcile` / invoke 目录同名一致。

## A1 锚点语义（task 档专节钉死 · 本 invoke 摘要）

A1 = ops.write.* 能力目录对账锚点：①**双口径**（intent 准入实际行为 × spec 目录声明）同时成立；②**双向漂移即缺陷**（声明有·行为无 / 行为有·声明无，对账测试下都必须红）；③**对账可机断**（断言锚到文件+键/函数/事件名/SSE 帧键）。红线继承：fail-closed 不放宽 · SSE 事件表零 diff · 改码面收敛（纯测试面）。

## 闸表（全部 pending）

| 闸 | blocks | 说明 |
|----|--------|------|
| HG-TASK-DRAFT | 20-R1, 30 | 初稿未经 20-task-audit 审查与维护者签收 |
| HG-AUDIT-R1 | 30 | 20-task-audit R1 审查文未落盘 |
| HG-GRAPH-MODULES | 30 | `none` 口径待签（纯测试面 · 承 cosign-gate-semantics 先例；30 实扫出图谱面须回签） |
| HG-OPS-WRITE-COVERAGE-DESIGN | 30 | **设计闸** · 覆盖形态三案（一致性机检/端到端实跑/两者 × intent 准入 vs spec 目录双口径） |

## 自检

| 命令 | 结果 |
|------|------|
| `npx --yes spec-wave@3.5.0 task lint --file docs/tasks/active/task_ops_write_catalog_reconcile.md` | **PASS**（2026-11-06 · 零 warn） |
| `npx --yes spec-wave@3.5.0 task lint-wiki-delta --target .` | **PASS**（scope all · 本档 wiki_delta 预填） |

## 禁区复核

- 未改 `app/` / `alembic/` / `tests/`（仅 `docs/tasks/active/` + `docs/harness/invokes/` + 本 invoke）。
- 未签任何 human_gate（四闸 pending 待维护者/lead 签收；覆盖形态裁决留 HG-OPS-WRITE-COVERAGE-DESIGN 随档裁决）。
- 10 档实扫只读（grep / git log / 文件读 · 零仓内状态变更）。
