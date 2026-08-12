# Task：RAG 关键词路 A 臂——zhparser 中文分词对照实验

> **状态**：active（draft · 待人审）  
> **类型**：对照实验（契约 Q6 裁决链路 · A/C 互斥候选）  
> **关联**：契约 Q6 · `experiments/rag_compare/` · 基准 `reports/r4-2.yaml` · D 臂 `reports/r4-D.yaml`  
> **分支**：`task/rag-zhparser-arm-a`

---

## 目标

同一 runner、同一金样（73 条）、同一嵌入模型，**只换 fts 分词配置**（'simple' → 中文配置），验证 zhparser 对关键词路的修复效果，产出与基准/D 臂可比的分象限 recall@5 数据，为 Q6 的 A/C 裁决提供 A 侧证据。

## 前置事实（已实测）

| 项 | 状态 |
|----|------|
| 病灶 | 'simple' 对中文分词失明（kw 全死 → D 臂复活至 5/73） |
| 语料 | 混合 23% + 中文 2% + docs 全中文；未来中文为主（Q6 前提修正） |
| 环境 | pgvector 0.8.5 镜像**不含** zhparser → 需自建镜像 |
| D 臂结论 | glossary 边际改进（kw 5/73），保留为辅助件（env 开关） |

## 实施步骤（本地影子库，不碰主库）

1. **自建镜像**：`Dockerfile.pg-zhparser` = `pgvector/pgvector:pg15` + 编译 zhparser（含 scws 依赖）
2. **影子容器**：独立 PG（端口 5433），`CREATE EXTENSION zhparser`；建 `chinese` 配置（`n,v,a,i,e,l,j` 映射 simple 保底英文）
3. **数据灌入**：`pg_dump ops_knowledge_chunks | psql 影子库`；fts_tokens 以 `to_tsvector('chinese', content)` 重算
4. **跑评测**：runner 指影子库（env 切 DSN），产出 `reports/r4-A.yaml`
5. **对比判读**：r4-A vs r4-2 / r4-D，重点 zh2zh / zh2en 的 kw 命中率与 recall@5 增量

## 验收

- [ ] `SELECT to_tsvector('chinese', '自动压缩')` 出词素（分词生效证明）
- [ ] r4-A.yaml 与 r4-2/r4-D 同表对比（分象限 recall@5 + kw 命中率）
- [ ] 结论回写契约 Q6 + `experiments/rag_compare/README.md`

**判读口径（预先约定，防事后解读）**：

- zh2zh recall@5 提升 **≥ +10pp** → A 有效，进入生产化成本评估（自建镜像上生产）
- 提升微弱 → 直接转 C 臂（稀疏向量）

## 不做

- 不碰主库/生产；不引 ES/独立检索服务；不与 C 臂并行（变量隔离）

## 风险

| 触发 | 行为 | 可重试 |
|---|---|---|
| arm64 编译 scws 失败 | 多阶段构建或换基底 | Y |
| 中文配置对纯英文文档退化 | 混合映射（CJK 走 zhparser，英文走 simple） | Y |

## 修订

| 日期 | 说明 |
|------|------|
| 2026-08-12 | 初版（AI 起草 · 待人审） |
