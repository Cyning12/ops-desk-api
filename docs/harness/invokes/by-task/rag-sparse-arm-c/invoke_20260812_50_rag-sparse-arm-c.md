# Invoke：50 · rag-sparse-arm-c（00 初步验收）

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 50 |
| task_slug | `rag-sparse-arm-c` |
| related_30 | [30-agent](33b4e5cf-1f1a-490b-b006-23bf530984f2) · commit `416e6c3` |
| git_branch | `task/rag-sparse-arm-c` |
| created_utc_or_local | 2026-08-12 |
| notes | 00 初验：产物+单测；**不含**全量重嵌/r4-C 实跑 |

---

## 50 初验结论：**PASS（附条件）**

条件：维护者按 `experiments/rag_compare/sparse_arm_c/README.md` 完成加列 → 全量重嵌 → `reports/r4-C.yaml` 后再做终验/判读。

### 对照验收

| 验收项 | 50 判定 | 证据 |
|---|---|---|
| sparse 列灌满 8574 | **deferred** | SQL + `embed_sparse.py` 已交付 |
| r4-C 分象限对比 | **deferred** | README 评测命令已备 |
| A 入口仍可调 | **pass** | `Dockerfile.pg-zhparser` · `zhparser_arm_a/` · `RAG_FTS_CONFIG` 仍在 |
| 未写生产 / dense 未改 | **pass**（设计） | 实验 SQL + 仅 UPDATE sparse 列脚本 |
| 默认 fts 不回归 | **pass** | 复跑 27 passed |
| `RAG_SECOND_PATH=sparse` 开关 | **pass** | `retrieve.py` + 单测 |

### 50 复跑

| 命令 | 退出码 |
|---|---|
| pytest second_path + fts_config + golden_eval_runner | 0（27 passed） |
| ruff retrieve.py sparse_vec.py | 0 |
| harness verify --task task_rag_sparse_arm_c.md | PASS |

### 给维护者的实跑清单

1. `add_sparse_embedding.sql`（本地/影子库，禁生产误操作）  
2. `embed_sparse.py` 全量至 filled=8574  
3. `RAG_SECOND_PATH=sparse RAG_KW_EXPAND=false` → `run_eval.py --out reports/r4-C.yaml --stability 0`  
4. 按 task 判读：zh2zh Δ vs r4-2 + **sparse 非空命中率**

### 50 不通过项

无（deferred 不记 fail）。
