# invoke · CLOSE · memory-facts-p1

| 项 | 内容 |
|----|------|
| **时间** | 2026-09-21 |
| **帽** | 00（delegate-only · 全程未改实现码 · 30/40 均派子 Agent） |

## 闭环摘要

| 环节 | 结果 |
|---|---|
| 前置 | PR #144（P0）维护者合并 `39f6863` · P1 分支 base master |
| 10-spec | SPEC-memory-facts-p1_v1 · HG-SPEC-SIGNOFF=approved（维护者「签收」） |
| 10-task | task 落稿 V0–V4 · R0–R5 全轮 · lint PASS（P0 B1 教训预置内化） |
| 20-task-audit | R1 即终轮 · 零阻塞签收 |
| 闸 | 三闸 approved（维护者令 · 00 代录）· 图谱 memory 行 P1 备注 + 人签记录 |
| 30 | V0–V4 交付（embedding 列 · 向量融合召回 · 离线抽取 · 红线 22 新测） |
| 40 | 独立核验 PASS（11/11 · conftest 偏差裁定接受） |

## 交接

- 分支 `task/memory-facts-p1` → commit + PR（base master）；合并前 CI 须绿
- P1 两开关默认关（`MEMORY_FACTS_VECTOR_RECALL_ENABLED` / `MEMORY_FACTS_EXTRACT_ENABLED`）——生产开启前建议先跑金样评估抽取精度与融合权重
- 后续候选（均另 SPEC/task）：既有行 embedding 回填 · 画像记忆（kind=preference）· 金样迭代调权
