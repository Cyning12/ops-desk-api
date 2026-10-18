# Invoke · 10-task · local-rag-knowledge-rebuild · task 落稿

| 字段 | 值 |
|------|-----|
| **hat** | 10-task |
| **task_slug** | `local_rag_knowledge_rebuild` |
| **日期** | 2026-10-18 |
| **动作** | 起草 task（含写动作 · 本地运维重建）+ 实证勘察（全亲跑亲读）+ 执行棒形态裁定 + 双 lint 验证 |
| **授权源** | 维护者 2026-10-18（会话 m01159）授权自动推进 B2=本地 RAG 知识库重建（上游三线闭合后知识为空：PG 0 / Qdrant 0 / 水位 match(0/0/0)） |
| **产物** | docs/tasks/active/task_local_rag_knowledge_rebuild.md（本 invoke 同录） |
| **git** | 零 git 操作 · 零码改（`app/** · scripts/**` 零 diff） |

## 1. 范围（本 invoke 做了什么）

1. 实证勘察（见 §3）：重建管线四件全文亲读（rag_ingest.py / ingest.py / shadow_write.py / embedder.py / check_vector_waterline.py）；语料源计数亲跑；环境三面亲跑（容器/密钥/collection）；历史基准与金样依赖亲读；expand_synthetic 不适用裁定实证。
2. 先例体例亲读：docs/tasks/done/task_ruff_baseline_cleanup.md（最新 task 格式）· docs/tasks/done/task_local_qdrant_orphan_points_cleanup.md（40 单棒零落码先例）· docs/tasks/close/close_hitl_resume_async_20261015.md。
3. 起草 task：背景/范围 F1–F5/非范围 7 条/验收 TC-RK-1..7（机断优先）/FP-1..FP-10/R0–R5 实填/人工闸三栏全 pending（GRAPH n/a 未代签）/graph_change_layer=none/review_hat=20/required_invoke_hats=10,40。
4. 验证：`npx spec-wave task lint --file docs/tasks/active/task_local_rag_knowledge_rebuild.md` → **LINT: PASS**；`npx spec-wave task lint-wiki-delta --target . --scope active` → **LINT-WIKI-DELTA: PASS**（scanned: 1 · issues: 0）。

## 2. 实证锚点（落 task「实证锚点」表 · 40 必读）

| 锚点 | 实证 |
|------|------|
| 重建管线 CLI | scripts/rag_ingest.py（88 行）：--dry-run/--only/--docs-root/--embedder st\|api/--limit（:41-53）；docstring :12-14 历史全量形态 docs-root=../ops-desk-workspace/docs/05-plan+contracts；app/config.py:11 import 即 load_dotenv 仓根 .env → CLI 直跑可见影子写开关与密钥 |
| 入库核心 | app/ops/rag/ingest.py ingest()（:179）：content_hash 水位对比 :186-191（空库→全量 to_upsert）；维度断言 1024 不符即停 :225-230；整组替换逐单元 PG commit :284 → 影子写 enqueue_shadow_upsert :287；返回 {scanned,to_upsert,unchanged,to_delete,chunks_written}；:214 注释历史全量实测 9/2748 空正文单元 |
| 影子写 | app/ops/rag/shadow_write.py：开关 RAG_QDRANT_SHADOW_WRITE（:27-32 · .env 实证=true）；PG commit 后 ThreadPoolExecutor 异步 upsert；失败进 ops_qdrant_dlq 表（:150-184）不回滚 → 核验必含 DLQ depth=0 |
| Embedder | app/ops/rag/embedder.py：api=SiliconFlow bge-m3（缺 SILICONFLOW_API_KEY 即 raise :78-81 · HTTP 重试 3 次后抛 :90-110）；st=本地 bge-m3 ~2.3GB；两路 fingerprint 同名 BAAI/bge-m3 无混库风险 |
| 语料源 | docker exec ops-desk-api-db-1 psql 亲跑：ops_issues=881 · ops_pull_requests=1855（均 MoonshotAI/kimi-code）· ops_knowledge_chunks=0 · ops_qdrant_dlq=0；../ops-desk-workspace/docs 92 篇 md（contracts=8 · 05-plan=11） |
| 历史基准 | reports/qdrant_reconcile_20260813T125801Z.yaml：pg=qdrant=8574 pass · max_l_inf=0.0；e04_scroll_stats.txt（local-vector-data-state-audit 证据）：150 抽样 {issue:54,pr:55,doc:41} · chunk_index max 19 → ≈3.1 chunks/unit |
| 环境前提 | docker ps 亲跑：ops-desk-api-db-1 + ops-desk-api-qdrant-1 均 Up 2 days (healthy)；.env SILICONFLOW_API_KEY 存在非空（值不落档）；GET /collections/ops_knowledge：green · points=0 · dim=1024 Cosine · on_disk（无需 recreate） |
| 零点基线 | reports/vector_waterline_local_20261018T005534Z.yaml：pg=0/qdrant=0/count_diff=0/verdict=match/dlq empty |
| 验证路径 | scripts/check_vector_waterline.py --env local（只读 :4-6 · 报告落 reports/vector_waterline_local_<ts>.yaml）；scripts/rag_smoke.py（G01 默认 query :23 锚 issue#2720）；evals/golden/queries_v1.yaml 73 条金样（28 distinct 锚 · 2720/1566 在库实证）依赖本知识库但全量评测非本 task |
| pytest 依赖面 | 无测试依赖活体语料（conftest.py:233 自建表 · test_chat_ws.py:101 注明语料空无妨）；tests/test_check_vector_waterline.py 13 桩测 |
| 兜底写路径 | scripts/qdrant_migrate/export_vectors.py（ALLOWED_PAYLOAD :12 · PG→jsonl）→ bulk_upsert.py（:46 collection 缺省 ops_knowledge）即历史 8574 迁移链路，FP-5 差集补写零落码可用 |

## 3. 勘察数据（规模裁定支撑 · 亲跑实录）

- 语料单元：881 issues + 1855 pulls = **2736 units**（+ docs 两 root 19 篇 · 历史全量实测 2748 units · ingest.py:214 注释口径一致）
- 平均切块：e04 抽样 chunk_index max 19 → **≈3.1 chunks/unit**
- 预期终值量级：**8k–9k**；历史常态 8574（2026-08-13 对账 pass）
- **裁定区间 [6000, 12000]**：语料自然涨落正当，越区间=语料漂移/装载缺陷信号 → FP-4 即停查因照登，宁少勿滥，不设硬等式（验收钉三计数相等：chunks_written == PG 行数 == Qdrant 点数）
- expand_synthetic.py 裁定：Qdrant→Qdrant 压测扩样（不写 PG :2 · --source 缺省 ops_knowledge :91 · --target-n 800_000 :93 · :110-111 source 空即 raise SystemExit "source ops_knowledge empty"）→ 当前 source=0 不可用且语义不符，**钉死非范围**

## 4. 裁定记录

| 裁定 | 结论 | 依据 |
|------|------|------|
| 执行棒形态 | **40 单棒 · 零落码**（承 task_local_qdrant_orphan_points_cleanup 先例） | rag_ingest.py 现成 CLI 参数齐备（--docs-root/--embedder/--dry-run）· 影子写开关 .env 已配 · 核验脚本现成只读 · 兜底链路（export→bulk_upsert）现成 → 勘察未见须改脚本处；若执行中实证须改 → FP-8 STOP 升级 30+40 双棒并补 HG-GRAPH-MODULES |
| 图谱变更 | graph_change_layer=none · HG-GRAPH-MODULES=n/a | 零落码建议 · 无新模块/路由/表/事件类型 |
| Embedder 选择 | 默认 `--embedder api`（SiliconFlow bge-m3 · 与查询侧 fingerprint 同源）；成本/速率实测入报告；API 不稳可签注降判 st（fingerprint 同名无混库）· 最终选择交维护者签闸确认 | embedder.py :7-8/:78-81/:147-171 |
| 规模口径 | 恢复性重建=语料自然规模 · 区间 [6000,12000] · 不凑数不扩样 | §3 数据支撑 |
| docs roots | 钉死历史两目录（05-plan + contracts · rag_ingest.py :12-14）；workspace 其余 73 篇 md 入与不入为维护者签闸裁量点（R3 照登） | 历史形态先例 |
| 闸态 | HG-TASK-DRAFT pending · HG-AUDIT-R1 pending · HG-GRAPH-MODULES n/a · 未代签 | 纪律 |

## 5. 结论与交接

- task 落稿完成，双 lint PASS，闸未签禁 40。
- 交 20-task-audit R1（按维护者授权取舍）→ 维护者签 HG-TASK-DRAFT/HG-AUDIT-R1 → 40 实证执行（F1 前置核验 → F2 dry-run → F3 全量重建 → F4 双侧核验三对照 → F5 检索抽检）。
- 诚实纪律遵守：本 invoke 所载实证全部亲跑亲读于 2026-10-18；未实测项（embedding API 实际速率/成本、影子写异步沉降时长）已显式标注为执行时留档项，未冒充已验证。
