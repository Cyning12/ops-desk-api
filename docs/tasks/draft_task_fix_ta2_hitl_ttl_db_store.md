---
title: task · fix · ta2 HITL TTL db-store 过期不消费
---

# task · fix · ta2 HITL TTL db-store 过期不消费

> **状态**：`draft`（P0' 收官衍生落卡 · 待排期过闸）
> **来源**：issue Cyning12/ops-desk-workspace#23 · P0' 波次偏差登记

## Harness 元信息

| 键 | 值 |
|----|----|
| task_slug | fix-ta2-hitl-ttl-db-store |
| 关联 issue | Cyning12/ops-desk-workspace#23 |

## 背景

`tests/test_hitl_approval_consumption.py::test_ta2_ttl_db_store_expired_not_consumed` 在本地真 PG 环境恒红（T4 起登记 · baseline cc622403 同红 → 既有问题非任何 P0' diff 引入）。CI 因无 PG service 该用例 skip 呈假绿——本地 PG（opsdesk_test）可用后才显现。

## 范围（草案）

1. 复现定位：db-store 路径下 TTL 过期单据仍被消费（或不消费断言失败）的根因（时区/时钟源/查询谓词候选）。
2. 修复 + 用例转绿；补防回归断言。

## 非范围

- HITL 契约/语义变更；闸参数调整。

## 验收（草案）

- [ ] ta2 用例本地真 PG 转绿；hitl 套件回归全绿
- [ ] ruff / import-linter / graph check 不受影响

