# Invoke：30（含 40）· rag-sparse-arm-c

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 30（含 40） |
| task_slug | `rag-sparse-arm-c` |
| task_paths | `docs/tasks/active/task_rag_sparse_arm_c.md` |
| related_review_or_none | `docs/harness/reviews/task_rag_sparse_arm_c_audit_R1_20260812.md` |
| git_branch | `task/rag-sparse-arm-c` |
| created_utc_or_local | 2026-08-12 |
| notes | 00 派工；全量重嵌/r4-C 实跑可标维护者；须保留 A 入口 |

---

## GATE_VERIFY（首输出须重读 task 表）

| human_gate_id | task表status | blocks_30 | 30可开工？ |
|---|---|---|---|
| HG-TASK-DRAFT | approved | N | Y |
| HG-AUDIT-R1 | approved | Y | Y |

reviews R1：是 · pre-30 invoke 10：是 · 结论：可开工

---

## 交付范围（30）

1. `RAG_SECOND_PATH=fts|sparse`（默认 `fts`）：sparse 时第二路走 `sparse_embedding`，**不删** FTS / `RAG_FTS_CONFIG` / A 脚本  
2. 影子列 SQL / migration 说明（本地可加列；不写生产）  
3. FlagEmbedding 批重嵌脚本（断点续写 · 8574）  
4. `retrieve.py` sparse 路 + 单测（默认 fts 不回归）  
5. `experiments/rag_compare/sparse_arm_c/README.md` 实跑步骤  
6. 40：pytest/ruff；全量 r4-C 若未跑完须 checkpoint 并回填自检「未测项」  
7. **不要**默认打开 `RAG_KW_EXPAND`；**不要**删 A 入口  

评测命令口径：

```bash
export RAG_SECOND_PATH=sparse
export RAG_KW_EXPAND=false
.venv/bin/python evals/golden/run_eval.py --out reports/r4-C.yaml --stability 0
```
