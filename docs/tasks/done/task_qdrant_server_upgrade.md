# Task：Qdrant server 升级（本机 + 生产 · 对齐 client 1.19）

> **状态**：completed（生产窗口完成 · PR #38 已合入）  
> **类型**：infra / 运维（镜像升级）  
> **上游**：`docs/tasks/done/task_qdrant_migration.md` · 热修 PR #37（`query_points`）  
> **审查对照**：`docs/harness/reviews/task_qdrant_server_upgrade_audit_R1_20260816.md`（20 · **pass**）  
> **分支**：`task/qdrant-server-upgrade`  
> **编排**：00 已签闸 → 30 本机先、再生产 → CLOSE

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `qdrant-server-upgrade` |
| **git_branch** | `task/qdrant-server-upgrade` |
| **test_strategy** | `required` |
| **test_strategy_note** | 既有 `pytest tests/test_rag_qdrant_backend.py`（无新业务逻辑则保持绿）；本机一问：日志无 client/server 版本 `UserWarning`、无 `fallback to pgvector` 暴涨 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `none` |
| **graph_delta** | `none` |
| **graph_delta_note** | 不改一级模块；仅 compose 镜像与文档版本句 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 不改 coding_wiki；运维说明落 cutover / SPEC 版本句 |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,30` |
| **invoke_retention_profile** | `minimal` |
| **thinking_profile** | `shortest` |
| **experience_capture** | `recommended` |
| **orchestration** | 轻量 · 本机 compose 升成功后再动生产 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | 00 签 2026-08-16：目标镜像 **1.19.x** 对齐 client；patch 由 30 查 Docker Hub 钉死 |
| HG-AUDIT-R1 | approved | 30 | 审查 `docs/harness/reviews/task_qdrant_server_upgrade_audit_R1_20260816.md` · 00 代签 |
| HG-GRAPH-MODULES | approved | 30 | 真值 `docs/_tech_graph/l1/01_modules.md`；本 task 不新增一级模块 |

---

## 背景与目标

本机/生产 Qdrant **server v1.13.6**，Python `qdrant-client` **1.19.0**。官方要求主版本一致、次版本差 ≤1，故每次检索打 `UserWarning`。热路径已改 `query_points`（PR #37），警告仍在。

**完成态**：本机与生产 compose 使用同一 **1.19.x** 镜像；检索不再报版本不兼容；PG 仍为向量真源。

---

## 范围

1. 本机：`docker-compose.yml` 的 `qdrant.image`：`v1.13.6` → **`qdrant/qdrant:v1.19.x`**（30 钉具体 patch tag）  
2. 生产：`../ops-desk-workspace/deploy/docker-compose.prod.yml` 同步同一 tag（跨仓，可另 PR）  
3. 文档版本句：`docs/spec/qdrant-migration/SPEC-qdrant-migration_v1.md` 引擎行；`docs/deployment/qdrant-cutover.md` / narrative 中 1.13.6 过时句  
4. **本机先行**：`compose pull && up -d qdrant` → 探活 6333 → 一问（LC Evidence 或 Chat）  
5. 若旧 volume 无法被 1.19 读取：删/换 volume，按 `docs/deployment/qdrant-cutover.md` 重建 collection + bulk_upsert + reconcile（PG 真源）  
6. 生产：维护窗口内同样 pull/up；必要时 Flag 暂切 `RAG_VECTOR_BACKEND=pgvector` 再灌库切回

---

## 非范围

- 改 `qdrant-client` 依赖范围或回退 `search` API  
- 改 `RAG_VECTOR_BACKEND` 默认值 / 切流策略  
- 改 HNSW 参数、payload 契约、hydrate SQL  
- 80 万 P95 / 扩容  
- 前端、LCEL 业务逻辑

---

## 依赖

| 项 | 说明 |
|---|---|
| 本机 compose | `docker-compose.yml` |
| 生产 compose | `../ops-desk-workspace/deploy/docker-compose.prod.yml` |
| 切流手册 | `docs/deployment/qdrant-cutover.md` |
| SPEC | `docs/spec/qdrant-migration/SPEC-qdrant-migration_v1.md`（引擎版本句） |
| 检索器 | `app/ops/rag/retrievers/qdrant_retriever.py`（已 `query_points`，本波原则上不改） |
| 编码规范 | `docs/standards/CODING_BACKEND_L2_v1_zh.md` |

---

## 实施步骤（建议 · 30）

1. 查 Docker Hub：钉 `qdrant/qdrant:v1.19.<patch>`（与 client 1.19 同 minor）。  
2. 改本机 compose → `up -d qdrant`。起不来则重建 volume + cutover 灌库。  
3. 本机一问：无版本 warning；无 `attribute 'search'`；无异常 fallback。  
4. `pytest tests/test_rag_qdrant_backend.py`。  
5. 同步生产 compose + SPEC/cutover 版本句 → 生产窗口执行。  
6. 30/40 invoke 留档。

---

## 验收标准

- [x] 本机与生产 compose 的 `qdrant.image` 为同一 `v1.19.x` tag（不再是 `v1.13.6`）→ **`qdrant/qdrant:v1.19.0`**
- [x] SPEC 引擎行已改为该 tag
- [x] `pytest tests/test_rag_qdrant_backend.py` 绿（9 passed）
- [x] 本机一问：日志**无** `incompatible with server version 1.13.6`
- [x] 本机一问：日志**无** `object has no attribute 'search'`
- [x] （人工）生产 up 后探活 6333；切流环境无持续 `qdrant fallback to pgvector` 暴涨 · 2026-08-16：1.19.0 healthy；删 `deploy_qdrant_data` 后从 PG 灌 8574；reconcile pass；`printenv`=`qdrant`
- [x] `git diff` **不改** `app/ops/chat/graph.py`

---

## failure_paths

| 触发 | 行为 | 可重试 | 用户可见 |
|---|---|---|---|
| 1.19 读不了 1.13 volume | 停服务；重建 collection + 从 PG upsert；reconcile | Y | 短暂 dense 不可用；可 Flag 切 pgvector |
| 生产 pull/up 失败 | 回滚镜像 tag 或切 `RAG_VECTOR_BACKEND=pgvector` | Y | Chat 仍可用（PG dense） |
| 灌库后 reconcile 失败 | 重跑 export/upsert；查 `ops_qdrant_dlq` | Y | 召回质量下降直至对账过 |
| 误改 client / 检索器 API | 验收打回 | N | PR 拒绝 |

---

## 给执行帽必读

1. 本 task  
2. `docker-compose.yml` · `../ops-desk-workspace/deploy/docker-compose.prod.yml`  
3. `docs/deployment/qdrant-cutover.md` · **`docs/deployment/qdrant-server-upgrade.md`（生产升镜像窗口）**  
4. `docs/spec/qdrant-migration/SPEC-qdrant-migration_v1.md` 引擎表  
5. `app/ops/rag/retrievers/qdrant_retriever.py`  
6. `docs/harness/invokes/by-task/qdrant-query-points/invoke_20260816_30_40_qdrant-query-points.md`

---

## 思考轮

### 思考轮控制

| 字段 | 值 |
|---|---|
| **actual_last_round** | R5 |
| **early_stop** | yes |
| **early_stop_reason** | 范围=镜像对齐 client 1.19；存储不兼容走既有 cutover 重建 |
| **residual_risks** | 1.13→1.19 on-disk 格式可能不兼容，生产须可回切 pgvector |

### R0
消掉 client 1.19 vs server 1.13.6 的兼容性警告，并让本机/生产 server 与现网 client 同 minor。

### R1
范围=compose 镜像 + 文档版本句 + 本机先于生产；非范围=改 client、改 graph、改切流默认。

### R2
升 server 到 1.19.x，不降 client。

### R3
volume 不兼容则从 PG 重建；生产失败切 pgvector。

### R4
pytest 绿 + 本机一问无 warning；生产探活为人工项。

### R5
闸已签；30 须本机先于生产，patch tag 钉 Docker Hub 真实存在的 `v1.19.x`。

---

### 自检结论

> 10-task 起草自检 · 闸已签（00 签收 2026-08-16）。

- [x] 验收 / failure_paths / 非范围 / 依赖齐全
- [x] 思考轮 R0–R5 + 控制表已写
- [x] 10-task invoke 已落档
- [x] HG-TASK-DRAFT approved（00 签 2026-08-16）
- [x] HG-AUDIT-R1 approved（R1 pass · 00 代签）
- [x] HG-GRAPH-MODULES approved（D4-a 真值已存在）

---

### 自检结论（执行者）

> 30 · 2026-08-16 · 本机+生产窗口完成 · PR #38 已合入 master

| 命令 / 窗口 | 摘要 |
|---|---|
| 本机 compose 钉 `qdrant/qdrant:v1.19.0` | 旧 volume 不兼容，从 PG 重建 8574 |
| 生产升镜像 | `docs/deployment/qdrant-server-upgrade.md`；reconcile pass；Flag=qdrant |
| pytest `tests/test_rag_qdrant_backend.py` | 随 PR #38 合入 |

---

### KPI

| 项 | 分 |
|---|---|
| Task_KPI% | 100 |

### 经验

- Wiki: n/a
- Qdrant 1.19 **读不了** 1.13 volume；升镜像须删盘从 PG 重建。

## CLOSE

| 项 | 内容 |
|---|---|
| 日期 | 2026-08-17 |
| 定稿 | `qdrant/qdrant:v1.19.0` · PR #38 |
| 归档 | `docs/tasks/done/task_qdrant_server_upgrade.md` |

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-16 | 10-task 首稿：本机+生产升 Qdrant 1.19.x；闸 pending |
| 2026-08-16 | 00 签收 HG-TASK-DRAFT / HG-AUDIT-R1；R1 留痕 |
| 2026-08-16 | 30：钉 v1.19.0；本机 volume 不兼容已从 PG 重建 8574；生产 compose 已改未 up |
| 2026-08-16 | 生产升镜像完整窗口：`docs/deployment/qdrant-server-upgrade.md` |
| 2026-08-16 | 生产窗口完成：1.19.0 · reconcile pass · Flag=qdrant |
| 2026-08-17 | PR #38 已合入；CLOSE 归档 |
