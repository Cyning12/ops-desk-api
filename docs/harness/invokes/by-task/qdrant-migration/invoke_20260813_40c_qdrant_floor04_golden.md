# Invoke · 40c · Qdrant dense + CE floor04 金样 · qdrant-migration

| 字段 | 值 |
|------|-----|
| **hat** | 40c（金样：Qdrant dense + Cross-Encoder floor=0.4 / ratio=0.75） |
| **task_slug** | `qdrant-migration` |
| **日期** | 2026-08-13 |
| **分支** | `task/qdrant-migration` |
| **环境** | 本机 Docker · `db` + `qdrant` healthy · 默认 `.env` **未**改 `RAG_VECTOR_BACKEND` |
| **对照** | `reports/r4-R-floor04.yaml`（pgvector 时代 CE floor04） |

## 环境锁死（金样进程）

```bash
export RAG_VECTOR_BACKEND=qdrant
export RAG_RERANK_ENABLED=true
export RAG_RERANK_MIN_SCORE=0.4
export RAG_RERANK_SCORE_RATIO=0.75
export RAG_SECOND_PATH=fts
export RAG_KW_EXPAND=false
export RAG_FTS_CONFIG=simple
export QDRANT_URL=http://127.0.0.1:6333
# RAG_GRADER_MODEL 未设；代码默认 qwen3.7-flash（与 floor04 一致）
```

## Dense 真走 Qdrant（确认）

- 进程环境 `RAG_VECTOR_BACKEND=qdrant`；`vector_backend() == qdrant`
- collection `ops_knowledge` points_count=8574 · status green
- `.env` 无 `RAG_VECTOR_BACKEND` 持久改动（仅本进程 export）
- 命令：`.venv/bin/python evals/golden/run_eval.py --out reports/r4-qdrant-R-floor04.yaml --stability 0`

## 报告头核对

| 字段 | 本棒 |
|------|------|
| `rerank_enabled` | true |
| `rerank_min_score` | 0.4 |
| `rerank_score_ratio` | 0.75 |
| `rerank_model` | BAAI/bge-reranker-v2-m3 |
| `grader` | qwen3.7-flash |
| `corpus` | ops_knowledge_chunks(N=8574) |
| `partial` | false · completed=73 |

## 对照摘要 vs r4-R-floor04

| 项 | r4-R-floor04（基线） | r4-qdrant-R-floor04（本棒） |
|----|---------------------|----------------------------|
| 报告 | `reports/r4-R-floor04.yaml` | `reports/r4-qdrant-R-floor04.yaml` |
| 稠密路 | pgvector（基线时代） | **qdrant** + PG hydrate |
| grader | qwen3.7-flash | qwen3.7-flash（一致） |
| CE | floor=0.4 / ratio=0.75 | 同左（一致） |
| **pass** | **57/73** | **47/73**（劣） |
| **negative_refuse** | **11/11** | **10/11**（劣） |
| zh2zh recall@5 | 18/20 | 18/20（并列） |
| zh2en recall@5 | 19/26 | 19/26（并列） |
| en2en recall@5 | 14/16 | **15/16**（优 1） |
| stability | （基线见报告） | 跳过（`--stability 0`） |
| FTS | simple（生产默认） | simple（锁死） |

### 结论

- 召回三象限：zh2zh / zh2en **并列**；en2en **略优**。
- 总 pass / negative **劣于** floor04 基线 → **禁止据此默认切流**。
- grader 字符串与基线一致（flash），可比性优于 40b 的 max→flash 降级场景；仍不关账。
- eval 进程 exit_code=1（金样未全绿，属预期；报告已完整落盘）。

## 未做

- 未改 `.env` 默认 `RAG_VECTOR_BACKEND`
- 未关账
- 未跑 80 万压测
