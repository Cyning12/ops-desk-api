# Task：P0' T6 审计统一视图——v_audit_unified（单张 DB view）

> **状态**：in_progress（2026-11-14 起）
> **类型**：迁移（CREATE VIEW · 零表结构变更 · 零读写代码）
> **落盘**：`docs/tasks/active/task_p0prime_t6_audit_view.md`；验收后 `git mv` → `docs/tasks/done/`
> **来源**：ops-desk-workspace `06-kickoff-readiness.md` 任务卡 T6（:41）+ R4 裁定 P3（:16 · issue #23；T5 已闭环 df3177b2/9c1d2c03）

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `p0prime-t6-audit-view` |
| **test_strategy** | `required` |
| **test_strategy_note** | 三源表种子行 → view 跨域 run_id+时间窗查询真 PG 实证；迁移 up/down scratch 实证 |
| **code_quality_bar** | `recommended` |
| **orchestration** | P0' 任务卡 T6（关键链外 · T5 已闭环） |
| **semi_auto** | `false` |
| **audit_profile** | `human_only` |
| **invoke_retention_profile** | `default` |
| **required_invoke_hats** | `10,30,40` |
| **git_branch** | `task/p0prime-t6-audit-view` |
| **graph_change_layer** | `G-L1` |
| **graph_delta** | `note-only` |
| **graph_delta_note** | 不新增一级模块；`01_modules.md` db 行登记 view + HG-GRAPH-MODULES 签收行 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 本仓未启用 WikiTrack |
| **review_hat** | `20` |
| **close_pr_policy** | `required` |
| **experience_capture** | `recommended` |
| **kpi_rubric** | `KPI_RUBRIC_v1_2` |
| **kpi_aggregator** | `CLOSE` |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| **HG-TASK-DRAFT** | approved | 22-R1, 30 | 维护者授权（issue #23 R4 评论 + 会话 m00177「签收，开始」） |
| **HG-AUDIT-R1** | approved | 30 | 维护者会话签收（m00177，覆盖 P0' T1–T7）；R1 审查文 `docs/harness/reviews/task_p0prime_t6_audit_view_audit_R1_20261114.md` |
| **HG-GRAPH-MODULES** | approved | 30 | 仅 db 行登记 view，不新增一级模块；签收行见 `01_modules.md` |

---

## 背景与目标

R4 裁定 P3：P0' 合格线 = **一张 DB view `v_audit_unified`**——union receipts/llm_usage/hitl_requests，公共列 `ts/tenant_id/user_id/run_id/domain/action/outcome`，带 tenant_id 过滤（view 暴露 tenant_id 列，过滤在查询侧）。**不做端点、不做聚合页**。审计现状是三张分域表（无统一视图），跨域拉一条 run 的执行链要三次查询。

**完成态**：

- [ ] `alembic/versions/20261114_v_audit_unified.py`（down_revision=`20261114_ops_goals`）：CREATE OR REPLACE VIEW + down=DROP VIEW IF EXISTS。
- [ ] `tests/test_v_audit_unified.py`：三源种子行 → run_id+时间窗一条 SQL 拉出跨三域执行链（P3 验收原文）+ tenant_id 列过滤可用 + llm 行 tenant_id='' 从严。
- [ ] 图谱 db 行登记 + 签收行；registry N3 entry；invoke 10/30/40；R1 审查文。

**设计裁定（30 钉死）**——三源列面勘察（models.py）：

| 公共列 | receipts (:433) | hitl_requests (:540) | llm_usage (:710) |
|--------|-----------------|----------------------|-------------------|
| ts | created_at | created_at | created_at |
| tenant_id | 有 | 有 | **缺 → ''（从严口径承 data 层先例）** |
| user_id | 有 | **缺 → COALESCE(decision_by,'')** | **缺 → ''** |
| run_id | **缺 → NULL** | 有 | 有（nullable 原样） |
| domain | 'capability_receipt' | 'hitl' | 'llm_usage' |
| action | capability_id | blocked_by | COALESCE(task_type, surface) |
| outcome | CASE ok → 'ok'/'error' | status 原值 | 'recorded' |

1. **不改三源表**（零 ALTER）——view 只读投影，源表零风险；缺列域按上表补 NULL/''。
2. 附 `source_id` 列（三源各自 PK）供回查对账；不附其他域专有列（P3 公共列口径）。
3. 不物化、不加索引、不做端点/聚合页（P3 非范围）；view 随查询走源表索引。
4. CREATE OR REPLACE（幂等可重放）；down=DROP VIEW IF EXISTS。

## 范围

`alembic/versions/20261114_v_audit_unified.py`（新建）· `tests/test_v_audit_unified.py`（新建）· `docs/_tech_graph/l1/01_modules.md` · registry/invokes/审查文/本 task 单。

## 非范围

审计端点/聚合页/物化视图/源表结构变更/Langfuse 侧改动（P3 裁定钉死「不做端点、不做聚合页」）。

## 失败路径

| 失败 | 语义 |
|------|------|
| 迁移 down | DROP VIEW IF EXISTS，幂等 |
| 代码回滚 | view 无任何代码读写方，回滚零影响 |

## 验收标准

- [ ] 迁移 up/down 本地真 PG scratch 实证通过（`DATABASE_URL` 覆盖——T5 教训）。
- [ ] 新 DB 用例真 PG 全绿：**按 run_id+时间窗一条 SQL 拉出跨三域执行链**（P3 验收原文）+ tenant_id 过滤可用。
- [ ] 干净 worktree（无 .env）全量 pytest 零新红（既有 ta2 红除外）；ruff 绿；lint-imports 绿；spec-wave task lint PASS。
- [ ] registry entry 登记（base=9c1d2c0 · banned_prefixes 空——含 alembic/ 迁移文件）。

## 给执行帽的必读列表

- `docs/tasks/done/task_p0prime_t5_goals_ddl.md`（承继体例 + alembic URL/ORM None 教训）
- `app/db/models.py`（OpsCapabilityReceipt :433 / OpsHitlRequest :540 / OpsLlmUsage :710）
- workspace `docs/01-scope/03-general-agent/06-kickoff-readiness.md`（任务卡 T6 :41 · 裁定 P3 :16）

## 思考轮控制

| 轮 | 结论 | early_stop |
|----|------|-----------|
| R0 | 审计=三分域表无统一视图；P3=单 view 合格线 | 否 |
| R1 | 三闸 approved；列映射裁定钉死（含缺列域补值口径） | 否 |
| R2 | 迁移 → 测试 两竖切 | 否 |
| R3 | down 幂等；view 零读写方回滚零影响 | 否 |
| R4 | 种子行跨域查询真 PG；scratch up/down 实证（DATABASE_URL 覆盖） | 否 |
| R5 | 验收 4 条过 → 交付 | 否 |

### R0 · 问题框定

审计现状 receipts/llm_usage/hitl_requests 三分域表；跨域拉 run 执行链需三查。P3 合格线=单张 view。

### R1 · 开工闸

三闸 approved（见人工闸表）；列映射裁定（含 receipts 无 run_id、llm_usage 无 tenant/user 的补值口径）钉死。

### R2 · 竖切

迁移 `20261114_v_audit_unified` → `tests/test_v_audit_unified.py`。

### R3 · 失败语义

见失败路径表；CREATE OR REPLACE 幂等可重放，down=DROP VIEW IF EXISTS。

### R4 · 可测性

三源种子行 → view 跨域查询真 PG 实证（承 T4/T5 brew postgresql@18）；scratch 迁移实证用 `DATABASE_URL` 覆盖（T5 教训）。

### R5 · 交付判定

验收 4 条全过 + PR CI 绿 + CLOSE 波次。

### 自检结论

（40 验证回填）

## 实现备忘

（30 回填）

## 测试策略（Harness）

- `tests/test_v_audit_unified.py`：三源种子 → run_id+时间窗跨域查询 + tenant 过滤 + 缺列补值断言（_DB_REQUIRED skip 体例承 T4/T5）。
- 迁移：scratch 库 upgrade/downgrade/upgrade 实证（`DATABASE_URL` 覆盖）。

## 修订记录

| 日期 | 修订 |
|------|------|
| 2026-11-14 | 初版（00 起草 · 10 过闸） |
