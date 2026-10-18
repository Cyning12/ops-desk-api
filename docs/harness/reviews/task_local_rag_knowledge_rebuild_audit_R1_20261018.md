# Review：task_local_rag_knowledge_rebuild · 20-task-audit R1 书面审查

| 字段 | 值 |
|------|-----|
| **审查对象** | `docs/tasks/active/task_local_rag_knowledge_rebuild.md`（2026-10-18 10-task 落稿） |
| **审查轮次** | R1 |
| **审查日期** | 2026-10-18 |
| **审查帽** | 20-task-audit（只审不改 · 零 git 操作 · 零码改） |
| **授权来源** | 维护者 2026-10-18 授权自动推进 B2，20 R1 按授权取舍执行（task 元信息 orchestration 行照登） |

---

## 结论摘要

- **内容面**：本帽对 task_local_rag_knowledge_rebuild（HG-AUDIT-R1 被审对象）经书面审查与逐项核对，结论**签收（无需退回 · 零阻塞 · PASS）**。nit 4 条照登不阻签收，明细见下。

### 内容审查：**签收**（零阻塞 B · nit 4 条照登）

范围/非范围/验收 TC-RK-1..7/failure_paths FP-1..10/思考轮 R0–R5 逐项核对通过；10 自报锚点 **13/13 独立复核命中**（明细见下）。规模裁定 [6000,12000] 数据支撑成立（2736 units × ≈3.1 chunks/unit ≈ 8.5k，对照历史常态 8574）。验收七条均可实证或机断断言，失败路径十条覆盖假绿/混库/规模失控/顺手落码/外推生产五类主要风险，兜底链路（export_vectors→bulk_upsert 差集补写）为既有零落码复用，可执行。

### 流程闸：**pending 未代签 · 照登**

- HG-TASK-DRAFT：**pending**（blocks 20,40）
- HG-AUDIT-R1：**pending**（blocks 40）
- HG-GRAPH-MODULES：**n/a**（graph_change_layer=none，零图谱改动，未代签）

三闸均保持 task 表原状，本审查未代签任何闸。机检 `npx spec-wave verify` **EXIT=2**，尾行 `VERIFY: BLOCKED · HG-AUDIT-R1 pending · task_local_rag_knowledge_rebuild.md`——pending 期 fail-closed 属预期。`npx --yes spec-wave task lint` **EXIT=0 · LINT: PASS**。

---

## 锚点独立复核明细（13/13 命中 · 2026-10-18 亲跑亲读）

| # | 锚点（10 自报） | 复核方式 | 结果 |
|---|------------------|----------|------|
| 1 | PG 源表 ops_issues=881 · ops_pull_requests=1855 · ops_knowledge_chunks=0 · ops_qdrant_dlq=0 | `docker exec ops-desk-api-db-1 psql -U ops -d opsdesk` 四表 count 亲跑 | ✅ 881 / 1855 / 0 / 0 全中 |
| 2 | `scripts/rag_ingest.py` :12-14 历史 docs roots（05-plan + contracts） | 亲读 :1-60 | ✅ docstring :12-14 全量灌库形态两 `--docs-root` 逐字命中 |
| 3 | `app/ops/rag/ingest.py` content_hash 水位 :186-191 → 整组替换逐单元 PG commit :284 → 影子写 :287 | 亲读 :179-203 / :275-304 | ✅ :186-191 `_existing_hashes` 对比+空库→全量 to_upsert；:284 `session.commit()`（注释「PG 先提交；影子写失败不得回滚」）；:287 `enqueue_shadow_upsert(shadow_points)` 逐字命中 |
| 4 | `RAG_QDRANT_SHADOW_WRITE=true`（.env）· `app/config.py:11` load_dotenv | .env grep 计数 + 亲读 config.py:1-20 | ✅ grep `RAG_QDRANT_SHADOW_WRITE=true` 计数=1；:11 `load_dotenv(Path(__file__).resolve().parent.parent / ".env")` 逐字命中 |
| 5 | `SILICONFLOW_API_KEY` 存在非空（值不落档） | .env grep 计数（不取值） | ✅ 存在且非空计数=1 |
| 6 | 规模裁定区间 [6000,12000]：2736 units × ≈3.1 chunks/unit（e04 chunk_index max 19） | 亲读 `e04_scroll_stats.txt` | ✅ total_ids=8574 · sample=150 · chunk_index max=19 · source_type dist {issue:54,pr:55,doc:41} 全中 |
| 7 | 历史常态 8574（reports/qdrant_reconcile_20260813T125801Z.yaml） | 亲读 yaml 全文 | ✅ status=pass · pg_count=qdrant_count=8574 · max_l_inf=0.0 · mean_topk_overlap=1.0 全中 |
| 8 | `expand_synthetic.py` :110-111 压测工具钉死非范围 | 亲读 :100-119 | ✅ :110-111 `if src_n <= 0: raise SystemExit(f"source {args.source} empty")` 逐字命中；Qdrant→Qdrant 不写 PG 语义成立 |
| 9 | Qdrant ops_knowledge green · points=0 · dim=1024 · Cosine | `curl -s http://127.0.0.1:6333/collections/ops_knowledge` 亲跑 | ✅ status=green · points_count=0 · size=1024 · distance=Cosine · m=12 · ef_construct=80 全中 |
| 10 | 双容器 Up healthy | `docker ps` 亲跑 | ✅ ops-desk-api-db-1 + ops-desk-api-qdrant-1 均 Up 2 days (healthy) |
| 11 | 零点基线 reports/vector_waterline_local_20261018T005534Z.yaml | 亲读 yaml 全文 | ✅ pg=0 · qdrant=0 · count_diff=0 · verdict=match · dlq verdict=empty · degraded=false 全中 |
| 12 | 验证路径 check_vector_waterline.py --env local + rag_smoke.py G01 锚 issue#2720 | `grep -c '^  - id: G' evals/golden/queries_v1.yaml` + G01–G05 锚 grep + PG 2720/1566 亲跑 | ✅ 金样 73 条实测命中；G01–G05 expect_hit source_id=2720 五行命中；ops_issues 2720/1566 均在库 |
| 13 | docs 语料面：05-plan=11 · contracts=8 · workspace 共 92 篇 md | `ls`/`find` 亲跑 | ✅ 11 / 8 / 92 全中 |

另抽查：`app/ops/rag/shadow_write.py` :27-32 `shadow_write_enabled()` 读 `RAG_QDRANT_SHADOW_WRITE` 逐字命中；`rag_ingest.py` :52 `--embedder` 缺省 `st`（task F3 显式带 `--embedder api`，无歧义）。

---

## 阻塞项（B）

**零。**

## 非阻塞项（N · 照登，无需退回）

- **N1**：「≈3.1 chunks/unit」源自 e04 150 抽样观测（chunk_index max 19），是历史均值近似而非全量上界；8574/2748 units ≈ 3.12 与裁定口径自洽，区间 [6000,12000] 裕度充足（上下各 ±40% 量级）。照登。
- **N2**：task 引 `ingest.py` 注释历史全量实测 2748 units 与当前亲跑 2736（881+1855）+docs 19 篇有出入，属语料自然漂移；规模裁定以区间吸收、验收钉三对照而非规模硬等式，处理正当。照登。
- **N3**：TC-RK-2「scanned=to_upsert · unchanged=0」预期以空库为前提，ops_knowledge_chunks=0 已亲跑实证成立；若 40 执行前库态被外部改动则预期不成立——FP-4 已覆盖该查因路径，无新增风险。照登。
- **N4**：行为变更类 checklist 项「旧测 grep 影响面」——本 task 为零落码运维重建（非行为变更类），该提醒不适用；TC-RK-7 已含 `tests/test_check_vector_waterline.py` 13 测桩测复证+零 diff 白名单作零越界旁证，覆盖面等价。照登。

## 思考轮审查（R0–R5）

| 项 | 核对结论 |
|----|----------|
| 控制表完整性 | R0–R5 六轮结论/early_stop/reason/residual_risks 四列齐备 |
| 回填闭合 | R5 `actual_last_round=R5（early_stop）` 声明与控制表一致 |
| early_stop 理由 | 「管线与语料面全部亲读亲跑量化，F1–F5 边界闭合，再轮无新信息」——与 13 项实证锚点互证，成立 |
| residual_risks | 「闸未签 · embedder api/st 最终选择待维护者签闸确认」如实照登，未粉饰 |
| 正文 R0–R5 小节 | 与控制表逐轮对应，无遗漏无矛盾 |

思考轮审查通过。

---

## 回填清单

**零**（无内容阻塞，无要求 10-task 回填项）。

## 维护者签闸（20 后 · 40 前）

- [ ] 已读 R1 审查结论（本文）
- [ ] 在 task 人工闸表将 HG-TASK-DRAFT 改为 approved（维护者 · 日期）
- [ ] 在 task 人工闸表将 HG-AUDIT-R1 改为 approved（维护者 · 日期）
- [ ] 签闸时一并确认 embedder api/st 最终选择与 docs roots 裁量（R5 residual_risks 照登项）
- [ ] commit task 文档或确认已签
- [ ] 再下发 40 实证执行 Prompt

40 Agent 将以 task 表为准；HG-AUDIT-R1 pending 时必须拒开工（FP-1 · 本 task 含写动作，闸未签禁一切写）。

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-18 | 20-task-audit R1 书面审查：内容签收（零阻塞 · nit 4 条照登）· 锚点 13/13 独立复核命中 · 思考轮 R0–R5 闭合 · verify EXIT=2（pending 期预期 fail-closed）· task lint PASS · 三闸 pending/n-a 未代签 · 附维护者签闸清单 |
