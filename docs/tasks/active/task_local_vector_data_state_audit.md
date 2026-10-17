# Task：local-vector-data-state-audit（FP-7 上抛开账 · 本地 Qdrant 8574 点 vs PG 0 行数据态溯源核查）

> **状态**：approved 待 40（三闸 approved · 维护者 2026-10-17 授权 00 代录 m00914 · 承 m00238 总授权 · R1 审查签收 nit 2 项已修正）
> **类型**：本地数据态核查（**只读排查优先 · 零改码 · 40 轨实证棒** · 处置方案须实证后另行裁定）
> **上游**：[`task_vector_waterline_local_rerun.md`](../done/task_vector_waterline_local_rerun.md) 自检结论 FP-7 上抛（:173「本地 Qdrant 8574 points vs PG 0 行 → verdict=mismatch · 疑墓碑/脏点或本地 DB 重建清空 · 建议维护者另立处置 task」）；维护者 2026-10-17（会话 m00847）选定立本 task 溯源本地数据态来源
> **分支**：无（零改码 · 零 git 操作纪律；报告产物提交与否由 00/维护者事后裁定）
> **现网默认**：`RAG_VECTOR_BACKEND=qdrant`（compose Qdrant v1.19.0 · 失败降级 pgvector · 影子写/DLQ）

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `local_vector_data_state_audit` |
| **git_branch** | 无（零改码 · 零 git 操作） |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 实证 + 机断混合：本地 compose 真实只读排查出结论报告（40 实证）+ 既有桩测 `tests/test_check_vector_waterline.py` 复跑零红（零越界旁证）；无新代码、无新测试 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `none` |
| **graph_delta** | `none` |
| **graph_delta_note** | 仅只读排查本地数据态并产出结论报告；无新模块/无对外契约/无配置改动 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 本地数据态结论报告属运维证据留痕；是否回写路线/wiki 由维护者阅报后裁定，非本 task |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,40` |
| **invoke_retention_profile** | `default`（实取 10+40 · 本 task 无 30 改码棒 · 20 按授权） |
| **experience_capture** | `recommended` |
| **kpi_aggregator** | `n/a` |
| **orchestration** | 10 落稿 → 20 R1（按维护者授权取舍）→ 维护者签闸 → 40 只读排查实证 + 结论报告落盘 + 验收勾选/自检结论回填 → CLOSE |
| **freeze_id** | 无 |
| **related_tasks** | [`task_vector_waterline_local_rerun.md`](../done/task_vector_waterline_local_rerun.md)（上抛母体 · FP-7 :173）· [`task_prod_vector_waterline_check.md`](../done/task_prod_vector_waterline_check.md)（核查资产母体）· [`task_qdrant_migration.md`](../done/task_qdrant_migration.md)（迁移与 2026-08-13 对账先例） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | approved | 20, 40 | 维护者 2026-10-17 授权 00 代录（m00914 · 承 m00238 总授权） |
| HG-AUDIT-R1 | approved | 40 | 维护者 2026-10-17 授权 00 代录（m00914）· R1 审查文 task_local_vector_data_state_audit_audit_R1_20261017.md 签收零阻塞 nit 2 已修正 |
| HG-GRAPH-MODULES | approved | 40 | 维护者 2026-10-17 授权 00 代录（m00914）· `graph_change_layer=none` 本 task 零图谱改动 |

> 关联闸照登：HG-PROD-READONLY-ACCESS 仍 pending（仅阻生产执行 TC-WL-8）；**本 task 零涉生产**，不受其阻、也不消解之。

---

## 背景与目标

task_vector_waterline_local_rerun 40 亲跑实证（2026-10-17 · 报告 `reports/vector_waterline_local_20261017T123649Z.yaml`）：本地 PG `ops_knowledge_chunks` **0 行** / DLQ `ops_qdrant_dlq` **空**（depth=0）/ Qdrant `ops_knowledge` **8574 points**（count 与 scroll 一致），count_diff=-8574，verdict=**mismatch**（Qdrant 独有 8574 · PG 独有 0）。母体按 FP-7 纪律只记录不处置，上抛另立。维护者 2026-10-17（会话 m00847）裁定立本 task 溯源：**这 8574 个点从哪来、PG 为什么是空的、当前数据态该如何定性**。

**头号待证假设**（R1 证据）：`reports/qdrant_reconcile_20260813T125801Z.yaml` 记 2026-08-13 本地对账 pg_count=8574 == qdrant_count=8574 · max_l_inf=0.0 —— 8574 与今日 Qdrant 点数**逐数相等**，强提示点为 2026-08-13 前后 `scripts/qdrant_migrate/bulk_upsert.py` 迁移写入、PG 侧其后被重建清空（DLQ 亦空与「库重建」自洽）；但本假设**未经实证**，本 task 即以证据定真伪。

### 实证锚点（10 已亲读复核 · 40 必读）

| 主题 | 路径 · 锚点 | 现状（2026-10-17 亲核） |
|------|-------------|--------------------------|
| 实跑报告（本 task 立案证据） | `reports/vector_waterline_local_20261017T123649Z.yaml` | pg_face.row_count=0 · dlq.depth=0 verdict=empty · qdrant_face.points_count=scrolled_ids=8574 · reconcile.count_diff=-8574 verdict=mismatch · qdrant_only 8574（抽样 id 1/10/100/1000…）· degradation.degraded=false |
| 降级照登旁证 | `reports/vector_waterline_local_20261017T123538Z.yaml` | 同日首跑（shell 代理污染致 Qdrant 面 no_evidence · degraded）—— 证明降级机制真实生效、8574 非脚本伪造 |
| 只读核查脚本 | `scripts/check_vector_waterline.py`（scroll 形态 :131-144） | count + scroll `with_payload=False, with_vectors=False` 只取 id；**F1 抽样须自行发只读 scroll（with_payload=True），禁改本脚本** |
| collection/写入路径 | `app/ops/rag/backend.py` :38-39 | `qdrant_collection()` 缺省 `ops_knowledge`；`RAG_VECTOR_BACKEND` 缺省 qdrant :26-31 |
| 影子写与 DLQ | `app/ops/rag/shadow_write.py` | `enqueue_shadow_upsert` :75（PG commit 后非阻塞入队 · `RAG_QDRANT_SHADOW_WRITE` 开关 :26-31）· `enqueue_shadow_delete` :92（整组替换/墓碑删除）· DLQ 表 `ops_qdrant_dlq` 写入 :149-185（op/point_ids/payload/error） |
| payload 键集真值 | `app/ops/rag/shadow_write.py` `filter_payload` :55-72 | Qdrant payload 仅 5 键：source_type/repo/source_id/chunk_index/tenant_id（tenant_id 缺省试点 A）· **无时间戳字段** —— 点时间线不可由 payload 直读，F1 须如实记录此限制（FP-4） |
| 业务写入点 | `app/ops/rag/ingest.py` :284 | ingest 收尾 `enqueue_shadow_upsert(shadow_points)` |
| 迁移写入点（头号嫌疑来源） | `scripts/qdrant_migrate/bulk_upsert.py` :46 · `create_collection.py` :15 · `export_vectors.py` :41 | collection 缺省 `ops_knowledge`；export 自 `ops_knowledge_chunks ORDER BY id`；`expand_synthetic.py` 缺省目标 `ops_knowledge_scale`（非本 collection；实测仅 `--source`/`--target` 参数 :91-92，无 `--collection`，缺省不落 ops_knowledge） |
| 本地对账先例（8574 同源线索） | `reports/qdrant_reconcile_20260813T125801Z.yaml` | 2026-08-13：pg_count=8574 == qdrant_count=8574 · count_diff=0 · max_l_inf=0.0 · mean_topk_overlap=1.0 —— 彼时双侧一致 |
| runbook（判读口径） | `docs/guides/RUNBOOK_prod_vector_waterline_v1_zh.md` | §3 判读表 :52-61：Qdrant 有 PG 无 = 墓碑未删/脏点嫌疑；§4 mismatch → 另立处置 task（本 task 即其核查前置）· §2 local 命令 :39-43 |
| 容器现状（10 起草时实证） | `docker ps` | `ops-desk-api-qdrant-1` Up 30h **(healthy)** 6333-6334 映射 · `ops-desk-api-db-1` Up 30h **(healthy)** 5432 映射 —— 排查前置现实满足（Up 时长 ≠ Created 时间，F2 须 `docker inspect` 实证） |
| PG 迁移史 | `alembic/versions/` | 16 个迁移 .py 在库（20260715_init 至 20260923_memory_episodes · R1 N1 修正）；`alembic_version` 表当前 head 与库创建时间属 F2 实证项 |

### 目标

F1：Qdrant 8574 点**来源判定**（只读 scroll 抽样 payload 元数据 + 对照影子写/DLQ 历史 + 迁移脚本实证）。F2：PG 空表**成因判定**（库是否重建清空 · alembic/容器历史 · 本地属开发库口径）。F3：结论报告落盘，含处置建议（清理脚本 / 重建索引 / 保持原样 三选一，**须实证支撑**；处置执行本身为非范围另立）。

---

## 范围

- **F1 · Qdrant 8574 点来源判定**：
  - 只读抽样 scroll `ops_knowledge`（`with_payload=True`，禁取 vector 减少搬运），样本 ≥100 点、覆盖 id 头/中/尾段；实录 payload 键集与取值分布（source_type/repo/tenant_id 分布 · chunk_index 形态）。
  - 对照判定：`ops_qdrant_dlq` 全量 SELECT（现 depth=0 照登）· `RAG_QDRANT_SHADOW_WRITE` 本地 env 实况 · `scripts/qdrant_migrate/bulk_upsert.py` 调用痕迹（reports/ 迁移期报告 · `reports/qdrant_reconcile_20260813T125801Z.yaml` 8574 逐数对照）。
  - 定性三态：**历史正常写入（迁移/影子写）** vs **墓碑/脏点** vs **无法判定**；判据逐条落报告。
- **F2 · PG 空表成因判定**：
  - 复核 `ops_knowledge_chunks` 行数=0 与 `alembic_version` 当前 head；`docker inspect ops-desk-api-db-1` 实证容器 Created 时间与挂载卷（volume 重建即库清空实证）；对照 2026-08-13 先例（pg=8574）收窄清空时间窗。
  - 定性：**DB 重建清空** vs **数据被删** vs **无法判定**；并如实记「本地属开发库口径，结论不外推生产」。
- **F3 · 结论报告落盘**：落 `reports/local_vector_data_state_audit_<UTCts>.md`（对齐水位报告惯例；维护者指定 `docs/reports/` 亦可）；含 F1/F2 判定、证据附件索引（scroll 命令+输出）、**处置建议三选一**（清理脚本 / 重建索引 / 保持原样）及其实证支撑理由；**处置执行另立 task**。
- **F4 · 留档收口**：40 invoke 落 `docs/harness/invokes/by-task/local-vector-data-state-audit/`；本档验收勾选 + 自检结论 + 修订记录回填。

## 非范围

- **生产环境任何访问**（HG-PROD-READONLY-ACCESS 仍 pending · 本 task 仅本地 compose）
- **直接删/改 Qdrant 或 PG 数据**：清理脚本执行、重建索引执行、DLQ 重放、删点/删表均为**处置执行**，另立 task；本 task 只允许 SELECT / count / scroll / docker inspect 等只读动作
- **功能改码**：`scripts/check_vector_waterline.py` · `app/ops/rag/shadow_write.py` · `app/ops/rag/ingest.py` · `scripts/qdrant_migrate/*` 等零 diff 硬约束；**若实证发现须改码即 STOP，另立 task**
- 改 ingest 管线 / compose 默认值 / 任何配置；新写测试；监控/告警接线

---

## 失败路径

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----------|----------|--------|----------|
| FP-1 闸 pending 即 40 排查 | GATE_VERIFY **拒开工**（真值在本档人工闸表） | 是 | — |
| FP-2 容器不可达/瞬态重启 | 如实记 `no_evidence` 不假绿；先 `docker ps`/`docker inspect` 留证容器态，必要时 `docker compose up -d db qdrant` 待 healthy 重跑；**容器瞬态导致证据前后不一致时两段都照登，不挑有利的记** | 是 | 报告标注 + stderr |
| FP-3 抽样证据不可复现 | scroll 命令全文 + 原始输出附件必落档（随报告或 invokes 引用）；缺附件即 TC 判 FAIL；**禁凭记忆转述样本内容** | 是 | 40 invoke 实录 |
| FP-4 payload 无时间戳字段 | 如实记「点时间线不可直读」限制（`filter_payload` :55-72 仅 5 键）；时间窗改由库/容器/报告历史间接收窄；**不硬判写入时间** | — | 报告 |
| FP-5 结论无法判定 | 如实记「无法判定 + 已排除项清单」（已排除什么、为什么剩下的判不了）；**不硬判**、不为了出结论而结论 | — | 报告 |
| FP-6 实证发现须改码（脚本/ingest/影子写 bug） | **STOP**；只把 bug 证据与复现路径写入报告，改码另立 task | — | 报告 + 40 invoke |
| FP-7 处置冲动（顺手清数据/重建索引） | 禁止；本 task 只出建议；任何写动作出现即越界，TC-DA-6 判 FAIL | — | 报告 + git status 白名单 |
| FP-8 本地结论误当生产口径 | 报告钉死「本地/compose 开发库口径 · 不得外推生产」；生产核查仍属 TC-WL-8（HG-PROD-READONLY-ACCESS pending） | — | 报告 disclaimer |

---

## 验收标准

- [x] **TC-DA-1（实证）**：F1 只读抽样完成 —— scroll `ops_knowledge` `with_payload=True` 样本 ≥100 点且覆盖 id 头/中/尾段；实录 payload 键集（预期 source_type/repo/source_id/chunk_index/tenant_id 五键，偏差照实记）与 source_type/repo/tenant_id 分布统计；scroll 命令全文 + 原始输出附件落档可复现（FP-3）
- [x] **TC-DA-2（实证）**：F1 来源定性出结论 —— 三态之一（历史正常写入 / 墓碑·脏点 / 无法判定）且判据逐条引证据（DLQ 全量复核 depth=0 · 影子写 env 实况 · bulk_upsert 迁移痕迹 · `reports/qdrant_reconcile_20260813T125801Z.yaml` 8574 逐数对照）；无法判定时已排除项清单非空（FP-5）
- [x] **TC-DA-3（实证）**：F2 PG 空表成因出结论 —— `ops_knowledge_chunks` 行数复核=0 · `alembic_version` head 实录 · `docker inspect ops-desk-api-db-1` Created/卷挂载实证 · 清空时间窗推断（对照 2026-08-13 pg=8574 先例）；定性三态之一（DB 重建清空 / 数据被删 / 无法判定）· 「本地属开发库口径」钉死（FP-8）
- [x] **TC-DA-4（实证）**：结论报告 `reports/local_vector_data_state_audit_<UTCts>.md`（或维护者指定 `docs/reports/`）落盘 —— 含 F1/F2 判定与判据、证据附件索引、处置建议三选一（清理脚本 / 重建索引 / 保持原样）**且每条建议有实证支撑理由**、disclaimer 含「本地/compose 开发库口径不得外推生产」与「处置执行另立 task」
- [x] **TC-DA-5（机断）**：不假绿核验 —— 报告内每个判定均可回溯到落档证据（命令+输出）；容器瞬态/降级情形照登无挑选（FP-2）；不确定项显式列出（FP-4/FP-5）；报告无伪造计数（8574/0/-8574 与 `vector_waterline_local_20261017T123649Z.yaml` 一致）
- [x] **TC-DA-6（机断 · 零越界）**：`scripts/` · `app/**` · `alembic/**` · `docker-compose.yml` **零 diff**（git status 仅新增报告 + invokes + 本档）；`uv run pytest tests/test_check_vector_waterline.py -q` 13 passed 复证（只读脚本未被顺手改的旁证）；`npx --yes spec-wave task lint --file docs/tasks/active/task_local_vector_data_state_audit.md` LINT: PASS

## 依赖

- 上抛母体与关账档：[`task_vector_waterline_local_rerun.md`](../done/task_vector_waterline_local_rerun.md)（FP-7 上抛 :173 · 自检结论）· 立案证据 `reports/vector_waterline_local_20261017T123649Z.yaml` · 降级旁证 `reports/vector_waterline_local_20261017T123538Z.yaml`
- 资产（只读 · 零 diff）：`scripts/check_vector_waterline.py`（scroll 形态 :131-144）· `docs/guides/RUNBOOK_prod_vector_waterline_v1_zh.md`（§3 判读口径 · §4 mismatch 处置分流）· `tests/test_check_vector_waterline.py`
- 写入路径真值（只读 · 零 diff）：`app/ops/rag/backend.py`（collection 缺省 :38-39）· `app/ops/rag/shadow_write.py`（payload 键集 :55-72 · DLQ :149-185）· `app/ops/rag/ingest.py`（:284）· `scripts/qdrant_migrate/bulk_upsert.py` · `scripts/qdrant_migrate/create_collection.py` · `scripts/qdrant_migrate/export_vectors.py`
- 本地对账先例：`reports/qdrant_reconcile_20260813T125801Z.yaml`（2026-08-13 pg=qdrant=8574 · 头号同源线索）
- 编码规范：`docs/standards/CODING_BACKEND_L2_v1_zh.md`

## 给执行帽的必读列表

1. 本 task 全文（非范围四条 · 不假绿纪律 · 闸表）。
2. `reports/vector_waterline_local_20261017T123649Z.yaml` 全文（立案证据 · 计数钉死 8574/0/-8574）。
3. `reports/qdrant_reconcile_20260813T125801Z.yaml`（8574 同源线索 · 时间窗锚点）。
4. `app/ops/rag/shadow_write.py` 全文（payload 键集 :55-72 · 影子写开关 :26-31 · DLQ 形状 :149-185 —— 禁信转述 · 行号 40 按实校正）。
5. `docs/guides/RUNBOOK_prod_vector_waterline_v1_zh.md` §3/§4（判读口径与处置分流）。
6. `scripts/check_vector_waterline.py` :125-151（既有 scroll 只读形态参照；F1 抽样禁改本脚本，另发只读 scroll）。
7. `docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`（GATE_VERIFY 形状 · 本 task 阻塞面 = 40）。

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|---|------|------------|----------------------|----------------|
| R0 | 框定：FP-7 上抛开账 = 本地 Qdrant 8574 点 vs PG 0 行的数据态溯源；只读排查优先 · 零改码 · 零涉生产 · 处置另立 | false | — | 闸未签 |
| R1 | 证据：五锚点亲读（报告/脚本/backend/shadow_write/runbook）+ 先例 2026-08-13 pg=qdrant=8574 逐数相等（头号同源线索）+ 写入路径三处定位（影子写/ingest/bulk_upsert）+ 容器双 healthy 实证 | false | — | payload 无时间戳字段，时间线只能间接收窄（FP-4） |
| R2 | 方案：F1 抽样 scroll（with_payload=True ≥100 点）+ DLQ/env/迁移痕迹对照 → 来源三态定性；F2 行数复核 + alembic head + docker inspect 卷/容器史 → 空表成因三态定性；F3 报告落盘含处置三选一建议 | false | — | 本地库漂移史可能无留痕，判不定照登（FP-5） |
| R3 | 反例：禁顺手清数据/重建索引（FP-7）· 禁手改脚本（FP-6 即 STOP）· 禁凭记忆转述样本（FP-3 附件钉死）· 容器瞬态两段照登不挑有利（FP-2）· 本地口径防外推生产（FP-8） | false | — | 处置建议若缺实证支撑会退化为拍脑袋 —— TC-DA-4 要求每条建议引证据 |
| R4 | 验收：TC-DA-1..6 实证+机断混合（抽样可复现/来源定性/空表定性/报告落盘/不假绿回溯/零越界+lint） | false | — | 无 |
| R5 | 收口：草稿待维护者签三闸（全 pending 未代签）；范围聚焦单一 mismatch 溯源无新锚点 | true | 证据链齐备 + 写入路径全定位 + 头号假设已有逐数线索，再轮无新信息 | 闸未签 |

**actual_last_round**：R5（early_stop）

### R0 · 问题框定

母体 40 亲跑把「本地 Qdrant 8574 点 vs PG 0 行」如实记录并按 FP-7 上抛。本 task 回答三个问题：点从哪来、PG 为什么空、数据态如何定性。只读排查优先，处置方案须实证后另行裁定，处置执行另立。

### R1 · 证据收集

五锚点亲读：立案报告（8574/0/-8574 mismatch · DLQ empty）、只读脚本（scroll :131-144 只取 id）、backend（collection 缺省 ops_knowledge :38-39）、shadow_write（payload 仅 5 键无时间戳 :55-72 · DLQ :149-185）、runbook（§3 判读口径）。**关键线索**：`reports/qdrant_reconcile_20260813T125801Z.yaml` 记 2026-08-13 pg_count=8574 == qdrant_count=8574 · max_l_inf=0.0 —— 8574 逐数相等，头号假设 = 迁移期 bulk_upsert 写入 + PG 其后重建清空（DLQ 亦空自洽）。写入路径全定位：影子写（ingest.py:284 → shadow_write.py:75）、`scripts/qdrant_migrate/bulk_upsert.py`（collection 缺省 ops_knowledge :46）。起草时 `docker ps` 实证双容器 Up 30h (healthy)。

### R2 · 方案生成

40 实证棒流水线：F1 抽样 scroll（with_payload=True ≥100 点覆盖头中尾）→ payload 分布统计 → DLQ 全量/env/迁移痕迹对照 → 来源三态定性；F2 行数复核 + alembic_version head + `docker inspect` Created/卷 → 清空时间窗推断 → 成因三态定性；F3 报告落盘（判据逐条引证据 · 处置三选一建议各有实证支撑）；F4 invoke + 勾选回填。

### R3 · 反例与边界

最大风险是「结论不真」与「排查变处置」：凭记忆转述样本（FP-3 附件钉死）、为出结论硬判（FP-5 无法判定+已排除项合法）、顺手清数据重建索引（FP-7 越界即 FAIL）、发现脚本 bug 顺手修（FP-6 STOP 另立）。时间线判不定是结构性的（payload 无时间戳 · FP-4），靠库/容器/报告历史间接收窄，窄不了就照登。

### R4 · 验收/可测性

六条 TC 全部可实证或机断断言：样本量与覆盖段、附件存在性、三态定性+判据引证据、报告键项齐全且建议引证据、判定-证据可回溯、git status 白名单 + pytest 复证 + task lint。

### R5 · 收口

草稿交维护者签三闸（HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 全 pending 未代签）；闸未签禁 40。

### 自检结论（执行者）

40 实证棒 2026-10-17 亲跑（报告 `reports/local_vector_data_state_audit_20261017T135118Z.md` · 证据 `docs/harness/invokes/by-task/local-vector-data-state-audit/evidence/` e00–e05 · invoke `invoke_20261017_40_audit.md`）：

- **F1 定性：历史正常写入（迁移期 `export_vectors.py`→`bulk_upsert.py`）**。关键指纹：150/150 样本 payload 恰 4 键 {source_type,repo,source_id,chunk_index}（无 tenant_id · 与 export_vectors.py:12 ALLOWED_PAYLOAD 逐键相等；影子写 filter_payload :55-72 恒产 5 键 → 排除）；WAL/段文件 mtime 钉死单次批量写入窗口 **2026-08-18 02:54Z**（现 qdrant_data 卷 CreatedAt 08-16 > 08-13 先例，现为重迁）；8574 与 2026-08-13 先例逐数相等；DLQ depth=0 复核一致。
- **F2 定性：数据被删（表级清空）**，非库重建。pgdata 卷/PG_VERSION mtime=2026-07-16 钉死 initdb 未重建；ops_knowledge_chunks 堆文件 0 字节 mtime=**2026-09-07 02:19:59Z** → 清空窗 (2026-08-13, 2026-09-07]；checkpoint/rag/llm 等表有数排除整库清空；alembic head=20260923_memory_episodes（文件 mtime 09-29，清空后库仍正常升级）。
- **F3 处置建议：清理脚本**（三选一 · 每选项附实证支撑/排除理由 · 执行另立 task）。
- **TC-DA-1~6 全 PASS**：抽样 150 点头中尾覆盖可复现（附件钉死）· 不假绿（tenant_id 缺失偏差照实记 · 清空路径两解不硬判 · 计数 8574/0/-8574 与立案报告一致）· 零越界（git status 仅新增报告+invoke+本档 · `uv run --extra dev pytest tests/test_check_vector_waterline.py -q` 13 passed · `npx spec-wave task lint` PASS · 全程零写动作）。

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-17 | 10-task 落稿（FP-7 上抛开账 · 本地数据态溯源核查 · 只读优先 · 零改码 40 实证棒 · 三闸 pending 未代签 · 零 git 操作） |
| 2026-10-17 | 20-task-audit R1 签收（零阻塞 · nit 2 项 N1 迁移文件 17→16 / N2 expand_synthetic 参数名，均顺手修正）· 维护者 m00914 授权 00 代录三闸 approved → 待派 40 实证棒 |
| 2026-10-17 | 40 实证棒收口：F1=历史正常写入（迁移期 bulk_upsert · 键集指纹+WAL 时间窗 08-18 02:54Z+8574 逐数对照）· F2=数据被删表级清空（窗 (08-13, 09-07] · 卷/initdb 07-16 钉死排除库重建）· F3 建议清理脚本（执行另立）· TC-DA-1~6 全 PASS · 报告 reports/local_vector_data_state_audit_20261017T135118Z.md + 证据 e00–e05 + 40 invoke 落档 |
