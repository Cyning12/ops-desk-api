# invoke · 00 · memory-extract-calibration · 闸落录 + 派 30

| 项 | 内容 |
|----|------|
| **时间** | 2026-09-22 |
| **帽** | 00（delegate-only · 本窗未改实现码） |
| **维护者令** | 「已合并，继续回到刚才的150结束后的任务」（循环模式延续） |

## 前置确认

- PR #146 merged（`07b0eba`）→ master 已含：评测资产 + 调参定稿 90d/0.3/0.8 + tz 修复 + 全部记忆轨演进（画像/摘要/隔离/删除/回填/LLM 硬化）
- 抽取 prompt 已资产化（`app/ops/prompts/assets/memory.extract.system.md` v1 · PR #155）——校准循环的可改面就位
- base 直取 origin/master（无叠放 · 吸取 restack 教训）
- 已知环境干扰：用户 .env 开了 MEMORY_* 两开关 → 本地 pytest 需摘旗（5 条假设默认关的测试会挂 · CI 无 .env 不受影响）——已写进 30 环境节；**测试隔离是真实卫生债**（conftest 应隔离 MEMORY_* 旗标 · 值得小 task · 记入候选）

## 闸落录（00 代录）

| gate | 落录 |
|---|---|
| HG-AUDIT-R1 | approved（20 R1 终轮零阻塞） |
| HG-GRAPH-MODULES | approved · `memory` 行备注（校准循环 · 不新增模块） |

VERIFY: PASS · lint PASS

## 派发

- 已派子 Agent：**30**（校准循环：达标=连续 2 轮 precision≥0.9+noise≤0.1+supersede=1.0 且哨兵 top3≥0.8 · 上限 8 轮 · version bump 归因 · 防泄题 · 金样一字不改）
- 待派：**40** → 00 回写 → CLOSE → PR → 维护者裁决 `MEMORY_FACTS_EXTRACT_ENABLED`
