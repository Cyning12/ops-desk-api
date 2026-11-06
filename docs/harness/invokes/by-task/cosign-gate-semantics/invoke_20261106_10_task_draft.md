# invoke · 10 起草 · cosign-gate-semantics（2026-11-06）

| 项 | 值 |
|----|----|
| hat | `10`（task 起草 · 承 issue #333 维护者令） |
| task_slug | `cosign-gate-semantics` |
| task 文件 | `docs/tasks/active/task_cosign_gate_semantics.md` |
| 分支 | 落稿 `agent/cosign-semantics-task-022a61b26cba`（部署绑定末段=工单名）；30 执行分支预登记 `fix/cosign-gate-semantics`（base `master` · 待闸签收后另行授权） |
| 指令来源 | issue #333 维护者 comment `6676316476`（2026-11-06 03:46）：「请按 Harness 流程起草设计 task 文档（10 帽活：只产 docs/tasks/active/ task 档 + lint PASS + PR；30 待闸签收后另行授权）」五要求（设计闸决策点=同签语义裁决口径 / task 档六要素 / 红测先行或机断判据 / 三红线入 failure_paths / lint PASS 出货）· 受理依据 = 维护者 2026-11-06 08:48 授权（lead 代行签收与验收） |

## 输入真值（已读）

- issue #333 正文（backlog：human-gate co-sign branch（0c88ac32）缺机器人同签语义——绕过 record 杠杆仍在 · 来源 #323 40 invoke 增强/收尾清单 · 建议 fix task 流程 · 设计闸决策点=同签落点（消费门内 vs gate 记录层））+ comment `6676316476`（题面 = 同一维护者对同一工单的签认在跟进消息送达时的认定规则 · 三案对比 + 审计链影响面）。
- 10 档实扫：`git cat-file -t 0c88ac32` = 非本仓 git 对象 → 承载面按本仓 Harness 过程资产落档（闸表/代录/审计链/invoke），仓外运行时面如实登记 residual_risk。
- 现状锚（task 档背景节全引）：闸表四列契约=record 杠杆本体（task lint E 系机读 · GATE_VERIFY 唯一闸据）· 签认三形态（维护者直签 / 00 代录 `0c147a6` / lead 预授权代录 `6652283580` · 每处须引依据）· 审计链（闸表行→invoke→审查文→CLOSE 档 · 只追加先例）· 同签先例（w-join-gap 三闸同签=一次送达多闸，未覆盖多次送达）。

## R 轮结论摘要

| 轮 | 结论 |
|----|------|
| R0 | 缺陷 = 同签认定规则缺位（流程语义面 · 非码面）：重复送达既可能误读为新签（record 杠杆绕过面）也可能误读为冲突（流程死点）；0c88ac32 不在本仓 → 承载面限本仓过程资产，仓外面登记 residual_risk |
| R1 | 范围 = 裁决落文 + 机断回归 + 条件旧测适配；非范围八条（口径自裁/SSE/freeze/改码面外溢/spec-wave 上游/闸表契约/web·iOS） |
| R2 | 设计闸三案：**幂等**（单记录单效力 · 须绑 scope/窗口时效锚 · 绕过面最小）/ **覆盖**（须 append-only 防断链 + 人类显式意图判据 · 绕过面最大）/ **拒重复**（须消歧通道防死点）；落点子题（消费门内 vs gate 记录层 · #333 正文）随口径一并裁决；组合形态留维护者，10 档不预断 |
| R3 | FP-1~FP-11：四闸拒开工 / SSE 零 diff / freeze 不动 / 改码面收敛 / 决策点属闸 / 三案滑点（幂等滑覆盖·覆盖断链·拒重复死点）/ 闸表契约 / 验收不可机断 / 落文与处置面漂移 |
| R4 | 机断判据为主（条文 grep 锚 + 结构断言）；涉码则红测先行（负样本 = 重复送达误读为新签 · 真实送达→认定→记录路径驱动 · 禁直造记录）；live/独立复跑留 40 |
| R5 | 落稿 · 四闸 pending · NO-GO 20/30 · lint PASS 出货待审 · 30 待闸签收后另行授权 |

**actual_last_round**：R5 · **early_stop**：no · **residual_risks**：①0c88ac32 承载面在仓外运行时；②三案组合形态待设计闸裁决

## task_slug 说明

`cosign-gate-semantics`（fix/流程设计类 · 承载面 = human-gate 同签认定规则）；task 文件 / 30 分支 `fix/cosign-gate-semantics` / invoke 目录同名一致。

## 闸表（全部 pending）

| 闸 | blocks | 说明 |
|----|--------|------|
| HG-TASK-DRAFT | 20-R1, 30 | 初稿未经 20-task-audit 审查与维护者签收 |
| HG-AUDIT-R1 | 30 | 20-task-audit R1 审查文未落盘 |
| HG-GRAPH-MODULES | 30 | `none` 口径待签（无图谱面 · 承 planner-args 先例；30 实扫出图谱面须回签） |
| HG-COSIGN-SEMANTICS-DESIGN | 30 | **设计闸** · 同签语义裁决口径三案（幂等/覆盖/拒重复 + 审计链影响面）+ 落点子题（消费门内 vs gate 记录层） |

## 自检

| 命令 | 结果 |
|------|------|
| `npx --yes spec-wave@3.5.0 task lint --file docs/tasks/active/task_cosign_gate_semantics.md` | **PASS**（2026-11-06 · 零 warn） |
| `npx --yes spec-wave@3.5.0 task lint-wiki-delta --target .` | **PASS**（scope all · scanned 211 · missing 0 · issues 0） |

## 禁区复核

- 未改 `app/` / `alembic/` / `tests/`（仅 `docs/tasks/active/` + 本 invoke）。
- 未签任何 human_gate（四闸 pending 待维护者/lead 签收；裁决口径留 HG-COSIGN-SEMANTICS-DESIGN 随档裁决）。
- 10 档实扫只读（git cat-file / grep · 零仓内状态变更）。
