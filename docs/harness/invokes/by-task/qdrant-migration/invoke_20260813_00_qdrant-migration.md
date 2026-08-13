# Invoke · 00 编排 · qdrant-migration（人闸代签授权）

| 字段 | 值 |
|------|-----|
| **hat** | 00（编排） |
| **日期** | 2026-08-13 |
| **授权** | 维护者：「授权00进行所有步骤的人闸签收，但00除了关账不要进行其他操作，全部交由子agent」 |

## 00 已做

- 代签 `HG-TASK-DRAFT=approved`
- 派发 **20-task-audit** 子 agent（本 invoke 时刻）

## 00 将做（条件触发）

- 20 审查文落盘且结论 pass/conditional_pass → 代签 `HG-AUDIT-R1=approved`
- 派发 **30** 子 agent（实现）
- 验收齐备后 **关账**（仅此由 00 执行）

## 00 禁止

- 不写业务码、不跑 fio/灌库/压测、不改 compose 实现细节（交 30 子 agent）
