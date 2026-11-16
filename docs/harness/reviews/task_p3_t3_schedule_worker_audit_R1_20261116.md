# task_p3_t3_schedule_worker · R1 审查文（20 帽）

- 时刻：2026-11-16
- 审查人：exec-p3-t3（20 帽 · 夜间授权 issue Cyning12/ops-desk-workspace#23 m03064/m03283 · 00 代签体系）
- 对象：`docs/tasks/active/task_p3_t3_schedule_worker.md` v1

## 审查项

1. **范围对账**：task 范围 7 条与 14-p3-schedule-taskcard-design.md 终稿
   （§1.1 lifespan 周期任务+模块级句柄 · §1.3 触发语义前缀 · §1.4 DB
   抢占 SKIP LOCKED 同事务推进+fires INSERT · §1.5 补跑 fire_once+启动
   补链 · §1.6 归属复核 R6 · §1.7 总闸 OPS_SCHEDULE_ENABLED 默认 off
   不闸 REST · §1.8 预算归因显式 creator · §11 失败路径）+
   15-p3-contracts.md（commit 62af6ea）§4.1 fires 状态机三出路 ·
   §4.2 写入纪律（ON CONFLICT DO NOTHING）· §4.3 补链只信台账 ·
   §4.4 前缀仅展示 · §7.1 总闸 1:1 落入；委派书内联面（五件套承
   auto_resume · 函数级 import · 图谱/env 登记）全部锚定。GO。
2. **非范围**：REST 四端点/store 读写面（T2 已交付零改动）· capability
   manifest 面（T2b）· runs/events 端点（T4 并行）· lg_rag 本体 ·
   scripts/ · skill_registry/ · 新 SSE 事件类型 · worker 单独落 user
   turn · resolve_goal_for_thread 懒创建均明示排除。GO。
3. **状态机纪律**：契约 §4.1 claimed→fired/failed/skipped 三出路逐条
   有触发条件与落库动作（fired 须 UPDATE fires SET run_id,status,fired_at
   · failed 留痕不静默 logger.exception · skipped 覆盖 claim 后 pause/
   cancel 与 max_fires 达限）；失败回滚不留半成品（run_id 不落库）
   有测试锚。GO。
4. **抢占正确性**：PG 同事务撞 uq 会 abort 整事务 → SAVEPOINT 嵌套
   （禁外层吞 IntegrityError）；NOT EXISTS 预过滤 + uq 幂等键双保险；
   once_at 不推进防重火（D4）；max_fires 达限 skipped+推进（D3）。
   并发互斥 asyncio.gather 双扫合计 1 有锚。GO。
5. **补跑/补链安全**：fire_once 停机跨 N interval 只补一次（幂等键）；
   补链超时判据用 created_at 非 planned_fire_at（fire_once 补跑的
   planned 必在过去 · 误判超时双火窗口 → D5 加列+迁移 scratch 实证）；
   fresh claimed 不动防与在途触发双火；补链只信台账（§4.3）。GO。
6. **归因与归属**：预算归因 R4 = start_run_worker 显式传 creator 身份
   （user_id/tenant_id 取自 schedule 行）· 验收锚 OpsLgRagRun.user_id
   ==creator + spy kwargs（ops_llm_usage 无 user_id 列 · 归因链
   usage.run_id→runs.user_id 入 L2 限制）；归属复核 R6（thread 易主
   failed 不投递）+ 悬空 user R11（failed+schedule paused · FK CASCADE
   下 DB 层不可达为防御面 · 测试 monkeypatch 模拟）均有锚。GO。
7. **闸语义**：OPS_SCHEDULE_ENABLED 默认 off · 非法回退 off+warning
   （fail-closed 承 auto_resume_mode）· 只闸 worker 不闸 REST（§7.1）·
   off 态 TestClient 零 diff（lifespan 零创建 + REST 401 不闸）有锚；
   tick 默认 30 非法/越界回退 30。GO。
8. **体例对账**：registry entry base=17337d35 · banned_prefixes=[]
   （本波碰 alembic/ · 承 T2 先例 · 迁移文件列 allowed_tree_files）·
   invokes by-task 四件 {10,30,40,50} · 本审查文 GO 机读词 ·
   spec-wave task lint PASS 为闸 · 仓规条款一遵守（走 20-R1 审查文
   非 --allow-no-review）· .importlinter 零改动（12 contracts 无一涉
   schedule）。GO。
9. **验收可机判**：15 条验收逐条锚到 tests/test_schedule_worker.py
   六个测试类（31 用例）或迁移 scratch/图谱/env 文件证据；全套件三红
   （diff whitelist 两件 + wave_gate）为脏树期结构性红（委派书已预警
   · commit 后转绿 · CI 终裁）。GO。
10. **思考轮**：R0-R5 表 + actual_last_round=R5 + 六小节齐备；R3 记录
    D1-D5 偏差与不落 user turn/函数级 import 两决策；限制 L1 补链窗口
    /L2 归因链如实登记。GO。

## 结论

**GO（PASS · 通过 · 零阻塞）**——范围/非范围/验收/失败路径/思考轮与 14 终稿 + 15 契约对齐，
偏差 D1-D5 与限制 L1-L2 如实登记，可进 30。
