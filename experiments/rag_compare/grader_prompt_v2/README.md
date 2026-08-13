# Grader Prompt 版本对照（检索闸 · 非答问 Prompt）

在 **CE floor=0.4 / ratio=0.75** 基线上，用 env 切换 grader 文案，比较金样 pass/neg。

| 版本 | env | 说明 |
|------|-----|------|
| **v1**（默认） | `RAG_GRADER_PROMPT=v1` 或不设 | 历史基线（r4-2 / r4-R-floor04） |
| **v2** | `RAG_GRADER_PROMPT=v2` | 加严「可用证据」；四档枚举不变 |

代码：`app/ops/rag/grader.py`（`GRADER_SYSTEM_V1` / `GRADER_SYSTEM_V2`）。

## 对照跑法（因子隔离）

```bash
export RAG_RERANK_ENABLED=true
export RAG_RERANK_MIN_SCORE=0.4
export RAG_RERANK_SCORE_RATIO=0.75
export RAG_SECOND_PATH=fts
export RAG_KW_EXPAND=false
export RAG_FTS_CONFIG=simple
# grader 模型与 floor04 对齐（勿混 flash/max）
export RAG_GRADER_MODEL=qwen3.7-max-2026-05-20

# A：v1 基线（可与 reports/r4-R-floor04.yaml 比；若重跑建议新文件）
export RAG_GRADER_PROMPT=v1
.venv/bin/python evals/golden/run_eval.py --out reports/r4-R-floor04-grader-v1.yaml --stability 0

# B：v2 实验
export RAG_GRADER_PROMPT=v2
.venv/bin/python evals/golden/run_eval.py --out reports/r4-R-floor04-grader-v2.yaml --stability 0
```

报告 meta 含 `grader_prompt` 字段。生产默认保持 **v1**，确认 v2 更优后再议改默认。
