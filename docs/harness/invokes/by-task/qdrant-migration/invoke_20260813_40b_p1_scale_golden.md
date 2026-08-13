# Invoke · 40b / P1 续跑 · 金样 + 80 万扩样 · qdrant-migration

| 字段 | 值 |
|------|-----|
| **hat** | 40b（P1 续跑：金样纠偏 + 合成扩样） |
| **task_slug** | `qdrant-migration` |
| **日期** | 2026-08-13 |
| **分支** | `task/qdrant-migration` |
| **环境** | 本机 Docker · `db` + `qdrant` healthy · 默认 `.env` **未**改 `RAG_VECTOR_BACKEND` |
| **背景纠正** | 上一轮金样失败因误用 `RAG_FTS_CONFIG=chinese`（本地无 zhparser）；对照 `reports/r4-2.yaml` 生产默认 **`simple` FTS** |

## 环境锁死（金样进程）

```bash
export RAG_VECTOR_BACKEND=qdrant
export RAG_RERANK_ENABLED=false
export RAG_SECOND_PATH=fts
export RAG_KW_EXPAND=false
export RAG_FTS_CONFIG=simple
export QDRANT_URL=http://127.0.0.1:6333
export RAG_GRADER_MODEL=qwen3.7-flash   # max 额度耗尽后降级；见下
```

## Dense 真走 Qdrant（确认）

- `vector_backend() == qdrant`
- 同 query：`hybrid_recall_detail.semantic` ids **等于** `_semantic_search_qdrant`，与 `_semantic_search_pg` 排序可不同
- httpx 日志：`POST http://127.0.0.1:6333/collections/ops_knowledge/points/search` 200
- 无 qdrant→pgvector fallback 错误日志

## 任务 A · 金样 vs r4-2

| 项 | r4-2（基线） | r4-qdrant-p1（本棒） |
|----|--------------|---------------------|
| 报告 | `reports/r4-2.yaml` | `reports/r4-qdrant-p1.yaml` |
| grader | qwen3.7-**max** | qwen3.7-**flash**（max：bailian `insufficient_quota`） |
| corpus | N=8574 | N=8574（读 `ops_knowledge`；FTS=simple） |
| case 数 | 71 | 73（queries 集已增） |
| **pass** | **52/71** | **51/73** |
| **zh2zh recall@5** | **17/20** | **17/20**（并列） |
| en2en recall@5 | 15/16 | 15/16（并列） |
| zh2en recall@5 | 19/25 | 19/26（同 pass 数；分母+1） |
| **negative_refuse** | **9/10** | **7/11**（劣；grader 模型不可比） |
| stability | 0.75 | 跳过（`--stability 0`） |
| FTS | 生产 simple（推断） | **simple**（锁死） |
| 稠密路 | pgvector（基线时代） | **qdrant** + PG hydrate |

### 结论（金样）

- **召回（en2en / zh2zh）与基线并列**；zh2en pass 数并列、分母略增。
- **总 pass / negative** 略劣于 r4-2，但 grader 为 flash≠max，**不可严格归因于 Qdrant**。
- 按 task「不劣于（允许并列）」：召回维度 **可并列接受**；overall pass/neg **未宣称优于**，且 **禁止据此默认切流**。
- max 额度恢复后建议用 `RAG_GRADER_MODEL=qwen3.7-max` 重跑可比金样。

## 任务 B · 扩样至 ~80 万

| 项 | 值 |
|----|-----|
| 脚本 | `scripts/qdrant_migrate/expand_synthetic.py`（新增） |
| 源 | `ops_knowledge` N=8574 |
| 目标 collection | **`ops_knowledge_scale`**（独立；未写 PG） |
| **最终 N** | **800000** |
| id 策略 | `copy_idx * 1_000_000 + 原 id`；payload 保留 filter 字段 + `synthetic`/`synth_copy` |
| 构建峰值 RSS | **3430.4 MiB** ≤ 3800（过门） |
| 稳态 RSS | **≈1.12–1.23 GiB** ≪ 3.2 GiB（过门） |
| 耗时 | ≈424 s |
| RSS 记录 | `reports/qdrant_migrate/expand_rss.json` · `expand_docker_stats.log` |

### Bench（扩样后）

| 项 | 值 |
|----|-----|
| 报告 | `reports/qdrant_bench_800k.yaml` |
| Qdrant Top-10 P95 | **≈867 ms**（warm 复测 ≈974 ms）**≫ 150 ms → 门禁 FAIL** |
| 对照 8k collection P95 | ≈5.2 ms（同机同容器） |
| pgvector 基线 | **skip**：PG 仍 N=8574，规模不可比 |
| 归因 | on_disk HNSW + Docker volume 磁盘读放大（bench 期 BLOCK I/O 读量级数十 GB） |

### 结论（扩样/压测）

- **规模达标 80 万**；RSS 双门通过。
- **P95 硬门禁未过** → **禁止切流**（与 SPEC/task failure_paths 一致）。
- 本机 Docker/APFS 路径不能证明生产盘 IOPS；生产盘需另测。

## 命令摘要

| 步骤 | 命令 | exit |
|------|------|------|
| 金样 | env 锁死后 `.venv/bin/python evals/golden/run_eval.py --out reports/r4-qdrant-p1.yaml --stability 0` | 0 |
| 扩样 | `.venv/bin/python scripts/qdrant_migrate/expand_synthetic.py --source ops_knowledge --target ops_knowledge_scale --target-n 800000 --recreate --rss-container ops-desk-api-qdrant-1 --rss-log reports/qdrant_migrate/expand_rss.json` | 0 |
| bench | `.venv/bin/python scripts/qdrant_migrate/bench_hnsw.py --collection ops_knowledge_scale --baseline none --outs reports/qdrant_bench_800k.yaml --n-queries 200` | 0 measured |

## 未做 / 阻塞

- 未改生产默认 `RAG_VECTOR_BACKEND`（仍 pgvector）
- **未关账**
- grader max 额度耗尽 → flash 金样与 r4-2 **不完全可比**
- 800k P95 未过门禁 → 切流议案继续否决

## 下一棒（建议 00）

- 额度恢复后 max grader 重跑金样；或接受 flash 并列召回 + 书面记录 neg 不可比
- 生产盘 / 更高 IOPS 上复测 800k P95；本机 Docker 结果作「停迁证据」而非「可切流证据」
