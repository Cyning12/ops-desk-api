# RAG P0 · Cross-Encoder Reranker

承接 Q6 结论：主收益在**排序**而非第二路；本波在 RRF 粗排后插入 `bge-reranker-v2-m3`。

| 项 | 内容 |
|----|------|
| SPEC | `docs/spec/SPEC-rag-reranker-p0_v1.md`（signed） |
| task | `docs/tasks/active/task_rag_reranker_p0.md` |
| 代码 | `app/ops/rag/reranker.py` · 接入点 `app/ops/chat/rag_nodes.py::retrieve_node` |
| 基线 | `reports/r4-2.yaml` |
| 金样产出 | `reports/r4-R.yaml`（维护者复测） |

## 链路

```text
embed(query)
  → hybrid_recall(k_each=K, top_n=M)   # 仅 RAG_RERANK_ENABLED=true 时 K/M 默认 20
  → rerank(query, candidates) → top-5
  → grade_chunks(top-5) → decide
```

关闭时：`k_each=10`、`top_n=5`，**不**加载 CE（与现网一致）。

## 环境变量

| env | 默认 | 含义 |
|-----|------|------|
| `RAG_RERANK_ENABLED` | `false` | 生产/合入默认关 |
| `RAG_RERANK_MODEL` | `BAAI/bge-reranker-v2-m3` | CE 模型 |
| `RAG_RERANK_CANDIDATES` | `20` | 粗排 top-M |
| `RAG_RECALL_K_EACH` | `20` | 每路召回（仅开启时） |
| `RAG_RERANK_MIN_SCORE` | `0.6` | **顶分地板**：`max(score) < 此值` → 空召回拒答 |
| `RAG_RERANK_SCORE_RATIO` | `0.75` | **相对顶分**：保留 `score ≥ max * ratio` |

依赖：根 `requirements.txt` 已有 `sentence-transformers`（`CrossEncoder`）。权重走 HF cache，约 1GB；CPU 可跑，首检延迟较高。

## 失败行为

CE 加载/推理失败 → 打错误日志 → **回退粗排 top-5**（不拖垮 chat）。  
动态过滤（方案 B）：`max < RAG_RERANK_MIN_SCORE` → **空召回 → 拒答**；否则保留 `score ≥ max * RAG_RERANK_SCORE_RATIO`。  
分数不上 SSE/引用卡片。

## 复测（因子隔离）

```bash
export RAG_RERANK_ENABLED=true
export RAG_SECOND_PATH=fts
export RAG_KW_EXPAND=false
export RAG_FTS_CONFIG=simple
# 与误跑对照时：grader 字符串须与 reports/r4-R-misrun-no-ce.yaml 一致
export RAG_GRADER_MODEL=qwen3.7-max-2026-05-20
.venv/bin/python evals/golden/run_eval.py --out reports/r4-R.yaml --stability 0
```

对照：

| 报告 | 含义 |
|------|------|
| `reports/r4-R-misrun-no-ce.yaml` | 误标归档：runner 未接 CE，实质 Normal（73） |
| `reports/r4-R.yaml` | 方案 B 默认（floor=0.6 / ratio=0.75）：**54/73 · neg 11/11** |
| `reports/r4-R-pre-floor.yaml` | 无地板对照（neg 掉，不采纳） |
| `reports/r4-R-floor03.yaml` | floor=0.3 / ratio=0.75：57/73 但 **neg 10/11**（不采纳） |
| `reports/r4-R-floor03-ratio085.yaml` | floor=0.3 / ratio=0.85：51/73 · neg 10/11（不采纳） |
| `reports/r4-R-floor04.yaml` | floor=0.4 / ratio=0.75：**partial**（G48 grader 额度中断，不作裁决） |

合入默认仍为 `RAG_RERANK_ENABLED=false`（未达「总 pass +2 且 neg 不掉」）。

对比脚本：`experiments/rag_compare/reranker_p0/compare_r4r.py`

## 修订

| 日期 | 说明 |
|------|------|
| 2026-08-12 | 首版（P0 CE · 默认 false） |
| 2026-08-13 | 归档 floor 0.3/0.4 与 ratio=0.85 消融；默认参数仍 0.6/0.75 |
