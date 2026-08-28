# Task Audit R1：ops-sync-sender-migration

> **结论**：内容 **pass** · 建议代签 HG-TASK-DRAFT + HG-AUDIT-R1  
> 日期：2026-08-28 · hat 00（维护者令开工 sync · 迁移旧 runner · 00 不实现）

| 项 | 结论 |
|---|---|
| 方案二选一 | **迁移旧 runner 进本仓**；否决旧仓脚本+POST 适配。与「新 PG 自主数据源」一致 |
| 写库边界 | sender 只 POST SyncPayload；不拷 `store.py` / 不直连 PG — 钉死 |
| 机读鉴权 | 仅 sync POST 的 Bearer；cookie 保留；空 token 禁用 Bearer — 必要且最小 |
| 增量 | 48h overlap，不扩表 — 避免本波 Alembic |
| scan/graph | 可选 skip 不挡 GHA — 与旧 cron 兼容 |
| 生产同验 | 不挡 30 CLOSE — 合理（secrets 在维护者侧） |
| 图谱 | 仅 G-L1 admin 备注 + flow 节点；不增一级模块 |
| 混改 | 禁 RAG / Eval / capability — 清晰 |

无内容阻塞。可 GATE_VERIFY → 派 30。00 不得改 `app/`/`tests/`。

| 2026-08-28 | R1 pass · 00 代签 |
