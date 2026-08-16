# Invoke：30（含 40 自检）· qdrant-server-upgrade

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 30（含 40） |
| task_slug | `qdrant-server-upgrade` |
| freeze_id | — |
| task_paths | `docs/tasks/active/task_qdrant_server_upgrade.md` |
| related_review_or_none | `docs/harness/reviews/task_qdrant_server_upgrade_audit_R1_20260816.md` |
| git_branch | `task/qdrant-server-upgrade` |
| worktree_root | `.` |
| created_utc_or_local | 2026-08-16 |
| notes | 钉 `qdrant/qdrant:v1.19.0`；本机与生产 1.13 volume 均不兼容，已从 PG 重建 8574；生产 `printenv=qdrant` |

---

## 可复制 Prompt 快照

````text
Open Folder = ops-desk-api。分支 task/qdrant-server-upgrade。闸已签。

范围
- Docker Hub 钉 qdrant/qdrant:v1.19.<patch>（禁止臆造）
- 本机 docker-compose.yml 与 workspace deploy/docker-compose.prod.yml 同 tag
- SPEC 引擎行 + cutover/narrative 版本句
- 本机 pull && up -d qdrant；volume 不兼容则删 volume，从 PG 重建 ops_knowledge
- pytest tests/test_rag_qdrant_backend.py
- 本机一问：无 1.13.6 UserWarning、无 attribute search
- 禁止改 graph.py、禁止改 qdrant-client 范围、禁止改默认 RAG_VECTOR_BACKEND
````

---

## GATE_VERIFY 摘要

| human_gate_id | task表status | blocks_30 | 30可开工？ |
|---------------|--------------|-----------|------------|
| HG-TASK-DRAFT | approved | N | 可 |
| HG-AUDIT-R1 | approved | Y | 可 |
| HG-GRAPH-MODULES | approved | N | 可 |

reviews：R1 pass。pre-30 invoke：10、20 齐全。`harness verify`：PASS。

---

## 交付摘要

- **钉 tag**：Docker Hub 仅 `v1.19.0`（无更高 1.19 patch）→ `qdrant/qdrant:v1.19.0`
- **本机**：`docker-compose.yml` 已改；`up` 后 1.13 volume 读失败（`ops_knowledge_scale` JSON 反序列化 panic）→ 删 `ops-desk-api_qdrant_data` → 空 volume 起 **1.19.0 healthy** → 从 PG export/upsert **8574** 点到 `ops_knowledge`
- **生产**：scp compose → 1.19.0 读旧盘 Panic（同本机）→ 先切 `pgvector` → 删 `deploy_qdrant_data` → 空盘 healthy → export/upsert **8574** → reconcile **pass**（overlap≈0.993）→ `.env` 切回 `qdrant` + 影子写 true；`printenv` 已确认
- **文档**：SPEC 引擎行 v1.1.1；cutover 增 §1.1；narrative 记已收敛
- **测试**：`uv run pytest tests/test_rag_qdrant_backend.py -q` → **9 passed**
- **一问（client 直连 6333）**：`query_points` 3 hits；`WARNINGS: none`；无 `search` 属性（client 1.19 预期）；无 `1.13.6` / `incompatible`
- **未改**：`app/ops/chat/graph.py`、`qdrant_retriever.py`、`qdrant-client` 依赖
- **下一棒**：本仓 PR + workspace 仓 PR（锁定 prod compose tag，避免 scp 盖回 1.13.6）

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-08-16 | 30 落地：镜像 v1.19.0 + 本机 volume 重建灌库 |
| 2026-08-16 | 生产窗口完成：删卷重建 8574 · reconcile pass · Flag 切回 qdrant |
