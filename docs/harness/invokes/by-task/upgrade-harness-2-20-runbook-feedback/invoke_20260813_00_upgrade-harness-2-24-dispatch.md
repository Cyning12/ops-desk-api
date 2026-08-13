# Invoke：00 · upgrade-harness-2-20-runbook-feedback（改钉 2.24 · 派 30）

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 00 |
| task_slug | `upgrade-harness-2-20-runbook-feedback` |
| git_branch | `task/upgrade-harness-2-20-runbook-feedback`（30 自 master 续作） |
| created_utc_or_local | 2026-08-13 |
| notes | registry `@cyning/harness@2.24.0` · 仓内 manifest `2.22.0` · 维护者：改 task 后派 30；ops-sync 不碰 |

---

## 裁决

| 项 | 结论 |
|---|---|
| 是否仍停 2.22 | **否** · npm latest = **2.24.0** |
| task | 已改目标 · 完成态重开 · 闸保持 approved |
| 下一棒 | **30（含 40）** · 00 验收后 CLOSE |

## 给 30 的锁死

- 钉升 `@cyning/harness@2.24.0`；upgrade×2；local 块零手恢复
- FEEDBACK 新文件 `FEEDBACK_harness_2_24_0_…`
- 不改业务码；不动 `task_ops_sync_sender_migration`
- 关账由 **00** 做，30 只交 40 自检
