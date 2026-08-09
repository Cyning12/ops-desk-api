# Task：Ops sync sender 迁移（GHA 改 POST /api/ops/admin/sync）

> **状态**：active（draft · 待人审）  
> **类型**：技术债 / 基础设施（数据链断尾根治）  
> **关联**：`app/ops/admin/sync.py`（接收端 2026-07-17 已实现）· 旧仓 `ai-ink-brain-api-python/.github/workflows/ops_sync_kimi_code.yml` · workspace `docs/02-backend-analysis/00-current-state.md` §8.1  
> **合入**：走 PR（禁直推 master）

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `ops-sync-sender-migration` |
| **test_strategy** | `required` |
| **test_strategy_note** | SyncPayload 字段对齐测试；端到端手动触发一次 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `none` |
| **graph_delta** | `none` |
| **wiki_delta** | `n/a` |
| **review_hat** | `20` |
| **required_invoke_hats** | `30` |
| **orchestration** | 单 task |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | pending | 22-R1 | 维护者确认 sender 方案与 secrets 变更范围 |

---

## 背景与目标

新 PG 数据链断尾（2026-08-08 查证，见 workspace `00-current-state.md` §8.1）：

- 日更 GHA 在**旧仓** `ai-ink-brain-api-python`，直写 Supabase；
- 新 API 只有接收端 `POST /api/ops/admin/sync`，**无发送方**；
- 新库靠一次性快照 `import_from_supabase.py` 续命，水位定格。

本 task 让 sender 改道：**GHA 抓取产物对齐 SyncPayload → POST `/api/ops/admin/sync`**，新 PG 获得自己的持续数据源，脱离旧仓 + Supabase 依赖。

**完成态**：

- [ ] sender 方案人定稿：迁移旧仓 `api/ops/sync/` runner 进新体系，还是旧仓脚本加 POST 适配层（二选一，人拍板）
- [ ] SyncPayload 与旧 runner 产出字段 diff 清单（含 repo / issues / PRs / sync_run / scan / graph）
- [ ] GHA secrets 变更清单（API base URL、maintainer 凭证下发与轮换方式）
- [ ] 手动触发一次端到端：GHA → endpoint → 新 PG 新 issue 落库可见
- [ ] 旧 Supabase 直写路径标注 deprecated（保留可回滚）
- [ ] 生产同验

**不做**：

- 不碰 RAG 管线（本 task 只修数据链）
- 不下线 Supabase / 旧仓 GHA（仅标 deprecated）
- 评论抓取扩展（RAG 契约 v2 候选，另议）

---

## 失败路径

| 触发 | 行为 | 可重试 |
|---|---|---|
| endpoint 5xx / 网络失败 | GHA 失败告警，下次 cron 重试（upsert 幂等） | Y |
| payload 字段漂移 | 接收端 422 → 修 schema 对齐 | Y |
| maintainer 凭证泄漏 | 凭证只走 GHA secrets；轮换即失效 | — |

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-08 | 初版（AI 起草 · 待 HG-TASK-DRAFT 人审）：源自 RAG 前置查证发现的数据链断尾 |
