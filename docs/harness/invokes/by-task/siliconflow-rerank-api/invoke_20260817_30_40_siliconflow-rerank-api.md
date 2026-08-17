# Invoke：30（含 40）· siliconflow-rerank-api

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 30（含 40） |
| task_slug | `siliconflow-rerank-api` |
| freeze_id | — |
| task_paths | `docs/tasks/active/task_siliconflow_rerank_api.md` |
| related_review_or_none | `docs/harness/reviews/task_siliconflow_rerank_api_audit_R1_20260817.md` |
| git_branch | `task/siliconflow-rerank-api` |
| worktree_root | `.` |
| created_utc_or_local | 2026-08-17 |
| notes | 子 agent 30+40；未 close / 未 commit / 未 push；维护者本地验收前不关账 |

---

## GATE_VERIFY（首输出 · 读 task 表）

| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---------------|--------------|-----------------|--------|-----------|------------|
| HG-TASK-DRAFT | approved | approved（00 代签） | Y | N | Y |
| HG-AUDIT-R1 | approved | approved（00 代签） | Y | Y | Y |
| HG-GRAPH-MODULES | approved | approved | Y | Y | Y |

reviews：`task_siliconflow_rerank_api_audit_R1_20260817.md` 存在且 R1 内容 pass？ **是**

pre-30 invoke：`required ∩ {10,20,00}` 齐全？ **是**（有 10、00；`required_invoke_hats=10,30` · `minimal`）

Prompt 声称 verify 刚 PASS；闸真值以 task 表为准，与表一致。

结论：**可进入读码/改码**

---

## 可复制 Prompt 快照

````text
30-execute-code + 40-self-check · siliconflow-rerank-api
分支 task/siliconflow-rerank-api；闸已签；verify PASS 后仍须读 task 表填 GATE_VERIFY。
实现：reranker 默认 SiliconFlow POST /rerank；过滤方案 B 不改；mock httpx 单测；
.env.example + 生产 compose 透传 RAG_RERANK_BACKEND；禁止 commit / close。
````

---

## 交付范围（30）

1. `app/ops/rag/reranker.py`：`RAG_RERANK_BACKEND` 默认 `siliconflow`；`_score_siliconflow` httpx POST `/rerank`，`top_n=len(documents)`，按 `index` 填回等长分数后走既有地板 0.4 / ratio 0.75 / top-5；超时 12s；仅 429 短退避一次；缺 key 在 score 路径 raise → 既有 fallback
2. `tests/test_rag_reranker.py`：mock httpx；autouse delenv `RAG_RERANK_BACKEND` / `SILICONFLOW_API_KEY`；保留方案 B fake `score_fn` 单测
3. `.env.example`：`RAG_RERANK_BACKEND=siliconflow`
4. 跨仓：`ops-desk-workspace/deploy/docker-compose.prod.yml` + `deploy/.env.example` 透传
5. **未改** `app/ops/chat/graph.py` · hybrid_recall SQL · grader

---

## 验证摘要（30/40）

| 项 | 结果 |
|---|---|
| GATE_VERIFY | PASS（task 表三闸 approved） |
| ruff（相关路径） | exit 0 · All checks passed |
| `.venv/bin/pytest tests/test_rag_reranker.py -q` | exit 0 · **17 passed** |
| `git diff -- app/ops/chat/graph.py` | 空 |
| 关账 / commit / push | **未执行**（00 要求留给维护者） |

**40 结论：PASS**

---

## 下一棒

交还 00：维护者本地验收（开 Flag、不必打真实生产）→ 50 / CLOSE / 分仓 commit。
workspace 改动落在分支 `chore/prod-env-hf-passthrough`，需维护者决定如何并入。
