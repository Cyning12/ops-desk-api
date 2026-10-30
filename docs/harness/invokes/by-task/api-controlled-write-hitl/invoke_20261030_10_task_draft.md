# invoke · 10 起草 · api-controlled-write-hitl（2026-10-30）

| 项 | 值 |
|----|----|
| hat | `10`（task 起草） |
| task_slug | `api-controlled-write-hitl` |
| task 文件 | `docs/tasks/active/task_api_controlled_write_hitl.md` |
| 分支 | `task/api-controlled-write-hitl`（base `master`） |
| 指令来源 | 维护者令（00 转发）：起草阶段 W · api 侧「受控写 + HITL」task 壳 · 只写文档不改业务码 |

## 输入真值（已读）

- `docs/discussions/2026-09-17_interview_gaps_adoption_and_landing_v0.md` §8：阶段序 H→T→W→P 串行钉死；W = 首条极窄写能力 + 结构化 Intent + confirmation + Policy + 幂等审计；进入条件 = T 跨租户负样本达标 + 审批与令牌设计签收；§8.3 禁「写 = 自动提 PR / 改码合并」。
- workspace `05_post_h_stage_brief_v1_zh.md`：H α 验收 A–F，**E = span 预留 `approval_id`**；刻意未做含「写能力/HITL、服务化 Registry、改 SSE freeze」。
- workspace `06_stage_t_second_tenant_prep_v0_zh.md`：阶段 T Fixture 轨已 CLOSE（api PR #142 `f048c57` ∈ master · web PR #76）；契约 F1–F6 freeze；**生产 P 轨真种子仍 NO-GO 另轨**。
- 租户契约 freeze `api-v1-tenant-readonly-context-draft.md`：F1=C（session 真源 + `X-Ops-Tenant-Id` 一致否则 403）· F2 头名 · F3 workspace_id≡tenant_id · F4 跨租户对外 404 · F5 B=`ops-desk-pilot-b` · F6 web 切换 UI。
- 本仓 HITL 既有面实扫：`app/ops/hitl/router.py`（pending/decide/resume/callback/OA-HMAC · decide 两步钉死 · resume_mode 白名单三值未知 400 · 已决 409 · 未知/跨用户 404）· `auto_resume.py`（PR #223 · env `OPS_HITL_AUTO_RESUME` 默认 manual · PG 行锁认领 + 补偿扫描 · **恢复单路径 `router._execute_decided_resume`**）· `resume.py`。
- capability 写判定点：`types.py` `side_effect ∈ {none,read,write,irreversible}` / `WRITE_SIDE_EFFECTS`（注释钉死「写操作闸（与 HITL）的唯一挂钩点」）；`registry.py:120-121` deny_write / allow_write_tags_any（deny_high_risk 永不豁免）；`gateway.py:1318` span `approval_id` 预留未启用；PR #209 testing-write-capability 先例。
- web 冻结契约 `hitl-browser-decide-v1`（`ops-desk-web/src/api/hitl.ts`）：web 只承接禁改；api 侧 decide/resume 消费语义必须稳定。

## R 轮结论摘要

| 轮 | 结论 |
|----|------|
| R0 问题框定 | W 核心 = 「受控」：写类 capability 必过 Policy + HITL 审批闸 + 幂等审计；非自动改码、非平台项。T 已 CLOSE 故前提满足。 |
| R1 进入条件 | §8.1 W 进入条件两项：T 负样本门禁 ✓（PR #142 / web #76）；「审批与令牌设计签收」无现成闸 → **新增 `HG-STAGE-W-DESIGN`（blocks 30）** 承载。 |
| R2 竖切 | W0–W4 同 task（Policy 审批闸接通 → decide/resume 接合 auto_resume → tenant_scope 下推一致 → approval_id 审计 → 首条极窄写能力端到端）+ W5 图谱薄备注；双 freeze 红线：`hitl-browser-decide-v1` 消费语义稳定 + `lg-rag-sse-v1` SSE 零改。 |
| R3 复用优先 → **early_stop** | 挂钩点齐备（approval_id 预留 / side_effect 词表 / resume 单路径 / PR #209 先例）→ 30 性质为「接线 + 负样本」非新建；intent 载荷与审批令牌设计属 HG-STAGE-W-DESIGN 与 30 实扫，非 10 可钉。 |

**actual_last_round**：R3 · **early_stop：yes** · 依据：契约锚点齐、问题面框死，剩余未定项（写能力选型 / 令牌设计）归口 HG-STAGE-W-DESIGN 签收 · **residual_risks**：intent 载荷若大改既有 hitl 表结构 → 迁移面膨胀（30 实扫后回填）；设计签收周期长则 W 顺延。

## task_slug 说明

采维护者建议 `api-controlled-write-hitl`，**不调整**（与分支 `task/api-controlled-write-hitl`、invoke 目录同名一致）。

## 闸表（全部 pending）

| 闸 | blocks | 说明 |
|----|--------|------|
| HG-TASK-DRAFT | 20-R1, 30 | 壳未经审查 |
| HG-AUDIT-R1 | 30 | 20-R1 审查文未落盘 |
| HG-GRAPH-MODULES | 30 | 预估 G-L1 薄增量，不新增一级模块 |
| HG-STAGE-W-DESIGN | 30 | 审批与令牌设计签收（§8 W 进入条件） |

## 自检

| 命令 | 结果 |
|------|------|
| `npx spec-wave task lint --file docs/tasks/active/task_api_controlled_write_hitl.md` | **PASS**（2026-10-30） |

## 禁区复核

- 未改 `app/` / `alembic/` / `tests/`（仅 `docs/tasks/active/` + 本 invoke）。
- 未签任何 human_gate（四闸 pending 待维护者）。
