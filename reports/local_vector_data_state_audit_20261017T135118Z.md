# 本地向量数据态核查结论报告 · local_vector_data_state_audit（40 实证棒）

> **task**：`docs/tasks/active/task_local_vector_data_state_audit.md`（F1 来源判定 / F2 空表成因 / F3 本报告 / F4 留档）
> **recorded_at**：2026-10-17T13:51:18Z（UTC）· **executed_by**：40 实证棒（本地 compose · 全程只读 · 零改码）
> **立案证据**：`reports/vector_waterline_local_20261017T123649Z.yaml`（pg=0 · dlq=0 · qdrant=8574 · count_diff=-8574 · verdict=mismatch）
> **证据附件**：`docs/harness/invokes/by-task/local-vector-data-state-audit/evidence/`（e00 命令台账 · e01–e05 原始输出，FP-3 钉死可复现）
> **disclaimer**：**本报告为本地/compose 开发库口径，不得外推生产**（FP-8）；生产核查属 TC-WL-8（HG-PROD-READONLY-ACCESS 仍 pending）。**处置执行另立 task**，本报告仅出建议（FP-7）。

---

## 结论摘要（三态定性）

| 项 | 定性 | 置信 |
|----|------|------|
| **F1 · Qdrant 8574 点来源** | **历史正常写入（迁移期 `export_vectors.py` → `bulk_upsert.py` 批量写入）**；因 PG 侧其后被清空，现相对 PG 呈孤儿/墓碑形态 | 高（payload 键集指纹 + 文件时间戳链 + 逐数对照，多重互证） |
| **F2 · PG 空表成因** | **数据被删（表级清空）**，非库重建清空；清空完成时间不晚于 **2026-09-07 02:19:59Z**，晚于 2026-08-13 先例 | 高（卷/initdb 未重建钉死排除库级重建；表文件归零时刻钉死窗口） |
| **F3 · 处置建议** | **清理脚本**（三选一 · 理由见 §4 · 执行另立 task） | — |

### 重建后的时间线（全部由落档证据钉死，无记忆转述）

| 时刻（UTC） | 事件 | 证据 |
|-------------|------|------|
| 2026-07-16 08:19:50 | pgdata 卷创建 / PG 数据目录 initdb | e01b（volume CreatedAt）· e02（PG_VERSION mtime） |
| 2026-08-13 09:21–09:25 | 迁移期对账 pg_count=qdrant_count=8574 · max_l_inf=0.0（**旧 qdrant 卷**） | reports/qdrant_migrate/reconcile_p1_20260813.yaml · reports/qdrant_reconcile_20260813T125801Z.yaml（12:58Z 复测） |
| 2026-08-13 09:21:20 | DLQ 表文件最后被触碰（此后无写入） | e02b |
| 2026-08-16 10:43 | **当前** qdrant_data 卷创建（旧卷已废弃） | e01b |
| 2026-08-18 02:54 | 当前卷上 ops_knowledge 集合创建 + **单次批量写入 8574 点**（WAL closed-0/open-2/open-3 与全部 7 段 payload/vector 存储 mtime 均为此刻）；此后零写入 | e03b · e03c |
| 2026-08-21 01:54–02:36 | expand_synthetic 容量实验：以 ops_knowledge（source_n=8574）为源扩写 scale/scale_mem/scale_sq/scale_100k 集合 | e03b（集合目录 mtime）· reports/qdrant_migrate/expand_rss*.json（t=1787277274≈08-21 02:34Z） |
| **(08-13, 09-07]** | PG ops_knowledge_chunks 8574 行被清空；堆文件缩至 0 字节时刻 **2026-09-07 02:19:59** | e02b |
| 2026-09-29 09:51:40 | alembic_version 文件最后更新；当前 head=20260923_memory_episodes（清空后库仍正常迁移升级） | e02 · e02b |
| 2026-10-16 07:07:36 | 双容器本次启动（postmaster_start 一致；仅触碰 segment.json/newest_clocks.json，无数据写入） | e01 · e02 · e03c |
| 2026-10-17 12:36:49 | 水位核查发现 mismatch（8574/0/-8574）→ 本 task 立案 | 立案报告 |

---

## §1 F1 · Qdrant 8574 点来源判定（TC-DA-1 / TC-DA-2）

### 1.1 抽样实录（TC-DA-1 · FP-3 附件钉死）

- **方法**：只读 scroll（禁改 `scripts/check_vector_waterline.py`，另发一次性脚本走 stdin · 不落码文件 · 剥离代理环境变量）。先 id-only 全量 scroll（`with_payload=false, with_vector=false`，9 页 × limit=1000），再按排序 id 取**头 50（id 1–50）/中 50（4263–4312）/尾 50（8525–8593）= 150 点 ≥100**，`has_id` 过滤 + `with_payload=true, with_vector=false` 取回。命令全文见 e00；原始输出 e04_scroll_ids_raw.json / e04_sample_payloads_raw.json / e04_scroll_stats.txt。
- **id 空间**：8574 个唯一 int id，min=1，max=8593，**1 处宽度 20 的缺口（19 个 id 缺失）**，其余连续。与「自 PG `ORDER BY id` 导出」形态一致（e04_scroll_stats.txt）。
- **payload 键集（150/150 完全一致）**：`{source_type, repo, source_id, chunk_index}` **恰 4 键**。
  - **偏差照实记**：task 预期 5 键（含 tenant_id）——实测 **150/150 样本均无 tenant_id**。
- **取值分布**：source_type = issue 54 / pr 55 / doc 41；repo = MoonshotAI/kimi-code 109 / ops-desk-workspace 41；chunk_index 全为 int，min=0 max=19；source_id 为 issue/pr 号（如 "2720"、"770"）与文档路径（如 "contracts/rag-knowledge-contract-v1.md"）。均为真实业务内容形态，非随机垃圾。
- **collection 级佐证**：payload_schema 显示 source_type/repo/source_id 三键各覆盖 8574 点（e03，tenant_id 未建索引亦无键）。

### 1.2 来源定性判据（逐条引证据）

1. **键集指纹匹配迁移工具链**：`scripts/qdrant_migrate/export_vectors.py:12` `ALLOWED_PAYLOAD = ("source_type","repo","source_id","chunk_index")` 恰为实测 4 键；`bulk_upsert.py:86-95` 原样透传导出 payload。而影子写 `app/ops/rag/shadow_write.py` `filter_payload` :55-72 **恒产 5 键**（tenant_id 缺省 TENANT_A :64/:71）。150/150 无 tenant_id → **排除影子写来源，锁定迁移工具链**。
2. **写入窗口钉死**：当前 qdrant_data 卷 CreatedAt=2026-08-16 10:43Z（e01b）；集合目录与 WAL/段存储全部 mtime=**2026-08-18 02:54**（e03b/e03c），其后零写入 → 8574 点为 08-18 单次批量写入（bulk_upsert 形态：batch 256 幂等 upsert）。
3. **逐数对照**：点数 8574 与 2026-08-13 先例 pg_count=qdrant_count=8574 逐数相等（reconcile_p1_20260813.yaml · qdrant_reconcile_20260813T125801Z.yaml）；08-21 expand_rss*.json source_n=8574 复证该集合彼时仍为 8574。注意：08-13 对账对象是**旧卷**（现卷 08-16 才创建），现有点为 **08-18 重迁**（彼时 PG 仍有 8574 行，见 §2 时间窗）。
4. **DLQ 全量复核**：`ops_qdrant_dlq` depth=0（e02，与立案报告一致）；DLQ 表文件 mtime=2026-08-13 09:21:20 后无写入（e02b）。
5. **影子写 env 实况**：本地无 .env（仅 .env.example）、shell 无 RAG_/QDRANT 变量；compose 默认 `RAG_QDRANT_SHADOW_WRITE=true`（docker-compose.yml:71）但 **api 容器当前未运行**（docker ps 仅 db+qdrant，e05）→ 影子写通道当前不活跃，与「08-18 后零写入」自洽。

**定性：历史正常写入（迁移期写入）。** 补充形态说明：点来源正当，但因 PG 对应行其后被清空（§2），当前相对 PG 呈 runbook §3「Qdrant 有 PG 无」的孤儿/墓碑形态——mismatch 的成因在 PG 侧清空，而非 Qdrant 侧脏写。

**FP-4 限制照登**：payload 无时间戳字段（filter_payload 仅 5 键且样本实测 4 键），点时间线不可由 payload 直读；本报告写入时刻（08-18 02:54）系由 WAL/段文件 mtime 间接钉死，非 payload 直读。

---

## §2 F2 · PG 空表成因判定（TC-DA-3）

### 2.1 复核实录

- `ops_knowledge_chunks` 行数复核 = **0**（e02，与立案报告一致）。
- `alembic_version` 当前 head = **20260923_memory_episodes**（e02；仓内 16 个迁移文件最新即此，R1 N1 已核）。
- `ops_qdrant_dlq` 行数复核 = **0**（e02）。
- `docker inspect`（e01）：db 容器 Created=2026-07-16T08:19:50Z · 挂卷 ops-desk-api_pgdata；qdrant 容器 Created=2026-08-21T02:15:06Z · 挂卷 ops-desk-api_qdrant_data；双容器 StartedAt=2026-10-16T07:07:36Z。

### 2.2 成因定性判据（逐条引证据）

1. **排除库重建清空**：pgdata 卷 CreatedAt=**2026-07-16**（e01b），PG_VERSION 文件 mtime=**2026-07-16 08:19:50**（e02，initdb 时刻近似）——数据目录自 07-16 初始化后**从未重建**；而 08-13 先例 pg_count=8574 证明彼时库内有数。卷级/实例级重建假设被钉死排除。
2. **表级清空时刻钉死**：ops_knowledge_chunks 主叉文件 size=**0 字节**、mtime=**2026-09-07 02:19:59Z**（e02b）→ 清空完成于 **(2026-08-13T12:58Z, 2026-09-07T02:19:59Z]** 窗口。
3. **清空形态**：relfilenode==oid=61170（未经 TRUNCATE/VACUUM FULL 的 relfilenode 重写），文件缩至 0 → 形态一=DELETE 后 VACUUM 截断尾部空页；形态二=DROP TABLE + 重建空表（oid 61170 为高值，不能排除）。**两解皆属「表级清空/数据被删」类**，均非库重建；本排查不硬判具体 DDL/DML 路径（FP-5 出口保留，见 §5）。
4. **非整库清空**：checkpoint_blobs 2032 / checkpoint_writes 4459 / checkpoints 1078 / ops_lg_rag_run_events 11805 / ops_llm_usage 510 / ops_invite_tokens 8 / ops_sessions 6 行等在库（e02-6）——库整体存活，仅 ops_knowledge_chunks（及 ops_repos/ops_issues/ops_pull_requests 等 sync 源表同为 0，照登不展开）被清。
5. **清空后库仍正常使用**：alembic_version head=20260923_memory_episodes、文件 mtime=2026-09-29（e02/e02b）——清空后迁移照常升级，排除「09-07 清空即弃库」。
6. **DLQ 空双解释区分**：DLQ 表文件 mtime=2026-08-13 09:21:20（e02b）**先于** PG 清空窗口（09-07）——DLQ 并非「09-07 库重建连 DLQ 一起清空」（库重建已被判据 1 排除），而是**影子写通道自 08-13 后无失败写入**，与「从未失败/未被触发」解释自洽。

**定性：数据被删（表级清空，窗口 (08-13, 09-07]，文件归零时刻 09-07 02:19:59Z）。**
**口径钉死（FP-8）：本地/compose 开发库口径，结论不得外推生产。**

---

## §3 mismatch 机制重建（F1+F2 合流）

8574 个点 = 08-18 迁移工具链自 PG（彼时仍有 8574 行）导出重迁至当前 qdrant 卷的正当写入；其后 PG 表在 09-07 前被表级清空（绕过应用层，故无影子删除、无 DLQ 痕迹），Qdrant 点保留至今 → count_diff=-8574 mismatch。**点非脏写、PG 非重建：是「迁移遗留点 + PG 后续表级清空」的叠加态。**

## §4 处置建议（三选一 · 每条附实证支撑 · 执行另立 task）

**建议：清理脚本（删除 ops_knowledge 中 8574 个孤儿点）。**

| 选项 | 实证支撑/排除理由 |
|------|--------------------|
| ✅ **清理脚本** | 来源已定性为迁移期正当写入、PG 对应行已被删且本地无恢复源（§2 判据 4：sync 源表同空）；点自 08-18 后零写入、无业务引用（api 容器未运行 · e05）；清理后复跑 `scripts/check_vector_waterline.py` 可归零 mismatch，消除后续每次核查的噪音（runbook §4 口径） |
| ❌ 重建索引 | 本地 PG 源数据已空（ops_knowledge_chunks=0 且 ops_repos/ops_issues/ops_pull_requests 同空，e02-6）——本地无料可重建；「重建」实为重新 sync+ingest 的全新数据生产，超出「恢复一致性」语义，且非本 task 能实证支撑其必要性 |
| ❌ 保持原样 | 8574 孤儿点使每次本地水位核查恒定 mismatch（立案报告即因此上抛）；本地开发库无保留墓碑的业务理由 |

**处置执行（清理脚本 + 复跑验证）另立 task，本 task 零写动作（FP-7）。**

## §5 不确定项与限制照登（FP-4 / FP-5 / 不假绿）

1. **FP-4**：payload 无时间戳字段，点时间线不可 payload 直读；写入时刻由 Qdrant WAL/段文件 mtime 间接钉死（2026-08-18 02:54）。
2. **清空路径两解**：DELETE+VACUUM 截断 vs DROP+重建空表（§2 判据 3），pg_stat_user_tables 计数器内部不自洽（多表 n_tup_ins=0 却有存量行，计数器历史上曾被重置）不可作判据——两解同属「表级清空」，不影响定性结论，照登不硬判。
3. **id 缺口**：8574 点分布于 [1,8593] 含 1 处宽 20 缺口（19 id 缺失）；可能为源表历史空洞或导出期缺页，无残留证据可进一步区分，照登。
4. **fp-2 容器态**：排查全程双容器 Up (healthy) 稳定，开工/收工两次 docker ps 一致（e05），无瞬态重启，无降级段需对照。
5. **计数一致性**：8574 / 0 / -8574 与立案报告 `vector_waterline_local_20261017T123649Z.yaml` 逐项一致，本报告零伪造计数。

## §6 证据附件索引（FP-3）

| 附件 | 内容 |
|------|------|
| evidence/e00_commands.md | 全部命令全文台账 |
| evidence/e01_docker_inspect_containers.json · e01b_* | 容器 Created/Mounts · 卷 CreatedAt |
| evidence/e02_pg_queries.txt · e02b_pg_table_files.txt | 行数/alembic head/pg_stat/表文件 mtime·relfilenode |
| evidence/e03_qdrant_collection_info.json · e03b_* · e03c_* | collection info（8574 · payload_schema）· 存储目录/WAL/段文件 mtime |
| evidence/e04_scroll_ids_raw.json · e04_sample_payloads_raw.json · e04_scroll_stats.txt | scroll 全量 id 原始输出 · 150 样本 payload 原始输出 · 分布统计 |
| evidence/e05_docker_ps_bookend.txt | 开工/收工容器态对照 |
