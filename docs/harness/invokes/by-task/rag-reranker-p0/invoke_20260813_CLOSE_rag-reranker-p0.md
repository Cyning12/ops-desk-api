# Invoke：CLOSE · rag-reranker-p0

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | CLOSE |
| task_slug | `rag-reranker-p0` |
| related_30 | invoke_20260812_30_40_rag-reranker-p0.md |
| git_branch | `task/rag-reranker-p0` |
| created_utc_or_local | 2026-08-13 |
| notes | 维护者授权：floor04 定稿后关账；生产 ENABLED 仍 false |

---

## CLOSE 结论：**PASS**

### 定稿参数

| 项 | 值 | 证据 |
|---|---|---|
| `RAG_RERANK_MIN_SCORE` | **0.4** | `app/ops/rag/reranker.py` · `reports/r4-R-floor04.yaml` |
| `RAG_RERANK_SCORE_RATIO` | **0.75** | 同上 |
| `RAG_RERANK_ENABLED` | **false**（生产默认不变） | SPEC 签收锁死 |

### 金样对照（vs misrun Normal 54/73 · neg 11/11）

| 报告 | pass | neg | 裁决 |
|---|---|---|---|
| floor04（定稿） | **57/73** | **11/11** | 采纳过滤初始值 |
| floor=0.6 | 54/73 | 11/11 | 无 pass 增益 |
| floor=0.3 | 57/73 | 10/11 | G71 漏，不采纳 |

### 关账动作

- 默认值写入代码/SPEC/实验 README
- `harness task close --file docs/tasks/active/task_rag_reranker_p0.md --yes`
- 归档 → `docs/tasks/done/task_rag_reranker_p0.md`
