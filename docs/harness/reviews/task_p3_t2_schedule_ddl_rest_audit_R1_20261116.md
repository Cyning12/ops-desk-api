# task_p3_t2_schedule_ddl_rest · R1 审查文（20 帽）

- 时刻：2026-11-16
- 审查人：exec-p3-t2（20 帽 · 夜间授权 issue Cyning12/ops-desk-workspace#23 m03064/m03283 · 00 代签体系）
- 对象：`docs/tasks/active/task_p3_t2_schedule_ddl_rest.md` v1

## 审查项

1. **范围对账**：task 范围 6 条与 14-p3-schedule-taskcard-design.md 终稿
   （R4 双上限+interval≥300 · R6 thread 归属校验 · R10 fires 幂等键
   ON CONFLICT DO NOTHING · R13-N4 fires.run_id 索引 · N5 PATCH 重算守卫 ·
   R20 humanized_display 文案）+ 15-p3-contracts.md（commit 62af6ea）
   §1.1 端点总表四件 · §1.2 响应对象全字段 · §1.3 创建语义 · §1.4 列表谓词 ·
   §1.5 单条+recent_fires · §1.6 PATCH 全可选至少一项 · §1.7 归属校验 ·
   §1.8 双上限与 422 文案词表 · §4.1 fires 表结构与状态机 1:1 落入；
   委派书内联面（down_revision=链尖 · zoneinfo 否 croniter · store 承
   goals 先例 · 图谱登记）全部锚定。GO。
2. **非范围**：worker/点火循环/启动补链/OPS_SCHEDULE_ENABLED 总闸（T3）·
   capability manifest 面（T2b）· runs/events 端点（T4 并行）·
   scripts/ · skill_registry/ · capability/ · lg_rag/ 本体均明示排除。GO。
3. **422 文案逐字纪律**：§1.8 七条词表（per-user 超限/per-tenant 超限/
   interval<300/词表外 kind/词表外 status/非 thread_owner/已 cancelled 再改）
   在 task 范围 3/4 与验收 4 逐字登记，前端不二次包装；测试断言逐字比对
   （非模糊匹配）。GO。
4. **DDL 完整性**：ops_schedules 全列含 tenant_id（R7 租户谓词）+ user_id
   FK ops_users + thread_id 无 FK（§1.2 钉明）+ idx_ops_schedules_next_fire
   (status,next_fire_at)（§4.2 worker 扫描面预留）；ops_schedule_fires
   schedule_id 无 FK（删除不级联台账保留）+ uq(schedule_id,planned_fire_at)
   幂等键 + run_id 索引（§3.1 归因反查防 N+1）。GO。
5. **uq 索引形态**：§4.1 原文「部分唯一索引」无 WHERE 语义，取普通
   UNIQUE INDEX——ON CONFLICT (schedule_id, planned_fire_at) DO NOTHING
   直接可用（T3 §4.2 写入纪律依赖），最小满足语义，入 R3 决策记录。GO。
6. **排期算术**：zoneinfo（stdlib 零新依赖）daily_at 时区内下一时刻；
   once_at run_at 须未来；interval≥300；N5 重算守卫（重算值>now 否则 422）。
   边界推演（time_of_day 恰等当前时刻取次日 · run_at=now 拒 · resume
   不重算）入 R1/R3 与限制 L1。GO。
7. **归属与零写**：端点谓词 tenant_id+user_id 否则 404 不泄露存在性；
   创建/PATCH thread 存在须归属当前用户否则 422 零写，thread 不存在允许
   （fire 时 worker 自建 · §1.7-2）；PATCH 已 cancelled 422 终态不可逆。GO。
8. **体例对账**：registry entry base=f1d0dd28 · banned_prefixes=[]（本波
   碰 alembic/ · 承 p0prime-t4/t5 先例 · 迁移文件列 allowed_tree_files）·
   invokes by-task 四件 · 本审查文 GO 机读词 · spec-wave task lint PASS
   为闸 · 仓规条款一遵守（走 20-R1 审查文非 --allow-no-review）。GO。
9. **验收可机判**：10 条验收逐条锚到 tests/test_ops_schedule_ddl.py /
   tests/test_schedule_store.py / tests/test_schedule_rest.py 或文件证据；
   脏树期 wave_gate 红为在途面咬禁改面常态（commit 后转绿 · CI 终裁）。GO。
10. **思考轮**：R0-R5 表 + actual_last_round=R5 + 六小节齐备；R3 记录
    zoneinfo/uq 形态/store 布局/resume 不重算四决策。GO。

## 结论

**GO（PASS · 通过 · 零阻塞）**——范围/非范围/验收/失败路径/思考轮与 14 终稿 + 15 契约对齐，
偏差与限制如实登记，可进 30。
