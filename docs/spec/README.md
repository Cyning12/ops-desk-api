# docs/spec · ops-desk-api 索引

> **公约**：新长期 SPEC → 专属夹 `docs/spec/<slug>/`（见 [`doc-health/`](./doc-health/) POINTER · 契约真值在 dsh-coding-kit）。  
> **禁止**：再新增根级裸 `SPEC-*.md`。

---

## 专属夹（推荐形态）

| slug | 路径 | 状态 | 一句话 |
|------|------|------|--------|
| `inform-graph-backfill` | [`inform-graph-backfill/`](./inform-graph-backfill/) | draft/执行中 | Inform 图谱补齐 |
| `agent-infra` | [`agent-infra/`](./agent-infra/) | active | Capability / Structured Output 等 |
| `doc-health` | [`doc-health/`](./doc-health/) | **1.7.1 已发版** · 试点镜像 | 文档健康度 + CLOSE 强绑定 · FEEDBACK |

---

## 历史债 · 根级裸 SPEC（warn · 不强制本波搬迁）

> **感知通道（已拍板）**：本表（立刻可见）+ 日后 kit CLI/`verify` warn。不挡 close/merge。

| 文件 | 建议迁入（观察 · 非本波执行） |
|------|------------------------------|
| [`SPEC-gha-deploy-api_v1.md`](./SPEC-gha-deploy-api_v1.md) | 另建专属夹或归入既有运维夹 |
| [`SPEC-harness-to-dsh-kit-graph-migrate_v0.md`](./SPEC-harness-to-dsh-kit-graph-migrate_v0.md) | 可并入 graph 迁移夹 |
| [`SPEC-inform-graph-backfill_v1.md`](./SPEC-inform-graph-backfill_v1.md) | 已有 [`inform-graph-backfill/`](./inform-graph-backfill/) · 宜改 POINTER |
| [`SPEC-langchain-evidence-chain_v1.md`](./SPEC-langchain-evidence-chain_v1.md) | 专属夹或 agent/rag 族 |
| [`SPEC-langfuse-sdk-v4-migration_v1.md`](./SPEC-langfuse-sdk-v4-migration_v1.md) | 专属夹 |
| [`SPEC-lc-evidence-chain-hardening_v1.md`](./SPEC-lc-evidence-chain-hardening_v1.md) | 与 evidence-chain 合并夹 |
| [`SPEC-qdrant-migration_v1.md`](./SPEC-qdrant-migration_v1.md) | 专属夹 |
| [`SPEC-rag-reranker-p0_v1.md`](./SPEC-rag-reranker-p0_v1.md) | 专属夹 |

---

## 修订记录

| 日期 | 摘要 |
|------|------|
| 2026-08-26 | 建索引 + 历史债表；挂 doc-health 试点 |
| 2026-08-26 | doc-health 对齐 kit 1.7.1；`check` 根级裸 SPEC WARN **8** 条 |
