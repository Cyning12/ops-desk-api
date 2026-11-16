# R1 审查文 · task_fix_434_worker_thread_upsert

> **审查帽**：20-task-audit（R1）
> **task**：docs/tasks/active/task_fix_434_worker_thread_upsert.md
> **日期**：2026-11-17
> **授权链**：issue Cyning12/ops-desk-workspace#23（m03064/m03283/m03694 夜间授权）· 来源 issue Cyning12/ops-desk-api#434（第一项）· 契约真源 15-p3-contracts.md §1

## 结论

**GO · PASS · 零阻塞** — task 档范围/非范围/验收/failure_paths/思考轮（R0-R5）齐备，与 issue #434 第一项（worker-fired run 面板 404）及契约 15 §1「thread 不存在 fire 时自建」逐条对齐，可进 30。

## 核对项

| 项 | 结论 | 依据 |
|----|------|------|
| 范围4条 ↔ 委派书/issue #434 第一项 | 一致 | worker fire 路径补 thread upsert · 真 PG 验证含端点 200 · 图谱签收 · 过闸落盘 |
| 非范围 | 一致 | 第二项离线交付留 APNs 波（14 文 R21 已登记）· R6/R11/runs 端点/thread_store 零触 · alembic//scripts/ 禁入 |
| 验收标准 | 7 条全机判锚 | upsert 行存在+二火不动 · 端点 200 含 run_id · R6 回归 · 六文件回归+全量 · ruff · 图谱两件 · 过闸四件 |
| failure_paths | 6 条 | 并发 PK 冲突 · DB 故障 · 类型一致 · 并行冲突 · 环境性红对照 · 脏树期 registry 红常态 |
| 思考轮 | R0-R5 齐 · actual_last_round=R5 | 表头 `| 轮 | 结论 | early_stop |` 合规 |
| 人工闸表 | 三行 approved | HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES · issue #23 授权 |
| 体例 | 照 T3/T7 done 模板 | registry/invokes/图谱签收承 p3-t3-schedule-worker 先例 |
| 仓规条款一 | 遵守 | 本审查文即 20-R1 路径 · 未用 --allow-no-review |

## 关键决策复核

- **upsert 落点=worker._execute_fire 同事务（而非 persist 路径）**：成立——sse_stream.py:504-506 persist 仅正常 done 且 user_id 非空时调用，waiting_approval/error/disconnected 终态不走 persist；fire 同事务建行覆盖全终态，失败整体回滚不留半建行。R6（外来 thread failed）先行于 upsert，语义不破。
- **最小字段裁剪（D1）**：OpsLgRagThread（app/db/models.py:226-238）仅 id/user_id/created_at/updated_at 四列，无 tenant_id——委派书字段单按模型实际裁剪为 id+user_id，合理且已登记。
- **并发 PK 冲突→failed 不自动重火**：极端小概率 · 台账 failed 可审计 · 与既有 except 路径一致，接受。

## 偏差确认

- D1 最小字段按模型裁剪（无 tenant_id 列）——授权范围内登记，接受。

## 机读通过词

PASS（spec-wave task lint 命令：`npx --yes spec-wave@3.5.0 task lint --file docs/tasks/active/task_fix_434_worker_thread_upsert.md`）
