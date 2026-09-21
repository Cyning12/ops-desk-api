# invoke · 40 · memory-fuse-tz-fix · 独立核验

| 项 | 内容 |
|----|------|
| **时间** | 2026-09-21 |
| **帽** | 40（子 Agent 独立核验 · 未复信 30） |
| **结论** | **40 PASS**（A–G 全过 · 8/8 验收映射 · 零退回） |

## 关键证据

- diff 面仅声明 3 文件 · models/alembic/conftest 零 diff · 主检出零码痕
- `_as_utc` 语义亲读：naive→UTC 原样归一 · 半衰公式逐字未变
- datetime 扫描独立复核无遗漏（7 类点位）
- 四象限 18 条全绿 · naive≡UTC 逐位相等 + +08:00 偏移两语义钉死断言
- 真 PG（timestamptz 实核）aware 场景复跑：recall_with_vector 全路径不抛 · 清场残留 0
