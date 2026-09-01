# 生产：Qdrant server 升级操作指南（v1.13.6 → v1.19.0）

> **日期**：2026-08-16  
> **对照**：本机已升完；生产机 **仍须人工窗口**。GHA 只重建 `api`，**不会**同步 compose、**不会**升 Qdrant 镜像。  
> **切流总册**（首次上架 Qdrant）：[`qdrant-cutover.md`](./qdrant-cutover.md)  
> **钉死镜像**：`qdrant/qdrant:v1.19.0`（对齐 `qdrant-client` 1.19）  
> **写源**：PostgreSQL；Qdrant 只是稠密副本。升镜像失败时读路径可立刻切回 `pgvector`。

---

## 0. 你要做的事（一句话）

先把生产读路径切到 PG（网站还能答）→ 把新 compose scp 上去 → `pull/up` Qdrant → 若旧盘读不了就删 volume 从 PG 重建 → 对账过后再切回 `qdrant`。

**不要** `docker compose down`（会停 `db`/`api`）。**不要**删 `pgdata`。

| 本机（已做完，勿重复） | 生产（本指南） |
|---|---|
| 容器已是 1.19.0 | 仍是 1.13.6，直到你 `up` |
| 旧 volume 已重建，`ops_knowledge`=8574 | 大概率同样读不了 1.13 盘，按 §5 重建 |
| 合成库 `ops_knowledge_scale` 已丢弃 | 生产不要建 scale 库 |

建议窗口：**15–30 分钟**（重建 8574 点本身很快；时间主要在 scp / 探活 / 对账）。

---

## 1. 现网事实

| 项 | 值 |
|---|---|
| SSH | `ssh ops-desk`（`ubuntu@` 生产机；见 narrative） |
| compose | `/opt/ops-desk/deploy/docker-compose.prod.yml` |
| env | `/opt/ops-desk/.env` |
| api 代码 | `/opt/ops-desk/api` |
| 仓内真值 | `ops-desk-workspace/deploy/docker-compose.prod.yml` |
| 现网读 Flag | 切流后已是 `RAG_VECTOR_BACKEND=qdrant` |
| Qdrant 端口 | **不映射公网**；只在 compose 内网 `http://qdrant:6333` |
| 本机 compose 源 | `ops-desk-api/docker-compose.yml`（已是 `v1.19.0`） |

zsh 不要写 `COMPOSE="docker compose ..."` 再 `$COMPOSE ps`（会变成 `command not found: docker`）。下面一律写全命令，或用数组：

```bash
C=(docker compose -f docker-compose.prod.yml --env-file /opt/ops-desk/.env)
"${C[@]}" ps
```

---

## 2. 窗口前检查（本机 + SSH）

### 2.1 本机确认要 scp 的文件

```bash
grep -n 'image: qdrant' \
  /Users/cyning/Desktop/Ops-desk/ops-desk-workspace/deploy/docker-compose.prod.yml
# 期望：image: qdrant/qdrant:v1.19.0
```

该文件目前在 workspace 分支 `task/qdrant-server-upgrade`。**可以先 scp 再合 PR**；合入只是让仓内真值与现网一致。

### 2.2 SSH 上看现状（先记下来，回滚时对照）

```bash
ssh ops-desk
cd /opt/ops-desk/deploy

docker compose -f docker-compose.prod.yml --env-file /opt/ops-desk/.env ps
docker compose -f docker-compose.prod.yml --env-file /opt/ops-desk/.env \
  exec -T api printenv RAG_VECTOR_BACKEND RAG_QDRANT_SHADOW_WRITE QDRANT_URL QDRANT_COLLECTION
curl -fsS http://127.0.0.1:8000/health

docker compose -f docker-compose.prod.yml --env-file /opt/ops-desk/.env \
  exec -T api python -c "import urllib.request; print(urllib.request.urlopen('http://qdrant:6333', timeout=5).read().decode())"
# 升级前期望 version 含 1.13.6
```

确认 PG 点数（重建后应对齐）：

```bash
docker compose -f docker-compose.prod.yml --env-file /opt/ops-desk/.env \
  exec -T db psql -U ops -d opsdesk -c "SELECT count(*) FROM ops_knowledge_chunks;"
```

若 `count=0`：**停止升级**，先查语料（见 narrative「本机 vs 生产语料混淆」），空库灌进 Qdrant 会把检索打空。

---

## 3. 切读到 pgvector（保网站可用）

编辑 `/opt/ops-desk/.env`：

```bash
RAG_VECTOR_BACKEND=pgvector
RAG_QDRANT_SHADOW_WRITE=false
```

影子写先关：升镜像 / 删 volume 期间 Qdrant 不可用，继续影子写只会堆 `ops_qdrant_dlq`。

让 api 读到新 env（不必 `--build`）：

```bash
cd /opt/ops-desk/deploy
docker compose -f docker-compose.prod.yml --env-file /opt/ops-desk/.env \
  up -d --force-recreate api

docker compose -f docker-compose.prod.yml --env-file /opt/ops-desk/.env \
  exec -T api printenv RAG_VECTOR_BACKEND RAG_QDRANT_SHADOW_WRITE
curl -fsS http://127.0.0.1:8000/health
```

期望：`RAG_VECTOR_BACKEND=pgvector`，health `{"status":"ok"}`。  
此时 Chat / LC Evidence 走 PG dense，**可以继续对外**。

任意后续步骤失败：停在这一步即可，网站仍可用。

---

## 4. scp 新 compose → pull / up

**本机**（另开终端，不要在生产机上找这份文件）：

```bash
scp /Users/cyning/Desktop/Ops-desk/ops-desk-workspace/deploy/docker-compose.prod.yml \
  ops-desk:/opt/ops-desk/deploy/docker-compose.prod.yml
```

**生产机**确认 tag 再拉镜像：

```bash
cd /opt/ops-desk/deploy
grep 'image: qdrant' docker-compose.prod.yml
# 必须是 qdrant/qdrant:v1.19.0

docker compose -f docker-compose.prod.yml --env-file /opt/ops-desk/.env pull qdrant
docker compose -f docker-compose.prod.yml --env-file /opt/ops-desk/.env up -d qdrant
```

等健康（约 10–20 秒）：

```bash
docker compose -f docker-compose.prod.yml --env-file /opt/ops-desk/.env ps qdrant
docker compose -f docker-compose.prod.yml --env-file /opt/ops-desk/.env logs --tail 40 qdrant
```

### 4.A 成功：healthy 且日志是 `Version: 1.19.0`，无 Panic

探活：

```bash
docker compose -f docker-compose.prod.yml --env-file /opt/ops-desk/.env \
  exec -T qdrant bash -c 'exec 3<>/dev/tcp/127.0.0.1/6333 && echo tcp_ok'

docker compose -f docker-compose.prod.yml --env-file /opt/ops-desk/.env \
  exec -T api python -c "import urllib.request,json; print(json.loads(urllib.request.urlopen('http://qdrant:6333',timeout=5).read())['version'])"
# 期望：1.19.0
```

点数量（应仍接近 PG count，本机经验是旧盘往往直接崩，不一定走到这里）：

```bash
docker compose -f docker-compose.prod.yml --env-file /opt/ops-desk/.env \
  exec -T api python -c "import urllib.request,json; print(json.loads(urllib.request.urlopen('http://qdrant:6333/collections/ops_knowledge',timeout=5).read()))"
```

若 collection 还在、点数与 PG 一致 → **跳过 §5**，直接 §6。

### 4.B 失败：容器反复重启 / 日志 Panic（本机已发生）

本机原文：加载旧 collection 时 `Failed to (de)serialize from/to json: invalid type: map, expected a sequence`。  
**走 §5**，不要反复 `up`。

---

## 5. 旧 volume 不兼容：删盘 + 从 PG 重建

只动 Qdrant 卷。先看名字再删：

```bash
cd /opt/ops-desk/deploy
docker compose -f docker-compose.prod.yml --env-file /opt/ops-desk/.env stop qdrant
docker compose -f docker-compose.prod.yml --env-file /opt/ops-desk/.env rm -f qdrant

docker volume ls | grep qdrant
# 常见：目录名为 deploy 时是 deploy_qdrant_data；以实际输出为准
# 确认没有 pgdata 字样后再删

docker volume rm deploy_qdrant_data   # ← 换成上一步看到的名字
```

空盘启动：

```bash
docker compose -f docker-compose.prod.yml --env-file /opt/ops-desk/.env up -d qdrant
docker compose -f docker-compose.prod.yml --env-file /opt/ops-desk/.env ps qdrant
docker compose -f docker-compose.prod.yml --env-file /opt/ops-desk/.env logs --tail 20 qdrant
# 期望：Version: 1.19.0，无 Panic，STATUS healthy
```

建 collection + 灌库 + 索引 + 对账（在 **api 容器**内，能连 `db` 与 `qdrant`）：

```bash
cd /opt/ops-desk/deploy

docker compose -f docker-compose.prod.yml --env-file /opt/ops-desk/.env \
  exec -T api python scripts/qdrant_migrate/create_collection.py \
  --url http://qdrant:6333 --name ops_knowledge --recreate

docker compose -f docker-compose.prod.yml --env-file /opt/ops-desk/.env \
  exec -T api python scripts/qdrant_migrate/export_vectors.py \
  --out /tmp/ops_vectors.jsonl

docker compose -f docker-compose.prod.yml --env-file /opt/ops-desk/.env \
  exec -T api python scripts/qdrant_migrate/bulk_upsert.py \
  --url http://qdrant:6333 --in /tmp/ops_vectors.jsonl --wait

docker compose -f docker-compose.prod.yml --env-file /opt/ops-desk/.env \
  exec -T api python scripts/qdrant_migrate/ensure_payload_indexes.py \
  --url http://qdrant:6333 --collection ops_knowledge

docker compose -f docker-compose.prod.yml --env-file /opt/ops-desk/.env \
  exec -T api python scripts/qdrant_migrate/reconcile.py \
  --qdrant-url http://qdrant:6333 --sample 500
```

**对账没绿（missing / extra / mismatch 明显不为 0）→ 不要做 §6。** 保持 `pgvector`，查 export 行数与 `count(*)`。

本机对照：export **8574**、upsert **8574**。生产应对齐现网 `ops_knowledge_chunks` 行数。

找不到脚本：说明服务器 api 代码太旧，先等 GHA 把含 `scripts/qdrant_migrate/` 的 master 部署上去（脚本在迁移 PR #31 已合入，现网应已有）。

---

## 6. 切回 qdrant

对账通过后，编辑 `/opt/ops-desk/.env`：

```bash
RAG_VECTOR_BACKEND=qdrant
RAG_QDRANT_SHADOW_WRITE=true
QDRANT_URL=http://qdrant:6333
QDRANT_COLLECTION=ops_knowledge
```

```bash
cd /opt/ops-desk/deploy
docker compose -f docker-compose.prod.yml --env-file /opt/ops-desk/.env \
  up -d --force-recreate api

docker compose -f docker-compose.prod.yml --env-file /opt/ops-desk/.env \
  exec -T api printenv RAG_VECTOR_BACKEND QDRANT_URL QDRANT_COLLECTION
curl -fsS http://127.0.0.1:8000/health
```

期望：`qdrant` / `http://qdrant:6333` / `ops_knowledge`，health ok。

---

## 7. 窗口后看 15–60 分钟

| 检查 | 通过标准 |
|---|---|
| `ps qdrant` | `v1.19.0` · healthy |
| api `printenv` | `RAG_VECTOR_BACKEND=qdrant` |
| `/health` | ok |
| `logs -f api` | 提问时有 `POST .../lg-rag/stream`（原 `POST .../chat/stream` 已 410 · T6 2026-08-31）或 LC Evidence invoke；**无**持续 `qdrant fallback to pgvector` |
| DLQ | `SELECT status, count(*) FROM ops_qdrant_dlq GROUP BY 1;` 不堆积 |
| 版本警告 | api 日志无 `incompatible with server version 1.13.6` |

成功路径默认不太打 Qdrant INFO，**不能**用「日志里没有 qdrant 字样」当失败。

抽样问答或 LC Evidence 走一问即可。

---

## 8. 随时回滚（读路径）

不回滚镜像也可以先救人：

```bash
# /opt/ops-desk/.env
RAG_VECTOR_BACKEND=pgvector
RAG_QDRANT_SHADOW_WRITE=false

cd /opt/ops-desk/deploy
docker compose -f docker-compose.prod.yml --env-file /opt/ops-desk/.env \
  up -d --force-recreate api
```

若必须把镜像退回 1.13.6：把 compose `image` 改回 `qdrant/qdrant:v1.13.6` 再 `up -d qdrant`。  
**注意**：已经用 1.19 写过的新 volume，1.13 **未必能读**；退镜像前同样可能要重建。优先 Flag 回滚，不要先退镜像。

---

## 9. 禁止事项

- 改 `qdrant-client` 依赖范围，或把检索改回 `search`
- 改 `RAG_VECTOR_BACKEND` 的 compose **默认值**（生产靠 `.env` 显式 `qdrant`）
- 改 HNSW / payload / hydrate
- 生产建 `ops_knowledge_scale`（那是本机 80 万合成盘）
- `docker compose down`、删 `pgdata`
- 对账失败仍切读

---

## 10. 做完后勾哪些账

- task `docs/tasks/active/task_qdrant_server_upgrade.md` 人工项：生产探活 6333、无 fallback 暴涨  
- workspace 仓：compose 变更走 PR 合入 `main`（若你已 scp、仓内未合，补合以免下次被旧文件覆盖）  
- 本仓 api PR：只含本机 compose + 文档；**合入不会升生产 Qdrant**
