# Qdrant 迁移整体过程纪要（2026-08-13）

> **状态**：生产已切读（2026-08-13 晚）· 前端 chat 未联调验收  
> **范围仓**：`ops-desk-api`（实现）· `ops-desk-workspace`（生产 compose）  
> **主 PR**：[#31](https://github.com/Cyning12/ops-desk-api/pull/31) 能力合入 · [#32](https://github.com/Cyning12/ops-desk-api/pull/32) reconcile 兼容  
> **运维清单（可执行）**：[`qdrant-cutover.md`](./qdrant-cutover.md)  
> **契约真值**：[`SPEC-qdrant-migration_v1.md`](../spec/SPEC-qdrant-migration_v1.md)（v1.1）  
> **Task 关账**：[`task_qdrant_migration.md`](../tasks/done/task_qdrant_migration.md)

本文记录**一次完整迁移**：从选型/SPEC → 实现与评测 → 本机灌库 → 生产切流 → 收尾清分支，供后续 RAG 研发与复盘引用。

---

## 1. 一句话结论

把 dense 向量检索从 **PostgreSQL/pgvector** 解耦到 **Qdrant（HNSW on_disk）**：PG 仍是写真源与正文；Qdrant 只存向量 + 过滤字段；读路径用 Flag 切流，失败即时降级回 pgvector。

| 维度 | 结果 |
|---|---|
| 代码能力 | 已合入 `master`（Flag / hydrate / 影子写 / 迁移脚本 / DLQ） |
| 代码默认读路径 | **`qdrant`**（后期定稿；切流前曾短暂默认 `pgvector`） |
| 现网规模（N=8574） | 对账 pass · bench P95≈14.6ms · 金样 Qdrant+CE floor04+grader v1 **55/73**（对照 pg floor04 **57/73**） |
| 合成 80 万 | RSS 过门 · **P95≈867ms 未过**（&lt;150ms）→ **不宣称峰值就绪** |
| 本机 | 8574 灌库 + reconcile pass · api 健康 · `.env` 已 qdrant |
| 生产 | Qdrant 服务 up · PG/Qdrant 各 8574 · `RAG_VECTOR_BACKEND=qdrant` · health ok |
| 前端 | **未接** chat 联调；生产业务验收待前端 |

---

## 2. 为什么迁

### 痛点

- dense 检索与业务库同机同库，扩展与资源争用绑死。
- 2C4G 目标机上要为向量检索留独立内存/磁盘预算与可回滚 Flag。

### 非目标（明确不做）

- Kafka CDC、GPU ANN、DiskANN、把 FTS/sparse 迁进 Qdrant  
- 反向把 Qdrant 灌回 PG  
- 拆独立 retrieval 微服务（仅文档预留蓝绿）

### 与「第一次生产构建」的关系

[`01-environment-setup.md`](../../../ops-desk-workspace/docs/04-infrastructure/01-environment-setup.md) 是买机/Docker/域名的**从零手册**（已完成）。  
本次是在**已有** `/opt/ops-desk/deploy` + GHA 发版之上，**增量**加 Qdrant 读索引，见 [`qdrant-cutover.md`](./qdrant-cutover.md)。

---

## 3. 架构定稿（SPEC v1.1）

| 决策 | 选择 |
|---|---|
| 引擎版本 | Qdrant **v1.19.0**（`qdrant/qdrant:v1.19.0`；对齐 client 1.19） |
| 索引 | HNSW **`on_disk`**（非 DiskANN、非全内存上架） |
| 向量 | Cosine / **1024**（BGE-M3） |
| Payload | **仅 filter**（`source_type` / `repo` / `source_id` / `chunk_index`） |
| 正文 | **禁止**进 Qdrant；Top-k id → **PG hydrate** → `RetrievedChunk` |
| 写源 | **PostgreSQL**；ingest commit 后 **影子写** Qdrant；失败入 `ops_qdrant_dlq` |
| 读 Flag | `RAG_VECTOR_BACKEND=pgvector\|qdrant`；失败重试 1 次 → **即时**降级 PG（无跨进程 fail_streak） |
| 第二路 | FTS / sparse **仍在 PG**；生产 FTS=`simple`；`chinese`/zhparser **不上生产** |
| 精排 | 生产推荐 CE `0.4/0.75`；金样对照锁 `reports/r4-2.yaml`；grader 用 **v1**（勿用 v2 混比） |

硬门禁（摘要）：fio/IOPS；构建峰值 RSS≤3.8GB；稳态&lt;3.2GB；80 万 Top-10 P95&lt;150ms（**未达成**）；对账 L∞&lt;1e-5 且 Top-5 overlap≥95%。

---

## 4. 时间线（按阶段）

```text
SPEC 起草 / 20-audit / 人签 v1.1
    → 00 出 task（人闸代签授权）
    → 30 实现 P0（backend / retriever / shadow / scripts / alembic / tests）
    → 40 现网规模：migrate / reconcile / bench / 金样
    → 40b 合成 80 万（RSS ok · P95 FAIL）
    → 40c/40d 金样 + CE：发现 grader v2 假性回退 → 定稿 grader v1
    → task 关账 · PR #31
    → CI：qdrant-client 钉版本冲突 → 放宽 ≥1.14 + CI 改 uv pip
    → 代码默认改为 qdrant · 运维文档改写
    → 本机：8574 灌库 + reconcile + 冒烟
    → 生产：compose 加 qdrant → 合入 #31 → 语料导入 → 灌 Qdrant → Flag 切读
    → PR #32 reconcile 兼容 client 1.19 · 分支清零
```

主要合入：

| 节点 | 说明 |
|---|---|
| PR #31 | Qdrant dense 后端全量能力 |
| PR #32 | `reconcile.py` 改用 `query_points`（client 1.19 无 `search`） |
| workspace `main` | `deploy/docker-compose.prod.yml` 增加 qdrant 服务与 RAG env 透传 |

---

## 5. Harness / 协作方式

- Open Folder：`ops-desk-api`  
- 维护者授权：**00 可代签全部人闸**；00 不改业务码，实现交子 agent  
- 闸：`HG-SPEC-SIGNOFF` → `HG-TASK-DRAFT` / `HG-AUDIT-R1` → 30  
- 过程 invoke：`docs/harness/invokes/by-task/qdrant-migration/`  
- 审查：`docs/harness/reviews/spec_qdrant-migration_audit_R1_20260813.md` · `task_qdrant_migration_audit_R1_20260813.md`

---

## 6. 代码与产物清单

### 运行时

| 路径 | 作用 |
|---|---|
| `app/ops/rag/backend.py` | Flag、fallback、collection 名 |
| `app/ops/rag/retrievers/qdrant_retriever.py` | Qdrant 检索 + PG hydrate |
| `app/ops/rag/shadow_write.py` | commit 后影子 upsert/delete、DLQ 入队 |
| `app/ops/rag/retrieve.py` | hybrid 稠密路接 Flag；FTS/`RAG_FTS_CONFIG` |
| `alembic/versions/20260813_qdrant_dlq.py` | `ops_qdrant_dlq` |
| `tests/test_rag_qdrant_backend.py` | Flag / fallback / 影子写单测 |

### 迁移脚本 `scripts/qdrant_migrate/`

`create_collection` · `ensure_payload_indexes` · `export_vectors` · `bulk_upsert` · `reconcile` · `bench_hnsw` · `expand_synthetic` · `fio_randread_gate.sh`

### 配置

- 本地：`docker-compose.yml` 含 qdrant；`.env.example` 默认 qdrant  
- 生产：`ops-desk-workspace/deploy/docker-compose.prod.yml`（GHA **不**自动同步，需 scp）

---

## 7. 评测与门禁结果

| 项 | 报告 / 结论 |
|---|---|
| fio（本机 APFS） | `reports/qdrant_migrate/fio_gate_*.yaml`（非生产盘；仅记录） |
| N=8574 对账 | `reconcile_p1_20260813.yaml` / 本机 `qdrant_reconcile_20260813T125801Z.yaml` · **pass** |
| N=8574 bench | `reports/qdrant_bench.yaml` · P95 **≈14.6ms** |
| 合成 80 万 | `expand_rss.json` · `qdrant_bench_800k.yaml` · RSS ok · **P95 FAIL** |
| 金样无 CE | `reports/r4-qdrant-p1.yaml` |
| 金样 CE floor04 + grader v2 | `r4-qdrant-R-floor04.yaml` · 47/73（**假性回退**：多半因 grader v2） |
| 金样 CE floor04 + grader **v1** | `r4-qdrant-R-floor04-v1.yaml` · **55/73** vs pg **57/73** |
| 本机冒烟 3 条 | `reports/r4-qdrant-local-smoke3.yaml` · 2/3 |

**定稿评测口径**：对照用 grader **v1**；生产推荐 `RAG_RERANK_MIN_SCORE=0.4` · `RAG_RERANK_SCORE_RATIO=0.75`。

---

## 8. 本机验收过程（摘要）

1. 确认语料在本机 Docker：`ops_knowledge_chunks` = **8574**（与生产 initially 空库不同）。  
2. api 容器曾因镜像缺 migration、DB 已 stamp `20260813_qdrant_dlq` 而退出 → `--no-cache` 重建后恢复。  
3. 灌库用本机 Python（不必长期起 api）：export → upsert → reconcile **pass**。  
4. `.env`：`RAG_VECTOR_BACKEND=qdrant` · 影子写 true · CE 0.4/0.75 · grader v1。  
5. `curl /health` ok；金样冒烟 2/3。

---

## 9. 生产切流实录

### 9.1 环境事实

| 项 | 值 |
|---|---|
| SSH | `Host ops-desk` → `ubuntu@82.157.125.39` |
| 目录 | `/opt/ops-desk/deploy` · `/opt/ops-desk/api` · `/opt/ops-desk/.env` |
| 切流前 | issues≈599 · **chunks=0** · 仅 db+api |

### 9.2 实际步骤

1. **scp** 更新后的 `docker-compose.prod.yml` → `up -d qdrant`（healthy）。  
2. 合入 PR #31 → GHA `deploy-api` rsync + 重建 → `ops_qdrant_dlq` 出现。  
3. 建 collection + payload 索引（空架子）。  
4. **语料问题**：生产 `rag_ingest` 需拉 HuggingFace（分词器），服务器 **网络不可达** → 放弃现场嵌入。  
5. **处置**：本机导出 CSV（去掉本地独有 `sparse_embedding` 列）→ ssh 管道上传 → 生产 PG `COPY` **8574** 行。  
6. 生产 api 容器内 export / upsert → 8574；reconcile 初版因 client 1.19 无 `search` 失败 → 热修 `query_points` 后 **pass**（overlap≈0.99）。  
7. `/opt/ops-desk/.env` 写入 `RAG_VECTOR_BACKEND=qdrant` 等 → recreate api → `printenv` 确认 · health ok。  
8. PR #32 合入固化 reconcile；workspace 推送 compose；分支清零。

### 9.3 切流后核验命令

    cd /opt/ops-desk/deploy
    C="docker compose -f docker-compose.prod.yml --env-file /opt/ops-desk/.env"
    $C exec -T api printenv RAG_VECTOR_BACKEND QDRANT_URL
    curl -s http://127.0.0.1:8000/health
    # 期望：qdrant / http://qdrant:6333 / {"status":"ok"}

业务验收（待前端）：网站提问时 `logs -f api` 应出现 `POST .../chat/stream`（2026-08-31 T6 起为 `POST .../lg-rag/stream`；chat/stream 已 410），且**无**刷屏 `qdrant fallback to pgvector`。  
说明：Qdrant **成功路径默认不打 INFO**，不能只靠「没有 qdrant 字样」判断。

### 9.4 回滚

    # /opt/ops-desk/.env
    RAG_VECTOR_BACKEND=pgvector
    RAG_QDRANT_SHADOW_WRITE=false
    # 然后 recreate api

---

## 10. 踩坑清单（可复用）

| 坑 | 现象 | 处理 |
|---|---|---|
| 本机 vs 生产语料混淆 | 生产 export **0** | 先 `count(*)`；本机 8574、生产曾 0 |
| zsh `$COMPOSE="docker compose"` | `command not found: docker compose` | 用数组 `COMPOSE=(docker compose)` 或直接写命令 |
| CI `qdrant-client<1.14` | uv 跨版本解析失败 | `>=1.14,<2`；CI 改 **Python 3.11 + uv pip**（不 `uv sync`） |
| client 1.19 vs server 1.13.6（已收敛） | 曾 Warning / `search` 缺失 | 热路径 `query_points`（PR #37）；server 升 **v1.19.0** |
| api 镜像旧 / alembic stamp 新 | `Can't locate revision 20260813_qdrant_dlq` | `build --no-cache api` |
| 生产 ingest 拉 HF | Network unreachable | 拷贝已嵌入语料或配镜像/离线 tokenizer |
| `RAG_FTS_CONFIG=chinese` | 无 zhparser 则 KW 路炸 | 生产只用 **simple**；A 臂实验不上生产 |
| grader v2 | 金样假性大回退 | 生产/对照用 **v1** |
| GHA 不部署 compose | 服务器无 qdrant 服务 | 手动 scp workspace prod compose |
| 仅见 `/health` 日志 | 未打到 chat | 前端未接或未提问；属探活正常 |

---

## 11. 与 FTS / chinese 的关系

- **机制保留**：`RAG_FTS_CONFIG` 仍切换 regconfig。  
- **生产**：`simple`。  
- **chinese / zhparser**：A 臂实验 recall 无增益 → **不上生产**；入口在 `experiments/rag_compare/zhparser_arm_a/`。  
- 与 Qdrant dense **正交**（第二路仍在 PG）。

---

## 12. 现状快照（文档落盘时）

| 环境 | 读路径 | 语料 | 备注 |
|---|---|---|---|
| 本机 Docker | qdrant | 8574 | 开发/金样主战场 |
| 生产 | qdrant | 8574（自本机 CSV 导入） | 非现场重嵌入；与生产 issues 水位未必同源演进 |
| 影子写 | 生产 true | — | 新 ingest 双写；生产现场 ST/HF 仍受限 |

已知技术债：

1. 生产语料来源应改为「生产 issues/PR/docs 现场 ingest」（需解决 HF/镜像或 ApiEmbedder 分词依赖）。  
2. client/server 次版本差已收敛：compose 钉 **v1.19.0**（task `qdrant-server-upgrade`）。  
3. 80 万 P95 未过 → 峰值容量不作 SLA 承诺。  
4. DLQ cron 重放器非本波交付。  
5. 前端 chat 联调验收未做。

---

## 13. 文档与报告索引

| 类型 | 路径 |
|---|---|
| SPEC | `docs/spec/SPEC-qdrant-migration_v1.md` |
| Task 关账 | `docs/tasks/done/task_qdrant_migration.md` |
| 切流操作 | `docs/deployment/qdrant-cutover.md` |
| 生产升镜像 | `docs/deployment/qdrant-server-upgrade.md` |
| GHA 发版 | `docs/deployment/gha-api-deploy.md` |
| 本纪要 | `docs/deployment/qdrant-migration-narrative.md` |
| Invokes | `docs/harness/invokes/by-task/qdrant-migration/` |
| 图谱 | `docs/_tech_graph/l1/01_modules.md` |
| 评测报告 | `reports/qdrant_*` · `reports/r4-qdrant_*` · `reports/qdrant_migrate/` |

---

## 14. 后续 RAG 研发衔接建议

切流已落地，下一波宜**新开 task**（勿在无闸的 `master` 直改），候选方向例如：

- 生产现场 ingest 通路（HF/镜像/API 分词）与水位日更（`ops-sync-sender-migration` 等相关）  
- 观测：成功路径也打结构化日志（backend / latency / fallback）便于无前端时验收  
- 峰值容量（若业务需要）单独立项，不以本次 80 万 FAIL 冒充通过  

---

## 15. 修订记录

| 日期 | 说明 |
|---|---|
| 2026-08-14 | 首版：汇总 SPEC→生产切流全流程、踩坑与索引 |
| 2026-08-16 | 引擎版本句改为 v1.19.0；client/server 差记为已收敛 |
