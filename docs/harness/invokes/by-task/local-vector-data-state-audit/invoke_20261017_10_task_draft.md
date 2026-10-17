---
hat: 10-task
task_slug: local_vector_data_state_audit
date: 2026-10-17
---

# invoke · 10-task 起草 · local_vector_data_state_audit（FP-7 上抛开账 · 本地 Qdrant 8574 vs PG 0 数据态溯源）

## 落稿摘要

- 起因：task_vector_waterline_local_rerun 40 亲跑实证（报告 `reports/vector_waterline_local_20261017T123649Z.yaml`）：本地 PG `ops_knowledge_chunks` 0 行 / DLQ 空 / Qdrant `ops_knowledge` 8574 points，count_diff=-8574，verdict=mismatch（Qdrant 独有 8574 · PG 独有 0）；母体按 FP-7 纪律只记录不处置上抛（done 档自检结论 :173）。维护者 2026-10-17（会话 m00847）选定立本 task 溯源本地数据态来源。
- 实证锚点（全部亲读复核）：
  - `reports/vector_waterline_local_20261017T123649Z.yaml`（立案证据 · 8574/0/-8574 · degraded=false · disclaimer 钉死）
  - `scripts/check_vector_waterline.py`（scroll 形态 :131-144 · count+scroll 只取 id 零数据搬运 · reconcile 双向差集 :154-179）
  - `app/ops/rag/backend.py`（`qdrant_collection()` 缺省 ops_knowledge :38-39 · backend 缺省 qdrant :26-31）
  - `app/ops/rag/shadow_write.py`（`filter_payload` :55-72 仅 5 键 source_type/repo/source_id/chunk_index/tenant_id **无时间戳** · 影子写开关 :26-31 · DLQ `ops_qdrant_dlq` 写入 :149-185）
  - `app/ops/rag/ingest.py` :284（`enqueue_shadow_upsert(shadow_points)` 业务写入点）
  - `scripts/qdrant_migrate/bulk_upsert.py` :46 / `create_collection.py` :15 / `export_vectors.py` :41（迁移写入点 · collection 缺省 ops_knowledge · 头号嫌疑来源）
  - `reports/qdrant_reconcile_20260813T125801Z.yaml`（**关键线索**：2026-08-13 pg_count=8574 == qdrant_count=8574 · max_l_inf=0.0 —— 8574 与今日 Qdrant 点数逐数相等，头号假设 = 迁移期写入 + PG 其后重建清空；DLQ 亦空与库重建自洽）
  - `docs/guides/RUNBOOK_prod_vector_waterline_v1_zh.md`（§3 判读表 :52-61：Qdrant 有 PG 无 = 墓碑未删/脏点嫌疑 · §4 mismatch → 另立处置 task）
- 起草时环境实证：`docker ps` → `ops-desk-api-qdrant-1` Up 30h (healthy) 6333-6334 映射 · `ops-desk-api-db-1` Up 30h (healthy) 5432 映射（Up 时长 ≠ Created 时间，F2 须 docker inspect 实证）；`alembic/versions/` 17 个迁移文件在库。
- 范围设计：F1 Qdrant 8574 点来源判定（只读 scroll with_payload=True 抽样 ≥100 点覆盖头中尾 + DLQ/env/迁移痕迹对照 → 三态定性）· F2 PG 空表成因判定（行数复核 + alembic head + docker inspect 卷/容器史 + 对照 2026-08-13 收窄时间窗）· F3 结论报告落盘（处置建议清理脚本/重建索引/保持原样 三选一须实证支撑 · 处置执行另立）· F4 留档收口。
- 非范围四条钉死：生产任何访问 · 直接删/改 Qdrant 或 PG 数据（处置另立）· shadow_write.py 等功能改码（须改码即 STOP 另立）· 配置/测试/监控改动。
- failure_paths 八条：不假绿 · 抽样证据可复现（命令+输出附件钉死 FP-3）· 容器瞬态两段照登不挑有利（FP-2）· payload 无时间戳限制如实记（FP-4）· 无法判定+已排除项合法不硬判（FP-5）· 处置冲动即越界（FP-7）· 本地口径防外推生产（FP-8）。
- TC 六条（实证+机断混合）：TC-DA-1 抽样可复现 · TC-DA-2 来源定性引证据 · TC-DA-3 空表成因+时间窗 · TC-DA-4 报告落盘+建议引证据 · TC-DA-5 不假绿回溯 · TC-DA-6 零越界+pytest 复证+task lint。
- 闸设计：HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES **全 pending 未代签**（阻塞面 = 40；本 task 无 30 棒）。graph_change_layer=none · review_hat=20 · required_invoke_hats=10,40。
- 纪律遵守：零 git 操作 · 仅新增 untracked 文件（本档 + invoke · 起草后 git status 旁证无既有文件改动）；`npx --yes spec-wave task lint` 结果见下。
- 交付：`docs/tasks/active/task_local_vector_data_state_audit.md`。

## lint 结果

`npx --yes spec-wave task lint --file docs/tasks/active/task_local_vector_data_state_audit.md` → `LINT: PASS · task_local_vector_data_state_audit.md` · EXIT=0（一次过）。

## 实证发现（起草期 · 供 40/20 参考）

1. **8574 逐数相等**：2026-08-13 对账先例 pg_count=qdrant_count=8574（max_l_inf=0.0）与今日 Qdrant 8574 完全一致 —— 头号假设：点为迁移期 `bulk_upsert.py` 写入，PG 侧其后被重建清空（DLQ 空与库重建自洽）。**未经实证**，本 task F1/F2 定真伪。
2. **payload 无时间戳字段**：`filter_payload`（shadow_write.py:55-72）仅 source_type/repo/source_id/chunk_index/tenant_id 五键 —— 点时间线不可由 payload 直读，只能由库/容器/报告历史间接收窄（已落 FP-4）。
3. **写入路径仅三处**：影子写（ingest.py:284 → shadow_write.py:75，开关 `RAG_QDRANT_SHADOW_WRITE`）、`scripts/qdrant_migrate/bulk_upsert.py`（collection 缺省 ops_knowledge）、`create_collection.py` 建集合；`expand_synthetic.py` 缺省目标 ops_knowledge_scale 非本 collection。
4. **DLQ 空的双解释自洽性**：DLQ depth=0 既可能是「影子写从未失败」，也可能是「库重建连 DLQ 一起清空」—— F2 docker inspect 卷/容器 Created 时间可区分两者。

## 留 20 审要点

- 只读边界是否钉死（非范围第 2 条 + FP-7 越界即 FAIL + TC-DA-6 零 diff）· 「须改码即 STOP 另立」边界（FP-6）· 无法判定不硬判的合法性（FP-5 + TC-DA-2/3 三态含无法判定）· 处置建议三选一须实证支撑是否可验收（TC-DA-4 引证据要求）· 闸阻塞面 = 40（无 30 棒）口径是否认可。
