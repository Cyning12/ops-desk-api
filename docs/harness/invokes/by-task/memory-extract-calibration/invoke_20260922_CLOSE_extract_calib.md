# invoke · CLOSE · memory-extract-calibration

| 项 | 内容 |
|----|------|
| **时间** | 2026-09-22 |
| **帽** | 00（delegate-only · 全程未改实现码 · 30/40 子 Agent · worktree 作业） |

## 闭环摘要

维护者令继续（循环模式）→ task（校准循环协议 + version bump 归因 + 防泄题禁令）→ 20 R1 终轮零阻塞 → 三闸 00 代录 → 30 循环 5 轮（v1→v4）→ 40 R1 FAIL（泄题纪律实战生效）→ 整改 → R4/R5 连续两轮四门槛全达（0.96/0.0714/1.0/top3 1.0）→ 40 R2 PASS → 归档 CLOSE。

## 交接（维护者动作）

1. 合并本 PR（base master · CI 须绿）
2. **三个开关可全开**（裁决依据齐）：
   - `MEMORY_FACTS_ENABLED=true`（P0 总开关）
   - `MEMORY_FACTS_VECTOR_RECALL_ENABLED=true`（调参定稿 90d/0.3/0.8 · top3 连续达标）
   - `MEMORY_FACTS_EXTRACT_ENABLED=true`（v4 校准达标 · 注意每 run 一次离线抽取调用成本）
   - 重启进程生效；观测 memory_facts_injected / memory_extract_candidates / *_degraded
3. 已知残余：NG09 闸诱导陷阱（噪声预算内容忍 · 收紧需闸级手段另议）· 测试 .env 旗标隔离（卫生 task 候选）
4. 占位 SPEC 剩 `multi-replica-verify`（另一窗口进行中）· 其余已全部闭环
