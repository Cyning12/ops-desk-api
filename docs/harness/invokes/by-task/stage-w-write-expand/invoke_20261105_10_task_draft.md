# invoke · 10 起草 · stage-w-write-expand（2026-11-05）

| 项 | 值 |
|----|----|
| hat | `10`（task 起草 · 00 拆 task 派发） |
| task_slug | `stage-w-write-expand` |
| task 文件 | `docs/tasks/active/task_stage_w_write_expand.md` |
| 分支 | 落稿 `agent/stage-w-task-split-dde653139625`；30 执行分支 `task/stage-w-write-expand`（base `master`） |
| 指令来源 | issue #323 维护者 2026-11-05：「按签收链下一棒：00 拆 task。新 task 档中 Q1 选型留闸待签，其余按 SPEC v0.1 执行」 |

## 输入真值（已读）

- `docs/spec/stage-w-write-expand/SPEC-stage-w-write-expand_v0.md` v0.1（分支 `spec/stage-w-write-expand` · fa83be6 · HG-SPEC-SIGNOFF approved 2026-11-05）：§1 设计纪律六条 + Q4 加载期断言豁免口径（B1 修订）· §2 范围 D1–D4 · §3 非范围八条 · §4 Q1 三案（S1 仓内落笔 / S2 issue 备注写 / S3 sync 触发写 · 建议序 S1 先行）+ Q2/Q3/Q4 · §5 FP-1~FP-7 · §6 A1–A8 · §7 R0–R5 全轮 done。
- issue #323 签收链：hat 20-spec-audit R1（PR #324 · fail 仅 B1）→ 维护者签 HG-SPEC-SIGNOFF（B1 修订 fa83be6 后人签）→ 00 拆 task（本档）。
- 上游实态：[`task_api_controlled_write_hitl`](../../../tasks/done/task_api_controlled_write_hitl.md) CLOSE（PR #303）+ fix 链 #307/#313-314/#319；全仓唯一 write capability = `testing.write.echo`（mock · opt-in · tenant_scoped=false）。
- HG-STAGE-W-DESIGN 先例：上游 task 同款「设计选型 task 闸」承载首条写能力选型（2026-10-30 维护者签）——本档新设 HG-STAGE-W-EXPAND-DESIGN 类比承载 Q1。

## R 轮结论摘要（承 SPEC §7 · task 不重开）

| 轮 | 结论 |
|----|------|
| R0 | 方向 = 受控写闸链接入第二条真实窄写能力（维护者 2026-11-05 立项令；active 为空时的排期裁定） |
| R1 | 范围 = D1 选型接入 + D2 租户下推负样本 + D3 审计观测（只验不建）+ D4 图谱回写；非范围八条（不多扩/不碰 irreversible/无 web/无 SSE 改/闸链一行不动） |
| R2 | Q1 三案留维护者 → task 闸 **HG-STAGE-W-EXPAND-DESIGN**（blocks 30）；Q2 建议 env 显式 opt-in；Q3 幂等键强制 + 新表义务修订表回填；Q4 tenant_scoped=true + 加载期断言（mock 特例清单不扩容） |
| R3 | FP-1~FP-7 锚既有语义（fail-closed 挂起 / F1–F6 跨租户 404 / env 未开启不可见 / 幂等不双写 / TTL 读时过期 / S2 增 FP-6 / 静默改红线拒收） |
| R4 | A1–A8 可机验；pytest 不连真外网（S2 canned adapter）；live 面留 40 |
| R5 | SPEC 签收毕（HG-SPEC-SIGNOFF approved · B1 已修订）→ 00 拆 task；Q1 选型随档裁决（维护者令） |

**actual_last_round**：R5（承 SPEC）· **early_stop**：no · **residual_risks**：Q1 选型未签；20-task-audit 未审；若 Q1=S1 须新表 → 修订表回填 alembic 义务

## task_slug 说明

采 SPEC `spec_slug` / `invoke_slug` = `stage-w-write-expand`（SPEC Harness 元信息既定 · 不调整；task 文件 / 分支 `task/stage-w-write-expand` / invoke 目录同名一致）。

## 闸表（全部 pending）

| 闸 | blocks | 说明 |
|----|--------|------|
| HG-TASK-DRAFT | 20-R1, 30 | 壳未经 20-task-audit 审查与维护者签收 |
| HG-AUDIT-R1 | 30 | 20-task-audit R1 审查文未落盘 |
| HG-GRAPH-MODULES | 30 | 预估 G-L1 行备注薄增量 · 不新增一级模块 · 30 回写回签 |
| HG-STAGE-W-EXPAND-DESIGN | 30 | Q1 选型签收（S1/S2/S3 · 建议序 S1 先行）+ Q2/Q3 随签；类比 HG-STAGE-W-DESIGN 先例 |

## 自检

| 命令 | 结果 |
|------|------|
| `npx spec-wave@3.5.0 task lint --file docs/tasks/active/task_stage_w_write_expand.md` | **PASS**（2026-11-05 · 零 warn） |
| `npx spec-wave@3.5.0 task lint-wiki-delta --target .` | **PASS**（scope all · scanned 206 · missing 0 · issues 0） |

## 禁区复核

- 未改 `app/` / `alembic/` / `tests/`（仅 `docs/spec/`（merge SPEC 正本）+ `docs/tasks/active/` + 本 invoke）。
- 未签任何 human_gate（四闸 pending 待维护者；Q1 留 HG-STAGE-W-EXPAND-DESIGN 随档裁决）。
- SPEC v0.1 正本经 merge `origin/spec/stage-w-write-expand`（fa83be6）入档，作者归属不变。
