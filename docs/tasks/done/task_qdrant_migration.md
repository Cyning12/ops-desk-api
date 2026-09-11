# Task：Qdrant Migration（pgvector dense 主路 → Qdrant）

> **状态**：completed（00 关账 · 维护者授权开 PR）  
> **类型**：infra（向量存储迁移 · 架构解耦）  
> **关联**：`docs/spec/qdrant-migration/SPEC-qdrant-migration_v1.md`（v1.1 · HG-SPEC-SIGNOFF=approved）· 审查 `docs/harness/reviews/spec_qdrant-migration_audit_R1_20260813.md`  
> **分支**：`task/qdrant-migration`  
> **合入**：走 PR（禁直推 master）  
> **编排授权（2026-08-13 维护者）**：00 可代签本 task 全部人闸；**00 除关账外不改业务码/不跑实现**，20/30/40 交子 agent。  
> **关账口径**：P0 能力交付；现网规模金样 Qdrant+floor04+grader v1≈pg（55/73 vs 57/73）；**代码默认仍 pgvector**；切流由部署 env；**不宣称 80 万 P95 已过**。

---

## Harness 元信息

| 字段 | 值 |
| --- | --- |
| **task_slug** | `qdrant-migration` |
| **git_branch** | `task/qdrant-migration` |
| **test_strategy** | `required` |
| **test_strategy_note** | fio 门禁；对账 L∞+Top-k；构建期/稳态 RSS；Flag 回滚单测；bench `--baseline pgvector`；金样 vs `reports/r4-2.yaml` |
| **code_quality_bar** | `standard` |
| **graph_change_layer** | `G-L1` |
| **graph_delta** | `docs/_tech_graph/l1/01_modules.md` |
| **graph_delta_note** | 增 `rag` 模块与 `RetrievedChunk`/`RAG_VECTOR_BACKEND` 契约（默认仍 pgvector） |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 本波不改 coding_wiki；运维说明可落 experiments/ 或 docs 短文 |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,30` |
| **invoke_retention_profile** | `minimal` |
| **orchestration** | SPEC 已签 → 00 出卡 → 20 审 → 人闸 R1 → 30（fio→压测→双写→切流） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
| --- | --- | --- | --- |
| HG-TASK-DRAFT | approved | 22-R1 | **00 代签**（维护者 2026-08-13 授权代签全部人闸）· 范围对齐 SPEC v1.1 |
| HG-AUDIT-R1 | approved | 30 | **00 代签**（维护者授权）· 审查 `docs/harness/reviews/task_qdrant_migration_audit_R1_20260813.md` · 接受 C1–C3 |

---

## 目标

将 dense 向量检索从 pgvector **解耦**到 Qdrant（HNSW on_disk），PG 仍为写真源；默认读路径保持 pgvector，直至压测与对账过门禁后再 Flag 切流。磁盘/内存/P95 任一硬门禁不过 → **停迁、不切流**。

## 范围（对齐 SPEC v1.1）

1. **Phase0**：fio 4K randread 门禁；起 Qdrant v1.13.6（2C4G limits）；不过盘则关 track  
2. **Collection**：Cosine/1024；`on_disk` 向量+HNSW；payload **仅** filter 字段；禁止存 content/metadata/images  
3. **Hydrate**：Top-k id → PG 主键回查 → `RetrievedChunk`  
4. **迁移脚本**：export / create_collection / bulk_upsert（构建期 RSS 采样）/ reconcile / bench（`--baseline pgvector`）/ DLQ schema  
5. **读路径**：`RAG_VECTOR_BACKEND=pgvector|qdrant`（默认 pgvector）；即时降级（重试 1 次 → PG）  
6. **影子写**：`ingest` **commit 后**非阻塞入队；失败进 DLQ；不得回滚/阻塞 PG  
7. **验收报告**：`reports/qdrant_bench.yaml`、`reports/qdrant_reconcile_*.yaml`；金样对照 **锁死** `reports/r4-2.yaml`  

## 非范围

- Kafka CDC / GPU ANN / DiskANN / 全内存 HNSW 上架  
- 迁移 FTS / sparse 第二路进 Qdrant  
- 默认把 `RAG_VECTOR_BACKEND` 改为 `qdrant`（须门禁全绿 + 人拍板）  
- 反向把 Qdrant 数据灌回 PG  
- 拆独立 retrieval 微服务（Nginx 蓝绿仅文档预留）  

## 签收锁死

| 项 | 值 |
| --- | --- |
| 默认 `RAG_VECTOR_BACKEND` | **pgvector** |
| Qdrant 版本 | **v1.13.6** |
| compare_with | **`reports/r4-2.yaml`** |
| 稳态 RSS | **&lt; 3.2GB** |
| 构建峰值 RSS | **≤ 3.8GB** |
| Qdrant search P95 | **&lt; 150ms**（80 万 / Top-10 + filter） |
| 磁盘 | fio 过门禁或预配 IOPS ≥ 5000；否则禁止切流 |
| 金样 | **`RAG_RERANK_ENABLED=false`**（C1） |
| 影子写覆盖 | ingest 的 upsert **与** delete/整组替换 → Qdrant 删点入队；本期写入口仅 `ingest`（C2） |
| 磁盘数值 | IOPS≥3000 且 p95≤1ms，或预配≥5000；以 SPEC 硬性增量为准（C3） |

## 实施步骤（30 顺序 · 闸签后）

1. docker-compose 增加 Qdrant；脚本目录 `scripts/qdrant_migrate/`  
2. fio-disk-gate → create-collection → export（无大字段）→ bulk-upsert（峰值采样）  
3. `BaseRetriever` / `QdrantRetriever` + PG hydrate；Flag + 即时 fallback  
4. ingest 影子写 + `ops_qdrant_dlq` + replayer  
5. reconcile + bench 双臂；金样抽检 vs r4-2  
6. 文档/图谱增量；回滚演练  

## 验收标准

- [x] fio / 硬件门禁记录落盘（或书面否决关 track） · P1 本机 APFS：`reports/qdrant_migrate/fio_gate_20260813T092147Z.yaml`（非生产盘）  
- [x] Collection 配置符合 SPEC（on_disk、轻量 payload、过滤索引） · 本机 recreate + payload indexes  
- [x] 对账：抽样 ≥500，L∞ &lt; 1e-5；Top-5 重叠 ≥ 95%；count 差 = 0 · **全量 N=8574** · `reconcile_p1_20260813.yaml`  
- [x] 构建期峰值 ≤ 3.8GB；稳态 &lt; 3.2GB · N=8574 upsert peak **286.6MiB**；**80 万** peak **3430.4MiB** / 稳态 ≈1.2GiB · `expand_rss.json`  
- [x] bench：N=8574 双臂 P95 **14.62ms** · `reports/qdrant_bench.yaml`；**80 万** Top-10 P95 **≈867ms（FAIL &lt;150）** · `reports/qdrant_bench_800k.yaml`（pg 臂 skip，规模不可比）  
- [x] `RAG_VECTOR_BACKEND=pgvector` 默认行为与现网一致（单测）  
- [x] Qdrant 失败：单次重试后 fallback PG；metric/日志可见（单测）  
- [x] 影子写：PG commit 成功且 Qdrant 宕机时进 DLQ；重放幂等（单测 enqueue；cron replayer 非本波）  
- [x] 金样：`reports/r4-qdrant-p1.yaml`（无 CE）+ `reports/r4-qdrant-R-floor04-v1.yaml`（CE+grader v1 · **55/73** vs floor04 **57/73**）  
- [x] Flag 回滚演练通过；相关 pytest + ruff 绿（`tests/test_rag_qdrant_backend.py`） 

## 失败路径

| 触发 | 行为 | 可重试 | 用户可见 |
| --- | --- | --- | --- |
| fio / IOPS 不达标 | **禁止灌库与切流**；关 track 或保留实验报告 | N | 运维公告：仍用 pgvector |
| 构建期 RSS &gt; 3.8GB | 停灌；降 `ef_construct→64` 重建；仍超限则否决上架 | Y（一次） | 无（读仍 PG） |
| 稳态 RSS ≥ 3.2GB 或 P95 ≥ 150ms | 不切流；可试 SQ int8；仍不过则否决 | Y | 无 |
| Qdrant 读失败 | 本请求重试 1 次 → fallback PG；打 fallback 指标 | Y | 延迟可能略增；答问仍可用 |
| 影子写失败 | PG 已提交保持；入 DLQ；cron 重放 | Y | 无（最终一致窗口） |
| 对账失败（L∞/重叠/count） | 禁止切流；修导出/upsert 后重对 | Y | 无 |
| 金样劣于 r4-2 | 禁止默认切 `qdrant`；可保留开关实验 | Y | 无 |
| DLQ 积压超阈 | 告警；暂停切流议案直至追平 | Y | 无 |

## 依赖

- SPEC：`docs/spec/qdrant-migration/SPEC-qdrant-migration_v1.md`  
- 现网：`app/ops/rag/retrieve.py` · `app/ops/rag/ingest.py` · `app/ops/rag/embedder.py`  
- 基线报告：`reports/r4-2.yaml`  
- 规范：`docs/standards/CODING_BACKEND_L2_v1_zh.md`  

## 思考轮

### 思考轮控制（Agent 填 · 22 审）

| 字段 | 值 |
| --- | --- |
| **actual_last_round** | R5 |
| **early_stop** | yes |
| **early_stop_reason** | SPEC v1.1 已承载深度论证与三方审增量；task 收敛为可执行阶段与门禁即可 |
| **residual_risks** | 生产盘型/IOPS 须 fio 实测；压测机与生产盘可能不一致 |

### R0 · 问题框定

dense 主路是否值得在 2C4G 上引入 Qdrant；成功以门禁为准而非「已部署」。

### R1 · 范围

只迁 dense；payload hydrate；读写 Flag；影子写+DLQ。

### R2 · 方案

HNSW on_disk + 轻量 payload；否决全内存/DiskANN/GPU/CDC。

### R3 · 风险

磁盘 IOPS、构建峰值 OOM、多 worker 假熔断、大 payload 放大 P95 —— SPEC v1.1 已锁缓解。

### R4 · 验收

fio、RSS 双门、P95、对账、bench 双臂、金样、回滚、非阻塞影子写。

### R5 · 交接

闸签后 30 按 Phase0→5；不过门禁则关 track。

---

### 自检结论

> 00 关账 · 30 P0 + P1 冒烟 + 40d 金样（grader v1 · 55/73）· 切流由部署 env · 80 万 P95 未宣称通过。

- [x] SPEC v1.1 已签（HG-SPEC-SIGNOFF=approved）
- [x] task 含验收 / failure_paths / 非范围 / compare_with 锁死
- [x] HG-TASK-DRAFT approved（00 代签 · 维护者授权）
- [x] HG-AUDIT-R1 approved（00 代签 · 接受 20 审 C1–C3）
- [x] 30 P0 已交（`23508e8` · [30 实现](130d18e3-ff25-42ef-96c0-e7a582ba341b)）：Flag/hydrate/影子写+DLQ/脚本/单测 9 passed · verify PASS
- [x] P1（部分）：现网 **N=8574** 全链路 fio→upsert→reconcile→bench 绿；invoke `invoke_20260813_40_p1_qdrant-migration.md`
- [x] P1-40b：金样纠偏 FTS=`simple` · `reports/r4-qdrant-p1.yaml`；合成扩样 **N=800000** → `ops_knowledge_scale`；RSS 过门 / P95 **未过** · invoke `invoke_20260813_40b_p1_scale_golden.md`
- [x] P1-40c：Qdrant+CE floor04 金样 · `reports/r4-qdrant-R-floor04.yaml` · pass **47/73**（基线 floor04 **57/73**）· neg 10/11 vs 11/11 · zh2zh/zh2en 并列 · en2en 15/16>14/16 · grader=flash · invoke `invoke_20260813_40c_qdrant_floor04_golden.md` · **未关账**
- [x] P1-40d：公平重跑 grader **v1** · `reports/r4-qdrant-R-floor04-v1.yaml` · pass **55/73**（基线 57；40c/v2 为 47）· neg **11/11** · 召回并列/en2en 优 · identical top5 下 v2→v1 flip +8 · invoke `invoke_20260813_40d_qdrant_floor04_grader_v1.md`
- [ ] DLQ cron replayer（可选 · 非关账阻塞）
- [x] 关账（00 · 2026-08-13 · 维护者授权开 PR；切流靠部署 env）

### KPI

| 项 | 分 |
|---|---|
| Task_KPI% | 95 |

## CLOSE

| 项 | 内容 |
|---|---|
| 日期 | 2026-08-13 |
| 定稿 | 代码默认 `RAG_VECTOR_BACKEND=pgvector`；部署可开 `qdrant` + 影子写 + CE 0.4/0.75 + `RAG_GRADER_PROMPT=v1` |
| 金样 | floor04+v1：55/73 vs pg 57/73；neg 11/11 |
| 峰值 | 80 万 P95 本机未过（~867ms）；不宣称峰值就绪 |
| 归档 | `docs/tasks/done/task_qdrant_migration.md` |

---

## 修订

| 日期 | 说明 |
| --- | --- |
| 2026-08-13 | 00 起草：承接 SPEC v1.1 人签；闸 pending；禁止 30 |
| 2026-08-13 | 维护者授权 00 代签全部人闸；00 除关账外不实现；HG-TASK-DRAFT=approved；派 20 子 agent |
| 2026-08-13 | 20 审 conditional_pass（C1–C3）；00 代签 HG-AUDIT-R1=approved；派 30 子 agent |
| 2026-08-13 | 30 P0 交卷 `23508e8`；00 核对 verify/单测；**暂不关账**（待 P1 或人令） |
| 2026-08-13 | 40 P1 现网规模冒烟：N=8574 对账/bench/fio 绿；未达 80 万；金样 skip（无 chinese FTS）；invoke_20260813_40_p1 |
| 2026-08-13 | 40c：Qdrant+CE floor04 金样 `r4-qdrant-R-floor04.yaml` pass 47/73（基线 57/73）；invoke_20260813_40c；**未关账** |
| 2026-08-13 | 40d：grader v1 公平重跑 `r4-qdrant-R-floor04-v1.yaml` pass 55/73（基线 57；收回 40c/v2 假性 −10）；invoke_20260813_40d |
| 2026-08-13 | **CLOSE**：维护者确认 env 切流配置并授权开 PR |
