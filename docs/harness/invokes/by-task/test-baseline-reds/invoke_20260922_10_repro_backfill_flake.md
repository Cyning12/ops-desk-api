# invoke · 10-task · D3 backfill flaky 复现

> hat=10 · 2026-09-22

## 命令与结果

| 命令 | 结果 |
|------|------|
| `pytest tests/test_memory_embedding_backfill.py -q`（单文件） | 15 passed |
| 单测 `test_reconcile_mismatch_marks_failed` **连跑 20 次** | **8 failed / 12 passed（≈40% 翻车率）** |

实测翻车率与「随机 uuid 落水位前/后各 ≈50%」的理论模型吻合（嵌入维度等次要时序使实际略低于 50%）。

注：仓内未装 pytest-randomly/xdist；「随机序 flaky」的本质不是测试序，而是用例内部并发注入的随机 uuid。
