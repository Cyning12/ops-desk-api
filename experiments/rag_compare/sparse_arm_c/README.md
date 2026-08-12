# RAG C 臂：bge-m3 稀疏向量（第二路）对照实验

对照实验：影子列 `sparse_embedding` + `RAG_SECOND_PATH=sparse`。  
**不碰生产主库写路径**；**不删** A 臂入口（`Dockerfile.pg-zhparser` / `zhparser_arm_a/` / `RAG_FTS_CONFIG`）。  
dense `embedding` 列语义不变。

> 全量 8574 重嵌与 `reports/r4-C.yaml` 依赖本机算力 / grader 额度。  
> 本地栈：`ops-desk-api-db-1` → 宿主机 **5432**（主库）；`pg-zhparser-shadow` → **5433**（仅 A 臂，C 勿用）。

---

## 命令速查（每行用途）

按顺序执行。以下为 **2026-08-12 本机已验证** 路径。

### 0) 建隔离 Python（解决 pyenv 缺 `_lzma`）

| 命令 | 用途 |
|------|------|
| `rm -rf .venv-sparse` | 删掉旧隔离环境（若曾用 pyenv 建过且报 `_lzma`） |
| `/opt/homebrew/bin/python3 -m venv .venv-sparse` | 用 **Homebrew Python** 新建 venv（自带 lzma；勿用 pyenv `python3`） |
| `.venv-sparse/bin/pip install -U pip` | 升级 pip，避免装 FlagEmbedding 时解析失败 |
| `.venv-sparse/bin/pip install -r experiments/rag_compare/sparse_arm_c/requirements.txt` | 安装 FlagEmbedding（拉 bge-m3 sparse 编码能力） |
| `.venv-sparse/bin/pip install 'sqlalchemy>=2' 'psycopg[binary]>=3.1'` | 重嵌脚本写库用的同步 ORM/驱动 |
| `.venv-sparse/bin/python -c "import lzma; from FlagEmbedding import BGEM3FlagModel; print('ok')"` | 自检：lzma + FlagEmbedding 可导入 |

```bash
rm -rf .venv-sparse
/opt/homebrew/bin/python3 -m venv .venv-sparse
.venv-sparse/bin/pip install -U pip
.venv-sparse/bin/pip install -r experiments/rag_compare/sparse_arm_c/requirements.txt
.venv-sparse/bin/pip install 'sqlalchemy>=2' 'psycopg[binary]>=3.1'
.venv-sparse/bin/python -c "import lzma; from FlagEmbedding import BGEM3FlagModel; print('ok')"
```

> 若坚持用根 `.venv`：`uv pip install -r …/requirements.txt` —— 但本机 pyenv 3.11.15 **无 `_lzma`**，FlagEmbedding→datasets 会挂；C 重嵌请用上面 brew 路径。

### 1) 确认容器 / 加影子列

| 命令 | 用途 |
|------|------|
| `docker ps --format '{{.Names}}\t{{.Ports}}' \| grep 5432` | 查出主库容器全名与端口（期望 `ops-desk-api-db-1` · `5432`） |
| `docker exec -i ops-desk-api-db-1 psql -U ops -d opsdesk < …/add_sparse_embedding.sql` | 在**主库**执行：建 `sparsevec` 扩展（若无）· 加 `sparse_embedding` 列 · 建索引 |
| （勿用）`pg-zhparser-shadow` | A 臂 chinese FTS 影子库（5433）；**不要**往里面加 C 列做本臂评测 |

```bash
docker ps --format '{{.Names}}\t{{.Ports}}' | grep 5432

docker exec -i ops-desk-api-db-1 psql -U ops -d opsdesk \
  < experiments/rag_compare/sparse_arm_c/add_sparse_embedding.sql
```

期望输出含：`CREATE EXTENSION`（或 already）· `ALTER TABLE` · `CREATE INDEX`。

列灌满前自检（可选）：

```bash
# 用途：看 total / filled / nulls（重嵌前 filled 应为 0）
docker exec -i ops-desk-api-db-1 psql -U ops -d opsdesk -c \
  "SELECT count(*) AS total,
          count(sparse_embedding) AS filled,
          count(*) FILTER (WHERE sparse_embedding IS NULL) AS nulls
   FROM ops_knowledge_chunks;"
```

### 2) 稀疏重嵌

| 命令 | 用途 |
|------|------|
| `export DATABASE_URL="postgresql+asyncpg://ops:ops_password@localhost:5432/opsdesk"` | 指向宿主机主库 5432；脚本内会把 asyncpg DSN 转成 psycopg 写库 |
| `…/embed_sparse.py --limit 32 --batch-size 8` | **冒烟**：只编 32 行，验证模型下载/编码/写库；首次会下 bge-m3（约数 GB） |
| `…/embed_sparse.py --batch-size 16` | **全量**：对仍为 NULL 的行断点续写，目标 filled=8574 |
| （中断后）再跑同一全量命令 | 已非 NULL 行会跳过，从剩余 NULL 继续 |

```bash
export DATABASE_URL="postgresql+asyncpg://ops:ops_password@localhost:5432/opsdesk"

# 冒烟（已通过示例：wrote 32/32 · filled=32）
.venv-sparse/bin/python experiments/rag_compare/sparse_arm_c/embed_sparse.py \
  --limit 32 --batch-size 8

# 全量（下一步；可反复跑）
.venv-sparse/bin/python experiments/rag_compare/sparse_arm_c/embed_sparse.py \
  --batch-size 16
```

验收：脚本结束 `filled=8574` 且 `nulls=0`（或与库内实际总块数一致）。只写 `sparse_embedding`，**不动** dense。

### 3) 跑 r4-C 评测

> **不要用「裸」`.venv-sparse` 直接跑 `run_eval.py`**：它缺 `pydantic` 等 app 依赖（会报 `No module named 'pydantic'`）。  
> 重嵌用 sparse venv；评测需要 **app 全依赖 + FlagEmbedding**（且 Python 须带 `_lzma`）。

| 命令 | 用途 |
|------|------|
| `.venv-sparse/bin/pip install -r requirements.txt` | 把项目运行依赖补进 sparse venv（一次即可；含 pydantic/asyncpg 等） |
| `export DATABASE_URL=…5432/opsdesk` | 评测读主库（须已灌满 sparse 列） |
| `export RAG_SECOND_PATH=sparse` | 第二路改走 `sparse_embedding` |
| `export RAG_KW_EXPAND=false` | 关掉 glossary，与 D 臂隔离 |
| `.venv-sparse/bin/python evals/golden/run_eval.py --out reports/r4-C.yaml --stability 0` | 全量金样；逐条落盘；跳过稳定性抽查 |
| `… --resume --stability 0` | 额度耗尽/中断后续跑 |

```bash
# 补齐 app 依赖（只需一次；若已装过可跳过）
.venv-sparse/bin/pip install -r requirements.txt

export DATABASE_URL="postgresql+asyncpg://ops:ops_password@localhost:5432/opsdesk"
export RAG_SECOND_PATH=sparse
export RAG_KW_EXPAND=false

.venv-sparse/bin/python evals/golden/run_eval.py \
  --out reports/r4-C.yaml --stability 0

# 断点续跑
.venv-sparse/bin/python evals/golden/run_eval.py \
  --out reports/r4-C.yaml --resume --stability 0
```

对照：`reports/r4-2.yaml` / `r4-A.yaml` / `r4-D.yaml`。  
主看 **zh2zh** recall@5 增量，以及报告里第二路命中（`keyword_hits` 在 sparse 模式下表示 sparse 路命中）。

> 勿用根 `.venv` 跑 C 评测：本机 pyenv 无 `_lzma`，`import FlagEmbedding` 会挂。

### 4) 判读（人工，非命令）

见 `docs/tasks/active/task_rag_sparse_arm_c.md`：

- zh2zh 相对 r4-2 **≥ +10pp**（或双象限明显优于 A）→ 采 C  
- **+5～8pp** → 缓上生产，入口保留  
- **< +5pp** → 维持 dense + glossary  

---

## 运行时开关摘要

| env | 值 | 含义 |
|---|---|---|
| `RAG_SECOND_PATH` | `fts`（默认） | 现网关键词路（含 `RAG_FTS_CONFIG` / `RAG_KW_EXPAND`） |
| `RAG_SECOND_PATH` | `sparse` | 第二路 `sparse_embedding <#> query_sparse` |
| `RAG_KW_EXPAND` | 评测 C 时 `false` | 与 D 臂隔离 |
| `RAG_FTS_CONFIG` | 默认 `simple` | A 臂仍可用 `chinese`；C 首表不参与 |

## 容器对照

| 名称 | 端口 | C 臂？ | 说明 |
|------|------|--------|------|
| `ops-desk-api-db-1` | 5432 | **是** | 主库：加列 + 重嵌 + 评测 |
| `pg-zhparser-shadow` | 5433 | 否 | 仅 A 臂 zhparser |
| `ops-desk-api-api-1` | 8000 | 否 | API，与本实验无关 |

## 可选 alembic

本臂**优先**实验 SQL，避免误伤生产升级。当前不落强制 migration。

## 已知坑

| 现象 | 原因 | 处理 |
|------|------|------|
| `No module named '_lzma'` | pyenv Python 未链 xz | 用 `/opt/homebrew/bin/python3 -m venv .venv-sparse` |
| `zsh: no such file … .venv-sparse/bin/python` | 尚未创建 venv | 先跑 §0 |
| `No module named 'pydantic'` | 用裸 `.venv-sparse` 跑了 `run_eval.py` | `.venv-sparse/bin/pip install -r requirements.txt` 后再评测 |

## 修订

| 日期 | 说明 |
|------|------|
| 2026-08-12 | 初版：加列 SQL · 断点重嵌 · 评测 env |
| 2026-08-12 | 落盘「每行命令用途」；brew Python / db-1 / 已知坑（本机实跑） |
