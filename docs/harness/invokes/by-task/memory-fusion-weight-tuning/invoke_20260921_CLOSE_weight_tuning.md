# invoke · CLOSE · memory-fusion-weight-tuning

| 项 | 内容 |
|----|------|
| **时间** | 2026-09-21 |
| **帽** | 00（delegate-only · 全程未改实现码 · 30/40 子 Agent · worktree 作业） |

## 闭环摘要

维护者令循环任务 → task（循环协议四停则 + 防过拟合三条）→ 20 R1 终轮零阻塞 → 三闸 00 代录 · VERIFY PASS → 30 循环执行：R1 异常停（叠放 base 缺 tz 修复 · 协议异常分支实战验证）→ 00 restack（077f500 · merge origin/master · 冲突解）→ R2/R3 连续 top3=1.0 **达标停止** → 定稿 90d/0.3/0.8（top1=0.9167）→ 40 PASS（8/8 · 藏丑核查通过）→ 归档 CLOSE。

## 交接（维护者动作）

1. 合并链：#146（eval runner + live 报告）→ 本 task PR（先指 `task/memory-golden-eval` · #146 合后改指 master）
2. **开向量开关**（裁决依据已齐 · 报告头部四门槛连读）：
   - `MEMORY_FACTS_ENABLED=true` + `MEMORY_FACTS_VECTOR_RECALL_ENABLED=true` + 重启进程
   - `MEMORY_FACTS_EXTRACT_ENABLED` **保持关**（precision 0.21 / 噪声 0.36 远未达标 · 抽取校准 task 另开）
3. 建议同步跑 `alembic upgrade head`（embedding 列）· 存量事实无向量（回填 = 占位 SPEC `memory-embedding-backfill`）
4. 下一候选：抽取 prompt/key 校准（live 数据：precision 0.18–0.26 · supersede 0.2–0.4 · key 漂移规模化）· 或建议序 2 `llm-layer-hardening`（另一窗口已在进行）
