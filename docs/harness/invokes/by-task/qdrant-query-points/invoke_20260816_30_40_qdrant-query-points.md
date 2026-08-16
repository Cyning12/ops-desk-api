# Invoke：30（含 40）· qdrant-query-points

> **用途**：热修留档（无独立 10-task）。对齐 `reconcile.py` 已用的 `query_points`。  
> **非** 升 Qdrant server / 钉 client 消版本 warning。

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 30（含 40） |
| task_slug | `qdrant-query-points` |
| freeze_id | — |
| task_paths | 无（fix 热修 · 无独立 task 文件） |
| related_review_or_none | 无 |
| git_branch | `fix/qdrant-query-points` |
| worktree_root | `.` |
| created_utc_or_local | 2026-08-16 |
| notes | 紧急修复：client 1.19 无 `search`，热路径每次失败两次再 fallback pgvector |

---

## 可复制 Prompt 快照

````text
fix 分支：fix/qdrant-query-points（从 origin/master 切出，勿叠 images 热修）

范围
- app/ops/rag/retrievers/qdrant_retriever.py：_search_hits 优先 query_points，无该 API 再走 search
- tests/test_rag_qdrant_backend.py：mock query_points 返回 .points
- 禁止改 graph.py、禁止升 docker Qdrant 镜像、禁止改 pyproject qdrant-client 范围

验收
- pytest tests/test_rag_qdrant_backend.py 绿
- ruff 相关路径绿
- 本机再跑一问：日志无 object has no attribute 'search'（server 1.13.6 兼容性 warning 可暂忽略）
````

---

## GATE_VERIFY 摘要

无独立 task 闸表。维护者口头「开 fix 修 Qdrant」授权热修；HG-GRAPH-MODULES 真值已存在（不新增一级模块）。

---

## 交付摘要

- **改动**：`QdrantRetriever._search_hits` → `query_points`（`hasattr` 回退 `search`）
- **测试**：`uv run pytest tests/test_rag_qdrant_backend.py -q` → **9 passed**
- **ruff**：`uv run ruff check app/ops/rag/retrievers/qdrant_retriever.py tests/test_rag_qdrant_backend.py` → PASS
- **变更路径**：`app/ops/rag/retrievers/qdrant_retriever.py`、`tests/test_rag_qdrant_backend.py`
- **下一棒**：PR #37 CI 绿后合入；本机 `make dev` 复跑一问确认无 `search` 报错

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-08-16 | 30+40 代码已合入 PR #37；补落本 invoke（事后补档） |
