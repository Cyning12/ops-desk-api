---
title: task · feat · P1-T1 goal_store 模块
---

# task · feat · P1-T1 goal_store 模块

> **状态**：`active`（2026-11-15 过闸开工）
> **来源**：issue Cyning12/ops-desk-api#385（维护者派单 · 设计真源 07-p1-goal-design.md commit d19fdaa）

## Harness 元信息

| 键 | 值 |
|----|----|
| **task_slug** | p1-t1-goal-store |
| base | 0dfc697 |
| 关联 issue | Cyning12/ops-desk-api#385 · Cyning12/ops-desk-workspace#23 |
| 关联 PR | 待回填 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 本仓未启用 WikiTrack |

## 人工闸（维护者授权）

- 三闸引用 m00177「签收，开始」：禁止 freeze 帧/schema 触碰 · 禁止跨 task 承载 · 禁止 freeze 概念语义漂移。
- 设计真源 07 §1 状态机 / §5 T1 行 / §6 终裁（O-1 人工复活 · O-3 1:1 · R-2 不加 FK）。

## 背景

P1（Goal → supervisor 收敛）第一单：ops_goals 表（T5 · 仅 DDL）的读写模块。本单只交付模块+单测，T4 才接线。

## 范围

1. 新模块 `app/ops/goals/store.py`：resolve_goal_for_thread（非终态查询→懒创建 · objective 单行化截 200 · IntegrityError 重读消化竞态）/ get_goal / list_goals / patch_goal_status（状态机校验 · 终态不可逆 · 非法流转抛 GoalStateTransitionError）。
2. ORM 补 `__table_args__`：OpsGoal（idx_ops_goals_tenant_status · idx_ops_goals_thread）与 OpsLgRagRun（idx_ops_lg_rag_runs_status_created · idx_ops_lg_rag_runs_thread）对齐既有 DB 索引名，消 autogenerate 漂移。**零新迁移**。
3. tests/test_goal_store.py：状态机全矩阵 · tenant 隔离 · 懒创建幂等/竞态重读 · DB 故障 resolve 返回 None。

## 非范围

router/continuity/图内任何接线；REST 面；SSE 面；新 alembic 迁移（唯一新 DDL uq_ops_goals_active_thread 属 T4）。

## 失败路径

- 状态机词表漂移 → 以 07 §1 矩阵为准回退。
- ORM __table_args__ 与 DB 索引名不一致 → autogenerate 校验显形，回退本卡。

## 验收标准

- [ ] 状态机全矩阵单测（含非法流转拒绝 · 终态不可逆）
- [ ] tenant 隔离（跨租户 get/patch 返回 None）
- [ ] 懒创建幂等与竞态重读（catch IntegrityError）
- [ ] DB 故障时 resolve 返回 None 不炸（日志带 thread_id）
- [ ] patch 路径显式抛错不吞（分层纪律）
- [ ] 真 PG 本地全量绿；lint PASS

### 自检结论

- （过闸时为空 · 关账回填）

## 必读列表

- `app/db/models.py:303-323`（OpsGoal）
- `app/ops/lg_rag/run_store.py:1-87`（纪律先例）
- `alembic/versions/20261114_ops_goals.py:37-43`（既有索引名）

## 思考轮控制

- R0（勘察）：run_store 纪律/迁移索引名/测试 fixture 模式已核。
- R1（审查）：docs/harness/reviews/task_p1_t1_goal_store_audit_R1_20261115.md。
- R2–R4：实施中按证补充。
- R5（组织人终裁）：维护者。

## 测试策略

真 PG（DB_AVAILABLE skipif 体例）；纯函数部分（sanitize/状态机判定）不依赖 DB。

## 修订记录

- 2026-11-15：落卡过闸。
