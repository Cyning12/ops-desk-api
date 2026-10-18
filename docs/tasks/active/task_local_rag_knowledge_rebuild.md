# Task：local-rag-knowledge-rebuild（B2 · 本地 RAG 知识库重建：语料→embedding→PG ops_knowledge_chunks + Qdrant ops_knowledge 双侧重灌 · 含写动作）

> **状态**：done（2026-10-18 40 实证执行完成：8648/8648/8648 三对照 · 水位 verdict=match · DLQ=0 · 规模 8648∈[6000,12000] · 降级向量抽检锚 issue#2720 双中 · 零落码零 diff · pytest 13 passed · LINT PASS；报告 reports/local_rag_knowledge_rebuild_20261018T0731Z.md）
> **类型**：本地运维重建（**含写动作——PG ops_knowledge_chunks 写入 + Qdrant ops_knowledge 点写入**；建议零落码 · 40 实证执行棒 · 承 task_local_qdrant_orphan_points_cleanup 先例）
> **上游**：本地向量数据态三线闭合（2026-10-18）：水位亲跑 mismatch（PG 0 / Qdrant 8574）→ [`task_local_vector_data_state_audit.md`](../done/task_local_vector_data_state_audit.md) 溯源判定 8574 为迁移期正当重迁 + PG 表级清空 → [`task_local_qdrant_orphan_points_cleanup.md`](../done/task_local_qdrant_orphan_points_cleanup.md) 删 8574。现状：ops_knowledge_chunks=0 行 · Qdrant ops_knowledge=0 points · 水位 verdict=match（0/0/0）——**本地 RAG 无知识可检**。维护者 2026-10-18（会话 m01159）授权自动推进 B2=本地 RAG 知识库重建
> **分支**：无（建议零落码 · 零 git 操作纪律；报告/invoke 产物提交与否由 00/维护者事后裁定）
> **现网默认**：`RAG_VECTOR_BACKEND=qdrant`（compose Qdrant v1.19.0 · 卷 qdrant_data · REST 6333 本机映射）· `RAG_QDRANT_SHADOW_WRITE=true`（.env 已配）

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `local_rag_knowledge_rebuild` |
| **git_branch** | 无（零落码建议 · 零 git 操作） |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 实证 + 机断混合：本地 compose 真实执行（dry-run 计数 → 全量重建 → 水位双侧核验 → 检索抽检全链命令+输出留档）；零落码故无新代码、无新测试；`tests/test_check_vector_waterline.py` 复跑零红作零越界旁证 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `none` |
| **graph_delta** | `none` |
| **graph_delta_note** | 建议零落码（现成 CLI `scripts/rag_ingest.py` + 既有影子写开关 + 只读核验脚本，全链零新码）；无新模块/路由/表/事件类型/配置改动；若执行中裁定须落 `scripts/` 工具码即 STOP 退回补 30 棒+图谱闸评估（FP-8） |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 本地运维重建留痕属运维证据；是否回写路线/wiki 由维护者阅报后裁定，非本 task |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,40` |
| **invoke_retention_profile** | `default`（实取 10+40 · 零落码建议下无 30 改码棒 · 20 按授权） |
| **experience_capture** | `recommended` |
| **kpi_aggregator** | `n/a` |
| **orchestration** | 10 落稿 → 20 R1（按维护者授权取舍）→ 维护者签闸 → 40 实证执行（F1 前置核验 → F2 dry-run 计数 → F3 全量重建 → F4 双侧核验 → F5 检索抽检）+ 报告落盘 + 验收勾选/自检结论回填 → CLOSE |
| **freeze_id** | 无 |
| **related_tasks** | [`task_local_qdrant_orphan_points_cleanup.md`](../done/task_local_qdrant_orphan_points_cleanup.md)（直接上游 · 40 单棒先例）· [`task_local_vector_data_state_audit.md`](../done/task_local_vector_data_state_audit.md)（溯源母体）· [`task_qdrant_migration.md`](../done/task_qdrant_migration.md)（8574 迁移与对账先例）· [`task_prod_vector_waterline_check.md`](../done/task_prod_vector_waterline_check.md)（水位核查脚本母体） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | approved | 20, 40 | 2026-10-18 维护者 m01159「完成后继续自动开启下一项任务」授权链（承 m00238/m01101）00 代录 · 签注：embedder=api（SiliconFlow bge-m3）· docs roots=两历史目录（05-plan+contracts）· 规模区间 [6000,12000] 越限即停 |
| HG-AUDIT-R1 | approved | 40 | R1 签收零阻塞 nit×4 照登（[审查文](../../harness/reviews/task_local_rag_knowledge_rebuild_audit_R1_20261018.md)）· 2026-10-18 维护者 m01159 授权链 00 代录 |
| HG-GRAPH-MODULES | n/a | — | `graph_change_layer=none` 零图谱改动（建议零落码 · 无新模块/路由/表/事件）；若执行中裁定转落码即 FP-8 STOP 回抛并补签本闸 |

> 关联闸照登：HG-PROD-READONLY-ACCESS 仍 pending（仅阻生产侧任何动作）；**本 task 零涉生产**（本地 compose 口径），不受其阻、也不消解之（FP-9）。

---

## 背景与目标

本地向量数据态三线闭合后，`ops_knowledge_chunks`=0 行、Qdrant `ops_knowledge`=0 points、水位 verdict=match（0/0/0）——数据态自洽但**知识为空**，本地 RAG 检索链（retrieve→grade→answer）与金样评测（`evals/golden/queries_v1.yaml` 73 条）失去语料支撑。本 task 从既有语料源（PG 源表 issues/pulls + ops-desk-workspace docs）经既有入库管线重建本地知识库，写 PG 与 Qdrant 双侧，并以水位核验 + 检索抽检实证「知识可检」。

### 实证锚点（10 亲跑亲读 2026-10-18 · 40 必读）

| 主题 | 命令 / 路径 · 锚点 | 现状（亲跑实录） |
|------|---------------------|-------------------|
| 重建管线 CLI | `scripts/rag_ingest.py`（88 行全文亲读） | 用法：`python scripts/rag_ingest.py [--dry-run] [--only issues\|pulls\|docs] [--docs-root ...] [--embedder st\|api] [--limit N]`（:41-53）；docstring :12-14 历史全量形态 = `--docs-root ../ops-desk-workspace/docs/05-plan --docs-root ../ops-desk-workspace/docs/contracts`；同步 psycopg 引擎（:59）；`app/config.py:11` import 即 load_dotenv 仓根 .env → CLI 直跑即可见 RAG_QDRANT_SHADOW_WRITE/SILICONFLOW_API_KEY |
| 入库核心 | `app/ops/rag/ingest.py`（304 行全文亲读） | `ingest()`（:179）：content_hash 水位对比（:186-191 · 空库→全量 to_upsert）→ clean/chunk/前缀（:204-222 · E7 空正文单元仅标题 chunk :213-215 · 注释记历史全量实测 9/2748）→ 批量 embed+维度断言 1024 不符即停（:225-230）→ **整组替换逐单元 PG commit（:284）→ 影子写 enqueue_shadow_upsert（:287）** → 全集对账删墓碑（:292-302）；返回报告 {scanned,to_upsert,unchanged,to_delete,chunks_written}（:192-198） |
| 影子写开关与 DLQ | `app/ops/rag/shadow_write.py` | `shadow_write_enabled()`（:27-32）读 `RAG_QDRANT_SHADOW_WRITE`；.env 实证 `=true`；PG commit 后 ThreadPoolExecutor 异步 upsert Qdrant（:111-128 · point_id=PG chunk id）；失败进 `ops_qdrant_dlq` 表（:150-184）**不回滚不阻塞**——故核验必须含 DLQ depth=0（FP-5） |
| Embedder 两路 | `app/ops/rag/embedder.py` | `--embedder api` = ApiEmbedder（SiliconFlow OpenAI 兼容 /embeddings · model=BAAI/bge-m3 · 缺 SILICONFLOW_API_KEY 即 raise 拒绝本地回落 :78-81 · HTTP 失败重试 3 次指数退避后抛错 :90-110）；`--embedder st` = SentenceTransformerEmbedder（本地 bge-m3 ~2.3GB 懒加载 :34-47）；两路 `name` 同为 "BAAI/bge-m3" fingerprint 一致无混库风险（:7-8）；查询侧默认 ApiEmbedder（:147-171） |
| 语料源数据面 | `docker exec ops-desk-api-db-1 psql -U ops -d opsdesk` 亲跑 2026-10-18 | **ops_issues=881 · ops_pull_requests=1855（均 MoonshotAI/kimi-code · repos 另含 Cyning12/ai-ink-brain-api-python 但无 issue/pr 行）· ops_knowledge_chunks=0 · ops_qdrant_dlq=0**；docs 语料：`../ops-desk-workspace/docs` 92 篇 md（contracts=8 · 05-plan=11 两历史 root） |
| 历史规模基准 | `reports/qdrant_reconcile_20260813T125801Z.yaml` | status=pass · **pg_count=qdrant_count=8574** · max_l_inf=0.0 · mean_topk_overlap=1.0（2026-08-13）——历史常态是有数据且双侧逐向量一致 |
| 历史语料分布 | `docs/harness/invokes/by-task/local-vector-data-state-audit/evidence/e04_scroll_stats.txt` | 8574 id（min=1 max=8593）；150 抽样 source_type dist {issue:54, pr:55, doc:41} · repo dist {MoonshotAI/kimi-code:109, ops-desk-workspace:41} · chunk_index max 19 → 量级 ≈3.1 chunks/unit |
| Qdrant collection 现状 | `curl -s http://127.0.0.1:6333/collections/ops_knowledge` 亲跑 2026-10-18 | status=green · **points_count=0** · dim=1024 Cosine · on_disk vectors/HNSW/payload · m=12 ef_construct=80（与 `scripts/qdrant_migrate/create_collection.py:19-20` 缺省一致）——**collection 已存在且配置正确，重建无需 recreate** |
| 容器与密钥前提 | `docker ps` 亲跑 2026-10-18 · .env grep | `ops-desk-api-db-1` + `ops-desk-api-qdrant-1` 均 Up 2 days (healthy)；`SILICONFLOW_API_KEY` 在 .env 存在且非空（grep 计数=1 · 值不落档）；`RAG_QDRANT_SHADOW_WRITE=true` |
| 删后水位基线 | `reports/vector_waterline_local_20261018T005534Z.yaml`（上游 40 实证） | pg=0 · qdrant=0 · count_diff=0 · verdict=match · dlq empty · degraded=false——本 task 重建前的零点基线 |
| 验证脚本 | `scripts/check_vector_waterline.py`（366 行全文亲读） | 只读硬约束（:4-6 禁写 API）；`--env local` 复跑：PG 行数/水位/DLQ + Qdrant count/scroll id 集对账 verdict（:154-184）· 报告落 `reports/vector_waterline_local_<UTCts>.yaml`（:274-281）；重建后预期 pg=qdrant>0 verdict=match |
| 检索抽检路径 | `scripts/rag_smoke.py`（51 行全文亲读）· `scripts/lg_rag_smoke.py` | rag_smoke G01 默认 query（:23）走 retrieve→grade→answer 全链（需 LLM env）；轻量降级=纯向量检索（嵌入 query→Qdrant search→断言 top-5 含 issue#2720）不假绿标注（FP-7） |
| 金样依赖 | `evals/golden/queries_v1.yaml`（575 行）· `evals/golden/run_eval.py:51` | **73 条金样查询**（`grep -c '^  - id: G'` 实测）· expect_hit 锚 28 个 distinct source_id · G01–G05 锚 kimi-code issue#2720、G06/G07 锚 #1566——PG 实证 2720/1566 均在 ops_issues；**金样召回评测依赖本知识库**（重建是其前置）；全量金样评测非本 task（见非范围） |
| pytest 依赖面 | grep tests/ 亲跑 | 无 pytest 测试依赖活体知识库语料（conftest.py:233 自建表 · test_chat_ws.py:101 注明语料为空也无妨）；`tests/test_check_vector_waterline.py` 13 测为桩测 |
| expand_synthetic 不适用裁定 | `scripts/qdrant_migrate/expand_synthetic.py`（248 行全文亲读） | 定位=Qdrant→Qdrant 向量复制合成扩样（**不写 PG** · :2 注释 · --source 缺省 ops_knowledge :91 · --target 缺省 ops_knowledge_scale :92 · --target-n 缺省 800_000 :93）；:110-111 source 空即 `raise SystemExit("source ops_knowledge empty")`——**当前 source=0 不可用，且其语义是压测扩样非知识恢复 → 非范围钉死** |

### 目标

F1 前置核验（容器/密钥/collection 三面实证 · 缺一降级不硬闯）→ F2 dry-run 计数（`--dry-run` 出 scanned/to_upsert 基线 · 规模裁定核验）→ F3 全量重建执行（`rag_ingest.py` 全量：issues+pulls+docs · PG 整组替换逐单元 commit + 影子写 Qdrant · 报告落档）→ F4 双侧一致性核验（水位脚本复跑 pg=qdrant>0 verdict=match · DLQ empty · 计数三对照）→ F5 检索抽检（G01 锚 issue#2720 命中实证）+ 报告落盘。全链不假绿、规模不凑数。

---

## 范围

- **F1 · 前置核验（降级前置）**：
  - `docker ps`/`docker inspect` 实证 `ops-desk-api-db-1` + `ops-desk-api-qdrant-1` Up (healthy)（异常按 FP-2 分支处理，不硬闯）。
  - .env 密钥核验：`SILICONFLOW_API_KEY` 存在非空（grep 计数留档 · **密钥值永不落档**）；`RAG_QDRANT_SHADOW_WRITE=true` 留档。
  - Qdrant collection 核验：`GET /collections/ops_knowledge` 实证 points_count=0 · dim=1024 · Cosine 留档（若 collection 缺失→走 `scripts/qdrant_migrate/create_collection.py` 缺省参数创建并留档；若 dim≠1024 即 FP-4 STOP 防混库）。
- **F2 · dry-run 计数（只读 · 规模裁定核验）**：
  - `python scripts/rag_ingest.py --dry-run --docs-root ../ops-desk-workspace/docs/05-plan --docs-root ../ops-desk-workspace/docs/contracts`（零写库 · 不加载模型）。
  - 报告 {scanned, to_upsert, unchanged, to_delete} 落档；空库预期 scanned=to_upsert · unchanged=0 · to_delete=0。
  - **规模裁定核验**：scanned 与语料面预期对照（881 issues + 1855 pulls + docs roots 实数）；显著不符即 FP-4 STOP 查因照登，禁带病重建。
- **F3 · 全量重建执行（本 task 写动作）**：
  - `python scripts/rag_ingest.py --docs-root ../ops-desk-workspace/docs/05-plan --docs-root ../ops-desk-workspace/docs/contracts --embedder api`（默认建议 api=SiliconFlow · 与查询侧 fingerprint 同源；速率/成本面实测留档——总 chunks 量级 × 平均 token 估算入报告 · 若执行时实证 API 不稳可签注降判 `--embedder st`，fingerprint 同名无混库风险但须留档裁定理由）。
  - ingest 报告 {scanned, to_upsert, chunks_written, to_delete} 全文落档；**chunks_written 必须 >0 且与 PG 实落行数一致**。
  - embedding 中途失败：ApiEmbedder 重试 3 次后抛错 → 进程非零退出如实记；管线逐单元 commit 崩溃可续（水位跳过已写 · ingest.py:232 注释），重跑续传；**禁假绿**（FP-3）。
  - 进程退出前影子写沉降：ThreadPoolExecutor 进程退出 join 兜底，但 F4 核验前须实证 Qdrant 侧点数追上（不齐则按 FP-5/FP-6 处置，不等待无证据假设）。
- **F4 · 双侧一致性核验（只读 · 硬闸验收）**：
  - 复跑 `python scripts/check_vector_waterline.py --env local`：预期 **pg_count == qdrant_count > 0 · count_diff=0 · verdict=match · dlq verdict=empty · degraded=false**；报告落 `reports/vector_waterline_local_<UTCts>.yaml`。
  - 三对照：ingest 报告 chunks_written == PG ops_knowledge_chunks 行数 == Qdrant points_count；任一不符即 FP-5 不假绿。
  - DLQ 核验：ops_qdrant_dlq depth=0；非零即影子写失败证据照登（FP-5），裁定差集补写路径（`export_vectors.py`→`bulk_upsert.py` 既有迁移链路 · 零落码可用）。
- **F5 · 检索抽检与留档收口**：
  - 抽检实证「知识可检」：首选 `.venv/bin/python scripts/rag_smoke.py`（G01 默认 query · retrieve hits 非空且含 issue#2720 锚 · grade/answer 留档）；LLM env 不可用时降级为纯向量检索（嵌入 G01 query → Qdrant search → top-5 含 source_type=issue source_id=2720）**显式标注降级形态，不冒充全链**（FP-7）。
  - 重建报告落 `reports/local_rag_knowledge_rebuild_<UTCts>.md`：F1–F5 全链命令+输出索引 · 规模裁定对照（dry-run scanned → 终值 chunks_written vs 历史 8574 量级）· embedding 成本/速率实测 · disclaimer（本地/compose 口径不得外推生产）。
  - 40 invoke + 证据附件落 `docs/harness/invokes/by-task/local-rag-knowledge-rebuild/`；本档验收勾选+自检结论+修订记录回填。

## 非范围

- **生产环境任何访问**（HG-PROD-READONLY-ACCESS 仍 pending · 不消解 · FP-9）。
- **规模凑数/扩样**：`scripts/qdrant_migrate/expand_synthetic.py` 为压测扩样工具（source 空即退出 :110-111 · 不写 PG），本 task 明确不取；重建规模=语料自然规模（宁少勿滥）。
- **语料源扩面**：不新增 docs-root 目录、不接新 repo、不改 sync（ops_sync_kimi_code 重同步另 task）；docs roots 钉死历史两目录（05-plan + contracts）。
- **应用功能改码**：`app/** · scripts/** · alembic/** · docker-compose.yml` 零 diff 硬约束；执行中若裁定须改脚本即 **STOP** 退回补 30 棒 + HG-GRAPH-MODULES 图谱闸评估（FP-8）。
- **全量金样评测**：`evals/golden/run_eval.py` 73 条全量召回/精排评测非本 task（本 task 仅 F5 单条抽检实证可检性；金样 R4/R5 评测另案承 task_rag_golden_eval_r4_r5）。
- ops_knowledge 以外任何 collection（scale/scale_mem/scale_sq/scale_100k 等容量实验集合一律不动）· DLQ 历史条目处置（本 task 仅核验新建深度=0）· 监控/告警接线 · 新写测试。
- 备份产物入 git（二进制/报告 untracked 留本机 · 提交与否 00/维护者事后裁定）。

### 规模裁定（10 建议 · 维护者签闸时可改判）

**建议口径：恢复性重建 = 语料自然规模，不凑数、不扩样、宁少勿滥。** 数据支撑：(1) 历史常态 pg=qdrant=8574（2026-08-13 对账 pass · max_l_inf=0.0）；(2) 当前语料源 881+1855=2736 units + docs 两 root（历史全量实测 2748 units · ingest.py:214 注释），量级 ≈3.1 chunks/unit（e04 抽样 chunk_index max 19）→ **预期终值量级 8k–9k，对照区间 [6000, 12000]**；(3) 区间外（语料漂移/装载缺陷信号）即 FP-4 STOP 查因照登，不硬灌。验收钉「三计数相等」（chunks_written == PG 行数 == Qdrant 点数），规模数字本身不设硬等式——语料自然涨落正当，越区间才拦。

---

## 失败路径

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----------|----------|--------|----------|
| FP-1 闸 pending 即 40 执行 | GATE_VERIFY **拒开工**（真值在本档人工闸表 · 本 task 含写动作，闸未签禁一切写） | 是 | — |
| FP-2 前置缺失（容器非 healthy / SILICONFLOW_API_KEY 缺失 / collection 异常） | 容器：`docker compose up -d` 待 healthy 后复验，仍异常即 STOP 照登；密钥缺失：api 路径不可用 → **不擅自降判 st**，照登回抛维护者裁定；collection 缺失走 create_collection.py 缺省参数，dim≠1024 即 STOP 防混库 | 是 | 执行台账 + stderr |
| FP-3 embedding API 失败（HTTP 错误/限流/超时 · 重试 3 次后抛错） | 进程非零退出如实记失败计数与错误全文；已写单元 PG 已 commit 不丢（逐单元提交崩溃可续 · ingest.py:232）；重跑续传（水位跳过已写）；**失败照登不假绿**；持续失败回抛维护者裁定降判 st 或暂停 | 是 | 40 invoke + 报告 |
| FP-4 规模与裁定不符（dry-run scanned 异常 / 终值越 [6000,12000] 区间 / dim≠1024） | **即停**：查因（语料表漂移?docs root 路径错?模型/维度错?）照登实证，禁带病重建、禁凑数；回抛维护者 | 是 | 报告 + 40 invoke |
| FP-5 双侧一致性核验 FAIL（水位 mismatch / 三对照不等 / DLQ depth>0） | 不假绿；DLQ 条目照登为影子写失败证据；裁定差集补写：`export_vectors.py` 导 PG → `bulk_upsert.py` 补写 Qdrant（既有迁移链路零落码）→ 复跑水位至 verdict=match；仍 FAIL 则全链留痕回抛维护者；**禁手工改计数冒充** | 是 | 报告 + 台账 |
| FP-6 影子写未生效（PG>0 但 Qdrant=0 且 DLQ=0 · 开关未加载等） | 判影子写链路未生效（`app/config.py:11` load_dotenv 已实证 CLI 可见 .env，仍须实证排查）；走 FP-5 差集补写路径兜底；若实证须改脚本修复 → FP-8 STOP | 是 | 报告 + 40 invoke |
| FP-7 检索抽检 FAIL（hits 空 / 锚 issue#2720 未中 / LLM env 不可用） | 不假绿；LLM env 缺失 → 降级纯向量检索并**显式标注降级形态**；向量抽检也 FAIL → 查 embedder fingerprint/维度/collection 配置，照登回抛 | 是 | 报告标注 |
| FP-8 顺手落码冲动 | 执行中若判断须新落/改 `scripts/`、`app/** ` 任何码 → **STOP**；退回维护者裁定补 30 棒 + HG-GRAPH-MODULES 图谱闸评估，本 task 不边做边扩范围 | — | 报告 + 40 invoke |
| FP-9 本地口径误外推生产 | 报告/invoke 钉死「本地/compose 开发库口径 · 不得外推生产」；生产侧任何动作仍属 HG-PROD-READONLY-ACCESS（pending）管辖 | — | 报告 disclaimer |
| FP-10 证据不可复现 | 全链命令全文 + 原始输出附件必落档（对齐上游 e00–e11 先例）；缺附件即 TC 判 FAIL；**禁凭记忆转述** | 是 | 40 invoke 实录 |

---

## 验收标准

- [x] **TC-RK-1（实证 · 前置核验）**：F1 完成——`docker ps` 双容器 Up (healthy) 输出落档；.env `SILICONFLOW_API_KEY` 存在非空 + `RAG_QDRANT_SHADOW_WRITE=true` grep 计数落档（密钥值零落档）；`GET /collections/ops_knowledge` 实证 points_count=0 · dim=1024 · Cosine 落档（或 create_collection 创建记录落档）
- [x] **TC-RK-2（机断 · dry-run 基线）**：F2 完成——`rag_ingest.py --dry-run` 命令全文+报告落档；scanned=to_upsert · unchanged=0 · to_delete=0（空库预期）；scanned 与语料面（881+1855+docs 实数）对照结论落档；异常即 FP-4 STOP 记录
- [x] **TC-RK-3（实证 · 重建执行）**：F3 完成——全量 ingest 命令全文+报告 {scanned, to_upsert, chunks_written, to_delete} 落档；**chunks_written>0**；embedding 失败计数=0 或失败如实照登（FP-3）；embedding 成本/速率实测（总 chunks × token 估算 · 耗时）入报告
- [x] **TC-RK-4（机断 · 双侧一致硬闸）**：F4 完成——`check_vector_waterline.py --env local` 复跑报告落 `reports/vector_waterline_local_<UTCts>.yaml`：**pg_count == qdrant_count > 0 · count_diff=0 · verdict=match · dlq verdict=empty · degraded=false**；三对照（chunks_written == PG 行数 == Qdrant 点数）成立；任一不符 FP-5 处置记录而非假绿
- [x] **TC-RK-5（实证 · 检索可检）**：F5 抽检完成——G01 query 检索实证 hits 非空且 top-5 含 source_type=issue / source_id=2720 锚（rag_smoke 全链或降级纯向量检索 · 形态显式标注）；输出落档
- [x] **TC-RK-6（机断 · 规模裁定闭合）**：终值 chunks_written 在裁定区间 [6000, 12000] 内，或区间外但有 FP-4 查因照登+维护者裁定记录；重建报告 `reports/local_rag_knowledge_rebuild_<UTCts>.md` 落盘（含与历史 8574 量级对照 · disclaimer 钉死）
- [x] **TC-RK-7（机断 · 零越界+不假绿）**：`app/** · scripts/** · alembic/** · docker-compose.yml` 零 diff（git status 仅新增 untracked：报告+水位报告+invokes+证据附件）；`uv run pytest tests/test_check_vector_waterline.py -q` 13 passed 复证；每个计数/判定可回溯落档证据（FP-10）；`npx --yes spec-wave task lint --file docs/tasks/active/task_local_rag_knowledge_rebuild.md` LINT: PASS

## 依赖

- 重建管线（零 diff 复用）：`scripts/rag_ingest.py`（CLI · docstring :12-14 历史全量形态）· `app/ops/rag/ingest.py`（content_hash 水位 :186-191 · 整组替换 :240-289 · 维度断言 :225-230）· `app/ops/rag/embedder.py`（ApiEmbedder :64-110 · ST :33-61）· `app/ops/rag/shadow_write.py`（开关 :27-32 · DLQ :150-184）
- 核验与兜底链路（零 diff 复用）：`scripts/check_vector_waterline.py`（只读硬约束 :4-6）· `scripts/qdrant_migrate/export_vectors.py`（ALLOWED_PAYLOAD :12）· `scripts/qdrant_migrate/bulk_upsert.py`（:46 collection 缺省）· `scripts/qdrant_migrate/create_collection.py`（缺省 dim=1024 Cosine）
- 检索抽检：`scripts/rag_smoke.py`（G01 默认 query :23）· `scripts/lg_rag_smoke.py`（备选）
- 上游证据链：[`task_local_qdrant_orphan_points_cleanup.md`](../done/task_local_qdrant_orphan_points_cleanup.md) · `reports/vector_waterline_local_20261018T005534Z.yaml`（零点基线）· `reports/qdrant_reconcile_20260813T125801Z.yaml`（历史 8574 常态）· `docs/harness/invokes/by-task/local-vector-data-state-audit/evidence/e04_scroll_stats.txt`（历史分布）
- 语料源：PG ops_issues(881)/ops_pull_requests(1855) · `../ops-desk-workspace/docs/05-plan`(11 md) · `../ops-desk-workspace/docs/contracts`(8 md)
- 部署形态：`docker-compose.yml`（qdrant 段 v1.19.0 · qdrant_data 卷 · db 段）
- 编码规范：`docs/standards/CODING_BACKEND_L2_v1_zh.md`
- 闸与流程：`docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`（GATE_VERIFY 形状 · 本 task 阻塞面 = 40）

## 给执行帽的必读列表

1. 本 task 全文（**含写动作 · 前置核验/dry-run 规模核验/三对照硬闸/不假绿纪律** · 非范围七条 · 闸表 · 规模裁定）。
2. `scripts/rag_ingest.py` 全文 + `app/ops/rag/ingest.py` :179-304（管线语义 · 崩溃可续 · 影子写时序 —— 禁信转述）。
3. `app/ops/rag/shadow_write.py` 全文（开关 · 异步写 · DLQ 语义）。
4. `scripts/check_vector_waterline.py` :284-362（核验复跑形态 · 报告落盘 · 禁改本脚本）。
5. `reports/qdrant_reconcile_20260813T125801Z.yaml` + 上游零点基线 `reports/vector_waterline_local_20261018T005534Z.yaml`（规模对照锚）。
6. `docs/harness/invokes/by-task/local-vector-data-state-audit/evidence/e04_scroll_stats.txt`（历史语料分布 · 量级对照）。
7. `evals/golden/queries_v1.yaml` G01–G05 段（抽检锚 issue#2720 语义 · 全量评测非本 task）。
8. `docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`（GATE_VERIFY 形状 · 本 task 阻塞面 = 40）。

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|---|------|------------|----------------------|----------------|
| R0 | 框定：B2=本地 RAG 知识库重建（三线闭合后知识为空）· 含写动作（PG+Qdrant 双侧）· 本地口径 · 零涉生产 · 建议零落码 | false | — | 闸未签 |
| R1 | 证据：管线/影子写/embedder/核验脚本四件全文亲读 · 语料源计数亲跑（881+1855+0+0）· 容器/密钥/collection 三面亲跑 · 历史 8574 基准与分布亲读 · 金样 73 条锚依赖实证 · expand_synthetic 不适用裁定实证（:110-111） | false | — | embedding API 速率/成本面未实测（执行时留档） |
| R2 | 方案：F1 前置核验 → F2 dry-run 计数（规模裁定核验）→ F3 全量重建（api embedder · 崩溃可续）→ F4 双侧一致核验（三对照+DLQ）→ F5 检索抽检（G01 锚）+ 报告落盘；40 单棒零落码 | false | — | 影子写异步沉降须实证不得以假设冒充（FP-6） |
| R3 | 反例：禁凑数扩样（expand_synthetic 钉死非范围）· 规模越区间即停（FP-4）· embedding 失败照登不假绿（FP-3）· 双侧不符走差集补写不冒充（FP-5）· 顺手落码即 STOP（FP-8）· 本地口径防外推生产（FP-9） | false | — | docs roots 之外语料（如 workspace 其余 73 篇 md）是否该入裁量为维护者签闸点 |
| R4 | 验收：TC-RK-1..7 实证+机断混合（前置/dry-run/重建报告/水位 verdict=match 三对照/抽检锚命中/规模区间/零越界+lint） | false | — | 无 |
| R5 | 收口：实证齐备、F1–F5 边界闭合、规模裁定有数据支撑（8574 历史+2736 units+3.1 chunks/unit→[6000,12000] 区间）；草稿交维护者签闸（DRAFT/AUDIT pending · GRAPH n/a）；执行棒裁定=40 单棒零落码（现成 CLI+开关+核验脚本齐备 · 承 orphan cleanup 先例），若执行实证须改脚本则 FP-8 升级 30+40 | true | 管线与语料面全部亲读亲跑量化，F1–F5 边界闭合，再轮无新信息 | 闸未签 · embedder api/st 最终选择待维护者签闸确认 |

**actual_last_round**：R5（early_stop）

### R0 · 问题框定

三线闭合把本地向量数据态打回零点（0/0/0 match），副作用是本地 RAG 知识为空——检索链与 73 条金样评测失去语料。本 task 回答一个问题：**如何用既有管线从既有语料安全重建双侧知识库并实证可检**。与上游清理 task 的本质差异：写动作从「删」变「灌」，风险面从误删变为假绿/混库/规模失控。

### R1 · 证据收集

全部实证亲跑亲读于 2026-10-18：管线四件全文（rag_ingest.py 88 行 · ingest.py 304 行 · shadow_write.py 184 行 · embedder.py 172 行 · check_vector_waterline.py 366 行）；语料源亲跑（ops_issues=881 · ops_pull_requests=1855 · ops_knowledge_chunks=0 · dlq=0 · docs roots 92/8/11 篇）；环境三面亲跑（双容器 healthy · SILICONFLOW_API_KEY 存在 · collection green dim=1024 points=0）；历史基准亲读（reconcile 8574 pass · e04 分布 · 零点基线 yaml）；金样依赖实测（73 条 · 28 锚 · 2720/1566 在库）；关键裁定实证：expand_synthetic.py :110-111 source 空即退出+不写 PG（:2），对知识恢复不适用。另实证 `app/config.py:11` import 即 load_dotenv 仓根 .env → CLI 直跑影子写开关可见。

### R2 · 方案生成

40 实证执行流水线：F1 前置核验（容器/密钥/collection 三面 · 缺一降级不硬闯）→ F2 dry-run（零写库计数 · 空库预期 scanned=to_upsert · 规模裁定核验）→ F3 全量重建（`--embedder api` 与查询侧 fingerprint 同源 · 逐单元 commit 崩溃可续 · 报告落档）→ F4 双侧核验（水位脚本复跑 pg=qdrant>0 verdict=match · 三对照 · DLQ empty）→ F5 检索抽检（G01 锚 issue#2720 · 降级形态显式标注）+ 报告落盘。兜底路径预写：影子写失效/失败 → export_vectors→bulk_upsert 差集补写（既有迁移链路零落码）。

### R3 · 反例与边界

最大风险一是「灌了装灌好」（embedding 失败/影子写丢失却报绿 → FP-3/FP-5/FP-6 照登+三对照+DLQ 核验）；二是规模失控或凑数（越 [6000,12000] 区间即停 · expand_synthetic 压测扩样钉死非范围）；三是混库（dim≠1024 即停 · embedder fingerprint 同名 BAAI/bge-m3 两路无混库）；四是顺手落码扩范围（FP-8 STOP）；五是本地口径外推生产（FP-9 disclaimer 双落）。docs roots 钉死历史两目录（05-plan+contracts），workspace 其余 73 篇 md 入与不入是维护者签闸裁量点，照登不擅自扩。

### R4 · 验收/可测性

七条 TC 全部可实证或机断断言：前置输出落档、dry-run 计数三零预期、重建报告 chunks_written>0、水位报告 verdict=match+三对照+DLQ empty、抽检锚命中、规模区间闭合、git 白名单+pytest 桩测复证+task lint PASS。

### R5 · 收口

实证齐备、方案与反例闭合、规模裁定有数据支撑。草稿交维护者签 HG-TASK-DRAFT / HG-AUDIT-R1（GRAPH n/a 零图谱变更未代签）；执行棒裁定=40 单棒零落码（理由：rag_ingest.py 现成 CLI 参数齐备 · 影子写开关 .env 已配 · 核验脚本现成只读 · 承 task_local_qdrant_orphan_points_cleanup 先例），embedder api/st 选择与 docs roots 裁量一并交维护者签闸时确认；闸未签禁 40。

### 自检结论（执行者）

40 实证执行 2026-10-18 15:00–15:32 (+08) 完成，七条 TC 全过，证据全落档（docs/harness/invokes/by-task/local-rag-knowledge-rebuild/）。

- **终态三对照**：chunks_written 恢复轮 8429（+首轮 docs 219）== PG ops_knowledge_chunks 8648 == Qdrant ops_knowledge 8648；水位 verdict=match · diff=0 · DLQ=0 · degraded=false（reports/vector_waterline_local_20261018T072903Z.yaml）。
- **规模裁定**：8648 ∈ [6000,12000]，对照历史常态 8574 偏差 +0.9%——恢复性重建闭合，零凑数零扩样。
- **检索抽检**：rag_smoke 全链因环境缺 langchain（Langfuse 集成 graph 阶段报错）不可用 → FP-7 降级纯向量检索并显式标注；G01 query top-1/top-3 双中锚 issue#2720（score 0.7431/0.6958）。知识可检（向量层实证）；全链复验待 langchain 环境补齐，另案。
- **照登偏差三桩**：(1) shell NO_PROXY 含 [::1] 触发 httpx URLPattern 解析 bug（Invalid port: ':1]'）→ 零落码清洗 NO_PROXY 修复；(2) ApiEmbedder 无内部批切，ingest 全量单请求 ~8.6k 文本必超时（探测实证 API 单批安全上限 ≈500 文本）→ 零落码分批 --limit 75 步长递增（content_hash 水位跳过已写）；(3) 本人编排事故：standalone --only docs 触发 ingest.py:291-302 墓碑对账删 2736 单元（源表零损失 · DLQ=0 · 纠偏轮全量恢复 25/25 步 attempt=1）——教训：--only 局部跑禁作收尾。
- **零越界实证**：git diff 零（app/**/scripts/**/alembic/**/docker-compose.yml 未触）；untracked 仅任务档/审查文/invoke+证据/报告/水位报告；pytest tests/test_check_vector_waterline.py 13 passed；spec-wave task lint PASS。
- **后续建议（非本 task）**：ApiEmbedder 内部批切改码另立 task；rag_smoke 全链复验待 langchain 环境；金样 73 条评测承 task_rag_golden_eval_r4_r5。

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-18 | 40 实证执行完成（F1–F5 全链落档：8648/8648/8648 三对照 · 水位 match · DLQ=0 · 规模 8648∈[6000,12000] 对照历史 8574 · 降级向量抽检锚双中显式标注 · 两环境级失败+一编排事故全照登零遮掩 · 零落码零 diff · pytest 13 passed · LINT PASS；报告 reports/local_rag_knowledge_rebuild_20261018T0731Z.md · invoke_20261018_40_rebuild.md） |
| 2026-10-18 | 10-task 落稿（B2 本地 RAG 知识库重建 · 含写动作 PG+Qdrant 双侧重灌 · 实证锚点 13 项全亲跑亲读：语料源 881+1855 units/0 chunks/0 dlq · 双容器 healthy · SILICONFLOW_API_KEY 存在 · collection green dim=1024 points=0 · 历史 8574 基准 · 金样 73 条锚依赖 · expand_synthetic 不适用实证 · 规模裁定 [6000,12000] 区间对照历史量级 · 执行棒裁定=40 单棒零落码承 orphan cleanup 先例 · 三闸 DRAFT/AUDIT pending · GRAPH n/a 未代签 · 零 git 操作零码改） |
