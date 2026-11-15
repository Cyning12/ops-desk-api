---
title: task · feat · P1-T4 goal 入口接线 + uq 索引
---

# task · feat · P1-T4 goal 入口接线 + uq 索引

> **状态**：`in_progress`
> **来源**：issue Cyning12/ops-desk-api#396（维护者派单 · 设计真源 07-p1-goal-design.md commit d19fdaa）

## Harness 元信息

| 键 | 值 |
|----|----|
| **task_slug** | p1-t4-goal-entry |
| base | 0d62718 |
| 关联 issue | Cyning12/ops-desk-api#396 · Cyning12/ops-desk-workspace#23 |
| 关联 PR | 待建 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 本仓未启用 WikiTrack；闸默认 off 行为面零变化 |

## 人工闸（维护者授权）

- 三闸引用 m00177「签收，开始」：禁止 freeze 帧/schema 触碰 · 禁止跨 task 承载 · 禁止 freeze 概念语义漂移。
- 设计真源 07 §3（platform 修正③ 部分唯一索引）/ §5 T4 行；m02028「本窗口任务继续」直执行。

## 背景

T1 goal_store / T2 REST / T3 注入装配已闭环，但懒创建无入口接线——闸开也永不注入（无 goal 行）。本单接 `/lg-rag/stream` 入口并落 P1 唯一新 DDL `uq_ops_goals_active_thread`，DB 层执行 1 thread : 1 非终态 goal（O-3）。

## 范围

1. `app/ops/lg_rag/router.py` stream_lg_rag（_prepare_thread 后）闸内挂 `resolve_goal_for_thread(tenant_id, thread_id, query=body.query)`：`GOAL_INJECT_ENABLED` off 零触达；importlib 运行期解析 goals.store（承 T3 continuity 先例，守 lg-rag-outbound · .importlinter 零改动）；objective 用 body.query 原始用户输入（非 continue_from_run_id 拼接稿）。
2. `alembic/versions/20261115_uq_goals_active_thread.py`（down_revision=20261114_drop_legacy_chat_tables）：`CREATE UNIQUE INDEX uq_ops_goals_active_thread ON ops_goals (tenant_id, thread_id) WHERE status IN ('active','paused')`；downgrade DROP INDEX。
3. `app/db/models.py`：OpsGoal __table_args__ 补 Index 声明（名逐字对齐迁移 · postgresql_where 对齐）；docstring 更新「仅 DDL 零功能」→ P1-T4 已接线。
4. `tests/test_goal_entry_wiring.py`（真 PG · fake supervisor graph）：
   - 闸 off：POST /stream 后 ops_goals 零行。
   - 闸 on：懒创建一行（tenant/status/objective 单行化断言）；同 thread 二轮复用不重复建行。
   - 并发：asyncio.gather 10 路 resolve_goal_for_thread → 仅一行（uq 索引实证竞态消化）。
   - turns 表无 `[当前目标]` 横幅残留（闸 on 全流后 ops_lg_rag_turns 查询原文一致）。
5. 迁移 up/down scratch 库实证；01_modules.md goals 行备注 + 签收行。

## 非范围

- goal 自动流转（无 LLM 自判 · 无 hitl 联动）——O-1 裁定仅人工 PATCH（T2 已交付）。
- `/invoke` 入口懒创建（07 §5 T4 行仅列 stream；invoke 为内部冒烟入口，goal 存在时注入自然生效）。
- goal.updated SSE 帧（07 §4 明确不做）；REST 面（T2 已交付）；注入机制本体（T3 已交付）。

## 失败路径

- goals.store 不可导入 / DB 异常 → resolve_goal_for_thread 内部吞错返 None（T1 既有纪律），请求继续。
- 并发懒创建撞 uq 索引 → IntegrityError 重读返回既有行（T1 已实现，本单索引就位后路径激活）。
- 回退=关闸 + 回撤迁移互不影响（07 §5 T4 红线）。

## 验收标准

- [ ] 闸 off POST /stream → ops_goals 零行且 store 零触达
- [ ] 闸 on → 懒创建一行（objective=query 单行化截 200）；同 thread 3 轮对话复用同一行
- [ ] 并发 10 路 resolve → 仅一非终态行（uq 索引生效）
- [ ] turns 表无目标横幅残留（注入只在装配层消息，不落 turns）
- [ ] 迁移 upgrade/downgrade scratch 库可逆实证
- [ ] .importlinter 零改动（contract 测试绿）；01_modules.md 登记 + 签收行

### 自检结论

（实施时回填）

## 必读列表

- workspace 07 §3/§5 T4 行/§6 O-3
- `app/ops/goals/store.py:96-131`（resolve_goal_for_thread + IntegrityError 重读）
- `app/ops/lg_rag/router.py:452-500`（stream_lg_rag 接线点）
- `alembic/versions/20261114_ops_goals.py`（ops_goals 建表迁移风格）
- `tests/test_lg_rag_sse_stream.py:30-100`（fake graph + SSE 测试模式）

## 思考轮控制

- R0（勘察）：接线点 :466 后定论；head=20261114_drop_legacy_chat_tables；conftest create_all → ORM Index 声明自动进测试库；T1 已对齐既有两索引，本单只补新增 uq。
- R1（审查）：docs/harness/reviews/task_p1_t4_goal_entry_audit_R1_20261115.md。
- R2–R4：实施中按证补充。
- R5（组织人终裁）：维护者。

## 测试策略

真 PG + fake supervisor graph（承 test_lg_rag_sse_stream.py 模式）；并发用 asyncio.gather 直调 store；迁移可逆走 scratch 库。

## 修订记录

- 2026-11-15：落卡过闸。
