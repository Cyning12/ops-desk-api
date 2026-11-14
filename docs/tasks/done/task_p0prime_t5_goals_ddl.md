# Task：P0' T5 goal 落表——ops_goals 仅 DDL（零功能）

> **状态**：in_progress（2026-11-14 起）  
> **类型**：新表 + 迁移（**仅落表零功能**；注入与状态流转属 P1）  
> **关联图谱**：`docs/_tech_graph/l1/01_modules.md`（db 行登记新表 + 签收行）  
> **落盘**：`docs/tasks/active/task_p0prime_t5_goals_ddl.md`；验收后 `git mv` → `docs/tasks/done/`  
> **来源**：ops-desk-workspace `docs/01-scope/03-general-agent/06-kickoff-readiness.md` 任务卡 T5 + 裁定 A2（issue #23 Round 4；T4 已闭环 8287cfa1/fee74fa7）

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `p0prime-t5-goals-ddl` |
| **test_strategy** | `required` |
| **test_strategy_note** | DDL 约束 DB 用例——本地真 PG 实证（承 T4：brew postgresql@18 + opsdesk_test 已起）；迁移 up/down scratch 库实证 |
| **code_quality_bar** | `recommended` |
| **orchestration** | P0' 任务卡 T5（关键链外 · 与 T4 可并行 · T4 已闭环） |
| **semi_auto** | `false` |
| **audit_profile** | `human_only` |
| **invoke_retention_profile** | `default` |
| **required_invoke_hats** | `10,30,40` |
| **git_branch** | `task/p0prime-t5-goals-ddl` |
| **graph_change_layer** | `G-L1` |
| **graph_delta** | `note-only` |
| **graph_delta_note** | 不新增一级模块；`01_modules.md` db 行登记新表 + HG-GRAPH-MODULES 签收行 |
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
| **HG-AUDIT-R1** | approved | 30 | 维护者会话签收（m00177，覆盖 P0' T1–T7）；R1 审查文 `docs/harness/reviews/task_p0prime_t5_goals_ddl_audit_R1_20261114.md` |
| **HG-GRAPH-MODULES** | approved | 30 | 仅 db 行登记，不新增一级模块；签收行见 `01_modules.md` |

---

## 背景与目标

R4 裁定 A2（Goal 落地）：**图零改动，落图为外状态**——新建 `ops_goals(goal_id, tenant_id, thread_id, objective, status)`；P1 切入 = harness 在 stream 入口把 goal 摘要注入 query 前缀，status 规则流转（不让 LLM 自判）。**T5 只落表**：注入/流转/消费代码一律不做（P1 另卡），先把 DDL 事实固化，避免 P1 开工时再背迁移。

**完成态**：

- [ ] `app/db/models.py` 新增 `OpsGoal`（goal_id UUID PK 默认 uuid4 · tenant_id `String(64) NOT NULL DEFAULT ''` 承 notes/runs 先例 · thread_id String(255) 不加 FK · objective Text · status `String(32) NOT NULL DEFAULT 'active'` · created_at/updated_at）。
- [ ] `alembic/versions/20261114_ops_goals.py`（down_revision=`20261114_lg_rag_runs`）：CREATE TABLE + 索引 `(tenant_id,status)`/`(thread_id)`；down=DROP TABLE。
- [ ] `tests/test_ops_goals_ddl.py`：约束真值（默认 status/tenant、NOT NULL 拒 NULL、objective 必填）。
- [ ] 图谱 db 行登记 + 签收行；registry N3 entry；invoke 10/30/40；R1 审查文。

**设计裁定（30 钉死）**：

1. status 词表（docstring 登记，P1 规则流转可迁移修订）：`active`（默认）/ `paused` / `done` / `abandoned`；本卡不写任何流转代码（A2：不让 LLM 自判，流转属 P1）。
2. `thread_id` 不加 FK（承 run_events 顺序容错先例；goal 摘要注入锚点在 P1 才接线，DDL 期不锁死关系）。
3. 零服务层/零路由/零写路径——表落盘后无任何代码读写，off 态 drop 安全（承 memory 表先例）。

## 范围

`app/db/models.py` · `alembic/versions/20261114_ops_goals.py`（新建）· `tests/test_ops_goals_ddl.py`（新建）· `docs/_tech_graph/l1/01_modules.md` · registry/invokes/审查文/本 task 单。

## 非范围

- goal 注入 query 前缀 / status 流转 / 任何读写代码（P1 另卡）；goal 与 runs/threads 的 FK 关系；freeze 帧格式；supervisor 图（A2：diff 为零）。

## 失败路径

| 失败 | 语义 |
|------|------|
| 迁移 down | DROP TABLE IF EXISTS，幂等 |
| 代码回滚 | 表无任何读写方，回滚零影响 |

## 验收标准

- [ ] 迁移 up/down 本地真 PG 实证通过。
- [ ] 新 DB 用例本地真 PG 全绿（tenant_id NOT NULL 约束生效：NULL 插入 IntegrityError）。
- [ ] 干净 worktree（无 .env）全量 pytest 零新红（既有 ta2 红除外，baseline 同源已登记）；ruff 绿；graph-compile 过；lint-imports 绿；spec-wave task lint PASS。
- [ ] registry entry 登记（base=fee74fa · banned_prefixes 空——含 alembic/ 迁移文件）。

## 给执行帽的必读列表

- `docs/tasks/done/task_p0prime_t4_run_entity.md`（承继体例 + .importlinter/now_utc 教训）
- `app/db/models.py`（OpsLgRagRun :346 / OpsCapabilityNote tenant 先例）
- `alembic/versions/20261114_lg_rag_runs.py`（迁移体例 + down_revision 链）
- workspace `docs/01-scope/03-general-agent/06-kickoff-readiness.md`（任务卡 T5 :40 · 裁定 A2 :11）

## 思考轮控制

| 轮 | 结论 | early_stop |
|----|------|-----------|
| R0 | A2=仅落表零功能；先例锚点 notes/runs | 否 |
| R1 | 三闸 approved；设计裁定 3 条钉死 | 否 |
| R2 | 模型 → 迁移 → 测试 三竖切 | 否 |
| R3 | 迁移 down 幂等；零读写方回滚零影响 | 否 |
| R4 | 约束真值 DB 用例真 PG；迁移 up/down scratch 实证 | 否 |
| R5 | 验收 4 条过 → 交付 | 否 |

### R0 · 问题框定

goal 无落点；A2 裁定新建 `ops_goals` 仅 DDL，注入/流转属 P1。

### R1 · 开工闸

三闸 approved（见人工闸表）；R1 审查文 `docs/harness/reviews/task_p0prime_t5_goals_ddl_audit_R1_20261114.md`。

### R2 · 竖切

models.py `OpsGoal` → alembic `20261114_ops_goals` → `tests/test_ops_goals_ddl.py`。

### R3 · 失败语义

见失败路径表；迁移 down=DROP TABLE IF EXISTS 幂等；表零读写方，回滚零影响。

### R4 · 可测性

约束真值 DB 用例本地真 PG 实证（承 T4 brew postgresql@18）；ORM None quirk 用裸 SQL 触达 DB 级 NOT NULL。

### R5 · 交付判定

验收 4 条全过 + PR CI 绿 + CLOSE 波次。

### 自检结论

范围=仅 DDL 零功能（A2 钉死）：模型+迁移+约束测试+图谱登记，零读写代码、零路由、零 SSE 变更；不触碰 freeze/图/运行时；迁移 down 幂等独立可回退。验收 4 条全过（见 invoke_50_close 验证台账）。

## 实现备忘（30 回填 · 2026-11-14）

- models.py：`OpsGoal` 插于 `OpsSessionSummary` 前；goal_id client-side default `lambda: str(uuid4())`（承 turns/capability_notes 先例，server 侧无 default）。
- 迁移 `20261114_ops_goals`：goal_id `uuid PRIMARY KEY`（无 server default，承 `20261105_capability_notes:29` 先例——非 gen_random_uuid）；索引 `(tenant_id,status)`/`(thread_id)`。
- 测试 3 件真 PG 全绿；迁移 scratch 库 up/down/up 实证（`DATABASE_URL` env 覆盖）。
- 01_modules.md：db 行登记 ops_goals + **修复 T4 遗留文本错位**（capability_notes 收尾被挤到 runs 条目后）。
- 全量（干净 worktree ddfd1074）：2088 passed / 2 skipped / 1 failed（唯一红=既有 ta2，baseline 同源已登记）。

### 经验总结

1. **alembic env.py 读 `settings.database_url`（pydantic env 映射）——覆盖须用 `DATABASE_URL`，`ALEMBIC_DATABASE_URL` 无效**。误用会把迁移打到 .env 指向的 dev 库（本次实证首跑即踩：dev 库 opsdesk 被 upgrade/downgrade/upgrade 到 head——终态正确但方法错误，scratch 实证须 `DATABASE_URL=...` 前缀）。
2. **ORM 显式 None 赋有 client-side default 的列 → default 生效而非 NULL**（DID NOT RAISE IntegrityError）——DB 级 NOT NULL 约束验证须裸 SQL 触达。
3. 迁移 server default（timestamptz now()）与 create_all 表（timestamp naive）存在无害分歧——测试库走 create_all，真值以迁移为准。

## 测试策略

- `tests/test_ops_goals_ddl.py`：默认值/约束真值（DB 真跑，_DB_REQUIRED skip 体例承 T4）。
- 迁移：scratch 库 upgrade/downgrade/upgrade 实证（扩展预建体例承 T4）。

## 修订记录

| 日期 | 修订 |
|------|------|
| 2026-11-14 | 初版（00 起草 · 10 过闸） |
