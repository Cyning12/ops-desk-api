---
hat: 40-live-verify（实证棒）
task_slug: local_vector_data_state_audit
date: 2026-10-17
---

# invoke · 40 实证 · local_vector_data_state_audit（本地 Qdrant 8574 vs PG 0 数据态溯源核查）

> **授权链**：维护者 2026-10-17 授权三闸 approved（m00914 · 00 代录）→ 40 实证棒开工。GATE_VERIFY 首输出三闸全 approved（HG-TASK-DRAFT/HG-AUDIT-R1/HG-GRAPH-MODULES · 闸真值以 task 表为准）。
> **纪律**：全程只读（SELECT/count/scroll/docker inspect/exec ls）· 零改码 · 零数据写动作 · 代理剥离访问 Qdrant（承 123538Z 降级先例）。

## 输入

- task 全文（TC-DA-1~6 · FP-1~8 · 范围 F1-F4 · 非范围）
- R1 审查文 `docs/harness/reviews/task_local_vector_data_state_audit_audit_R1_20261017.md`（签收零阻塞 · nit 2 已修正）
- 10/20 invoke · 立案/降级/先例三报告 · shadow_write/export_vectors/bulk_upsert 真读（行号按实校正）

## 动作实录（全只读 · 命令全文见 evidence/e00_commands.md）

1. GATE_VERIFY 三闸全 approved → 开工；git status 基线仅 untracked（task 档+R1+invoke 目录）。
2. E1 容器/卷史：`docker inspect` 双容器 + `docker volume inspect`（e01/e01b）→ pgdata 卷 2026-07-16 · qdrant_data 卷 **2026-08-16 10:43**（晚于 08-13 先例 → 08-13 对账对象系旧卷）。
3. E2 PG 只读查询（e02/e02b）：ops_knowledge_chunks=0 · DLQ=0 · alembic head=20260923_memory_episodes · PG_VERSION mtime=07-16（initdb 未重建）· **ops_knowledge_chunks 堆文件 0 字节 mtime=2026-09-07 02:19:59Z** · relfilenode==oid=61170 · alembic_version 文件 mtime 09-29 · DLQ 文件 mtime 08-13 · 全表 n_live_tup 普查（checkpoint/rag/llm 表有数，非整库清空）。
4. E3 Qdrant 只读（e03/e03b/e03c）：collection info points_count=8574 · payload_schema 三键各 8574 覆盖 · WAL closed-0/open-2/open-3 与 7 段存储 mtime 全部 **2026-08-18 02:54**（单次批量写入，此后零写入）· scale 系集合 08-21 容量实验。
5. E4 scroll 抽样（e04，一次性 stdin 脚本不落码文件）：id-only 全量 scroll 9 页 8574 唯一 id ∈[1,8593] 含 1 处宽 20 缺口；头 50/中 50/尾 50=150 点 with_payload=True 取样 → 键集恰 4 键 {source_type,repo,source_id,chunk_index}（**150/150 无 tenant_id，偏差照实记**）· source_type issue54/pr55/doc41 · repo kimi-code 109/ops-desk-workspace 41 · chunk_index int 0..19。
6. 键集指纹对照：export_vectors.py:12 ALLOWED_PAYLOAD 恰 4 键 vs shadow_write.py filter_payload :55-72 恒产 5 键（tenant_id 缺省 TENANT_A）→ 锁定迁移工具链写入，排除影子写。
7. 迁移痕迹对照：reports/qdrant_migrate/reconcile_p1_20260813.yaml（pg=qdrant=8574 · max_l_inf=0.0）· expand_rss*.json（08-21 · source_n=8574）· 立案报告 8574/0/-8574 逐数一致。
8. F3 报告落盘 `reports/local_vector_data_state_audit_20261017T135118Z.md`；开工/收工 docker ps 双 healthy 一致（e05 · FP-2 无瞬态）。

## 结论（TC 逐项）

- **TC-DA-1 PASS**：抽样 150 点 ≥100 覆盖头中尾 · 键集/分布实录 · 命令+原始输出附件齐（FP-3）。
- **TC-DA-2 PASS**：F1 定性=**历史正常写入（迁移期 export_vectors→bulk_upsert）**；判据 5 条逐条引证据（键集指纹/WAL 时间窗/8574 逐数对照/DLQ=0/env 实况）。
- **TC-DA-3 PASS**：F2 定性=**数据被删（表级清空，窗口 (08-13, 09-07]，文件归零 09-07 02:19:59Z）**；库重建被卷/initdb 时间钉死排除；本地开发库口径钉死（FP-8）。
- **TC-DA-4 PASS**：报告落盘含 F1/F2 判据、附件索引、处置建议**清理脚本**（三选一 · 每选项有实证支撑/排除理由）· 双 disclaimer。
- **TC-DA-5 PASS**：判定全可回溯落档证据；无瞬态/降级段；不确定项 3 条显式列出（FP-4 无时间戳 · 清空路径两解 · id 缺口）；计数与立案报告一致零伪造。
- **TC-DA-6**：git 白名单 + pytest 13 绿 + task lint 复证见任务档自检结论回填。

## 不假绿声明

容器全程 healthy 无瞬态（FP-2 两段一致）；payload 无 tenant_id 为实测偏差，已照实记而非圆谎为 5 键；清空路径 DELETE+VACUUM vs DROP+重建两解未硬判（FP-5 出口）；零写动作（FP-7）。

## 交付

- 报告 `reports/local_vector_data_state_audit_20261017T135118Z.md`
- 证据 `docs/harness/invokes/by-task/local-vector-data-state-audit/evidence/`（e00–e05 共 13 件）
- 任务档 TC 勾选 + 自检结论 + 修订记录回填
