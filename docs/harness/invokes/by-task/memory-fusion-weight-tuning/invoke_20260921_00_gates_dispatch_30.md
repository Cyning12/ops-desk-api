# invoke · 00 · memory-fusion-weight-tuning · 闸落录 + 派 30

| 项 | 内容 |
|----|------|
| **时间** | 2026-09-21 |
| **帽** | 00（delegate-only · 本窗未改实现码） |
| **维护者令** | 「同意安排 · task 改为循环任务 · 改一次跑一次 · 超过 3 次变化不大或达到目标位置」 |

## 作业形态

worktree `../ops-desk-api-wtune`（分支 `task/memory-fusion-weight-tuning` · base 叠放 `task/memory-golden-eval` 因 runner 在未合的 #146）· 主检出留给 llm-layer-hardening 零触碰 · 本 task PR 将先指 `task/memory-golden-eval`，#146 合并后改指 master。

## 闸落录（00 代录）

| gate | 落录 |
|---|---|
| HG-AUDIT-R1 | approved（20 R1 终轮零阻塞） |
| HG-GRAPH-MODULES | approved · `memory` 行备注（调参循环定稿 · 仅三常量值） |

- VERIFY: PASS · lint PASS

## 循环协议（随 30 prompt 钉死）

首轮=(90d/0.3/0.8) · 达标=连续 2 轮 top3≥0.8 · 收敛=连续 3 轮 |Δtop3|≤0.05 且无上升趋势 · 上限 8 轮 · errors>0 即停 · 确认轮必须全量 50 · 逐轮留痕不藏丑 · 每轮清场核验。

## 派发

- 已派子 Agent：**30**（循环执行 + 定稿 + 测试期望维护）
- 待派：**40**（重点：藏丑核查 · 全量确认轮真实性 · 测试期望更新依据）→ 00 回写 → CLOSE → PR → 维护者裁决开向量开关
