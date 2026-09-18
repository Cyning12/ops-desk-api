# Invoke · 30 implement · tenant-readonly-predicate

> **hat**：30  
> **日期**：2026-09-18  
> **分支**：`task/tenant-readonly-predicate`  
> **task**：`docs/tasks/active/task_tenant_readonly_predicate.md`  
> **结论**：**PASS**（Fixture 本地 · **未 commit**）

---

## 人工闸扫描（GATE_VERIFY · 首输出）

| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---------------|--------------|-----------------|--------|-----------|------------|
| HG-TASK-DRAFT | approved | approved | Y | Y | 可 |
| HG-AUDIT-R1 | approved | approved | Y | Y | 可 |
| HG-GRAPH-MODULES | approved | approved | Y | Y | 可 |
| HG-STAGE-T-DATA | approved | approved | Y | Y | 可 |
| HG-CONTRACT-FREEZE | approved | approved | Y | Y | 可 |

reviews：Fixture 轨 · `--allow-no-review` 豁免留痕  
pre-30 invoke：缺 10/20 · `--allow-invoke-gap` 豁免留痕  

```text
npx spec-wave verify --target . --task docs/tasks/active/task_tenant_readonly_predicate.md \
  --allow-no-review --allow-invoke-gap
→ VERIFY: PASS
```

结论：**可进入读码/改码**

---

## 本窗改动要点

- 续作 WIP：F1=C session 真源 · 头不一致 403 · lookup SQL 租户谓词 · RAG metadata 过滤
- 补 T3：`tests/test_tenant_context.py::test_rag_filter_cross_tenant_negative`
- 补 T5：`docs/_tech_graph/l1/01_modules.md` auth/capability/lg_rag/rag 薄备注（不新增一级模块）
- invoke 与 stream 共用 `_resolve_request_tenant` + ContextVar
- 迁移 `20260918_tenant_readonly`：`ADD COLUMN IF NOT EXISTS` + 索引；默认回填 A；**不改** `(repo_id,number)` 唯一约束

## 命令实录

```text
.venv/bin/pytest tests/test_tenant_context.py tests/test_capability_lookups.py -q
→ 19 passed

.venv/bin/ruff check app/ops/tenant_context.py app/ops/auth.py app/ops/deps.py \
  app/ops/capability/lookups.py app/ops/capability/adapters/local_fn.py \
  app/ops/lg_rag/router.py app/ops/lg_rag/multi/nodes.py \
  app/ops/rag/retrieve.py app/ops/rag/shadow_write.py app/ops/rag/ingest.py \
  app/db/models.py tests/test_tenant_context.py tests/test_capability_lookups.py
→ All checks passed!

./scripts/graph-compile.sh → OK（既有 branches/triggers warning 不咬 exit）
npx spec-wave task lint --file docs/tasks/active/task_tenant_readonly_predicate.md → LINT: PASS
git diff -- app/ops/chat/graph.py → 0
```

### 本机 API（非 Docker :8000）

```text
base: http://127.0.0.1:8001
GET  /api/ops/auth/me              → tenant_id=ops-desk-pilot
POST /api/ops/auth/tenant A/B      → ok + allowlist
POST /api/ops/lg-rag/stream
  头 vs session 不一致             → HTTP 403 tenant_header_mismatch
  头一致                           → HTTP 200 + SSE run.start …
```

Docker `:8000` 可能无新路由；联调请对准本仓 uvicorn **8001**（或自行 `make`/`uvicorn` 起新进程）。

## 已知限制（给 web 00）

1. 生产 B 种子未做（Fixture 负样本 number=900001）；同号跨租户唯一约束本波不改。
2. SSE `event_type` 零改；租户仅 header/session/`/me`。
3. Qdrant payload index：脚本已含 `tenant_id`；本地影子写/存量 chunk 无字段时检索侧视为 A。
4. `opsdesk_test` 无 alembic_version（conftest create_all）；开发库已 stamp `20260918_tenant_readonly`。

## 禁止项核对

- 未 commit / push / PR  
- 未改 web/ios/workspace 业务码  
- 未改 `app/ops/chat/graph.py`  
- 未新增 G-L1 一级模块 · 未冻 SSE event_type
