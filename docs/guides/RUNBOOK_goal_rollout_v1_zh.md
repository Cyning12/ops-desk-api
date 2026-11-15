---
title: RUNBOOK · Goal 功能放量（GOAL_INJECT_ENABLED 三步灰度）
version: v1
date: 2026-11-15
status: active
owners: [ops]
related:
  - docs/_tech_graph/l1/10_flow_goals.md
  - docs/_tech_graph/l1/01_modules.md
design: ops-desk-workspace docs/01-scope/03-general-agent/07-p1-goal-design.md（§6 验收十条）
---

# RUNBOOK · Goal 功能放量（GOAL_INJECT_ENABLED 三步灰度）

## 0. 功能面速览

| 件 | 位置 | 交付波 |
|----|------|--------|
| ops_goals 表 + goal_store 状态机 | app/ops/goals/store.py · migration 20261114_ops_goals | P0' T5 / P1-T1 |
| REST 面 GET /api/ops/goals + PATCH /{goal_id} | app/ops/goals/router.py | P1-T2 |
| continuity 注入槽位（[当前目标] 横幅） | app/ops/goals/inject.py · lg_rag/continuity.py · prompts/slots.py | P1-T3 |
| 流入口懒创建 + uq_ops_goals_active_thread | lg_rag/router.py · migration 20261115_uq_goals_active_thread | P1-T4 |

**总闸**：`GOAL_INJECT_ENABLED`（env · 默认 off）。闸 off = 懒创建零触达（ops_goals 零写入）+ 装配零注入（逐字节一致）+ store 零调用。闸 on = 懒创建 + 注入同步生效（同一闸，07 §2 裁定）。

## 1. 三步放量

### 第①步：默认 off（交付态）

- 配置：不设置 `GOAL_INJECT_ENABLED`（或显式置空）。
- 预期：ops_goals 零行增长；装配 off 态与既有逐字节一致（tests/test_goal_inject.py 闸 off 对拍用例守护）。
- 适用：上线初期 / 观察期。

### 第②步：灰度（单环境开闸）

- 配置：灰度环境 `GOAL_INJECT_ENABLED=1`。
- 动作：内部 tenant 发起新会话（空 thread 首轮 query → 懒创建 active goal）；同 thread 追问验证复用不新建。
- 观测点：
  1. `ops_goals` 行增速（每新 thread 至多 1 行；`SELECT count(*) FROM ops_goals WHERE status='active'`）；
  2. Langfuse span `goal_inject_degraded`（timeout / error）——出现率应 ≈0；持续出现先回退再排查；
  3. 注入横幅可见性（DB 内 `ops_lg_rag_turns` **不应**出现 [当前目标] 字样——横幅仅存在于装配层 SystemMessage，不落盘）；
  4. REST 面手测：`GET /api/ops/goals?thread_id=<tid>` 返回该 goal；`PATCH /api/ops/goals/<gid> {"status":"paused"}` → 200；再 PATCH active → 200（O-1 复活）；PATCH done 后再 PATCH 任意 → 409。
- 通过标准：灰度 ≥3 天 · degraded span 零出现 · 状态机手测全过 · 无 turns 表横幅污染。

### 第③步：全开

- 配置：生产 `GOAL_INJECT_ENABLED=1`。
- 观测点同第②步，加：ops_goals 增速与 thread 增速比对（应 ≤1:1）；uq 冲突日志（IntegrityError 重读为正常路径，不应外溢 500）。

## 2. 回退

任意阶段回退 = 移除/置空 `GOAL_INJECT_ENABLED` 并重启进程（或滚动发布）。

- **秒级生效**：闸判定在请求路径运行时读取（goals/inject.py goal_inject_enabled()），无缓存。
- **无数据迁移**：ops_goals 存量行保留无害（闸 off 后零读写）；如需彻底清理可 DELETE/留档，不影响任何链路。
- **REST 面不受闸控**（T2 裁定：人工管理面常开），回退后 PATCH/GET 仍可用。

## 3. P1 验收十条对照（07 §6）

| # | 验收 | 实证位置 |
|---|------|----------|
| 1 | thread 首轮自动建 goal | tests/test_goal_entry_wiring.py（闸 on 懒创建） |
| 2 | 同 thread 复用不新建 | 同上（3 轮单行） |
| 3 | 注入进下一轮 SystemMessage 头部 | tests/test_goal_inject.py |
| 4 | 不落 turns 表 | tests/test_goal_entry_wiring.py（turns 无横幅） |
| 5 | paused 后不再注入 | tests/test_goal_inject.py（仅 active 注入） |
| 6 | done/abandoned 终态不可复活 | tests/test_goal_store.py（迁移矩阵 409） |
| 7 | 跨 tenant 不可见 | tests/test_goals_rest.py（404 防探测） |
| 8 | tenant_id 必填 | ops_goals DDL NOT NULL（tests/test_ops_goals_ddl.py） |
| 9 | DB 1:1 执行面（uq 部分唯一索引） | tests/test_goal_entry_wiring.py（并发 10 路单行） |
| 10 | 图零改动（graph-compile 节点/边不变） | T3 invoke_30 对拍证据 |

## 4. 故障排查

| 症状 | 排查 |
|------|------|
| goal_inject_degraded=timeout 持续 | goals.store find_active_goal 慢查 → 查 ops_goals 索引（tenant_id,status）是否生效；临时回退关闸 |
| 同 thread 出现两条 active | 不应发生（uq 索引 + IntegrityError 重读）；检查迁移 20261115_uq_goals_active_thread 是否应用（本地 create_all 库须 DROP TABLE 重建——create_all 不给既有表补索引） |
| turns 表出现 [当前目标] | 装配面被改动（横幅落盘=污染）——回退关闸并审查 continuity.py diff |
| PATCH 409 误判 | 当前 status 是否终态（done/abandoned 不可逆）；词表外值应为 422 非 409 |
