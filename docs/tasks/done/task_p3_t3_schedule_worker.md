---
title: task · feat · P3-T3 Schedule worker 点火执行器
---

# task · feat · P3-T3 Schedule worker 点火执行器

> **状态**：`active`（2026-11-16 落卡 · 夜间自动执行波）
> **来源**：issue Cyning12/ops-desk-workspace#23（m03064/m03283 夜间授权 · 设计真源 workspace 14-p3-schedule-taskcard-design.md 终稿 R1-R23 §1.1-§1.8 · 契约真源 15-p3-contracts.md commit 62af6ea §4/§7 · 操作真源 lead 委派书）

## Harness 元信息

| 键 | 值 |
|----|----|
| **task_slug** | p3-t3-schedule-worker |
| base | 17337d35 |
| 关联 issue | Cyning12/ops-desk-workspace#23 |
| 关联 PR | 待定（feat PR · 本波） |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 本仓未启用 WikiTrack；本波为 schedule worker 执行面 |
| graph_change_layer | G-L1（01_modules.md schedule 行 deps/备注 + db 行 created_at 列登记 + HG-GRAPH-MODULES 签收行） |
| review_hat | 20（R1 审查文已落盘 · GO） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | approved | 30 | approved 2026-11-16 · 授权 issue #23 m03064/m03283（夜间授权）+ 14 设计终稿 + 15 契约 §4/§7 为唯一范围真源 |
| HG-AUDIT-R1 | approved | 30 | approved 2026-11-16 · 同上授权 + R1 审查文 docs/harness/reviews/task_p3_t3_schedule_worker_audit_R1_20261116.md（GO） |
| HG-GRAPH-MODULES | approved | 30 | approved 2026-11-16 · 同上授权（schedule 行 deps 增 lg_rag + db 行加列登记属图谱登记义务 · 随 30 交付回填） |

## 背景

P3（Schedule/TaskCard 面）第 3 单。T2 已交付 schedule 数据面与 REST 管理面（ops_schedules + ops_schedule_fires 双表 + 四端点 + store）。本波交付触发执行器：lifespan 周期任务按 next_fire_at 到期点火，DB 抢占保证多实例互斥，fires 台账状态机留痕，触发走 lg_rag 内部通路（不经 HTTP），预算归因到 schedule 创建者。总闸 OPS_SCHEDULE_ENABLED 默认 off（契约 15 §7.1 总闸只管 worker 不闸 REST）。

## 范围

1. **worker 本体 `app/ops/schedule/worker.py`**（承 app/ops/hitl/auto_resume.py:273-309 五件套先例）：
   - 双闸 env：`OPS_SCHEDULE_ENABLED` ∈ {off(默认),on}，strip().lower()，非法回退 off + logger.warning（承 auto_resume_mode 先例 · 15 §7.1/R8）；`OPS_SCHEDULE_TICK_SECONDS` 默认 30，非法/越界 [1,3600] 回退 30（承 scan_interval_seconds 先例）。
   - start_schedule_worker()/stop_schedule_worker()：模块级句柄幂等复用 + asyncio.create_task + shutdown cancel + contextlib.suppress(CancelledError) await；loop 内 CancelledError raise · Exception logger.exception 下周期重试（14 §11：tick 内 DB 异常不炸 lifespan）。
   - main.py lifespan 挂接：on 才创建 worker task，finally 对称 stop（承 main.py:84-110 auto_resume 挂接先例 · import 期零副作用）。
2. **DB 抢占 `claim_due_schedules`**（batch=50 · SKIP LOCKED 先例锚 app/ops/hitl/store.py:261-277）：
   - SELECT status='active' AND next_fire_at<=now AND NOT EXISTS(fires 行 planned=next_fire_at) ORDER BY next_fire_at LIMIT 50 FOR UPDATE SKIP LOCKED；
   - 同事务逐行 db.begin_nested() 嵌套事务 INSERT fires(status='claimed')（撞 uq_ops_schedule_fires_planned 回滚 SAVEPOINT 跳过 —— PG 同事务撞 uq 会 abort 整事务，禁吞 IntegrityError 于外层）；
   - 命中即推进：非 once_at 重算 next_fire_at=compute_next_fire_at(...)（复用 store）；fire_count+1 · last_fired_at=now；once_at 不推进（无下一时刻 · 幂等键+NOT EXISTS 防重火）；
   - max_fires 达限（once_at 等价 max_fires=1 · 15 §1.2）：插入 fire 立即置 skipped，不增 fire_count，interval/daily 仍推进 next_fire_at（提高 max_fires 即自然恢复）。
3. **fires 状态机执行 `_execute_fire`**（契约 §4.1 claimed→fired/failed/skipped）：
   - 归属复核 R6：thread 存在且 user_id≠schedule.user_id → fires failed + 台账留痕不投递；悬空 user R11：OpsUser 不存在 → fires failed + schedule 自动 paused；
   - schedule 缺失/非 active（claim 后被 pause/cancel）→ fires skipped；
   - 触发语义 §1.3/§4.4：query = `[定时任务 · {name}] {instruction}`（前缀仅展示非归因/鉴权依据 · R12/SP2 · 唯一归因真源=fires 三元组 schedule_id/fire_id/run_id）；内部通路 run_store.create_run + run_worker.start_run_worker 函数直调（不经 HTTP · 承 router.py:454-487 不 await 先例 · R-P3-1）；预算归因 R4：显式传 creator 身份（user_id/tenant_id 取自 schedule 行）；
   - create_run 返 False/抛错 → raise → fires failed（失败回滚不留半成品 · run_id 不落库）· logger.exception（不静默）；成功 → UPDATE fires SET run_id,status='fired',fired_at=now() 才算 fired；审计日志 logger.info 三元组（source/schedule_id/fire_id/run_id）。
4. **补跑 + 启动补链**：
   - fire_once 补跑（§1.5）：每 tick（含启动首轮立即执行）对 next_fire_at<now 的 active 行各补一次并推进严格未来；停机跨 N 个 interval 只补一次（幂等键 (schedule_id,planned_fire_at)）；
   - 启动补链 R10（§1.5/§4.3「补链只信台账」）：lifespan 启动首轮对 status='claimed' AND run_id IS NULL 且 created_at 超时（CLAIM_STALE_SECONDS=120 · 偏差 D2）的 fires 行按台账重放触发（source="relink" · 承 run_worker.py:198 scan_orphan 思路）；fresh claimed 不动（防与在途触发双火）。
5. **fires.created_at 列**（偏差 D5 · R10 超时判据载体）：models.py OpsScheduleFire 加列 + 迁移 alembic/versions/20261116_ops_fires_created_at.py（down_revision=20261116_ops_schedules · ADD COLUMN IF NOT EXISTS timestamptz NOT NULL DEFAULT now() · scratch 真 PG upgrade head 实证）；planned_fire_at 会把 fire_once 补跑误判超时 → 双火窗口，必须 created_at。
6. **测试 `tests/test_schedule_worker.py`**（31 用例 · 真 PG opsdesk_test · autouse 清场 fixture 插真行+删行纪律 · CI 终裁）：双闸 env 参数化 · 抢占互斥（asyncio.gather 双扫合计 1）· 幂等键撞行 · once_at 只火一次 · max_fires 达限 skipped · 归因（spy start_run_worker kwargs + ops_lg_rag_runs.user_id==creator）· 归属复核 R6 · 悬空 user R11 · create_run 失败 failed 不留半成品 · 补跑单火+推进严格未来 · 补链 stale/fresh/paused 三路 · lifespan off 零创建+REST 不闸 · 五件套幂等+异常下周期重试。
7. **图谱 + env 文档**：01_modules.md schedule 行（deps 增 lg_rag + worker 备注）+ db 行（created_at 列登记 · fires 7→8 列）+ HG-GRAPH-MODULES 签收行；docs/guides/GUIDE_env_inventory_v1.md 登记 OPS_SCHEDULE_ENABLED / OPS_SCHEDULE_TICK_SECONDS（84→86 键）。

## 非范围

- 不碰 REST 四端点 / store 读写面（T2 已交付 · 本波零改动）。
- 不碰 capability manifest 面（T2b）· runs/events 端点（T4）· skill_registry/ · scripts/ · lg_rag/ 本体（仅消费既有公开函数）。
- 不新增 SSE 事件类型；worker 不单独落 user turn（带前缀 query 经既有管线 done 时 persist_thread_turns 落盘 · sse_stream.py:506 · 避免重复 user turn）。
- 不调 resolve_goal_for_thread 懒创建 goal（定时指令不该建 goal · continuity.py:583 装配期读取通路自然生效）。

## 失败路径

- OPS_SCHEDULE_ENABLED 非法值 → 回退 off + logger.warning（fail-closed）；OPS_SCHEDULE_TICK_SECONDS 非法/越界 → 回退 30 静默。
- worker tick 内 DB 异常 → logger.exception + 下周期重试（不炸 lifespan · 14 §11）。
- run 创建失败（create_run False/抛错）→ fires failed + 留痕，next_fire_at 已推进不重打（§11）。
- 幂等键撞行（他实例先占）→ SAVEPOINT 回滚跳过本行，不炸整批。
- thread 易主 → fires failed 不投递（R6）；创建者悬空 → fires failed + schedule paused（R11 防御性复核 · FK CASCADE 下 DB 层不可达）。
- claim 后 schedule 被 pause/cancel → execute 置 skipped（状态机字面）。
- 回退 = revert 本波 PR + alembic downgrade 回链尖（fires.created_at 列 drop · off 态零行为）。
- 并行 agent 撞 registry.yaml / 01_modules.md 同区冲突 → 保留双方 entry 手动解，冲突块如实登记。

## 验收标准

- [x] 闸默认 off 且非法回退 off + warning 有锚 → tests/test_schedule_worker.py::TestGateEnv（9 例 · 默认/off/ON 大小写/非法回退/tick 参数化）
- [x] DB 抢占互斥有锚 → TestClaim::test_concurrent_claim_mutex（asyncio.gather 双扫 fires 合计 1 · fire_count=1）
- [x] 幂等键撞行跳过有锚 → TestClaim::test_idempotency_key_existing_fire_skipped（NOT EXISTS 先过滤 · fire_count 不变）
- [x] once_at 只火一次不推进有锚 → TestClaim::test_once_at_claimed_once_not_advanced
- [x] max_fires 达限插 skipped 不增 count 仍推进有锚 → TestClaim::test_max_fires_reached_skipped
- [x] fires 状态机 + 归因有锚 → TestFireExecution::test_full_tick_fires_and_attributes（claimed→fired · spy kwargs query 前缀/user_id/tenant_id/mode/thread_id/run_id · OpsLgRagRun.user_id==creator · caplog 审计三元组）
- [x] 归属复核 R6 + 悬空 user R11 有锚 → test_foreign_thread_failed / test_dangling_user_failed_and_paused（FK CASCADE 下悬空场景 DB 层不可达 · 测试 monkeypatch AsyncSession.get 模拟防御面）
- [x] create_run 失败 failed 不留半成品有锚 → test_create_run_failure_failed（run_id 不落库 · logger.exception）
- [x] 补跑 fire_once 有锚 → TestCatchupAndRelink::test_catchup_fires_once_and_advances（过期 30min 单 tick 只火一次 · 推进严格未来 · 下轮 0）
- [x] 启动补链 R10 有锚 → test_relink_stale_claimed_fired / test_relink_fresh_claimed_untouched / test_relink_paused_schedule_skipped（stale 重放 · fresh 不动 · paused skipped）
- [x] lifespan 闸 off 零 diff 有锚 → TestLifespanGate（off 零创建 + REST 401 不闸 · 非法值零创建 · on 创建 shutdown 后句柄清空）
- [x] 五件套幂等 + 异常下周期重试有锚 → TestFivePieceSet（start 幂等复用 · tick 首轮抛错下周期重试）
- [x] `pytest tests/test_schedule_worker.py` 31/31 绿（真 PG opsdesk_test · 2026-11-16）；`ruff check` 两文件绿
- [x] 迁移 scratch 实证 → opsdesk_mig_test upgrade head：fires.created_at 列在 + 默认 now()（2026-11-16）
- [x] 01_modules.md schedule/db 行 + HG-GRAPH-MODULES 签收行回写（:40 / :42 / :145）；scripts/graph-compile.sh PASS；env 文档 84→86 键登记

### 自检结论

PASS（2026-11-16 close）。PR Cyning12/ops-desk-api#424 CI 四 job 全绿（check/import-linter/lint-wiki-delta/pytest）· squash merge 34b1609c。worker.py（双闸 env · claim_due_schedules SKIP LOCKED 抢占 · _execute_fire 状态机 · run_schedule_tick · relink_stale_claimed_fires · start/stop 五件套）+ main.py 三处挂接 + models.py fires.created_at（含 server_default=now() · 首轮 CI 红修复：CI 新库走 create_all 不跑迁移，T2/T4 裸 INSERT 用例靠 server_default · 修复后 create_all 口径 scratch 库全套件 2422 passed / 1 skipped 全绿）+ 迁移 20261116_ops_fires_created_at + 31 用例真 PG 全绿 + 图谱/env 文档登记完成。偏差 D1-D5 如实登记。并行波次 CONFLICTING 一次（P3-T5 #422/#423 先合）→ rebase origin/master 解 registry.yaml 保留双方 entry 强推 · 35 passed 复跑 · PR MERGEABLE。

## 必读列表

- 设计真源：`../ops-desk-workspace/docs/01-scope/03-general-agent/14-p3-schedule-taskcard-design.md` 终稿（R1-R23 · §1.1 lifespan/§1.3 触发语义/§1.4 DB 抢占/§1.5 补跑+补链/§1.6 归属复核/§1.7 总闸/§1.8 预算归因/§11 失败路径）
- 契约真源：`../ops-desk-workspace/docs/01-scope/03-general-agent/15-p3-contracts.md`（commit 62af6ea · §4.1 fires 状态机/§4.2 写入纪律/§4.3 补链只信台账/§4.4 前缀仅展示/§7.1 总闸）
- 先例：`app/ops/hitl/auto_resume.py`（:273-309 五件套 · env 回退）· `app/ops/hitl/store.py`（:261-277 SKIP LOCKED）· `app/ops/lg_rag/run_worker.py`（:93 start_run_worker · :198 scan_orphan）· `app/ops/lg_rag/run_store.py`（:52 create_run）· `app/ops/schedule/store.py`（compute_next_fire_at · FIRE_STATUSES）· `app/main.py`（:84-110 lifespan 挂接）
- T2 体例：`docs/tasks/done/task_p3_t2_schedule_ddl_rest.md` · registry `docs/harness/audit_gates/registry.yaml`

## 思考轮

| 轮 | 结论 | early_stop |
|----|------|-----------|
| R0 | 范围对账（委派书 vs 14 终稿 §1.1-§1.8 / 15 契约 §4/§7）done | false |
| R1 | 失败路径推演（§11 + 状态机三出路 + 幂等键撞行 + 归属/悬空）done | false |
| R2 | 非范围边界（REST/capability/lg_rag 本体/SSE/goal 懒创建）done | false |
| R3 | 关键决策记录（D1-D5 偏差 · 不单独落 user turn · 函数级 import 避环）done | false |
| R4 | 体例对账（T2 模板/registry/invokes 四件/审查文/图谱+env 登记）done | false |
| R5 | 收尾复核（验收 15 条全锚定 · 三红结构性归因）done | false |

actual_last_round: R5

### R0 · 范围对账

委派书与 14 终稿/15 契约逐条对照：lifespan 周期任务+模块级句柄（§1.1）· 触发语义前缀（§1.3/§4.4）· DB 抢占 SKIP LOCKED 同事务推进+fires INSERT（§1.4/§4.2）· 补跑 fire_once+启动补链（§1.5/§4.3）· 归属复核（§1.6/R6）· 总闸默认 off 不闸 REST（§1.7/§7.1/R8）· 预算归因显式 creator（§1.8/R4）。T2 既有面（REST/store/配额/词表）零改动确认。

### R1 · 失败路径推演

见「失败路径」节。新增推演：PG 同事务撞 uq 会 abort 整事务 → SAVEPOINT 嵌套（禁外层吞 IntegrityError）；create_run 失败时 run_id 不落库（失败回滚不留半成品）；fresh claimed 不补链（启动瞬间在途触发与补链双火窗口）；planned_fire_at 不可作补链超时判据（fire_once 补跑的 planned 必在过去 → 误判超时双火 · 故 D5 加 created_at）。

### R2 · 非范围边界

REST 四端点/store 读写面零触；capability manifest（T2b）与 runs/events（T4）不碰；lg_rag 本体零改（仅消费 start_run_worker/create_run 公开函数 · 函数级 import 避 import 环）；零新 SSE 事件类型；worker 不单独落 user turn（done 时既有管线落盘）；不调 resolve_goal_for_thread（定时指令不建 goal）。

### R3 · 关键决策记录

- **D1（抢占 SQL 形态）**：14 §1.4 原文单语句 UPDATE...WHERE schedule_id IN (SELECT ... FOR UPDATE SKIP LOCKED) RETURNING；因 next_fire_at 按 kind 分别计算（Python zoneinfo 算术），实施采 SELECT FOR UPDATE SKIP LOCKED + 同事务逐行推进 + INSERT fires（原子性等价 · 同事务纪律保持）。
- **D2（补链超时阈值）**：设计未钉值 → 模块常量 CLAIM_STALE_SECONDS=120，测试可 monkeypatch。
- **D3（max_fires 达限语义）**：插入 fire 立即置 skipped，不增 fire_count，interval/daily 仍推进 next_fire_at（提高 max_fires 即自然恢复 · 状态机字面）。
- **D4（once_at 推进）**：once_at 抢占后不推进 next_fire_at（无下一时刻可算 · once_at 过去时刻 compute 会 raise）；claim 查询加 NOT EXISTS(fires 行 planned=next_fire_at) 过滤 + 幂等键双保险防重火且不占 batch 名额。
- **D5（fires.created_at 列）**：R10 补链超时判据无载体（planned_fire_at 会把 fire_once 补跑误判超时 → 双火窗口）→ models.py 加列 + 迁移 20261116_ops_fires_created_at（ADD COLUMN IF NOT EXISTS · 默认 now() · scratch 实证）；fires 7→8 列，图谱 db 行同步修订。
- **不单独落 user turn**：带前缀 query 交既有管线，done 时 sse_stream.py:506 persist_thread_turns 落盘（worker 再落会重复 user turn）。
- **函数级 import lg_rag**：worker 模块顶 import run_worker 会形成 import 环风险，采函数级 import（承 auto_resume 局部 import 先例 · import 期零副作用纪律 · .importlinter 12 contracts 无一涉 schedule 零违约）。

### R4 · 体例对账

照 T2：task 档结构/人工闸表/registry entry（base=17337d35 · banned_prefixes=[] 因本波碰 alembic/ · 迁移文件列 allowed_tree_files）/invokes by-task 四件 {10,30,40,50}/R1 审查文 GO 机读词/spec-wave task lint PASS 为闸；仓规条款一遵守（走 20-R1 审查文非 --allow-no-review）。

### R5 · 收尾复核

验收 15 条逐条锚到测试或文件证据；全套件三红（diff whitelist 两件 + wave_gate）结构性归因=脏树期在途面咬禁改面常态（委派书预警），commit + registry 落盘后复跑对照，CI 终裁。回退路径=revert PR + alembic downgrade 回链尖。

## 实现备忘

### 偏差登记

- **D1**：抢占由单语句 UPDATE 拆为锁定 SELECT + 同事务逐行推进（R3 记录）。
- **D2**：CLAIM_STALE_SECONDS=120（设计未钉值 · 模块常量可 monkeypatch）。
- **D3**：max_fires 达限插 skipped + 推进（提高 max_fires 即恢复）。
- **D4**：once_at 不推进 next_fire_at（NOT EXISTS + 幂等键防重火）。
- **D5**：fires 加 created_at 列（新迁移 20261116_ops_fires_created_at · R10 超时判据载体 · 图谱 db 行同步）。

### 限制登记

- **L1（补链窗口）**：启动首轮 relink 与在途触发之间靠 run_id IS NULL + created_at 超时双条件防双火；worker 崩在 create_run 后 commit 前的极端窗口（毫秒级）行保持 claimed 且 run_id NULL，下轮 relink 重放——幂等由 create_run 幂等键（run_id 已分配不落库则新 run_id · 15 §4.3 补链只信台账允许）。
- **L2（预算归因链）**：ops_llm_usage 无 user_id 列，归因链 = usage.run_id → ops_lg_rag_runs.user_id（creator）；验收锚 OpsLgRagRun.user_id==creator + start_run_worker 显式收到 creator 身份。

## 测试策略

pytest tests（CI 终裁 · 真 PG opsdesk_test · autouse 清场 fixture 独立引擎用后即 dispose · 插真行+删行纪律 · 禁 DROP 式临时表容错）；worker 31 用例 + 迁移 scratch upgrade head 实证；ruff check app tests；import-linter 零新 forbidden 出边（.importlinter 零改动 · 12 contracts 无一涉 schedule）。

## 修订记录

| 日期 | 修订 |
|------|------|
| 2026-11-16 | 落卡（夜间自动执行波 · 授权 issue #23 m03064/m03283） |
