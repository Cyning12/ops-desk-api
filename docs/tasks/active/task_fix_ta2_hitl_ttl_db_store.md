---
title: task · fix · ta2 HITL TTL db-store 过期不消费
---

# task · fix · ta2 HITL TTL db-store 过期不消费

> **状态**：`active`（2026-11-14 过闸开工）
> **来源**：issue Cyning12/ops-desk-workspace#23 · P0' 波次偏差登记（draft → 正式落卡）

## Harness 元信息

| 键 | 值 |
|----|----|
| task_slug | fix-ta2-hitl-ttl-db-store |
| base | 510516c |
| 关联 issue | Cyning12/ops-desk-workspace#23 |
| 关联 PR | 待回填 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 本仓未启用 WikiTrack |

## 人工闸（维护者授权）

- 三闸引用 m00177「签收，开始」：禁止 freeze 帧/schema 触碰 · 禁止跨 task 承载 · 禁止 freeze 概念语义漂移。
- 本卡为**纯测试口径修复**，app 侧零改动（根因不在生产代码）。

## 背景

`test_ta2_ttl_db_store_expired_not_consumed` 在本地真 PG 恒红（T4 起登记 · baseline cc622403 同红 → 既有问题）。CI 无 PG service → skip 假绿。

## 根因（R0 实证）

`ops_hitl_requests.decided_at` 为 **naive UTC** 列约定（models.py:495 `Mapped[datetime | None]` 无 tz；写入侧 Python `now_utc()` 产出 naive UTC 墙钟；`_row_to_dict` 出 ISO str；`_decided_at_ts` nodes.py:349-369 对 naive 一律按 UTC 解释）。

测试拨回 SQL `SET decided_at = now() - interval '2 hours'` 用的是 **PG server TimeZone（Asia/Shanghai）** 的 `now()`：timestamptz 强存 naive 列时按 server TZ 去时区 → 落库值 = 本地墙钟-2h = UTC+6h「未来」→ `_decided_at_ts` 按 UTC 解释后 `time.time() - ts < 0` → TTL 判新鲜 → 过期单被消费 → `reason is None` 断言失败。实证：`SHOW TimeZone = Asia/Shanghai`。

修复 = 拨回 SQL 改 `(now() AT TIME ZONE 'UTC') - interval '2 hours'`，与 naive-UTC 列约定一致（同 T6 v_audit_unified 时间窗口径教训）。

## 范围

1. tests/test_hitl_approval_consumption.py ta2 stale 半 SQL 口径修正 + 行内注释钉约定。
2. 防回归：注释明示 naive-UTC 约定 + 既有「真读路径复核拨回已生效」断言保留。
3. 附带（同文件测试卫生）：三处 Db store 用例（ta2 新鲜半/ta2 过期半/TB6⑦）finally 补 `reset_hitl_store()`——`set_hitl_store` 是进程全局态，泄漏致 `-k hitl` 多文件联合跑时 ta4 红；复位后 231 passed 稳定。
4. ta4 红另一独立成因登记（不修）：主仓 .env 残留 `OPS_CAPABILITY_ALLOW_WRITE=1`（:85）会打开 Policy 写闸使 ta4 断言③失败——纯本地开发环境污染（CI/干净 checkout 无 .env 不现），本地协议沿用 T3 四键 blank。

## 非范围

- HITL 契约/语义变更；闸参数调整；app 侧代码；列类型改造（tz-aware 化属另议）。

## 失败路径

- 修复后仍红 → 说明根因不止时区口径，回退本卡重开 R0（当前实证已闭环）。

## 验收标准

- [ ] ta2 用例本地真 PG 转绿
- [ ] test_hitl_approval_consumption.py 全文件 + hitl 套件回归全绿
- [ ] ruff / import-linter / graph check 不受影响（纯测试改动）
- [ ] 干净 worktree 全量 0 failed（ta2 转绿后应全绿）

## 必读列表

- `app/ops/lg_rag/multi/nodes.py:349-369`（`_decided_at_ts` naive→UTC 解释）
- `app/db/models.py:495`（decided_at naive 列）
- `tests/test_hitl_approval_consumption.py:291-306`（拨回 SQL 现场）

## 思考轮控制

- R0 根因（已完成 · 见上「根因」节：时区口径实证闭环）。
- R1 设计审查：`docs/harness/reviews/task_fix_ta2_hitl_ttl_db_store_audit_R1_20261114.md`。
- R2-R5：修复/验证/回归/收尾。early_stop reason：单行口径修复，范围封闭。

## 实现备忘

<!-- CLOSE 前回填 -->

## 测试策略

目标：ta2 单件 + 全文件 + hitl 套件。回归：干净 worktree 全量。

## 修订记录

| 日期 | 变更 |
|------|------|
| 2026-11-14 | draft → 正式落卡过闸（根因实证闭环后） |
| 2026-11-14 | 范围追加：同文件三处 Db store 全局态复位（ta4 污染修复） |
