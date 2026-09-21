# docs/spec · ops-desk-api 索引

> **公约**：新长期 SPEC → 专属夹 `docs/spec/<slug>/`（见 [`doc-health/`](./doc-health/) POINTER · 契约真值在 spec-wave）。  
> **禁止**：再新增根级裸 `SPEC-*.md`。

---

## 专属夹（推荐形态）

| slug | 路径 | 状态 | 一句话 |
|------|------|------|--------|
| `memory-golden-eval` | [`memory-golden-eval/`](./memory-golden-eval/) | **signed · 已实施**（2026-09-21 · task/memory-golden-eval · PR 待开 · 真跑裁决待维护者） | 记忆抽取金样评测 + 融合权重调参（P1 生产开启前置） |
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
| `llm-layer-hardening` | [`llm-layer-hardening/`](./llm-layer-hardening/) | **signed · 已实施**（2026-09-21 · PR #148 已合 master · 40 核验 24/24 PASS） | L5 模型层硬化：重试退避 / provider 熔断 / 分档路由 / `ops_llm_usage` 账本 |
| `memory-embedding-backfill` | [`memory-embedding-backfill/`](./memory-embedding-backfill/) | **signed · 已实施**（2026-09-21 · PR #151 已合 master · 40 核验 21/21 PASS） | 存量行 embedding 回填 CLI（幂等断点续跑 · 限速报告）+ span 单测 |
| `continuity-dedup` | [`continuity-dedup/`](./continuity-dedup/) | **signed · 已实施**（2026-09-22 · PR #153 已合 master · 40 核验 17/17 PASS） | M7 · continuity 重复实现合并（硬删除 + 测试收敛 · 真源零 diff） |
| `prompt-asset-roadmap` | [`prompt-asset-roadmap/`](./prompt-asset-roadmap/) | **signed · 阶段一已实施**（2026-09-22 · P1 PR #155 已合 master · 40 核验 20/20 PASS；阶段二「看得见」/阶段三「分得开」待后续波次） | Prompt 资产化三阶段（改得动→看得见→分得开 · 顺序不可跳） |

---

## 占位 SPEC（待启动 · 含接续指引）

> **用法**：按「建议序」选下一项 → 新会话声明「接续 <slug>」→ 10-spec 补全（R0–R5/方案对比/failure_paths/验收断言化）→ 人签 → 标准五棒流。每个占位 SPEC 内含范围草案 + 关键锚点（file 指引）+ 验收方向 + 接续指引。

| 建议序 | slug | 一句话 | 类别 |
|---|---|---|---|
| （进行中） | `memory-golden-eval` | M1 · 抽取精度金样 + 调权（P1 开闸前置） | 放大器 · 记忆轨 |
| 2 | [`memory-preference-profile/`](./memory-preference-profile/) | M3 · 画像记忆（先事实型后偏好型） | 记忆轨 |
| 3 | [`session-summary-fallback/`](./session-summary-fallback/) | M5 · 会话真摘要（铁律：可回退原文） | 记忆轨 |
| 4 | [`security-hardening/`](./security-hardening/) | C2 · L7 注入/PII/脱敏/真沙箱（顺序：隔离→检测） | 承重墙缺角 |
| 5 | [`memory-compliance-delete/`](./memory-compliance-delete/) | M4 · 合规物理删除权（有合规要求再做） | 成熟度标志 |
| 6 | [`multi-replica-verify/`](./multi-replica-verify/) | C3 · L0 多副本验证（有真实流量前必答） | 成熟度标志 |

> 排序原则（手册 §3.4/B.1）：缺了会不会造成**不可逆或静默**的错 → 承重墙缺角优先；放大器按迭代瓶颈排；成熟度标志等量级。

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
| 2026-09-21 | 新增 `memory-golden-eval`（signed · M1）+ 9 个占位 SPEC（含接续指引 · 建议序 2–10） |
| 2026-09-21 | `memory-golden-eval` 已实施（task 闭环 · 40 PASS · 归档 done · 真跑裁决待维护者） |
