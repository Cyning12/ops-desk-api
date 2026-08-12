# RAG C 臂：bge-m3 稀疏向量（第二路）对照实验

对照实验：影子列 `sparse_embedding` + `RAG_SECOND_PATH=sparse`。  
**不碰生产主库写路径**；**不删** A 臂入口（`Dockerfile.pg-zhparser` / `zhparser_arm_a/` / `RAG_FTS_CONFIG`）。  
dense `embedding` 列语义不变。

> 全量 8574 重嵌与 `reports/r4-C.yaml` 全量评测依赖本机算力 / grader 额度；脚本与开关已交付，实跑可由维护者执行。

## 0. 依赖（隔离 venv，避免弄坏现有 torch）

根 `.venv` 已有 `sentence-transformers` / torch。FlagEmbedding 若冲突，**另建隔离环境**只做重嵌：

```bash
# 方案 A：尝试装进根 venv（不冲突则可）
uv pip install -r experiments/rag_compare/sparse_arm_c/requirements.txt

# 方案 B：隔离（推荐 · 冲突时）
python3 -m venv .venv-sparse
.venv-sparse/bin/pip install -U pip
.venv-sparse/bin/pip install -r experiments/rag_compare/sparse_arm_c/requirements.txt
.venv-sparse/bin/pip install 'sqlalchemy>=2' 'psycopg[binary]>=3.1'
# 重嵌时用 .venv-sparse/bin/python；评测仍用根 .venv（评测时 query sparse 也会懒加载 FlagEmbedding）
```

评测进程若走 `RAG_SECOND_PATH=sparse`，根 `.venv` 也需要能 `import FlagEmbedding`（或同样用隔离环境跑 `run_eval.py`）。

## 1. 加影子列 + 索引（本地 / 影子库）

```bash
# 示例：主库本地（请确认 DSN；生产禁止）
psql "$DATABASE_URL_PSYCOPG" -v ON_ERROR_STOP=1 \
  -f experiments/rag_compare/sparse_arm_c/add_sparse_embedding.sql

# 或 docker exec 指向影子容器
docker exec -i <pg-container> psql -U ops -d opsdesk \
  < experiments/rag_compare/sparse_arm_c/add_sparse_embedding.sql
```

期望：`CREATE EXTENSION`（可能 already）· `ALTER TABLE` · `CREATE INDEX`。

自检：

```sql
SELECT count(*) AS total,
       count(sparse_embedding) AS filled,
       count(*) FILTER (WHERE sparse_embedding IS NULL) AS nulls
FROM ops_knowledge_chunks;
```

## 2. 稀疏重嵌（断点续写 · 目标 8574）

```bash
export DATABASE_URL="postgresql+asyncpg://ops:ops_password@localhost:5432/opsdesk"

# 冒烟（少量行）
.venv-sparse/bin/python experiments/rag_compare/sparse_arm_c/embed_sparse.py --limit 32 --batch-size 8

# 全量（可反复跑；已写非 NULL 行会跳过）
.venv-sparse/bin/python experiments/rag_compare/sparse_arm_c/embed_sparse.py --batch-size 16
```

只 `UPDATE sparse_embedding`；dense 不动。中断后续跑同一命令即可。

验收：`filled = 8574` 且 `nulls = 0`（与库内总块数一致）。

## 3. 评测 env（r4-C）

第二路走 sparse；**关闭** glossary 展开以隔离变量；逐条落盘：

```bash
export DATABASE_URL="postgresql+asyncpg://ops:ops_password@localhost:5432/opsdesk"
export RAG_SECOND_PATH=sparse
export RAG_KW_EXPAND=false
# 勿依赖 RAG_FTS_CONFIG（本臂不走 FTS）；生产默认仍 fts+simple

.venv/bin/python evals/golden/run_eval.py --out reports/r4-C.yaml --stability 0

# 额度耗尽 / 中断后续跑
.venv/bin/python evals/golden/run_eval.py --out reports/r4-C.yaml --resume --stability 0
```

对照：`reports/r4-2.yaml` / `r4-A.yaml` / `r4-D.yaml`。主看 **zh2zh** recall@5 与 **sparse 路非空命中率**（日志/报告中的 `keyword_hits`）。

## 4. 运行时开关摘要

| env | 值 | 含义 |
|---|---|---|
| `RAG_SECOND_PATH` | `fts`（默认） | 现网关键词路（含 `RAG_FTS_CONFIG` / `RAG_KW_EXPAND`） |
| `RAG_SECOND_PATH` | `sparse` | 第二路 `sparse_embedding <#> query_sparse` |
| `RAG_KW_EXPAND` | 评测 C 时 `false` | 与 D 臂隔离 |
| `RAG_FTS_CONFIG` | 默认 `simple` | A 臂仍可用 `chinese`；C 首表不参与 |

## 5. 可选 alembic

本臂**优先**实验 SQL，避免误伤生产升级。若需 revision，须标注「实验可选、默认不强制 upgrade」——当前不落强制 migration。

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-12 | 初版：加列 SQL · 断点重嵌 · 评测 env |
