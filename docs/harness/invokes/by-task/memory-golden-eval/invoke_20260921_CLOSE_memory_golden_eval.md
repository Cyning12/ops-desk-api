# invoke · CLOSE · memory-golden-eval

| 项 | 内容 |
|----|------|
| **时间** | 2026-09-21 |
| **帽** | 00（delegate-only · 全程未改实现码 · 30/40 均派子 Agent） |

## 闭环摘要

| 环节 | 结果 |
|---|---|
| 前置 | PR #145（P1）已合并 `5deb430` · 用户令 M1 优先 + 9 占位 SPEC |
| 10-spec | SPEC-memory-golden-eval_v1 signed · R0–R5 |
| 10-task | E1–E5 竖切 · lint PASS · 零生产语义改动契约 |
| 20-task-audit | R1 终轮零阻塞（graph=none 裁定合理） |
| 闸 | 三闸 approved（维护者令 · 00 代录）· VERIFY PASS |
| 30 | 金样 50 + 双模式 runner + 27 组扫参 + 10 CI 测试 · 零 app diff · live 烟跑交两真实信号 |
| 40 | 独立核验 PASS（10/10 · 偏差#1 接受 · 藏丑核验通过） |

## 交接（维护者动作）

1. 合并本 task PR（CI 须绿）
2. **真跑裁决**（SPEC §8 复制区）：`run_eval.py --backend live` 全量 → 对照 D5 四门槛
3. 已知烟跑信号预判：key 漂移（真 LLM 倾向 project.* 前缀 vs 金样 key 约定）与复述 top1 压力 → 大概率先出 **prompt/金样 key 校准 task**，再议开 `MEMORY_FACTS_VECTOR_RECALL_ENABLED`；`MEMORY_FACTS_EXTRACT_ENABLED` 暂缓
4. 下一候选：建议序 2 = `llm-layer-hardening` 占位 SPEC（接续指引在 SPEC 内）
