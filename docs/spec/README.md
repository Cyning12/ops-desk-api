# docs/spec · ops-desk-api 索引

> **公约**：新长期 SPEC → 专属夹 `docs/spec/<slug>/`（见 [`doc-health/`](./doc-health/) POINTER · 契约真值在 spec-wave）。  
> **禁止**：再新增根级裸 `SPEC-*.md`。

---

## 专属夹（推荐形态）

| slug | 路径 | 状态 | 一句话 |
|------|------|------|--------|
| `memory-facts-p1` | [`memory-facts-p1/`](./memory-facts-p1/) | **signed · 已实施**（2026-09-21 · task/memory-facts-p1 · PR 待开） | 事实型记忆 P1（向量语义召回 + LLM 离线候选抽取） |
| `memory-facts-p0` | [`memory-facts-p0/`](./memory-facts-p0/) | **signed · 已实施**（2026-09-21 · task/memory-facts-p0 · PR 待开） | 事实型记忆 P0（ops_memory_facts + 写入闸 + 确定性召回注入） |
| `inform-graph-backfill` | [`inform-graph-backfill/`](./inform-graph-backfill/) | draft/执行中 | Inform 图谱补齐 |
| `agent-infra` | [`agent-infra/`](./agent-infra/) | active | Gateway stable + **Host flesh 规划**（`02_agent_host_plan_v0`） |
| `doc-health` | [`doc-health/`](./doc-health/) | **1.7.1 已发版** · 试点镜像 | 文档健康度 + CLOSE 强绑定 · FEEDBACK |
| `gha-deploy-api` | [`gha-deploy-api/`](./gha-deploy-api/) | accepted · 已实施 | GHA 部署 API（C-1 新夹 · 2026-09-11 归位） |
| `harness-to-dsh-kit-graph-migrate` | [`harness-to-dsh-kit-graph-migrate/`](./harness-to-dsh-kit-graph-migrate/) | done | graph 命令面 cyning-harness → kit 迁移（2026-09-11 归位） |
| `lc-evidence-chain` | [`lc-evidence-chain/`](./lc-evidence-chain/) | accepted · 已实施 | LC evidence chain v1 + hardening 合并夹（C-2 · 2026-09-11 归位） |
| `langfuse-sdk-v4-migration` | [`langfuse-sdk-v4-migration/`](./langfuse-sdk-v4-migration/) | draft · DEF-001 挂起 | Langfuse SDK v4 迁移（2026-09-11 归位） |
| `qdrant-migration` | [`qdrant-migration/`](./qdrant-migration/) | accepted · 已实施 | Qdrant 迁移（2026-09-11 归位） |
| `rag-reranker-p0` | [`rag-reranker-p0/`](./rag-reranker-p0/) | signed · 已实施 | RAG Reranker P0（2026-09-11 归位） |

---

## 历史债 · 根级裸 SPEC

> **已清零（2026-09-11 · `task_specwave_cleanup_2_1_3`）**：原 8 条根级裸 SPEC 全部迁入专属夹（见上表 · 夹内保留原文件名）；`spec-wave check` 零 WARN。感知通道维持：`check` WARN 再发即新增债。

---

## 修订记录

| 日期 | 摘要 |
|------|------|
| 2026-08-26 | 建索引 + 历史债表；挂 doc-health 试点 |
| 2026-08-26 | doc-health 对齐 kit 1.7.1；`check` 根级裸 SPEC WARN **8** 条 |
| 2026-08-26 | agent-infra 细分文档层级（域夹 + ROADMAP）；见 [`agent-infra/README.md`](./agent-infra/README.md) |
| 2026-08-27 | agent-infra Host flesh 初版规划 `02_agent_host_plan_v0` |
| 2026-09-11 | 历史债 8 条根级裸 SPEC 全部迁入专属夹（C-1/C-2/C-3 裁定）；L3 公约行旧名 → `spec-wave`；见 `task_specwave_cleanup_2_1_3` |
| 2026-09-21 | 新增 `memory-facts-p0` 专属夹（10-spec 初稿 · 待 HG-SPEC-SIGNOFF） |
| 2026-09-21 | `memory-facts-p0` signed → 已实施（task 闭环 · 40 PASS · 归档 done） |
| 2026-09-21 | 新增 `memory-facts-p1` 专属夹（10-spec 初稿 · 待 HG-SPEC-SIGNOFF） |
| 2026-09-21 | `memory-facts-p1` signed → 已实施（task 闭环 · 40 PASS · 归档 done） |
