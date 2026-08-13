# Task：Qdrant Migration（pgvector dense 主路 → Qdrant）

> **状态**：active（闸由 00 代签推进 · 实现交子 agent · 00 仅关账）  
> **类型**：infra（向量存储迁移 · 架构解耦）  
> **关联**：`docs/spec/SPEC-qdrant-migration_v1.md`（v1.1 · HG-SPEC-SIGNOFF=approved）· 审查 `docs/harness/reviews/spec_qdrant-migration_audit_R1_20260813.md`  
> **分支**：`task/qdrant-migration`  
> **合入**：走 PR（禁直推 master）  
> **编排授权（2026-08-13 维护者）**：00 可代签本 task 全部人闸；**00 除关账外不改业务码/不跑实现**，20/30/40 交子 agent。

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

- [ ] fio / 硬件门禁记录落盘（或书面否决关 track）  
- [ ] Collection 配置符合 SPEC（on_disk、轻量 payload、过滤索引）  
- [ ] 对账：抽样 ≥500，L∞ &lt; 1e-5；Top-5 重叠 ≥ 95%；count 差 = 0  
- [ ] 构建期峰值 ≤ 3.8GB；稳态 &lt; 3.2GB  
- [ ] bench：`--baseline pgvector` 报告存在；Qdrant search P95 &lt; 150ms（过门禁才允许切流议案）  
- [ ] `RAG_VECTOR_BACKEND=pgvector` 默认行为与现网一致（单测）  
- [ ] Qdrant 失败：单次重试后 fallback PG；metric/日志可见  
- [ ] 影子写：PG commit 成功且 Qdrant 宕机时进 DLQ；重放幂等  
- [ ] 金样 vs `reports/r4-2.yaml`：recall@5 / best_relevance 不劣于（允许并列）  
- [ ] Flag 回滚演练通过；相关 pytest + ruff 绿  

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

- SPEC：`docs/spec/SPEC-qdrant-migration_v1.md`  
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

> 00 编排回填 · 30 由子 agent 交付 P0 · **未关账**（P1 实测未齐）。

- [x] SPEC v1.1 已签（HG-SPEC-SIGNOFF=approved）
- [x] task 含验收 / failure_paths / 非范围 / compare_with 锁死
- [x] HG-TASK-DRAFT approved（00 代签 · 维护者授权）
- [x] HG-AUDIT-R1 approved（00 代签 · 接受 20 审 C1–C3）
- [x] 30 P0 已交（`23508e8` · [30 实现](130d18e3-ff25-42ef-96c0-e7a582ba341b)）：Flag/hydrate/影子写+DLQ/脚本/单测 9 passed · verify PASS
- [ ] P1：真实 fio / 80 万灌库 / bench 双臂实测 / 金样 vs r4-2（脚本具备，本机未跑通）
- [ ] DLQ cron replayer（可选）
- [ ] 关账（00 执行 · 待 P1 或维护者指示「按 P0 关账」）

---

## 修订

| 日期 | 说明 |
| --- | --- |
| 2026-08-13 | 00 起草：承接 SPEC v1.1 人签；闸 pending；禁止 30 |
| 2026-08-13 | 维护者授权 00 代签全部人闸；00 除关账外不实现；HG-TASK-DRAFT=approved；派 20 子 agent |
| 2026-08-13 | 20 审 conditional_pass（C1–C3）；00 代签 HG-AUDIT-R1=approved；派 30 子 agent |
| 2026-08-13 | 30 P0 交卷 `23508e8`；00 核对 verify/单测；**暂不关账**（待 P1 或人令） |
