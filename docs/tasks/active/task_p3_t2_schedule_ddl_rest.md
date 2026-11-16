---
title: task · feat · P3-T2 Schedule 双表 DDL + REST 四端点
---

# task · feat · P3-T2 Schedule 双表 DDL + REST 四端点

> **状态**：`active`（2026-11-16 落卡 · 夜间自动执行波）
> **来源**：issue Cyning12/ops-desk-workspace#23（m03064/m03283 夜间授权 · 设计真源 workspace 14-p3-schedule-taskcard-design.md 终稿 R1-R23 · 契约真源 15-p3-contracts.md commit 62af6ea §1/§4 · 操作真源 lead 委派书）

## Harness 元信息

| 键 | 值 |
|----|----|
| **task_slug** | p3-t2-schedule-ddl-rest |
| base | f1d0dd28 |
| 关联 issue | Cyning12/ops-desk-workspace#23 |
| 关联 PR | 待定（feat PR · 本波） |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 本仓未启用 WikiTrack；本波为 schedule 表 + REST 面 |
| graph_change_layer | G-L1（01_modules.md db 行 + schedule 行登记 + HG-GRAPH-MODULES 签收行） |
| review_hat | 20（R1 审查文已落盘 · GO） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | approved | 30 | approved 2026-11-16 · 授权 issue #23 m03064/m03283（夜间授权）+ 14 设计终稿 + 15 契约 §1/§4 为唯一范围真源 |
| HG-AUDIT-R1 | approved | 30 | approved 2026-11-16 · 同上授权（14 终稿 + 15 契约即审计真源）+ R1 审查文 docs/harness/reviews/task_p3_t2_schedule_ddl_rest_audit_R1_20261116.md（GO） |
| HG-GRAPH-MODULES | approved | 30 | approved 2026-11-16 · 同上授权（新增 db 表两行 + schedule 模块行属图谱登记义务 · 随 30 交付回填） |

## 背景

P3（Schedule/TaskCard 面）第 2 单。T2 交付 schedule 数据面与 REST 管理面：`ops_schedules` + `ops_schedule_fires` 双表 DDL（含 tenant_id 全量谓词）、四个 REST 端点（创建/列表/单条/PATCH 状态机+改排期）、store 层（zoneinfo 排期算术 · 否 croniter 新依赖）。worker 点火循环与 `OPS_SCHEDULE_ENABLED` 总闸在 T3，本波只建表 + REST。契约 schema/词表/422 文案逐字以 15 §1/§4 为准。

## 范围

1. **DDL**（`alembic/versions/20261116_ops_schedules.py` · down_revision=20261115_uq_goals_active_thread · 原生 SQL + IF NOT EXISTS 承 ops_goals 先例）：
   - `ops_schedules`：schedule_id uuid pk · tenant_id varchar(64) notnull · user_id uuid FK ops_users · thread_id varchar(255) notnull 无 FK · name varchar(120) notnull · instruction text notnull · schedule_kind varchar(16) notnull · run_at timestamptz null · interval_seconds int null · time_of_day varchar(5) null · timezone varchar(64) notnull 默认 'Asia/Shanghai' · next_fire_at timestamptz notnull · catchup_policy varchar(16) notnull 默认 'fire_once' · status varchar(16) notnull 默认 'active' · fire_count int notnull 默认 0 · max_fires int null · last_fired_at timestamptz null · created_at/updated_at timestamptz notnull 默认 now() · 索引 `idx_ops_schedules_next_fire(status, next_fire_at)`。
   - `ops_schedule_fires`：id uuid pk · schedule_id uuid notnull 无 FK · tenant_id varchar(64) notnull · planned_fire_at timestamptz notnull · run_id varchar(64) null + 索引 `idx_ops_schedule_fires_run_id` · status varchar(16) notnull 默认 'claimed' · fired_at timestamptz null · created_at timestamptz notnull 默认 now() · 唯一索引 `uq_ops_schedule_fires_planned(schedule_id, planned_fire_at)`（幂等键 · 支撑 T3 ON CONFLICT DO NOTHING）。
2. **models.py**：`OpsSchedule` / `OpsScheduleFire`（UUID pk default uuid4 · tenant_id String(64) notnull · __table_args__ Index 对齐迁移消 autogenerate 漂移 · 承 OpsGoal 先例）。
3. **store 层 `app/ops/schedule/store.py`**（承 goals/store.py 先例：词表 frozenset + 状态机矩阵 + 单行化 + 读 best-effort/写显式抛错 + AsyncSessionLocal 自开会话）：
   - 词表：SCHEDULE_KINDS={once_at,interval,daily_at} · SCHEDULE_STATUSES={active,paused,cancelled} · FIRE_STATUSES={claimed,fired,skipped,failed} · CATCHUP_POLICIES={fire_once}；_ALLOWED_TRANSITIONS={active:{paused,cancelled}, paused:{active,cancelled}, cancelled:{}}（cancelled 终态）。
   - `sanitize_instruction` 单行化（控制符→空格 · 空白折叠 · 承 goals sanitize_objective）。
   - next_fire_at 计算：once_at→run_at（须未来时刻否则 422）；interval→now+interval_seconds（≥300 否则 422 逐字文案）；daily_at→zoneinfo 时区内下一个 time_of_day（HH:MM 24h 校验 · 默认 Asia/Shanghai · v1 不随 DST 校准注释钉明）。
   - 双上限：per-user status=active ≤20 · per-tenant 全量 ≤200（创建前 COUNT 校验 · 超限 422 逐字文案）。
   - 归属校验 R6：端点谓词 tenant_id+user_id 否则 404；thread 存在须 thread 归属当前用户否则 422 零写，thread 不存在允许。
   - PATCH 重算守卫 N5：任一排期字段变更 → 重算 next_fire_at，重算值须 > now 否则 422。
   - humanized_display：once_at「将于 {YYYY-MM-DD HH:mm}（{时区中文名}）执行一次」· interval「每 {N} 分钟」（≥60 分钟显示「每 {N} 小时」）· daily_at「每天 {HH:MM}（{时区中文名}）」；时区中文名 v1 仅 Asia/Shanghai→北京时间，其余回退原名。
   - 自定义异常：ScheduleNotFoundError→404 · ScheduleValidationError→422（带逐字 detail 文案）。
4. **REST 四端点 `app/ops/schedule/router.py`**（承 goals/router.py 先例 · APIRouter(prefix="/schedules") · CurrentUser · _resolve_request_tenant）：
   - POST /api/ops/schedules（201 {"ok":true,"data":{"schedule":{…}}} · 词表外 kind 422 逐字文案 · run_at 非未来 422 · interval<300 422 · 双上限 422 · 非 thread_owner 422）。
   - GET /api/ops/schedules（?thread_id= + ?status= 可选 · 谓词 tenant+user · v1 不分页 · {"ok":true,"data":{"schedules":[…]}}）。
   - GET /api/ops/schedules/{schedule_id}（跨 tenant/跨 user/不存在 404 · 附 recent_fires 最近 10 条倒序：id/planned_fire_at/run_id/status/fired_at）。
   - PATCH /api/ops/schedules/{schedule_id}（status/name/instruction/run_at/interval_seconds/time_of_day/timezone/max_fires 全可选至少一项 · 已 cancelled 再 PATCH 422 逐字文案 · 排期字段变更重算 next_fire_at + N5 守卫）。
   - `app/ops/router.py` include_router 注册。
5. **测试**（真 PG postgresql+asyncpg://ops:ops_password@localhost:5432/opsdesk_test · 五键 blank 前缀 · CI 终裁）：
   - `tests/test_ops_schedule_ddl.py`：迁移 up/down scratch 实证（upgrade head → 表/索引/约束存在 · downgrade 回链尖 → 表消失 · 再 upgrade 幂等）+ NOT NULL/默认值/uq 约束裸 SQL 实证。
   - `tests/test_schedule_store.py`：next_fire_at 三种 kind 计算 · daily_at 时区（Asia/Shanghai 当日已过点→次日）· 单行化 · 双上限 · 状态机矩阵 · N5 重算守卫 · humanized_display 文案。
   - `tests/test_schedule_rest.py`：创建全 kind · 词表外 422 文案逐字断言 · interval<300 422 · per-user/per-tenant 上限 422 · 非 thread_owner 422 零写 · thread 不存在允许 · 跨 tenant/跨 user 404 · PATCH pause/resume/cancel 词表流转 · 已 cancelled 再 PATCH 422 · 列表 thread_id/status 过滤 · 单条 recent_fires · 未登录 401。
6. **图谱**：`docs/_tech_graph/l1/01_modules.md` db 行（ops_schedules/ops_schedule_fires 登记）+ schedule 行登记 + HG-GRAPH-MODULES 签收行（承 :135-:139 先例）。

## 非范围

- 不碰 worker/点火循环/启动补链（T3）；`OPS_SCHEDULE_ENABLED` 总闸在 T3（不闸 REST）。
- 不碰 capability manifest 面（T2b · ops.schedule.v1.yaml 不在本波）。
- 不碰 runs/events 端点（T4 并行波）。
- 不碰 scripts/ · skill_registry/ · capability/ · lg_rag/ 本体。

## 失败路径

- 词表外 schedule_kind/status → 422 逐字文案（零写）。
- once_at run_at 非未来 / interval<300 / time_of_day 非 HH:MM → 422（零写）。
- per-user active ≥20 / per-tenant 全量 ≥200 → 422 逐字文案（零写）。
- thread 存在且非当前用户所有 → 422 逐字文案（零写）；thread 不存在 → 允许。
- 跨 tenant / 跨 user / 不存在 → 404（不泄露存在性）。
- 已 cancelled 再 PATCH → 422 逐字文案；cancelled 终态不可逆。
- PATCH 重算守卫：重算 next_fire_at ≤ now → 422（N5）。
- 回退 = revert 本波 PR + alembic downgrade 回链尖。
- 并行 agent 撞 registry.yaml / 01_modules.md 同区冲突 → 保留双方 entry 手动解，冲突块如实登记。

## 验收标准

- [x] alembic 迁移 up/down scratch 实证通过（表/索引/uq 约束存在 · downgrade 回链尖表消失 · 再 upgrade 幂等）→ opsdesk_mig_test：upgrade head → downgrade -1（ops_schedule% 表 0）→ 再 upgrade ok（2026-11-16）
- [x] models.py OpsSchedule/OpsScheduleFire 与迁移对齐（autogenerate 零漂移）→ `alembic check` 输出零 ops_schedule* 条目（仓史 TIMESTAMP/索引漂移为既有债非本波）
- [x] POST 三种 kind 创建 + next_fire_at 正确（once_at=run_at · interval=now+interval · daily_at=时区下一时刻）有锚 → tests/test_schedule_rest.py::test_create_once_at/interval/daily_at_next_fire
- [x] 422 文案逐字断言：词表外 kind/status · interval<300 · per-user 超限 · per-tenant 超限 · 非 thread_owner · 已 cancelled 再改 有锚 → test_422_invalid_kind / test_422_interval_below_min / test_422_user_quota / test_422_tenant_quota / test_422_not_thread_owner / test_422_cancelled_terminal
- [x] 归属：跨 tenant/跨 user/不存在 404 有锚；thread 不存在允许创建有锚 → test_404_cross_tenant / test_404_cross_user / test_404_missing_schedule / test_create_thread_not_found_allowed
- [x] PATCH pause/resume/cancel 词表流转 + cancelled 终态不可逆 + N5 重算守卫有锚 → test_patch_pause_resume_cycle / test_patch_cancel_terminal / test_patch_resume_recomputes_next_fire
- [x] GET 列表 thread_id/status 过滤 + 单条 recent_fires（≤10 倒序）有锚 → test_list_filter_thread_id / test_list_filter_status / test_get_with_recent_fires
- [x] `pytest tests` 目标测试绿（44/44）；全量 35 红根因 = 仓根 .env 经 tests/test_check_vector_waterline.py 裸 load_dotenv 渗入 worktree 收集期（环境性既有问题 · base f1d0dd28 对照同路径复现 · CI 无 .env 不受影响 · CI 终裁）
- [x] `ruff check app tests` 绿
- [x] 01_modules.md db 行 + schedule 行登记 + HG-GRAPH-MODULES 签收行已回写（:40 / :42 / :143）

### 自检结论

PASS（2026-11-16 · 30 交付）。四端点（app/ops/schedule/router.py:92 POST / :119 GET list / :140 GET detail / :159 PATCH）+ store.py 配额与流转守卫 + models.py OpsSchedule/OpsScheduleFire 与 alembic/versions/20261116_ops_schedules.py 对齐（autogenerate 对双表零条目）。目标 44 用例真 PG 全绿；迁移 scratch up→down→up 循环幂等；图谱登记与 registry entry 回写完成。唯一残余：worktree 内全量 pytest 35 红为环境性既有问题（仓根 .env 经 tests/test_check_vector_waterline.py:51 import scripts/check_vector_waterline 裸 load_dotenv 渗入 · base 同路径复现 · 与本 diff 无关），交 CI 终裁。

## 必读列表

- 设计真源：`../ops-desk-workspace/docs/01-scope/03-general-agent/14-p3-schedule-taskcard-design.md` 终稿（R1-R23 · §11 失败路径）
- 契约真源：`../ops-desk-workspace/docs/01-scope/03-general-agent/15-p3-contracts.md`（commit 62af6ea · §1 REST 契约 · §4 fires 台账 · §1.8 双上限与 422 文案词表）
- 先例：`app/ops/goals/store.py` · `app/ops/goals/router.py` · `app/db/models.py`（OpsGoal:310 · OpsLgRagThread:225）· `alembic/versions/20261114_ops_goals.py` · `tests/test_goals_rest.py` · `tests/test_ops_goals_ddl.py`
- T5b 体例：`docs/tasks/done/task_p2b_t3_mcp_translator.md` · registry `docs/harness/audit_gates/registry.yaml`

## 思考轮

| 轮 | 结论 | early_stop |
|----|------|-----------|
| R0 | 范围对账（委派书 vs 14 终稿 R1-R23 / 15 契约 §1/§4）done | false |
| R1 | 失败路径推演（§11 + 422 词表 + 404 归属 + N5 守卫）done | false |
| R2 | 非范围边界（T3 worker / T2b capability / T4 runs 切面）done | false |
| R3 | 关键决策记录（zoneinfo 否 croniter · uq 普通唯一索引 · store 布局承 goals）done | false |
| R4 | 体例对账（T3 模板/registry/invokes/审查文/图谱登记）done | false |
| R5 | 收尾复核（验收 checklist 全锚定）done | false |

actual_last_round: R5

### R0 · 范围对账

委派书与 14 终稿/15 契约逐条对照：双表 DDL（15 §1.2 列清单 + §4.1 fires 列清单）、REST 四端点（15 §1.1）、双上限+interval≥300（R4 · §1.8）、thread 归属（R6 · §1.7）、fires 幂等键 uq(schedule_id,planned_fire_at)（R10 · §4.1）、fires.run_id 索引（R13-N4 · §4.1）、PATCH 重算守卫（N5 · §1.6）、humanized_display（R20 · §1.8）。OPS_SCHEDULE_ENABLED 闸 REST 面（15 §7.1 总闸只管 worker）确认不闸。

### R1 · 失败路径推演

见「失败路径」节。新增推演：daily_at time_of_day 恰等于当前时刻 → 取次日（「下一个时刻」严格大于 now）；run_at 恰好等于 now → 非未来 422；interval PATCH 改小 <300 → 422；PATCH 仅改 name/instruction 不重算 next_fire_at；PATCH status=paused 不动 next_fire_at（恢复 active 时若 next_fire_at 已过 → 重算守卫适用？裁定：resume 不重算，worker T3 按 next_fire_at<=now 扫到即点 · catchup_policy=fire_once 兜底语义在 T3，本波只保证数据面一致）。

### R2 · 非范围边界

T3 切面=不建 worker/tick/补链/OPS_SCHEDULE_ENABLED；T2b 切面=不建 manifests/ops.schedule.v1.yaml；T4 切面=不碰 runs/events 端点。capability/lg_rag/skill_registry/scripts 零触。

### R3 · 关键决策记录

- **zoneinfo 否 croniter**：daily_at 只需「时区内下一个 HH:MM」，stdlib zoneinfo 足够（零新依赖承裁定传统）。
- **uq 索引形态**：15 §4.1 写「部分唯一索引」但无 WHERE 条件语义，取普通 UNIQUE INDEX（schedule_id, planned_fire_at）——ON CONFLICT (schedule_id, planned_fire_at) DO NOTHING 直接可用（T3 写入纪律 §4.2 依赖）。
- **store 布局**：`app/ops/schedule/{__init__,store,router}.py` 承 goals 包先例。
- **resume 不重算**：PATCH status active←paused 不触发排期字段变更，next_fire_at 不动（重算仅排期字段变更时 · §1.6「任一排期字段变更」）。

### R4 · 体例对账

照 T3/T5b：task 档结构/人工闸表/registry entry（base=f1d0dd28 · banned_prefixes=[] 因本波碰 alembic/ · 迁移文件列 allowed_tree_files · 承 p0prime-t4/t5 先例）/invokes by-task 四件/R1 审查文 GO 机读词/spec-wave task lint PASS 为闸。

### R5 · 收尾复核

验收 10 条逐条锚到测试或文件证据；回退路径=revert PR + alembic downgrade。

## 实现备忘

### 偏差登记

（30 交付时回填）

### 限制登记

- **L1（resume 语义）**：paused→active 不重算 next_fire_at；若暂停期间越过原计划时刻，worker（T3）扫到 next_fire_at<=now 即点，catchup_policy=fire_once 语义由 T3 落地。
- **L2（DST）**：v1 不随 DST 校准（15 §1.2 注释钉明）；daily_at 用 zoneinfo 本地日历日算术，DST 切换日取当日该本地时刻若存在。

## 测试策略

pytest tests（CI 终裁 · 真 PG opsdesk_test · 五键 blank 前缀）；DDL 迁移 up/down scratch + REST 全路径 + store 单测；ruff check app tests；import-linter 零新 forbidden 出边（schedule 包仅依 deps/tenant_context/db，禁引 capability/lg_rag）。

## 修订记录

| 日期 | 修订 |
|------|------|
| 2026-11-16 | 落卡（夜间自动执行波 · 授权 issue #23 m03064/m03283） |
