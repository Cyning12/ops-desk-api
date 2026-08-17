# Invoke：30（含 40）· rag-embed-api-backend

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 30（含 40） |
| task_slug | `rag-embed-api-backend` |
| freeze_id | — |
| task_paths | `docs/tasks/active/task_rag_embed_api_backend.md` |
| related_review_or_none | `docs/harness/reviews/task_rag_embed_api_backend_audit_R1_20260817.md` |
| git_branch | `task/rag-embed-api-backend` |
| worktree_root | `.`（主仓 `ops-desk-api`，非 wt） |
| created_utc_or_local | 2026-08-17 |
| notes | 子 agent 10+20+30/40；**未** push / **未** PR / **未** harness close；交 00 验收 |

---

## GATE_VERIFY（首输出 · 读 task 表）

| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---------------|--------------|-----------------|--------|-----------|------------|
| HG-TASK-DRAFT | approved | approved（子 agent 代签：维护者授权实现、00 只验收 PR 关账） | Y | N | Y |
| HG-AUDIT-R1 | approved | approved（同上 · R1 内容 pass） | Y | Y | Y |
| HG-GRAPH-MODULES | approved | approved | Y | Y | Y |

reviews：`task_rag_embed_api_backend_audit_R1_20260817.md` 存在且 R1 内容 pass？ **是**

pre-30 invoke：`required ∩ {10,20,00}` 齐全？ **是**（有 10；`required_invoke_hats=10,30` · `default`）

`npx @cyning/harness verify --target . --task docs/tasks/active/task_rag_embed_api_backend.md` → **VERIFY: PASS**

结论：**可进入读码/改码**

---

## 可复制 Prompt 快照

````text
30-execute-code + 40-self-check · rag-embed-api-backend
主仓 ops-desk-api；分支 task/rag-embed-api-backend；闸已代签；verify PASS。
实现：get_query_embedder 默认 SiliconFlow ApiEmbedder；接线 retrieve + rag_nodes；
禁隐式回落 ST；禁改 graph.py；mock /embeddings 单测；.env.example + workspace compose 透传。
禁止 push / PR / CLOSE。
````

---

## 交付范围（30）

1. `app/ops/rag/embedder.py`：`get_query_embedder` / `RAG_EMBED_BACKEND` 默认 `siliconflow`；`RAG_EMBED_MODEL` 默认 `BAAI/bge-m3`；缺 key / HTTP 明确失败且**不**回落 ST
2. `app/ops/lc_evidence_chain/retrieve.py` · `app/ops/chat/rag_nodes.py`：走工厂；`asyncio.to_thread` 保留
3. `tests/test_rag_embedder.py`：mock httpx 保序/维数；siliconflow 不加载 ST；local stub；两入口接线
4. `.env.example`：`RAG_EMBED_BACKEND` / `RAG_EMBED_MODEL`
5. 跨仓：`ops-desk-workspace/deploy/docker-compose.prod.yml` + `deploy/.env.example` 透传（workspace **另 commit** 由 00）
6. G-L1 `01_modules.md` 一句 + `graph-compile.sh` exit 0
7. **未改** `app/ops/chat/graph.py` · ingest 默认 · `task_ops_sync_sender_migration` · 未跟踪 `lg_rag/`

---

## 验证摘要（30/40）

| 项 | 结果 |
|---|---|
| GATE_VERIFY | PASS（三闸 approved） |
| harness verify | PASS（缺 30 invoke 时曾 WARN；本文件补齐） |
| ruff（触及路径） | exit 0 · All checks passed |
| pytest `tests/test_rag_embedder.py` | exit 0 · **9 passed** |
| pytest `tests/test_rag_reranker.py` | exit 0 · **17 passed** |
| `git diff origin/master -- app/ops/chat/graph.py` | 空（0 bytes） |
| `./scripts/graph-compile.sh` | exit 0 |
| push / PR / CLOSE | **未执行** |

**40 结论：PASS**

---

## 下一棒

交还父窗 00：机械验收 → PR → CLOSE。workspace compose 改动需另 commit。
