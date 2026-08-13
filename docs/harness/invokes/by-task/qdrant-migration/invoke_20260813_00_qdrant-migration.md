# Invoke · 00 编排 · qdrant-migration（人闸代签授权）

| 字段 | 值 |
|------|-----|
| **hat** | 00（编排） |
| **日期** | 2026-08-13 |
| **授权** | 维护者：「授权00进行所有步骤的人闸签收，但00除了关账不要进行其他操作，全部交由子agent」 |

## 00 已做

- 代签 `HG-TASK-DRAFT=approved`
- 派发 **20-task-audit** 子 agent
- 接受 C1–C3 → 代签 `HG-AUDIT-R1=approved`
- 派发 **30** 子 agent → P0 交卷 `23508e8`
- 核对：verify PASS · `tests/test_rag_qdrant_backend.py` 9 passed

## 00 待做

- **关账**：待 P1（fio/灌库/金样）完成，或维护者指示「按 P0 关账」

## 00 禁止

- 不写业务码、不跑 fio/灌库/压测（交子 agent）
