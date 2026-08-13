# RAG A 臂：zhparser 影子库对照实验

对照实验脚本与 SQL；**不碰主库写路径**。实跑镜像构建 / 灌库 / `run_eval.py` 由维护者执行。

> **默认不装宿主机 `psql`**：下列步骤用 `docker exec` / 临时客户端容器。旧库可继续占 **5432**；影子库映射 **5433**，互不冲突。
>
> 下方命令已在本机实跑通过（2026-08-12）：分词探针 OK · COPY **8574** 行 / CSV **119MB** · `add_fts_chinese` OK。

## 1. 构建镜像

```bash
docker build -f Dockerfile.pg-zhparser -t pg-zhparser:15 .
```

> bookworm 源无 `libscws-dev`：Dockerfile 从 GitHub 源码编译 SCWS 1.2.3，再编 zhparser（首次构建较慢，需网络）。

## 2. 起影子容器（5433→5432）

```bash
docker run -d --name pg-zhparser-shadow \
  -e POSTGRES_USER=ops \
  -e POSTGRES_PASSWORD=ops_password \
  -e POSTGRES_DB=opsdesk \
  -p 5433:5432 \
  pg-zhparser:15
```

等就绪：`docker exec pg-zhparser-shadow pg_isready -U ops -d opsdesk`

## 3. 初始化 + 建表（无 fts）

在**仓根**执行：

```bash
docker exec -i pg-zhparser-shadow \
  psql -U ops -d opsdesk \
  < experiments/rag_compare/zhparser_arm_a/init_chinese_fts.sql

docker exec -i pg-zhparser-shadow \
  psql -U ops -d opsdesk \
  < experiments/rag_compare/zhparser_arm_a/schema_chunks_no_fts.sql
```

期望：`CREATE EXTENSION` ×2 · `CREATE TEXT SEARCH CONFIGURATION` · `ALTER TEXT SEARCH CONFIGURATION` · `CREATE TABLE` · `CREATE INDEX` ×2。

分词探针（验收）：

```bash
docker exec -i pg-zhparser-shadow \
  psql -U ops -d opsdesk -c \
  "SELECT to_tsvector('chinese', 'Kimi Code 自动压缩被取消');"
```

实跑示例输出：

```text
             to_tsvector
-------------------------------------
 'code':2 'kimi':1 '压缩':3 '取消':4
(1 row)
```

（中文已切词；`自动` 可能与邻词合并，属 zhparser/scws 正常行为。）

## 4. COPY 灌库（只读主库）

> **勿用变量名 `COLUMNS`**：zsh/bash 会把它改写成终端宽度（如 `86`），导出/导入都会坏掉。一律用 `CHUNK_COLS`。

```bash
CHUNK_COLS="id, repo, source_type, source_id, chunk_index, content, metadata, images, content_hash, embedding, embedded_at"
CSV=/tmp/ops_knowledge_chunks_shadow.csv

# 4a. 从主库导出到宿主机 /tmp（只读）
docker run --rm -v /tmp:/tmp postgres:15 \
  psql "postgresql://ops:ops_password@host.docker.internal:5432/opsdesk" \
  -v ON_ERROR_STOP=1 \
  -c "\\COPY (SELECT ${CHUNK_COLS} FROM ops_knowledge_chunks) TO '${CSV}' WITH CSV HEADER"

# 自检（实跑：COPY 8574 · 约 119MB · 表头为列名）
ls -lh "$CSV"
head -n 1 "$CSV"

# 4b. 拷进影子容器并导入
docker cp "$CSV" pg-zhparser-shadow:/tmp/chunks.csv
docker exec -i pg-zhparser-shadow \
  psql -U ops -d opsdesk -v ON_ERROR_STOP=1 \
  -c "\\COPY ops_knowledge_chunks (${CHUNK_COLS}) FROM '/tmp/chunks.csv' WITH CSV HEADER"

docker exec -i pg-zhparser-shadow \
  psql -U ops -d opsdesk -tAc "SELECT count(*) FROM ops_knowledge_chunks"
# 期望：8574（与主库一致）
```

若已安装宿主机 `psql`（如 `brew install libpq`），也可：

```bash
./experiments/rag_compare/zhparser_arm_a/shadow_copy_chunks.sh
```

（脚本内勿使用 shell 变量名 `COLUMNS`。）

## 5. 加 chinese 生成列 + GIN

```bash
docker exec -i pg-zhparser-shadow \
  psql -U ops -d opsdesk \
  < experiments/rag_compare/zhparser_arm_a/add_fts_chinese.sql
```

期望：`ALTER TABLE` · `CREATE INDEX`。（生成列会扫全表，8574 行通常很快。）

## 6. 评测 env 示例

评测跑在宿主机 Python，DSN 指向 **5433**（无需宿主机 `psql`）：

```bash
export DATABASE_URL="postgresql+asyncpg://ops:ops_password@localhost:5433/opsdesk"
export RAG_FTS_CONFIG=chinese
export RAG_KW_EXPAND=false
# 逐条落盘；额度耗尽 / 中断后可 --resume；稳定性失败也会保留主结果
.venv/bin/python evals/golden/run_eval.py --out reports/r4-A.yaml --stability 0
# 断点续跑（跳过已写入 id）
.venv/bin/python evals/golden/run_eval.py --out reports/r4-A.yaml --resume --stability 0
```

若终端日志还在、报告未写出，可从日志恢复（不调模型）：

```bash
.venv/bin/python evals/golden/run_eval.py \
  --from-log /path/to/terminal.log \
  --out reports/r4-A.yaml \
  --embed-name BAAI/bge-m3 \
  --grader-name qwen3.7-max \
  --corpus-n 8574
```

query 与 index 必须同用 `chinese`（`RAG_FTS_CONFIG` + 生成列），否则关键词路假死。对照基准：`reports/r4-2.yaml` / `reports/r4-D.yaml`；主看 **zh2zh** recall@5 增量。
