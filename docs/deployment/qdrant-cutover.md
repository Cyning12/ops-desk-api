# 生产：Qdrant 切流操作清单（对照现网）

> **整体过程纪要（选型→评测→本机→生产）**：[`qdrant-migration-narrative.md`](./qdrant-migration-narrative.md)

> **和 `01-environment-setup.md` 的关系**  
> 那份是**第一次**买机器 / 装 Docker / 配域名 / 起 db+api。你已经做完了，**不要重做**。  
> 本文件是：**现网已在跑**（`/opt/ops-desk/deploy` + GHA 发版 api）之后，再加一层 Qdrant 读索引。

> **现网目录（与 `gha-api-deploy.md` 一致）**  
> - 代码：`/opt/ops-desk/api`  
> - compose：`/opt/ops-desk/deploy/docker-compose.prod.yml`  
> - 环境变量：`/opt/ops-desk/.env`  
> - 常用：`docker compose -f /opt/ops-desk/deploy/docker-compose.prod.yml --env-file /opt/ops-desk/.env …`

> **写源仍是 PostgreSQL**；Qdrant 只存向量副本，回答内容仍从 PG hydrate。  
> **FTS**：生产用 `simple`；**不要**设 `RAG_FTS_CONFIG=chinese`。

---

## 先建立直觉（第 2 步以后在干什么）

| 步骤 | 一句话 | 类比 |
|---|---|---|
| 1 | 服务器上多跑一个 Qdrant 容器 | 像当初多跑一个 `db` |
| 2 | 建空「书架」+ DLQ 表 | collection = 空索引；DLQ = 双写失败记事本 |
| 3 | 把 PG 里已有向量**抄一份**进 Qdrant | 全量搬家；没抄完不能切读 |
| 4 | 新写入一边写 PG、一边异步写 Qdrant | 影子写，避免切读后落后 |
| 5 | 改 env，让 api **读** Qdrant | 真正切流 |
| 6 | 看健康 / 日志 / DLQ | 验收 |

回滚（任意步失败）：

```bash
# 编辑 /opt/ops-desk/.env
RAG_VECTOR_BACKEND=pgvector
RAG_QDRANT_SHADOW_WRITE=false

cd /opt/ops-desk/deploy
docker compose -f docker-compose.prod.yml --env-file /opt/ops-desk/.env up -d --build api
```

---

## 1. 一次性：把 Qdrant 加进现网 compose

仓内真值：`ops-desk-workspace/deploy/docker-compose.prod.yml`（已含 `qdrant` 服务）。  
GHA **不会**自动同步该文件，需拷到服务器：

```bash
# 在你本机（有 workspace 仓的机器）
scp /Users/cyning/Desktop/Ops-desk/ops-desk-workspace/deploy/docker-compose.prod.yml \
  ubuntu@<生产机>:/opt/ops-desk/deploy/docker-compose.prod.yml
```

然后在生产机：

```bash
cd /opt/ops-desk/deploy
docker compose -f docker-compose.prod.yml --env-file /opt/ops-desk/.env up -d qdrant
docker compose -f docker-compose.prod.yml --env-file /opt/ops-desk/.env ps
# 验收（未映射宿主机端口，用 exec）
docker compose -f docker-compose.prod.yml --env-file /opt/ops-desk/.env \
  exec qdrant bash -c 'exec 3<>/dev/tcp/127.0.0.1/6333 && echo ok'
```

切流前 **不要**在 `.env` 里设 `RAG_VECTOR_BACKEND=qdrant`（compose 默认仍 `pgvector`）。  
`api` 经 compose 网络访问 `http://qdrant:6333`。

### 1.1 镜像升级（v1.13.6 → v1.19.0）

完整窗口（先切 `pgvector` → scp compose → `pull/up` → 旧盘不兼容则重建 → 再切回 `qdrant`）：

**[`qdrant-server-upgrade.md`](./qdrant-server-upgrade.md)**

GHA **不会**升 Qdrant。本机已升完；生产必须人工执行该指南。

---

## 2. 一次性：空架子（表 + collection）

**在哪跑**：SSH 上生产机后，用 **api 容器**跑（它已有代码、依赖、能连 `db`；合入含脚本的版本后）。

```bash
cd /opt/ops-desk/deploy
COMPOSE="docker compose -f docker-compose.prod.yml --env-file /opt/ops-desk/.env"

# 2.1 DLQ 表：重启/重建 api 时 command 里已有 alembic upgrade head
# 若刚合入含 migration 的 master，执行一次：
$COMPOSE up -d --build api
# 验收：
$COMPOSE exec db psql -U ops -d opsdesk -c '\d ops_qdrant_dlq'

# 2.2 建空 collection（默认 dim=1024，与现网 embedding 一致）
$COMPOSE exec api python scripts/qdrant_migrate/create_collection.py \
  --url http://qdrant:6333 --name ops_knowledge

# 2.3 payload 过滤字段索引
$COMPOSE exec api python scripts/qdrant_migrate/ensure_payload_indexes.py \
  --url http://qdrant:6333 --collection ops_knowledge
```

到这里：**Qdrant 是空的**，生产问答仍走 pgvector（只要 env 还没切）。

---

## 3. 全量灌库（把现有知识抄进 Qdrant）

仍在生产机、仍用 api 容器：

```bash
COMPOSE="docker compose -f docker-compose.prod.yml --env-file /opt/ops-desk/.env"

# 3.1 从 PG 导出（只要 id + embedding + 过滤字段，不要正文）
$COMPOSE exec api python scripts/qdrant_migrate/export_vectors.py \
  --out /tmp/ops_vectors.jsonl

# 3.2 写入 Qdrant
$COMPOSE exec api python scripts/qdrant_migrate/bulk_upsert.py \
  --url http://qdrant:6333 --in /tmp/ops_vectors.jsonl

# 3.3 对账：PG 有的点，Qdrant 都要有（注意参数是 --qdrant-url，不是 --url）
$COMPOSE exec api python scripts/qdrant_migrate/reconcile.py \
  --qdrant-url http://qdrant:6333
# 通过标准：missing / extra / mismatch ≈ 0

# 3.4 可选：延迟冒烟（默认约 200 次查询，会打生产 PG + Qdrant；不是长时间压测）
# 灌库为 0 / 对账未过时不要跑
$COMPOSE exec api python scripts/qdrant_migrate/bench_hnsw.py \
  --qdrant-url http://qdrant:6333
```

**对账没绿 → 不要做第 5 步切读。**

---

## 4. 影子写窗口（可选但推荐）

目的：切读前先让「新入库」同时进 Qdrant，避免全量抄完后又落后。

在 `/opt/ops-desk/.env` 增加/修改：

```bash
RAG_QDRANT_SHADOW_WRITE=true
RAG_VECTOR_BACKEND=pgvector          # 这一阶段读仍用 PG
QDRANT_URL=http://qdrant:6333
QDRANT_COLLECTION=ops_knowledge
```

```bash
$COMPOSE up -d --build api
$COMPOSE exec db psql -U ops -d opsdesk -c \
  "SELECT status, count(*) FROM ops_qdrant_dlq GROUP BY 1;"
# pending/failed 应接近 0
```

---

## 5. 切读（真正改 Flag）

`/opt/ops-desk/.env`：

```bash
RAG_VECTOR_BACKEND=qdrant
RAG_QDRANT_SHADOW_WRITE=true
QDRANT_URL=http://qdrant:6333
QDRANT_COLLECTION=ops_knowledge
RAG_FTS_CONFIG=simple
RAG_KW_EXPAND=false
RAG_RERANK_ENABLED=true
RAG_RERANK_MIN_SCORE=0.4
RAG_RERANK_SCORE_RATIO=0.75
RAG_GRADER_PROMPT=v1
```

并确认 `docker-compose.prod.yml` 的 `api.environment` **把这些变量传进容器**（仅写 `.env` 但 compose 未引用 → api 看不到）。

```bash
$COMPOSE up -d --build api
curl -s http://127.0.0.1:8000/health
```

合入 master 后 GHA 只会重建 api：**不会自动起 qdrant、也不会改 `.env`**。基础设施与 Flag 仍靠本清单手工（或你后续改 deploy 脚本）。

---

## 6. 切流后看 30–60 分钟

| 检查 | 通过 |
|---|---|
| `/health` | ok |
| api 日志 | 无持续 `qdrant fallback to pgvector` 暴涨 |
| `ops_qdrant_dlq` | 不堆积 |
| 抽样问答 | 主观正常 |

---

## 7. FTS / chinese（与切流正交）

| 项 | 结论 |
|---|---|
| `RAG_FTS_CONFIG` | 机制保留；生产 **`simple`** |
| `chinese` | **不上生产**（需 zhparser；实验入口在 `experiments/rag_compare/zhparser_arm_a/`） |

---

## 8. 常见卡点

| 现象 | 处理 |
|---|---|
| `exec api` 找不到脚本 | 先合入/部署含 `scripts/qdrant_migrate/` 的 api |
| 连不上 `http://qdrant:6333` | qdrant 未 up，或不在同一 compose 网络 |
| hydrate 空 | 对账 missing；point id 必须等于 chunk id |
| 想立刻恢复 | §0 回滚：`RAG_VECTOR_BACKEND=pgvector` |
| 1.19 读不了 1.13 volume | 见 [`qdrant-server-upgrade.md`](./qdrant-server-upgrade.md) §5；先切 pgvector 再删卷重建 |
