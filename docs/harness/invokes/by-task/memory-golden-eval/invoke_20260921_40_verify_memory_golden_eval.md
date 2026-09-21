# invoke · 40 · memory-golden-eval · 独立核验

| 项 | 内容 |
|----|------|
| **时间** | 2026-09-21 |
| **帽** | 40（子 Agent 独立核验 · 未复信 30 报告） |
| **结论** | **40 PASS**（A–I 九项全过 · 10/10 验收映射 · 零退回） |

## 关键证据

- 零 diff 硬项：`git diff --stat -- app/ evals/golden/ tests/` 空输出
- 金样 50 条亲读：四类下限全超 · 负样本真双形态（闸可拒 7 / prompt 级 7）· 复述真改写
- fake 两跑逐字节一致（亲跑复验）；罐头抽取真过闸不绕过
- live 缺 key 亲跑 exit 2 显式失败；清场 tenant 级 DELETE 偏差**接受**（WHERE 严格限 memory-eval · 实测零残留零误伤）
- 扫参运行时覆盖/恢复等价有测试；27 组齐；recommended 诚实路径在（全低→null）
- 藏丑核验通过：key 漂移（supersede_accuracy=0.0）与 top1 压力（paraphrase_top1=0.0）均如实记录

## 已知未测项

live 全量真跑（维护者复制区）· 扫参 null 分支无强制单测 · 3 条既有环境失败根因（无关）
