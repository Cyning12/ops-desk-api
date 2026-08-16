# Task Audit R1：qdrant-server-upgrade

> **task**：`docs/tasks/active/task_qdrant_server_upgrade.md`  
> **日期**：2026-08-16 · 审查：00 统筹（维护者会话「签收」）  
> **结论**：`pass` · 建议 `HG-AUDIT-R1=approved`

---

## 核对

| 项 | 审阅 |
|---|---|
| 上游 | 迁移已关账；PR #37 热路径已 `query_points` |
| 范围 | 本机 + 生产 compose 镜像 1.13.6 → 1.19.x；SPEC/cutover 版本句；本机先于生产 |
| 非范围 | 改 client、改 graph、改默认 `RAG_VECTOR_BACKEND`、改 HNSW |
| 验收 | compose 同 tag · pytest 绿 · 本机一问无 1.13.6 warning / 无 `search` 缺失 |
| failure_paths | volume 不兼容从 PG 重建；生产可切 pgvector |
| 思考轮 | R0–R5 · `early_stop=yes` 合理（镜像对齐，细节交给 cutover） |
| `wiki_delta` | `n/a` · `graph_change_layer=none` |

## 内容

**零阻塞。** 升 server、不降 client，与现网 1.19 client 一致。生产 compose 在 workspace 仓，30 须另 PR 或同 Epic，不挡本仓先改本机 compose。

## 条件

- 30 钉 Docker Hub 上真实存在的 `v1.19.<patch>`，禁止臆造 tag
- 先本机 `up`；volume 失败再重建，禁止生产先动
- 不改 `qdrant_retriever.py`，除非 1.19 启动后 API 再回归

## HG-AUDIT-R1 建议

**approved**（00 代签 · 维护者「签收」）
