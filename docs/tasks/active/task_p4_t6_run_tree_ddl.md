---
title: task · P4-T6 · Run 树 DDL + 委派 claim + REST 投影
---

# task · P4-T6 · Run 树 DDL + 委派 claim + REST 投影

> **状态**：`active`（2026-11-18 落卡 · 夜间自动执行波）
> **来源**：workspace 18-p4-generalization-design.md §3/§7/§8.2 + 19-p4-contracts.md §7/§11（commit e453a36）· 授权 issue Cyning12/ops-desk-workspace#23（m03796 夜间预授权 · 委派书 p4-t6-run-tree-ddl）

## Harness 元信息

| 键 | 值 |
|----|----|
| **task_slug** | p4-t6-run-tree-ddl |
| base | cfe76b23 |
| 关联 issue | issue Cyning12/ops-desk-workspace#23（授权真源）· workspace 18 文 §3/§7/§8.2 + 19 文 §7/§11（需求真源） |
| 关联 PR | feat 本 PR · close chore PR（收口登记） |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 本仓未启用 WikiTrack；本波为 runs 表 DDL + run_store claim + REST 投影 + 图谱登记 |
| graph_change_layer | G-L1（01_modules.md lg_rag 行 p4-t6 备注 + HG-GRAPH-MODULES 签收行） |
| review_hat | 20（R1 审查文已落盘 · GO） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | approved | 30 | approved 2026-11-18 · 授权 issue Cyning12/ops-desk-workspace#23 m03796（夜间预授权）+ 委派书 p4-t6-run-tree-ddl 为唯一范围真源 |
| HG-AUDIT-R1 | approved | 30 | approved 2026-11-18 · 同上授权 + R1 审查文 docs/harness/reviews/task_p4_t6_run_tree_ddl_audit_R1_20261118.md（GO） |
| HG-GRAPH-MODULES | approved | 30 | approved 2026-11-18 · 同上授权（lg_rag 行 p4-t6 备注属图谱登记义务 · 随 30 交付回填） |

## 背景

P4 泛化设计（18 文 §3）要把 supervisor 的 tool 子任务委派提升为独立子 run（闸开时），其数据面前提（19 文 §7）是 runs 表加 Run 树三列 + 委派 claim 部分唯一索引（「建行即认领」）。本波 T6 只交付数据面与 REST 投影加性面：

- 19 §7.1 三列：`parent_run_id` String(64) null（不加 FK · 承 run_events 顺序容错先例 models.py:285-288 注释）· `subtask_id` String(64) null（父图内子任务 id · claim 业务键一半）· `depth` Integer NOT NULL DEFAULT 0（0=根 1=子 · 深度硬上限 1）。
- 19 §7.2 迁移（可逆）：三列 + `uq_ops_lg_rag_runs_parent_subtask` 部分唯一索引（`(parent_run_id, subtask_id) WHERE parent_run_id IS NOT NULL`）+ `idx_ops_lg_rag_runs_parent` 反查索引；`create_run` 扩三个可选 kw（缺省调用零 diff）。
- 19 §7.3/§7.4 claim 语义：INSERT ... ON CONFLICT DO NOTHING（PG 同事务撞 uq abort 教训 → 新写 ON CONFLICT 路径 · create_run check-then-insert 不复用）→ 撞 uq SELECT 取回已有 child run_id 复用零重复建行（防 replan/resume/checkpoint 重放重复建行）；并发双 INSERT 正确（败者阻塞至胜者提交后 SELECT 取回 · R9/N6）；claim 校验父 run depth=0 否则拒建 + logger.exception（防御性断言 · 结构性无环不靠运行时检测）；子 run 继承父 tenant_id/user_id/thread_id（从父行取值不从请求上下文取 · 18 §8.2 · 承 14 §1.8 纪律）。
- 19 §11.4 REST 投影加性：GET /api/ops/lg-rag/threads/{thread_id}/runs 列表项新增 `parent_run_id`（string·null）与 `depth`（int 0/1）——加性变更豁免「off 态零 diff」（19 §11.5：零 diff 仅指 SSE 帧面+行为面 · 消费方须容忍未知键）；不开 children 端点。

## 范围

1. **迁移** `alembic/versions/20261118_lg_rag_run_tree.py`（down_revision=20261116_ops_fires_created_at · 原生 op.execute SQL 承 20261114_lg_rag_runs.py 风格 · IF NOT EXISTS/IF EXISTS 幂等 · 可逆 downgrade 全量回退三列两索引）：
   - `ALTER TABLE ops_lg_rag_runs ADD COLUMN parent_run_id VARCHAR(64) NULL, ADD COLUMN subtask_id VARCHAR(64) NULL, ADD COLUMN depth INTEGER NOT NULL DEFAULT 0`（19 §7.2 SQL 逐字）；
   - `CREATE UNIQUE INDEX IF NOT EXISTS uq_ops_lg_rag_runs_parent_subtask ON ops_lg_rag_runs (parent_run_id, subtask_id) WHERE parent_run_id IS NOT NULL`；
   - `CREATE INDEX IF NOT EXISTS idx_ops_lg_rag_runs_parent ON ops_lg_rag_runs (parent_run_id)`。
2. **models.py 同步**：`OpsLgRagRun` 增三列 mapped_column + `__table_args__` 对齐两索引（`Index(..., unique=True, postgresql_where=text("parent_run_id IS NOT NULL"))` 承 uq_ops_goals_active_thread 先例 models.py:328-334）防 autogenerate 漂移；**不加 FK、不加 DB CHECK**（19 §7.2 SQL 无 · 深度约束由 claim 层断言承载 · 见偏差登记）。
3. **create_run 扩参**：`run_store.py::create_run` 扩 `parent_run_id`/`subtask_id`/`depth` 三个可选 kw（缺省 None/None/0 · 既有调用面零 diff）。
4. **claim 函数**：`run_store.py` 新增 `claim_child_run`（19 §7.3/§7.4 语义）：
   - 先取父行（tenant_id/user_id/thread_id/depth）；父不存在 → 拒建 + logger.exception；父 depth != 0 → 拒建 + logger.exception（防御性断言）；
   - INSERT ... ON CONFLICT (parent_run_id, subtask_id) WHERE parent_run_id IS NOT NULL DO NOTHING（§7.4 SQL 逐字 · status='running' · depth=1 · 归属从父行取值）；
   - 未插入（已委派过）→ SELECT run_id 取回已有 child 复用；返回 (child_run_id, created) 二元组。
5. **REST 投影加性**：`run_store.py::list_thread_runs_page` 与 `runs_router.py::_load_runs_page` 列表项增 `parent_run_id`/`depth` 两字段（既有字段零改 · 不开新端点 · cursor/分页面零 diff）。
6. **测试**（真 PG postgresql+asyncpg://ops:ops_password@localhost:5432/opsdesk_test · 五键 blank 前缀 OPS_HITL_PERSISTENCE= OPS_CAPABILITY_ALLOW_WRITE= OPS_CAPABILITY_ALLOW_WRITE_TAGS= OPS_CAPABILITY_PERSISTENCE= OPS_CAPABILITY_EXTRA_MANIFESTS=）：
   - 迁移 upgrade/downgrade scratch 库实证（承 tests/test_import_from_supabase.py:158-188 asyncpg ADMIN_DSN 先例 · 子进程传 DATABASE_URL）；
   - 两索引存在性（pg_indexes 承 test_ops_schedule_ddl.py 体例）；
   - uq claim：裸 SQL 二次 INSERT 撞 uq → IntegrityError · claim 两次同键 → 取回同一 child run_id 零重复建行（行数=1）· asyncio.gather 并发 claim 仅一胜（承 test_db_concurrent_claims_only_one_wins 体例 tests/test_capability_persistence_db.py:139）；
   - depth 断言：以 depth=1 的 run 为父 claim → 拒建 + logger.exception 记录；
   - 归属继承：claim 建行 tenant_id/user_id/thread_id 全从父行取值；
   - 投影契约：列表项含 parent_run_id/depth · 普通 run 默认 null/0 · 子 run 取回父 id/1；
   - 既有 runs 端点回归（tests/test_lg_rag_runs_readonly_api.py）零红 · run_store 回归（tests/test_lg_rag_run_store.py）零红 · 全量 pytest 绿（环境性红与 base cfe76b23 同路径基线逐签对照 · CI 终裁）· `ruff check app tests` 绿。
7. **图谱**：`docs/_tech_graph/l1/01_modules.md` lg_rag 行（:35）补 p4-t6 备注（runs 表三列 + 两索引 + claim 函数 + 投影加性）+ HG-GRAPH-MODULES 签收行（承 :41-:47 先例 · 无独立 db 行 · 见偏差登记）。
8. **落盘**：registry entry（status=active → close 波 closed 钉 wave_tip · banned_prefixes=[scripts/] 因本波须触 alembic/）· invokes by-task/p4-t6-run-tree-ddl/{10,30,40,50} · R1 审查文 · task 档 active→done。

## 非范围

- 不做委派执行提升（T7）：闸 `OPS_RUN_TREE_ENABLED` 三件套 · route_next_subtask 提升分支 · start_delegate_run_worker · join 轮询 · orphan 补偿扩面，全部归 T7。
- 不做 web 面（T8）。
- 不动 SSE 帧面/行为面/cursor（19 §11.5 铁律 · 本波零新帧类型零帧变更）。
- 不开 children 端点 · 不做树形合并流/跨 run cursor（被否已钉 19 §7.3/§13）。
- 不做 root_run_id 冗余列 · 深度参数化 · 运行时环检测 · 新 delegations 台账表（19 §7.3 被否）。
- 不引新依赖 · 不碰 scripts/ · 不动 .importlinter（无新跨模块 import 边）。

## 失败路径

- PG 同事务撞 uq abort：复用 create_run check-then-insert 会撞 14 R10 教训——必须新写 ON CONFLICT DO NOTHING 路径（19 §7.3 钉明 · 由并发 claim 用例守）。
- 归属错取：claim 若从请求上下文取 tenant/user/thread 会破 assert_run_owned/run_owner 链（19 §8.2）——从父行取值 · 由归属继承用例守。
- depth 约束失守：无 DB CHECK（契约 SQL 无）· 深度硬上限靠 claim 层断言 + 子 run 跑非委派管线的结构性前提——由 depth 断言用例守 · 登记为偏差（契约逐字对齐）。
- 投影破零 diff 口径：19 §11.5 裁定 REST 加性字段豁免（消费方须容忍未知键）· SSE 帧面/行为面零 diff 由既有帧面回归守 · 本波不触帧面。
- autogenerate 漂移：models.py 未同步 __table_args__ 会导致下次 autogenerate 出假 diff——同步两索引定义（承 models.py:302-308 注释纪律）· 迁移本体手写原生 SQL 不依赖 autogenerate。
- 并行 agent 撞 registry.yaml / 01_modules.md 同区冲突 → rebase origin/master 保留双方 entry 手动解 · 冲突块如实登记。
- 脏树期 wave_gate_registry 红为结构性常态（closed entry banned 面咬在途 alembic 文件 · 提交后复绿 · CI 终裁 · 委派书钉明）。
- PR CONFLICTING → CI 不触发 → rebase origin/master 解冲突重推（委派书并行铁律）。

## 验收标准

- [x] 迁移 upgrade/downgrade scratch 库实证通过（三列两索引建立与回退）
- [x] uq claim：二次裸 INSERT IntegrityError · claim 重入取回同一 child run_id 零重复建行 · 并发 claim 仅一胜
- [x] depth 断言：depth=1 为父 claim 拒建 + logger.exception
- [x] 归属继承：claim 建行 tenant_id/user_id/thread_id 从父行取值
- [x] 投影契约：runs 列表项含 parent_run_id/depth · 默认 null/0 · 子 run 父 id/1
- [x] 既有 runs 端点/run_store 回归零红 · 全量 pytest 绿（CI 终裁）· ruff 绿
- [x] models.py __table_args__ 同步两索引（autogenerate 漂移防线）
- [x] 01_modules.md lg_rag 行 p4-t6 备注 + HG-GRAPH-MODULES 签收行
- [x] 过闸四件：task lint PASS · registry entry · invokes {10,30,40,50} · R1 审查文 GO

### 自检结论

- 迁移：scratch 库（opsdesk_p4t6_<rand> · 重演 20261114 七列形态 → stamp → upgrade head → downgrade）实证三列两索引建立/回退通过；models 元数据对齐断言通过。
- claim：重入取回同一 child run_id 零重复建行；asyncio.gather 六并发仅一胜（sum(created)==1 · 同 run_id · 行数=1）；父 depth=1 拒建 + logger.exception（caplog 实证）；父缺失拒建。
- 投影：根 run null/0 · 子 run 父 id/1 契约断言通过；readonly 既有键集断言已补两加性字段 + 默认值断言。
- 回归：目标四档 24 passed（真 PG 五键 blank）；ruff All checks passed；全量脏树期 28 红逐签对照干净基线核定为非本波因果（4 环境性基线同红 · 21 并发 flaky 重跑全绿 · 3 结构性脏树期提交后复绿 CI 终裁）。
- 图谱：01_modules.md lg_rag 行 P4-T6 备注 + HG-GRAPH-MODULES 签收行（:48）· graph-compile.sh 绿。
- 过闸件：R1 审查文 GO/PASS · invoke_10/30 已落 · task lint 见 invoke_40 · registry entry active（CLOSE 后钉 wave_tip）。

## 必读列表

- workspace docs/01-scope/03-general-agent/18-p4-generalization-design.md §3/§7/§8.2（设计真源 · commit e453a36）
- workspace docs/01-scope/03-general-agent/19-p4-contracts.md §7/§11（契约真源 · 同上 commit）
- app/db/models.py:281-334（OpsLgRagRun + uq_ops_goals_active_thread 部分唯一索引先例）· :750-785（OpsScheduleFire 范式）
- app/ops/lg_rag/run_store.py（create_run :52-75 · list_thread_runs_page :211-253）
- app/ops/lg_rag/runs_router.py（_load_runs_page :86-97 · runs 端点 :105-119）
- alembic/versions/20261114_lg_rag_runs.py（迁移风格先例）
- tests/test_ops_schedule_ddl.py · tests/test_capability_persistence_db.py:139 · tests/test_lg_rag_runs_readonly_api.py · tests/test_import_from_supabase.py:158-188（测试先例）
- docs/tasks/done/task_p2c_t1_planner_tool_awareness.md（过闸体例先例）

## 思考轮控制

| 轮 | 结论 | early_stop |
|----|------|-----------|
| R0 | 范围五面对账 18/19 文锚 · T7/T8 排除 | 否 |
| R1 | 失败路径八条 · 并发 claim 测试形态定稿 | 否 |
| R2 | 非范围边界钉死（env 三件套/帧面/被否项） | 否 |
| R3 | 关键决策六条（原生 SQL · ON CONFLICT 新写 · (run_id, created) 签名 · 无 DB CHECK · 无 db 行 · 加性豁免） | 否 |
| R4 | 体例对账 p2c-t1 · 仓规条款一遵守 | 否 |
| R5 | 验收 9 条锚定 · 回退面明确 | 否 |

**actual_last_round**：R5 · **early_stop**：no · **residual_risks**：claim 无运行时调用方（T7 承接 · 测试直达守语义）

## 思考轮（actual_last_round=R5）

### R0 · 范围对账

委派书五条与 18/19 文锚逐条对齐：DDL（19 §7.1/§7.2 SQL 逐字 · 无 FK 无 DB CHECK）· claim（19 §7.3/§7.4 · ON CONFLICT 新写路径 · 归属从父行 · depth 断言）· 投影（19 §11.4 加性两字段）· 测试（迁移 scratch · uq 三态 · depth 断言 · 投影契约 · 回归）· 图谱（lg_rag 行 + 签收行 · 无独立 db 行登记为偏差）。T7/T8 面全部排除。

### R1 · 失败路径推演

见「失败路径」节。增补：claim 并发败者阻塞至胜者提交后 SELECT 取回（19 §7.3 R9/N6 复核结论）——测试用 asyncio.gather 多连接并发同键不同 child_run_id，断言全返回同一 run_id 且行数=1。

### R2 · 非范围边界

OPS_RUN_TREE_ENABLED 三件套属 T7（本波 models/run_store/runs_router 均不引用该 env）· web T8 · children 端点/树形合并流被否 · 帧面/cursor 铁律不动。claim 函数本波交付即「建好待 T7 消费」· 无运行时调用方（T7 接入前零生产路径触达 · 测试直达）。

### R3 · 关键决策记录

- **迁移手写原生 SQL 不走 autogenerate**：承 20261114_lg_rag_runs.py 风格（op.execute + IF NOT EXISTS）· 可逆 downgrade 对称回退；models.py __table_args__ 同步仅为消 autogenerate 漂移（仓内注释纪律）。
- **claim 新写 ON CONFLICT 路径不复用 create_run**：14 R10 已记录 PG 同事务撞 uq abort 教训；create_run 保持 check-then-insert 现状零改（既有调用面零 diff）。
- **claim 返回 (run_id, created) 二元组**：created 供 T7 决定是否启动 delegate worker（撞 uq 取回=worker 可能已在飞）· 本波不消费但签名预留（避免 T7 改签名波及）。
- **深度约束无 DB CHECK**：19 §7.2 SQL 逐字无 CHECK · §7.3 钉 claim 层断言 + 「结构性无环不靠运行时检测」——DB 面加 CHECK 属契约外膨胀，登记偏差按契约逐字执行。
- **无独立 db 行**：01_modules.md 模块表无 db module_id（l0 db 节点为 external PostgreSQL 无表级清单）——runs 表归属 lg_rag 模块 · 承 p2c-t1/fix-434 先例登记于 lg_rag 行 + HG 签收行。
- **投影加性豁免**：19 §11.5 钉「off 态零 diff = SSE 帧面+行为面」· REST 新增字段为加性变更——不引 env 闸 · 字段无条件常加。

### R4 · 体例对账

照 task_p2c_t1_planner_tool_awareness.md：task 档结构/人工闸表/registry entry（base=cfe76b23 · allowed_app_files=[app/db/models.py, app/ops/lg_rag/run_store.py, app/ops/lg_rag/runs_router.py] · banned_prefixes=[scripts/] 因触 alembic/）/invokes by-task 四件 {10,30,40,50}/R1 审查文 GO 机读词/spec-wave@3.5.0 task lint PASS 为闸；图谱签收承 :41-:47 先例。仓规条款一遵守（走 20-R1 审查文非 --allow-no-review）。

### R5 · 收尾复核

验收 9 条逐条锚：迁移 scratch 可逆 · uq 三态（IntegrityError/取回/并发一胜）· depth 断言 · 归属继承 · 投影契约（默认 null/0 + 子 run 值）· 回归零红+全量+ruff · models 同步 · 图谱两件 · 过闸四件。回退 = revert 迁移/models/run_store/runs_router/测试 · downgrade 已实证可逆。

## 实现备忘

### 偏差登记

1. **无独立 db 行**：委派书图谱条写「db 行+lg_rag 行」· 实际 01_modules.md 模块表无 db module_id（l0 db 节点 external PostgreSQL 无表级清单）——按归属模块先例登记于 lg_rag 行 + HG-GRAPH-MODULES 签收行（承 p2c-t1/fix-434 先例）· 最小改动如实登记。
2. **无 DB 层 CHECK**：委派书范围条提「CHECK depth∈(0,1)」· 19 §7.2 SQL 逐字无 DB CHECK · §7.3 钉 claim 层断言承载深度硬上限——按契约逐字执行 · depth 断言用例守（契约优先于委派书转述 · 语义一致仅承载层不同）。
3. 其余无偏差：范围/非范围/铁律（帧面/cursor 不动）全部按 10 档执行。

### 限制登记

1. claim 函数本波无运行时调用方（T7 接入前零生产路径触达 · 测试直达 · 委派书范围钉明 T7 不做）。
2. 全量 pytest 环境性红若存在，与 base cfe76b23 同路径基线逐签对照登记 · CI 终裁。

## 测试策略

pytest tests（CI 终裁 · 真 PG postgresql+asyncpg://ops:ops_password@localhost:5432/opsdesk_test · 五键 blank 前缀 OPS_HITL_PERSISTENCE= OPS_CAPABILITY_ALLOW_WRITE= OPS_CAPABILITY_ALLOW_WRITE_TAGS= OPS_CAPABILITY_PERSISTENCE= OPS_CAPABILITY_EXTRA_MANIFESTS=）；新增 tests/test_lg_rag_run_tree_ddl.py（迁移 scratch + uq 三态 + depth 断言 + 归属继承）与 tests/test_lg_rag_run_tree_projection.py（投影契约）；目标回归 tests/test_lg_rag_runs_readonly_api.py / tests/test_lg_rag_run_store.py 全绿；全量回归环境性红与 base cfe76b23 同路径基线逐签对照；ruff check app tests 绿；allowed_app_files=[app/db/models.py, app/ops/lg_rag/run_store.py, app/ops/lg_rag/runs_router.py] 机判。

## 修订记录

| 日期 | 修订 |
|------|------|
| 2026-11-18 | 落卡（夜间自动执行波 · 授权 issue Cyning12/ops-desk-workspace#23 m03796 · 来源 workspace 18 文 §3/§7/§8.2 + 19 文 §7/§11） |