# 生产：Qdrant 切流操作清单

> **前提**：PR 合入后代码默认 `RAG_VECTOR_BACKEND=qdrant`。  
> **写源仍是 PostgreSQL**；Qdrant 为 dense 读索引 + PG hydrate。  
> **FTS**：生产用 `RAG_FTS_CONFIG=simple`（或省略）；**不要**设 `chinese`，除非库已装 zhparser 且 index/query 同配置。

---

## 0. 回滚一句话

任一步失败或 P95/金样异常：

```bash
# 生产 .env / compose 环境变量
RAG_VECTOR_BACKEND=pgvector
RAG_QDRANT_SHADOW_WRITE=false   # 可选：先停影子写再回退读
# 然后重建 api：docker compose up -d --build api
```

读路径即时降级也会在 Qdrant 失败时走 pgvector；Flag 回退是硬切。

---

## 1. 一次性：基础设施

| # | 操作 | 验收 |
|---|---|---|
| 1.1 | 部署 Qdrant **v1.13.6**（与 compose 镜像一致；生产可用同 tag） | `curl -s $QDRANT_URL/readyz` → ok |
| 1.2 | 持久化 volume + 资源上限（compose 已有 `mem_limit` 参考） | 重启后 collection 仍在 |
| 1.3 | 网络：api 容器能访问 `QDRANT_URL`（compose 服务名或内网地址） | api 内 `curl`/`wget` 通 |
| 1.4 | （可选）fio 随机读门禁：`scripts/qdrant_migrate/fio_randread_gate.sh` | 按 SPEC 阈值绿 |

---

## 2. 一次性：库表与集合

在 **能连生产 PG + Qdrant** 的机器上（建议跳板 / 维护窗）：

```bash
cd /opt/ops-desk/api   # 或本地已配好 DATABASE_URL / QDRANT_URL 的检出

# 2.1 DLQ 表
alembic upgrade head
# 验收：\d ops_qdrant_dlq

# 2.2 建 collection（HNSW on_disk；维度与现网 embedding 一致）
python scripts/qdrant_migrate/create_collection.py

# 2.3 payload 索引（过滤字段）
python scripts/qdrant_migrate/ensure_payload_indexes.py
```

---

## 3. 全量灌库（现网规模）

```bash
# 3.1 从 PG 导出向量 JSONL
python scripts/qdrant_migrate/export_vectors.py --out /tmp/ops_vectors.jsonl

# 3.2 批量 upsert
python scripts/qdrant_migrate/bulk_upsert.py --in /tmp/ops_vectors.jsonl

# 3.3 对账
python scripts/qdrant_migrate/reconcile.py
# 验收：missing / extra / mismatch 为 0（或在约定阈值内）

# 3.4 （可选）延迟冒烟
python scripts/qdrant_migrate/bench_hnsw.py
```

**不要**在未对账通过时把读切到 qdrant。

---

## 4. 影子写（双写）窗口

在切读之前或同时：

| 变量 | 建议值 | 说明 |
|---|---|---|
| `RAG_QDRANT_SHADOW_WRITE` | `true` | ingest 提交后异步 upsert；失败入 DLQ |
| `RAG_VECTOR_BACKEND` | 可暂 `pgvector` | 先双写、读仍 PG，观察 DLQ |

验收：

```bash
# DLQ 持续接近 0；偶发可重放
SELECT status, count(*) FROM ops_qdrant_dlq GROUP BY 1;
```

---

## 5. 切读（生产 Flag）

在服务器 `/opt/ops-desk/deploy` 的 `.env` / `docker-compose.prod.yml` 中设置：

```bash
RAG_VECTOR_BACKEND=qdrant
RAG_QDRANT_SHADOW_WRITE=true
QDRANT_URL=http://qdrant:6333          # 按实际改
QDRANT_COLLECTION=ops_knowledge
RAG_FTS_CONFIG=simple                  # 或删除该行用代码默认
RAG_KW_EXPAND=false
RAG_RERANK_ENABLED=true
RAG_RERANK_MIN_SCORE=0.4
RAG_RERANK_SCORE_RATIO=0.75
RAG_GRADER_PROMPT=v1                   # 勿用 v2 做生产裁决
```

然后：

```bash
cd /opt/ops-desk/deploy
docker compose -f docker-compose.prod.yml up -d --build api
# 若 qdrant 为 compose 服务：确保 qdrant 已 up
curl -s https://<api-host>/health
```

合入 master 后 GHA 部署会重建 api；**务必确认生产 env 已写入上述变量**（仅靠代码默认不够，若生产仍显式写着 `pgvector`）。

---

## 6. 切流后验收（30–60 min）

| # | 检查 | 通过标准 |
|---|---|---|
| 6.1 | `/health` | ok |
| 6.2 | 日志无持续 `qdrant fallback to pgvector` 暴涨 | fallback 计数平稳 |
| 6.3 | `ops_qdrant_dlq` | pending/failed 不堆积 |
| 6.4 | 抽样问答 / 金样子集 | 与切前主观一致；正式对照用 grader **v1** |
| 6.5 |（可选）`bench_hnsw.py` | 现网规模 P95 可接受（**不**用 80 万合成失败结果宣称峰值就绪） |

---

## 7. 与 FTS / `RAG_FTS_CONFIG` 的关系

| 项 | 结论 |
|---|---|
| 机制 | **未删除**：`RAG_FTS_CONFIG` 仍切换 FTS `regconfig` |
| 生产 | **`simple`**（标准 `pgvector` 镜像无 zhparser） |
| `chinese` / zhparser | **不上生产**（A 臂实验：recall 无增益、运维重）；入口保留在 `experiments/rag_compare/zhparser_arm_a/` |
| 误配后果 | 设 `chinese` 且库无扩展 → 关键词路 `UndefinedObjectError` |

第二路若开 sparse：`RAG_SECOND_PATH=sparse`（与 Qdrant dense 正交；切流清单默认保持 `fts`）。

---

## 8. 常见失败

| 现象 | 处理 |
|---|---|
| CI / 本地缺 `qdrant-client` | `requirements.txt`：`qdrant-client>=1.14.0,<2` |
| hydrate 空结果 | 对账 missing；检查 point id = chunk id |
| 延迟飙高 | 查磁盘 IOPS / `QDRANT_HNSW_EF`；必要时 Flag 回 `pgvector` |
| grader 分数骤降 | 确认 `RAG_GRADER_PROMPT=v1`，勿与 v2 混比 |
