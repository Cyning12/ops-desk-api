# Invoke · 40d · Qdrant + CE floor04 + grader prompt v1 公平重跑 · qdrant-migration

| 字段 | 值 |
|------|-----|
| **hat** | 40d（公平重跑：消除 40c 报告混入 `grader_prompt: v2`） |
| **task_slug** | `qdrant-migration` |
| **日期** | 2026-08-13 |
| **分支** | `task/qdrant-migration` |
| **环境** | 本机 Docker · `db` + `qdrant` healthy · 默认 `.env` **未**改 `RAG_VECTOR_BACKEND` |
| **对照** | `reports/r4-R-floor04.yaml`（pgvector+floor04）· `reports/r4-qdrant-R-floor04.yaml`（40c · grader v2） |

## 动机

40c 报告 `r4-qdrant-R-floor04.yaml` summary 含 `grader_prompt: v2`，与 `r4-R-floor04` 时期默认 v1 **不可比**。本棒进程内锁死 `RAG_GRADER_PROMPT=v1`，其余 CE/FTS/Qdrant 与 floor04 对齐。

## 环境锁死（金样进程 · 不改 .env 文件）

```bash
export RAG_VECTOR_BACKEND=qdrant
export RAG_RERANK_ENABLED=true
export RAG_RERANK_MIN_SCORE=0.4
export RAG_RERANK_SCORE_RATIO=0.75
export RAG_SECOND_PATH=fts
export RAG_KW_EXPAND=false
export RAG_FTS_CONFIG=simple
export QDRANT_URL=http://127.0.0.1:6333
export RAG_GRADER_PROMPT=v1
export RAG_GRADER_MODEL=qwen3.7-flash
```

命令：`.venv/bin/python evals/golden/run_eval.py --out reports/r4-qdrant-R-floor04-v1.yaml --stability 0`

## 报告头核对

| 字段 | 本棒 |
|------|------|
| `rerank_enabled` | true |
| `rerank_min_score` | 0.4 |
| `rerank_score_ratio` | 0.75 |
| `rerank_model` | BAAI/bge-reranker-v2-m3 |
| `grader` | qwen3.7-flash |
| `grader_prompt` | **v1** |
| `corpus` | ops_knowledge_chunks(N=8574) |
| `partial` | false · completed=73 |

## 对照摘要

| 项 | r4-R-floor04（pg） | r4-qdrant-R-floor04（40c·v2） | r4-qdrant-R-floor04-v1（本棒） |
|----|-------------------|------------------------------|-------------------------------|
| 稠密路 | pgvector | qdrant | qdrant |
| grader_prompt | （未记；时代默认 v1） | **v2** | **v1** |
| CE | 0.4 / 0.75 | 同左 | 同左 |
| **pass** | **57/73** | **47/73** | **55/73** |
| **negative_refuse** | **11/11** | **10/11** | **11/11** |
| zh2zh recall@5 | 18/20 | 18/20 | 18/20 |
| zh2en recall@5 | 19/26 | 19/26 | 19/26 |
| en2en recall@5 | 14/16 | 15/16 | 15/16 |

### 差分（短统计）

- vs 40c（v2）：pass **+8**（47→55）；neg **+1**（10→11）；v2FAIL→v1PASS：G04/G15/G25/G29/G44/G48/G58/G63；v2PASS→v1FAIL：0
- identical top5 v2↔v1：**73/73**；其中 verdict flip **8**（全为 FAIL→PASS）→ **差距主因是 grader prompt v2，非检索排序**
- vs pg floor04：pass 仍 **-2**（55 vs 57）；pg PASS→v1 FAIL：**4**（G12/G17/G45/G54，四条 top5 均 identical，属 grader 评级波动）；pg FAIL→v1 PASS：2（G25/G28）

### 结论

- v1 公平重跑 **收回** 40c 相对基线的大部分假性回退（+8 pass / neg 回满）。
- 相对 pg floor04 仍差 **2 pass**；召回三象限 ≥ 基线（en2en 优 1）。
- **仍禁止据此默认切流**；**未关账**；未改 `.env` 默认 backend。
- eval exit_code=1（金样未全绿，属预期；报告完整落盘）。

## 未做

- 未改 `.env` 默认 `RAG_VECTOR_BACKEND` / 未持久改 grader
- 未关账
- 未跑 80 万压测
