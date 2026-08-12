# Invoke：30（含 40）· rag-reranker-p0

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 30（含 40） |
| task_slug | `rag-reranker-p0` |
| task_paths | `docs/tasks/active/task_rag_reranker_p0.md` |
| related_review_or_none | `docs/harness/reviews/task_rag_reranker_p0_audit_R1_20260812.md` |
| git_branch | `task/rag-reranker-p0` |
| created_utc_or_local | 2026-08-12 |
| notes | 00 派工；全量 r4-R 标维护者复测；生产默认保持 false；本波不关账 |

---

## GATE_VERIFY（首输出须重读 task 表）

| human_gate_id | task表status | blocks_30 | 30可开工？ |
|---|---|---|---|
| HG-TASK-DRAFT | approved | N | Y |
| HG-AUDIT-R1 | approved | Y | Y |

reviews R1：是 · pre-30 invoke 10：是 · 结论：可开工

---

## 交付范围（30）

1. `app/ops/rag/reranker.py`：CE 懒加载单例 + `rerank_chunks`；加载失败回退粗排 top-5  
2. `retrieve_node`：`RAG_RERANK_ENABLED` 控制；开启时 k_each/M→CE→5；span 含 rrf vs rerank 锚点  
3. env：`RAG_RERANK_ENABLED`（默认 false）/ `RAG_RERANK_MODEL` / `RAG_RERANK_CANDIDATES` / `RAG_RECALL_K_EACH`  
4. 单测：fake scorer 排序与截断；关闭时不调 CE  
5. `experiments/rag_compare/` 短文 + Q6 报告「下一步」指针  
6. 40：ruff + pytest；**不**跑全量金样  
7. **不要**改生产默认 true；**不要**关账  

复测命令（维护者）：

```bash
export RAG_RERANK_ENABLED=true
export RAG_SECOND_PATH=fts
export RAG_KW_EXPAND=false
export RAG_FTS_CONFIG=simple
.venv/bin/python evals/golden/run_eval.py --out reports/r4-R.yaml --stability 0
```

---

## 验证摘要（30/40 执行后）

| 项 | 结果 |
|---|---|
| GATE_VERIFY / harness verify | PASS（闸表 approved · R1 在 · pre-30 invoke 10 在） |
| 代码 | `reranker.py` · `retrieve_node` 接线 · `RetrievedChunk.rerank_score` · `reranker_p0/README.md` |
| 生产默认 | `RAG_RERANK_ENABLED=false`（未改 true） |
| ruff（相关文件） | exit 0 |
| pytest `test_rag_reranker` | exit 0 · 8 passed |
| `reports/r4-R.yaml` | **未产出**（维护者复测；因子隔离命令见上） |
| 关账 | **未执行**（按 00 授权停留关账前） |
