# Invoke · 40 / P1 实测 · qdrant-migration

| 字段 | 值 |
|------|-----|
| **hat** | 40（P1 实测执行） |
| **task_slug** | `qdrant-migration` |
| **日期** | 2026-08-13 |
| **分支** | `task/qdrant-migration` |
| **环境** | 本机 Docker Desktop · `docker compose` db + qdrant |
| **默认读路径** | 未改 `.env`；`RAG_VECTOR_BACKEND` 仍默认 **pgvector**（金样进程内临时 `qdrant` 失败见下） |

## 闸与范围

- 本棒：运维脚本 + 冒烟实测；**不改业务码**
- 语料规模：**N=8574**（现网全量）；**未做**合成扩样至 80 万 → **未达峰值门禁**
- Qdrant 镜像：`qdrant/qdrant:v1.13.6` · container `ops-desk-api-qdrant-1` · `mem_limit` 3.5g

## 命令与退出码

| 步骤 | 命令摘要 | exit |
|------|----------|------|
| compose | `docker compose up -d db qdrant` | 0（healthy） |
| migrate | `alembic upgrade head`（含 `20260813_qdrant_dlq`） | 0 |
| corpus | `SELECT count(*) FROM ops_knowledge_chunks` → **8574** | 0 |
| fio | `brew install fio`；`FIO_TARGET_DIR=reports/qdrant_migrate FIO_RUNTIME=30 bash scripts/qdrant_migrate/fio_randread_gate.sh` | **0 PASS** |
| create | `.venv/bin/python scripts/qdrant_migrate/create_collection.py --url http://localhost:6333 --name ops_knowledge --dim 1024 --metric Cosine --on-disk-vectors --on-disk-hnsw --recreate` | 0 |
| export | `python scripts/qdrant_migrate/export_vectors.py --out /tmp/ops_knowledge_points.jsonl` | 0（8574 lines） |
| upsert | `.venv/bin/python scripts/qdrant_migrate/bulk_upsert.py --wait --rss-sample-sec 10 --rss-container ops-desk-api-qdrant-1 --in /tmp/ops_knowledge_points.jsonl` | 0 |
| indexes | `.venv/bin/python scripts/qdrant_migrate/ensure_payload_indexes.py` | 0 |
| reconcile | `.venv/bin/python scripts/qdrant_migrate/reconcile.py --sample 8574 --out reports/qdrant_migrate/reconcile_p1_20260813.yaml` | **0 pass** |
| bench | `.venv/bin/python scripts/qdrant_migrate/bench_hnsw.py --baseline pgvector --outs reports/qdrant_bench.yaml`（无 `--skip-live`，n_queries=50） | **0 measured** |
| 金样 | `RAG_VECTOR_BACKEND=qdrant RAG_RERANK_ENABLED=false … evals/golden/run_eval.py --limit 5 --stability 0 --out reports/r4-qdrant-p1-smoke.yaml` | **1 跳过全量** |

## 关键指标

| 项 | 值 |
|----|-----|
| **N** | 8574（≠ 800000） |
| **fio** | IOPS≈139462.65 · p95_ms=0.0（解析/APFS 缓存偏乐观）· status=pass · 记录 `reports/qdrant_migrate/fio_gate_20260813T092147Z.yaml` |
| **fio 说明** | 目标目录为本机 `reports/qdrant_migrate`（APFS）；Docker volume 挂载点在 VM 内（`/var/lib/docker/volumes/...`）主机不可直写，**非生产盘型证明** |
| **RSS 构建峰值** | **286.6 MiB**（upsert 采样）≪ 3.8 GiB |
| **稳态 RSS（stats）** | ≈500 MiB / 3.5 GiB ≪ 3.2 GiB |
| **reconcile** | count_diff=0 · max_l_inf=0.0 · mean_topk_overlap=1.0 · sample=8574 |
| **bench P95** | pgvector **2.56 ms** · qdrant **14.62 ms**（预算 150 ms） |
| **80 万峰值** | **未跑**（诚实：未达峰值门禁） |
| **金样 vs r4-2** | **未完成**：本地 compose `db` 无 `zhparser`/`chinese` FTS（`RAG_FTS_CONFIG=chinese` → hybrid KW 路 `UndefinedObjectError`）；非 API 额度问题。冒烟 partial 报告：`reports/r4-qdrant-p1-smoke.yaml` |

## 报告路径

- `reports/qdrant_migrate/fio_gate_20260813T092147Z.yaml`
- `reports/qdrant_migrate/reconcile_p1_20260813.yaml`
- `reports/qdrant_bench.yaml`
- `reports/r4-qdrant-p1-smoke.yaml`（失败/partial）

## 建议（给 00）

- **不宜按「峰值+金样齐全」关账**：缺 80 万灌库、缺可比金样、fio 非生产盘。
- **可记现网规模 P1 冒烟绿**：迁移链路 / 全量对账 / bench 双臂 / 构建 RSS 在 N=8574 下通过；默认 Flag 仍 pgvector。
- 金样需在具备 `chinese` FTS 的库（或对照影子库）上重跑后再议切流。

## 下一棒

生产盘 fio；可选合成扩样；金样环境修好后 vs `reports/r4-2.yaml`；00 关账决策。
