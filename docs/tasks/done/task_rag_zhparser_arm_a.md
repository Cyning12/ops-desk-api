# Task：RAG 关键词路 A 臂——zhparser 中文分词对照实验

> **状态**：completed  
> **类型**：对照实验（契约 Q6 裁决链路 · A/C 互斥候选）  
> **关联**：契约 Q6 · `experiments/rag_compare/` · 基准 `reports/r4-2.yaml` · D 臂 `reports/r4-D.yaml` · 定稿 `reports/r4-A.yaml`  
> **分支**：`task/rag-zhparser-arm-a`（自 `master` 新开）

---

## Harness 元信息


| 字段                           | 值                                                             |
| ---------------------------- | ------------------------------------------------------------- |
| **task_slug**                | `rag-zhparser-arm-a`                                          |
| **git_branch**               | `task/rag-zhparser-arm-a`                                     |
| **test_strategy**            | `required`                                                    |
| **test_strategy_note**       | 影子库 `to_tsvector('chinese', …)` 分词证明 + r4-A 与 r4-2/r4-D 分象限对比 |
| **code_quality_bar**         | `standard`                                                    |
| **graph_change_layer**       | `none`                                                        |
| **graph_delta**              | `none`                                                        |
| **graph_delta_note**         | 对照实验：自建镜像/影子库/env 开关；不改 G-L1 模块边界与对外契约路由 |
| **wiki_delta**               | `n/a`                                                         |
| **wiki_delta_note**          | 对照实验（影子库/镜像）；不改 coding_wiki 正文                                |
| **review_hat**               | `20`                                                          |
| **required_invoke_hats**     | `10,30`                                                       |
| **invoke_retention_profile** | `minimal`                                                     |
| **orchestration**            | 单 task · 与 C 臂互斥顺序执行                                          |




### 人工闸


| human_gate_id | status   | blocks_hats | 说明                                             |
| ------------- | -------- | ----------- | ---------------------------------------------- |
| HG-TASK-DRAFT | approved | 22-R1       | 维护者 2026-08-12 签收：采纳 Dockerfile/COPY 灌库/判读补充口径 |
| HG-AUDIT-R1   | approved | 30          | 维护者 2026-08-12 签收；审查文 `docs/harness/reviews/task_rag_zhparser_arm_a_audit_R1_20260812.md` |


---



## 目标

同一 runner、同一金样（73 条）、同一嵌入模型，**只换 fts 分词配置**（`simple` → `chinese`/zhparser），验证中文分词对关键词路的修复效果，产出与基准/D 臂可比的分象限 recall@5，为 Q6 的 A/C 裁决提供 A 侧证据。

## 前置事实（已实测）


| 项     | 状态                                                      |
| ----- | ------------------------------------------------------- |
| 病灶    | `simple` 对中文分词失明（kw 全死 → D 臂复活至 5/73）                   |
| 语料    | 混合 23% + 中文 2% + docs 全中文；未来中文为主（Q6 前提修正）               |
| 环境    | `pgvector/pgvector:pg15` **不含** zhparser / 编译链 → 需自建镜像  |
| D 臂结论 | glossary 边际改进（kw 5/73），保留为辅助件（env 开关）                   |
| 英文退化  | 实测：纯英文退化为按空格切分，等价 `simple`；纯英 chunk **不退化**             |
| 镜像坑   | 官方镜像无 gcc/make/`libscws-dev`，直接编译必挂；须 `USER root` 装依赖再编 |


---



## 实施步骤（本地影子库，不碰主库）



### 1) 自建镜像 `Dockerfile.pg-zhparser`

基底 `pgvector/pgvector:pg15`；`USER root` 装 `build-essential` / `git` / `libscws-dev`；源码编译 [amutu/zhparser](https://github.com/amutu/zhparser)；清理编译垃圾后 `USER postgres`。

```bash
docker build -f Dockerfile.pg-zhparser -t pg-zhparser:15 .
```

（arm64 已实测可过；失败则多阶段或换基底，见风险表。）

### 2) 影子容器 + 文本检索配置

独立 PG，端口 **5433→5432**。初始化 SQL：

```sql
CREATE EXTENSION IF NOT EXISTS zhparser;
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TEXT SEARCH CONFIGURATION chinese (PARSER = zhparser);
ALTER TEXT SEARCH CONFIGURATION chinese ADD MAPPING FOR n,v,a,i,e,l,j WITH simple;

-- 验收探针
SELECT to_tsvector('chinese', 'Kimi Code 自动压缩被取消');
-- 期望：中文已拆开（如 '自动' '压缩' '取消'）+ 英文按词
```



### 3) 数据灌入（禁止全量 `pg_dump | psql`）

全量 dump 会带上旧 `fts_tokens` GENERATED 定义（`simple`），还要 ALTER 重建。推荐：

1. 影子库建表：**不含** `fts_tokens` 生成列（列：`id, repo, source_type, source_id, chunk_index, content, metadata, images, content_hash, embedding, embedded_at` 等业务列）。
2. 主库导出 / 影子导入（CSV `COPY`，排除 `fts_tokens`）：

```bash
# 主库导出（示例 DSN/账号以本机为准）
psql "$PRIMARY_DSN" -c "\COPY (
  SELECT id, repo, source_type, source_id, chunk_index, content,
         metadata, images, content_hash, embedding, embedded_at
  FROM ops_knowledge_chunks
) TO '/tmp/chunks.csv' WITH CSV HEADER"

# 影子库导入
psql "$SHADOW_DSN" -c "\COPY ops_knowledge_chunks (
  id, repo, source_type, source_id, chunk_index, content,
  metadata, images, content_hash, embedding, embedded_at
) FROM '/tmp/chunks.csv' WITH CSV HEADER"
```

1. 再加 chinese 生成列 + GIN：

```sql
ALTER TABLE ops_knowledge_chunks ADD COLUMN fts_tokens tsvector
  GENERATED ALWAYS AS (to_tsvector('chinese'::regconfig, content)) STORED;
CREATE INDEX idx_ops_knowledge_chunks_fts_gin
  ON ops_knowledge_chunks USING gin (fts_tokens);
```



### 4) 跑评测（DSN 切影子库）

混合召回**融合逻辑不改**。影子侧须保证 **query 与 index 同用** `chinese`（否则实验无效）：生产默认仍 `simple`；影子评测用 env（如 `RAG_FTS_CONFIG=chinese`）切关键词路 `regconfig`，**勿**硬改融合/RRF。

```bash
export DATABASE_URL="postgresql+asyncpg://ops:ops_password@localhost:5433/opsdesk"
export RAG_FTS_CONFIG=chinese
# 关闭 D 臂展开，隔离变量（对照基准 r4-2）
export RAG_KW_EXPAND=false
.venv/bin/python evals/golden/run_eval.py --out reports/r4-A.yaml
```



### 5) 对比判读

r4-A vs r4-2 / r4-D；**主看 zh2zh**（中文 query × 中文/混合 docs）；zh2en 作辅证。结论回写契约 Q6 + `experiments/rag_compare/README.md`。

---



## 验收标准

- [x] `SELECT to_tsvector('chinese', 'Kimi Code 自动压缩被取消')` 中文词素已拆开（维护者实跑）
- [x] `reports/r4-A.yaml` 产出，与 r4-2 / r4-D 同表对比（分象限 recall@5 + kw 命中率）
- [x] 结论回写：`experiments/rag_compare/README.md` + `REPORT_q6_arms_vs_baseline_20260812.md`（裁决弃 A→C；契约正文随 C 臂）
- [x] 未碰主库/生产数据与生产镜像

**实测结论（2026-08-12 · 相对 r4-2）**：

| 指标 | r4-2 | r4-A | Δ |
|---|---|---|---|
| zh2zh recall@5 | 17/20（85%） | 17/20（85%） | **+0pp** |
| zh2en recall@5 | 19/25 | 19/26 | ≈持平 |
| kw 非空 | 5/71 | 5/73 | 仍几乎全死；zh2zh **0/20** |
| 同 id recall 翻转 | — | fixed=0 / regressed=0 | 无结构变化 |

→ 落在判读末档（&lt; +5pp）：**放弃 A 上生产，转 C 臂**。  
→ **保留 A 可调用入口**（不删）：`Dockerfile.pg-zhparser` · `experiments/rag_compare/zhparser_arm_a/` · env `RAG_FTS_CONFIG=chinese`（默认仍 `simple`）。

**判读口径（预先约定，防事后解读）**：


| zh2zh recall@5 增量（相对 r4-2） | 裁决                                |
| -------------------------- | --------------------------------- |
| **≥ +15pp**                | 果断走 A；Dockerfile 纳入 CI 自动构建       |
| **≥ +10pp 且 < +15pp**      | A 有效，进入生产化成本评估（自建镜像运维 ≈ 0.5 人天/月） |
| **+5～8pp**                 | **放弃 A → 转 C 臂**（自定义镜像运维成本不值）     |
| **&lt; +5pp / 微弱**            | 直接转 C 臂（稀疏向量）                     |


---



## 不做

- 不碰主库/生产；不引 ES/独立检索服务
- 不与 C 臂并行施工（变量隔离：先 A 后 C）
- 不改 RRF / 语义路 / 嵌入模型
- 不把全量 `pg_dump` 当灌库主路径

---



## 失败路径


| 触发                          | 行为                              | 可重试 |
| --------------------------- | ------------------------------- | --- |
| arm64 编译 scws / zhparser 失败 | 多阶段构建或换基底                       | Y   |
| COPY 灌库列不一致 / 序列漂移          | 对齐列清单；必要时 `setval` 修 serial     | Y   |
| query 仍用 `simple` 导致 kw 假死  | 强制影子评测 `RAG_FTS_CONFIG=chinese` | Y   |
| 提升落在 +5～8pp 灰色带             | 按口径转 C，不追加调参拖延                  | —   |


---



## 风险


| 触发                               | 行为                          | 可重试 |
| -------------------------------- | --------------------------- | --- |
| 官方 pgvector 镜像缺编译链/`libscws-dev` | 按 §1 Dockerfile 装齐再编        | Y   |
| 中文配置影响纯英文                        | 实测退化为空格切分≈simple；主看 zh2zh   | —   |
| K8s/Swarm 上生产要换自定义镜像             | 成本计入 ≥+10pp 门槛；+5～8pp 直接弃 A | —   |


---



### 自检结论（执行者）

> 30/40 回填区（命令、退出码、验收摘要、已知未测项）。

- [x] 闸：`HG-TASK-DRAFT` approved · `HG-AUDIT-R1` 已签 · `harness verify` PASS（2026-08-12）
- [x] 镜像构建通过；影子库分词探针通过（维护者实跑）
- [x] r4-A 已出并完成分象限对比表（zh2zh +0pp → 弃 A 转 C）
- [x] 未污染主库；契约 Q6 正文回写可随 C 臂
- [x] 本地单测通过；runner 已支持逐条落盘 / `--resume` / `--from-log`

**40 命令与结果（2026-08-12）**

| 命令 | 退出码 | 结果 |
|------|--------|------|
| `uv run pytest tests/test_rag_fts_config.py tests/test_golden_eval_runner.py -q --tb=short` | 0 | 16 passed（后增 from-log 单测 → 11 in golden file alone） |
| `uv run ruff check app/ops/rag/retrieve.py` | 0 | All checks passed |

**维护者实跑**：docker build · 影子库探针 · COPY 8574 · `reports/r4-A.yaml`（日志恢复 + 逐条落盘改造）。

**交付摘要**：A 臂对照完成 · zh2zh +0pp → **弃 A 上生产、转 C** · 保留 `Dockerfile.pg-zhparser` / `zhparser_arm_a/` / `RAG_FTS_CONFIG=chinese`（默认仍 `simple`）。

---

### KPI

| 项 | 分 |
|---|---|
| Task_KPI% | 100 |

## CLOSE

| 项 | 内容 |
|---|---|
| 日期 | 2026-08-13 |
| 定稿 | zh2zh +0pp · 弃 A→C · `reports/r4-A.yaml` |
| 归档 | `docs/tasks/done/task_rag_zhparser_arm_a.md` |
| A 入口 | 保留（不删）；生产 FTS 默认仍 `simple` |

## 修订

| 日期 | 说明 |
|------|------|
| 2026-08-12 | 初版（AI 起草 · 待人审） |
| 2026-08-12 | HG-TASK-DRAFT 签收；写入 Dockerfile/COPY 灌库/英文退化实测/判读三档（含 +5～8pp 弃 A）与 `RAG_FTS_CONFIG` 同配置约束 |
| 2026-08-12 | HG-AUDIT-R1 签收；派 30/40；实跑镜像/灌库/r4-A 留给维护者 |
| 2026-08-12 | 50 初验 PASS（附条件）；补 graph_delta_note；实跑仍待维护者 |
| 2026-08-12 | 实测 r4-A：zh2zh +0pp、kw 仍死 → **弃 A 转 C**；保留 `RAG_FTS_CONFIG` / Dockerfile / 影子脚本入口 |
| 2026-08-13 | 关账：验收全勾 · KPI · CLOSE；归档 done |


