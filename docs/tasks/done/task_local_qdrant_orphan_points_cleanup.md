# Task：local-qdrant-orphan-points-cleanup（本地 Qdrant ops_knowledge 8574 遗留孤儿点清理处置 · 含写动作）

> **状态**：done（2026-10-18 CLOSE · PR #272 MERGED squash 6ee1f61 · TC-OC-1~6 全 PASS 零假绿 · 8574 孤儿点已清理 · 删后水位 verdict=match（0/0/0）· 快照备份留存本机 backups/ · 归档 done/）
> **类型**：本地运维处置（**含写动作——删除 Qdrant 遗留点**；与上游只读核查 task 不同，安全前置钉死 · 40 实证执行棒 · 建议零落码一次性命令行执行）
> **上游**：[`task_local_vector_data_state_audit.md`](../done/task_local_vector_data_state_audit.md)（PR #270 已并 · 40 实证钉死：本地 Qdrant ops_knowledge 8574 点 = 2026-08-18 迁移期正当重迁写入，payload 恰 4 键指纹与 `scripts/qdrant_migrate/export_vectors.py:12` ALLOWED_PAYLOAD 逐键相等；PG ops_knowledge_chunks 于 (2026-08-13, 2026-09-07] 窗口被表级清空（绕过应用层无影子删除）→ mismatch · F3 处置建议 = **清理脚本**）；维护者 2026-10-17（会话 m00954）选定立本清理 task
> **分支**：无（建议零落码 · 零 git 操作纪律；报告/invoke 产物提交与否由 00/维护者事后裁定）
> **现网默认**：`RAG_VECTOR_BACKEND=qdrant`（compose Qdrant v1.19.0 · 卷 qdrant_data · REST 6333 本机映射）

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `local_qdrant_orphan_points_cleanup` |
| **git_branch** | 无（零落码建议 · 零 git 操作） |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 实证 + 机断混合：本地 compose 真实执行（备份 → dry-run → 分批删除 → 删后核验全链命令+输出留档）+ 既有桩测 `tests/test_check_vector_waterline.py` 复跑零红（零越界旁证）；建议零落码故无新代码、无新测试 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `none` |
| **graph_delta** | `none` |
| **graph_delta_note** | 建议零落码（一次性 curl 命令行执行 · 命令全文留档）；无新模块/无对外契约/无配置改动；若执行中裁定须落 `scripts/` 工具码即 STOP 退回补 30 棒+图谱闸评估（FP-8） |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 本地运维处置留痕属运维证据；是否回写路线/wiki 由维护者阅报后裁定，非本 task |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,40` |
| **invoke_retention_profile** | `default`（实取 10+40 · 零落码建议下无 30 改码棒 · 20 按授权） |
| **experience_capture** | `recommended` |
| **kpi_aggregator** | `n/a` |
| **orchestration** | 10 落稿 → 20 R1（按维护者授权取舍）→ 维护者签闸 → 40 实证执行（F1 备份 → F2 dry-run → F3 删除 → F4 核验）+ 报告落盘 + 验收勾选/自检结论回填 → CLOSE |
| **freeze_id** | 无 |
| **related_tasks** | [`task_local_vector_data_state_audit.md`](../done/task_local_vector_data_state_audit.md)（处置建议母体 · F3 清理脚本）· [`task_vector_waterline_local_rerun.md`](../done/task_vector_waterline_local_rerun.md)（立案母体）· [`task_qdrant_migration.md`](../done/task_qdrant_migration.md)（迁移与对账先例） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | approved | 20, 40 | 维护者 2026-10-18 授权 00 代录（m01000 · 承 m00238 总授权）· 含写动作安全链已审查闭合 |
| HG-AUDIT-R1 | approved | 40 | 维护者 2026-10-18 授权 00 代录（m01000）· R1 审查文 task_local_qdrant_orphan_points_cleanup_audit_R1_20261017.md 签收零阻塞 nit 2 已顺手精化 |
| HG-GRAPH-MODULES | approved | 40 | 维护者 2026-10-18 授权 00 代录（m01000）· 落码裁定=**零落码 curl**（m01000 采纳建议）· graph_change_layer=none 成立；执行中转落码则 FP-8 STOP 回抛 |

> 关联闸照登：HG-PROD-READONLY-ACCESS 仍 pending（仅阻生产侧任何动作）；**本 task 零涉生产**，不受其阻、也不消解之（FP-7）。

---

## 背景与目标

上游 task_local_vector_data_state_audit 40 实证棒（2026-10-17 · 报告 `reports/local_vector_data_state_audit_20261017T135118Z.md` · 立案证据 `reports/vector_waterline_local_20261017T123649Z.yaml`）钉死：本地 Qdrant `ops_knowledge` collection 内 **8574 个点**为 2026-08-18 迁移期 `export_vectors.py` → `bulk_upsert.py` 正当重迁写入；PG `ops_knowledge_chunks` 其后于 (2026-08-13, 2026-09-07] 窗口被表级清空（堆文件归零时刻 2026-09-07 02:19:59Z · 绕过应用层故无影子删除/DLQ 痕迹）→ count_diff=-8574 mismatch。F3 处置建议三选一定为**清理脚本**：重建索引无本地源数据支撑（sync 源表同空）· 保持原样则每次水位核查恒定 mismatch 噪音。维护者 2026-10-17（会话 m00954）选定立本清理 task。

**本 task 是写动作 task**：删除 Qdrant 遗留点属不可逆写，安全前置（备份硬闸 + dry-run 核验 + 白名单钉死 + 回滚预案）必须先于一切删除动作落实。

### 实证锚点（10 已亲读复核 · 40 必读）

| 主题 | 路径 · 锚点 | 现状（2026-10-17 亲核） |
|------|-------------|--------------------------|
| F3 处置建议与证据索引 | `reports/local_vector_data_state_audit_20261017T135118Z.md` | §4 清理脚本建议（每选项附实证支撑/排除理由）· §1 键集指纹锁定迁移工具链 · §6 证据附件索引（e04_scroll_ids_raw.json = 8574 全量 id 原始输出，dry-run 对照基准） |
| 立案计数钉死 | `reports/vector_waterline_local_20261017T123649Z.yaml` | pg=0 · dlq=0 verdict=empty · qdrant points_count=scrolled_ids=8574 · count_diff=-8574 verdict=mismatch · degradation.degraded=false |
| 删除目标 id 集基准 | `docs/harness/invokes/by-task/local-vector-data-state-audit/evidence/e04_scroll_ids_raw.json` | 8574 个唯一 int id · min=1 max=8593 · 1 处宽 20 缺口（19 id 缺失）；dry-run id 集须与其逐集相等（FP-3） |
| 迁移写入工具链（来源定性） | `scripts/qdrant_migrate/export_vectors.py:12` · `bulk_upsert.py:46` | ALLOWED_PAYLOAD 恰 4 键 · collection 缺省 ops_knowledge；**scripts/qdrant_migrate/ 无现成点级（points）delete 工具**（10 亲核目录 9 脚本+README：bench_hnsw/bulk_upsert/check_dlq_schema/create_collection/ensure_payload_indexes/expand_synthetic/export_vectors/reconcile/fio_randread_gate.sh；`create_collection.py:60`/`expand_synthetic.py:59` 的 --recreate 分支含 delete_collection 整集删除，非点级删除 · R1 N1 精化） |
| 删后核验脚本 | `scripts/check_vector_waterline.py` | 只读硬约束（:4-6 禁写 API）· 删后复跑预期 pg=0/qdrant=0/count_diff=0/verdict=match · 报告落 `reports/vector_waterline_local_<UTCts>.yaml`（:274-281） |
| 判读口径 | `docs/guides/RUNBOOK_prod_vector_waterline_v1_zh.md` | §4 mismatch → 另立处置 task（本 task 即其处置执行）· §3 判读表 |
| Qdrant 部署形态 | `docker-compose.yml` qdrant 段（:22-39）· volumes（:82-84） | qdrant/qdrant:v1.19.0 · 卷 `qdrant_data:/qdrant/storage`（快照容器内落 /qdrant/storage/snapshots/）· 6333/6334 本机映射 · mem_limit 8192m |
| Snapshot/Delete API（v1.19.x 文档已 web 核） | Qdrant 官方文档 | 建快照 `POST /collections/{name}/snapshots`（同步返回 snapshot_name · tar 归档含 collection 配置+全部点+payload）· 列出 `GET /collections/{name}/snapshots` · 下载 `GET /collections/{name}/snapshots/{snapshot_name}` · 恢复 `PUT /collections/{name}/snapshots/recover`（body `{"location": "file:///qdrant/storage/snapshots/<name>/<snapshot_name>"}` 或上传端点）· 删点 `POST /collections/{name}/points/delete?wait=true`（body 二选一：`{"points": [<id>...]}` PointIdsList 或 `{"filter": ...}` FilterSelector —— **本 task 只用 points 显式 id 白名单，禁 filter**） |

### 目标

F1 快照/备份前置（无备份禁删硬闸）→ F2 dry-run 先行（只读列出将删 id 集 · 与立案报告/审计证据计数与集合双重一致核验）→ F3 删除执行（显式 id 白名单分批 delete · 命令留痕）→ F4 删后核验（count=0 · 水位脚本复跑 verdict 转 match · 报告落盘）。全链不假绿、可回滚。

---

## 范围

- **F1 · 快照/备份前置（硬闸）**：
  - 前置实证：`docker ps`/`docker inspect` 确认 `ops-desk-api-qdrant-1` Up (healthy)（异常即 FP-2 分支处理，不硬闯）。
  - Qdrant snapshot：`POST http://127.0.0.1:6333/collections/ops_knowledge/snapshots`，取回 snapshot_name；`GET /collections/ops_knowledge/snapshots` 复核列出。
  - 备份产物落 host 钉死路径：`backups/local_qdrant_orphan_cleanup_<UTCts>/ops_knowledge-<snapshot_name>`（`GET .../snapshots/{snapshot_name}` 下载拷出 · **二进制产物不入 git · untracked 留本机**）；sha256 落执行台账。**无备份产物+sha256 核验通过 → 禁止进入 F3（FP-2 硬闸）**。
  - 备份可读性核验（R1 N2 顺手精化）：host 侧只读 `tar -tf <备份产物> | head` 实证归档可解 · size>0 + sha256 记录入台账；不可读即视为备份失败 → FP-2 禁删分支。
- **F2 · dry-run 先行（只读）**：
  - 只读 scroll 全量 id（`with_payload=false, with_vectors=false` · 形态参照 `scripts/check_vector_waterline.py:131-144`，一次性命令行/stdin 执行零落码）；得将删 id 集 S。
  - 双重一致核验：|S| == 8574 且 S 与审计证据 `e04_scroll_ids_raw.json` id 集**逐集相等**；任一不符即 **STOP**（FP-3：数据态已漂移，禁按旧报告删，回抛维护者）。
- **F3 · 删除执行（本 task 唯一写动作）**：
  - `POST /collections/ops_knowledge/points/delete?wait=true`，body `{"points": [<id>...]}`，**仅 F2 核验通过的 8574 id 白名单**，分批（每批 ≤1000，对齐 SCROLL_BATCH=1000 形态），每批响应（status/usage/耗时）逐条落执行台账。
  - **禁** filter-selector 删除、**禁** delete collection、**禁** 任何 truncate 等价物（即使实证「8574 = 全集合」为空集合等价形态，亦不走全集合删除路径；维护者另行书面批准除外）。
- **F4 · 删后核验与报告**：
  - `count(ops_knowledge)` == 0（exact）实证。
  - 复跑 `scripts/check_vector_waterline.py --env local`：预期 pg=0 · qdrant=0 · count_diff=0 · verdict=match · dlq verdict=empty；报告落 `reports/vector_waterline_local_<UTCts>.yaml`。
  - 处置报告落 `reports/local_qdrant_orphan_points_cleanup_<UTCts>.md`：含备份产物路径+sha256 · dry-run 核验结论 · 分批删除台账索引 · 删后核验计数 · 与立案报告计数对照（8574/0/-8574 → 0/0/0）· disclaimer（本地/compose 口径不得外推生产）。
- **F5 · 留档收口**：40 invoke + 执行台账/原始输出证据附件落 `docs/harness/invokes/by-task/local-qdrant-orphan-points-cleanup/`；本档验收勾选 + 自检结论 + 修订记录回填。

## 非范围

- **生产环境任何访问**（HG-PROD-READONLY-ACCESS 仍 pending · 不消解 · FP-7）
- **PG 任何写**（禁 INSERT/UPDATE/DELETE/DDL；PG 侧仅删后核验脚本既有只读 SELECT 复跑）
- **应用功能改码**：`app/**` · `scripts/**` · `alembic/**` · `docker-compose.yml` 零 diff 硬约束；10 建议**零落码**（一次性 curl/stdin 命令行执行 · 理由见下）；若执行中裁定须新落 `scripts/` 工具码即 **STOP**，退回补 30 棒 + HG-GRAPH-MODULES 图谱闸评估后另议（FP-8）
- ops_knowledge 以外任何 collection（scale/scale_mem/scale_sq/scale_100k 等容量实验集合一律不动）· DLQ 处置 · sync/ingest 数据重生产
- 备份产物入 git（二进制 untracked 留本机）· 监控/告警接线 · 新写测试

### 落码与否的 10 建议（维护者裁定参考）

**建议：零落码，一次性 curl 命令行执行。** 理由：(1) 删除目标为**已实证钉死的固定 8574 id 集**，一次性本地运维处置，无复用场景；(2) `scripts/qdrant_migrate/` 现无点级 delete 工具（10 亲核 · R1 N1），新落脚本 = 为单次动作引入永久维护面 + 触发 30 棒 + HG-GRAPH-MODULES 图谱闸评估，成本远超收益；(3) 上游审计 task 已立先例：一次性只读脚本走 stdin 零落码、命令全文落 e00 台账，可复现性由「命令全文+原始输出附件」保障而非脚本文件；(4) 零落码则 graph_change_layer=none 成立、required_invoke_hats=10,40 成立。反方风险照登：curl 多批手工执行有误粘/漏批风险 → 由 F3 分批台账逐批核验 + F4 count=0 兜底对冲。

---

## 失败路径

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----------|----------|--------|----------|
| FP-1 闸 pending 即 40 执行 | GATE_VERIFY **拒开工**（真值在本档人工闸表 · 本 task 含写动作，闸未签禁一切写） | 是 | — |
| FP-2 无备份禁删硬闸 | snapshot 创建失败/下载拷出失败/sha256 核验缺失 → **禁止进入 F3**；如实记失败原因，排除后重试备份；容器不健康先 `docker compose up -d qdrant` 待 healthy | 是 | 执行台账 + stderr |
| FP-3 dry-run 与立案基准不一致 | |S|≠8574 或 id 集与 `e04_scroll_ids_raw.json` 非逐集相等 → **STOP**；判数据态漂移，禁按旧报告删；现状证据落档回抛维护者 | — | 报告 + 40 invoke |
| FP-4 删除中途失败（批次报错/超时/连接断） | 立即停止后续批次；已删/未删 id 集如实记录不伪造；评估二选一：续删剩余白名单批次（需重新 dry-run 核验剩余集）或整体回滚（FP-5 路径）；**禁盲目重试放大** | 部分 | 执行台账 |
| FP-5 删后核验 FAIL（count≠0 或 verdict≠match） | 不假绿；启动回滚预案：`PUT /collections/ops_knowledge/snapshots/recover`（body `{"location": "file:///qdrant/storage/snapshots/ops_knowledge/<snapshot_name>"}` · 快照在 qdrant_data 卷内）自 F1 备份恢复 → 复跑核验脚本确认回到 8574 → 全链留痕回抛维护者 | 是 | 报告 + 台账 |
| FP-6 删除目标越界 | 白名单钉死：仅 F2 核验通过的 8574 id 集；禁 filter 删除/禁 delete collection/禁 truncate 等价物；发现 collection 内出现白名单外 id（dry-run 得 >8574）即按 FP-3 STOP | — | 台账白名单核验段 |
| FP-7 本地口径误外推生产 | 报告/invoke 钉死「本地/compose 开发库口径 · 不得外推生产」；生产侧任何动作仍属 HG-PROD-READONLY-ACCESS（pending）管辖 | — | 报告 disclaimer |
| FP-8 顺手落码冲动 | 执行中若判断须新落 `scripts/` 工具码 → **STOP**；退回维护者裁定补 30 棒 + HG-GRAPH-MODULES 图谱闸评估，本 task 不边做边扩范围 | — | 报告 + 40 invoke |
| FP-9 证据不可复现 | 全链命令全文 + 原始输出附件必落档（对齐上游 e00–e05 先例）；缺附件即 TC 判 FAIL；**禁凭记忆转述** | 是 | 40 invoke 实录 |

---

## 验收标准

- [x] **TC-OC-1（实证 · 备份硬闸）**：F1 完成 —— `docker inspect` 容器态留证；snapshot 创建+列出+下载拷出全链命令与输出落档；备份产物在 `backups/local_qdrant_orphan_cleanup_<UTCts>/` 存在、size>0、sha256 落台账；**无此核验记录则后续 TC 全判 FAIL（FP-2）**
- [x] **TC-OC-2（实证 · dry-run 一致）**：F2 完成 —— 只读 scroll 全量 id 原始输出落档；|S|=8574 且与 `e04_scroll_ids_raw.json` 逐集相等（diff 为空集）的核验命令+输出落档；不一致则全链 STOP 记录（FP-3）
- [x] **TC-OC-3（实证 · 白名单删除）**：F3 完成 —— 删除请求全部为 `points/delete` 显式 id 白名单批次（每批 ≤1000 · 批次并集 == S · 台账逐批响应落档）；**零 filter 删除、零 delete collection、零 truncate**；ops_knowledge 以外 collection 零触碰（删除前后 collections 列表对照落档）
- [x] **TC-OC-4（实证 · 删后核验）**：F4 完成 —— count(ops_knowledge)=0 实证落档；`scripts/check_vector_waterline.py --env local` 复跑报告 `reports/vector_waterline_local_<UTCts>.yaml` 含 pg=0 · qdrant=0 · count_diff=0 · verdict=match · dlq verdict=empty · degraded=false；处置报告 `reports/local_qdrant_orphan_points_cleanup_<UTCts>.md` 落盘（备份路径+sha256 · dry-run 结论 · 删除台账索引 · 计数对照 8574/0/-8574 → 0/0/0 · disclaimer 钉死）
- [x] **TC-OC-5（机断 · 不假绿+可回滚）**：报告内每个计数/判定均可回溯到落档证据（命令+输出）；回滚预案命令（snapshot recover）在报告内预写且 F1 备份产物可支撑；任一环节 FAIL 如实记不冒充（FP-4/FP-5）；本地口径 disclaimer 双落（报告+invoke · FP-7）
- [x] **TC-OC-6（机断 · 零越界）**：`scripts/` · `app/**` · `alembic/**` · `docker-compose.yml` **零 diff**（git status 仅新增 untracked：处置报告 + 水位报告 + 备份目录 + invokes + 本档回填）；`uv run pytest tests/test_check_vector_waterline.py -q` 13 passed 复证；`npx --yes spec-wave task lint --file docs/tasks/active/task_local_qdrant_orphan_points_cleanup.md` LINT: PASS

## 依赖

- 处置建议母体与证据：[`task_local_vector_data_state_audit.md`](../done/task_local_vector_data_state_audit.md) · `reports/local_vector_data_state_audit_20261017T135118Z.md`（§4 建议 · §6 证据索引）· 立案计数 `reports/vector_waterline_local_20261017T123649Z.yaml` · dry-run 基准 `docs/harness/invokes/by-task/local-vector-data-state-audit/evidence/e04_scroll_ids_raw.json`
- 资产（只读复用 · 零 diff）：`scripts/check_vector_waterline.py`（删后核验 · 只读硬约束 :4-6 · scroll 形态 :131-144）· `docs/guides/RUNBOOK_prod_vector_waterline_v1_zh.md`（§4 mismatch 处置分流）· `tests/test_check_vector_waterline.py`
- 来源定性锚点（背景真值 · 零 diff）：`scripts/qdrant_migrate/export_vectors.py`（:12 ALLOWED_PAYLOAD）· `scripts/qdrant_migrate/bulk_upsert.py`（:46 collection 缺省）
- 部署形态：`docker-compose.yml`（qdrant 段 :22-39 · qdrant_data 卷 :82-84）
- 外部 API 真值：Qdrant v1.19.x 官方文档（snapshots / points delete —— 10 已 web 核，执行时以实例实测为准）
- 编码规范：`docs/standards/CODING_BACKEND_L2_v1_zh.md`

## 给执行帽的必读列表

1. 本 task 全文（**含写动作 · 安全前置四条：备份硬闸/dry-run 一致/白名单钉死/回滚预案** · 非范围五条 · 不假绿纪律 · 闸表）。
2. `reports/local_vector_data_state_audit_20261017T135118Z.md` 全文（§4 处置建议实证支撑 · §6 证据附件索引）。
3. `reports/vector_waterline_local_20261017T123649Z.yaml` 全文（立案计数 8574/0/-8574 钉死）。
4. `docs/harness/invokes/by-task/local-vector-data-state-audit/evidence/e00_commands.md` + `e04_scroll_ids_raw.json`（一次性只读脚本执行先例 · dry-run id 集对照基准 —— 禁信转述）。
5. `scripts/check_vector_waterline.py` :125-151（scroll 只读形态参照 · 禁改本脚本）。
6. `docs/guides/RUNBOOK_prod_vector_waterline_v1_zh.md` §3/§4（判读口径与处置分流）。
7. Qdrant v1.19.x snapshots / points delete 官方文档（命令构造前复核 · 以实例实测为准）。
8. `docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`（GATE_VERIFY 形状 · 本 task 阻塞面 = 40）。

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|---|------|------------|----------------------|----------------|
| R0 | 框定：上游 F3 建议落地 = 本地 Qdrant 8574 遗留孤儿点清理；**含写动作** · 本地口径 · 零涉生产 · 建议零落码 | false | — | 闸未签 |
| R1 | 证据：必读锚点全亲读（F3 报告/立案 yaml/审计证据 e04/迁移脚本/水位脚本/runbook/compose）+ scripts/qdrant_migrate/ 无 delete 工具亲核 + Qdrant snapshot/delete API v1.19.x 文档 web 核 | false | — | API 细节以实例实测为准（文档与 v1.19.0 实行为准绳差异风险低） |
| R2 | 方案：F1 快照+host 备份（sha256 台账 · 无备份禁删硬闸）→ F2 dry-run（scroll 全量 id · 8574 计数+e04 逐集双重一致）→ F3 显式 id 白名单分批 delete（≤1000/批 · wait=true · 台账）→ F4 count=0+水位脚本复跑 verdict=match+报告落盘 | false | — | 删除中途失败需不重试放大（FP-4 两段处置钉死） |
| R3 | 反例：无备份禁删（FP-2）· dry-run 漂移即 STOP（FP-3）· 禁 filter/truncate 全集合删除（FP-6 白名单钉死）· 删后 FAIL 走快照恢复不硬撑（FP-5）· 顺手落码即 STOP（FP-8）· 本地口径防外推生产（FP-7） | false | — | curl 多批手工执行误粘/漏批风险 → 分批台账+F4 count=0 兜底 |
| R4 | 验收：TC-OC-1..6 实证+机断混合（备份可核验/dry-run 一致/白名单删除/删后核验/不假绿+可回滚/零越界+pytest+lint） | false | — | 无 |
| R5 | 收口：草稿待维护者签三闸（全 pending 未代签）；落码与否给出建议（零落码 · 四条理由+反方风险照登）待维护者裁定 | true | 上游证据链齐备 + 删除目标已实证钉死为固定 id 集 + API 已文档核，再轮无新信息 | 闸未签 · 落码裁定待维护者确认 |

**actual_last_round**：R5（early_stop）

### R0 · 问题框定

上游审计 task（PR #270 已并）把「本地 Qdrant 8574 孤儿点」来源与成因钉死并建议清理脚本处置。本 task 回答一个问题：**如何安全地删掉这 8574 个点并实证删净**。与上游的本质差异：本 task 含不可逆写动作，安全前置必须先于删除落实。

### R1 · 证据收集

必读锚点全亲读：F3 报告（§4 清理脚本建议 · §6 证据索引含 e04 全量 id 基准）、立案 yaml（8574/0/-8574 钉死）、export_vectors.py:12（4 键指纹）、bulk_upsert.py:46（collection 缺省）、check_vector_waterline.py（只读硬约束 :4-6 · scroll :131-144 · 报告落盘 :274-281）、runbook §4（mismatch 处置分流）、docker-compose.yml qdrant 段（v1.19.0 · qdrant_data 卷 :82-84）。**关键确认**：`scripts/qdrant_migrate/` 目录 10 亲核无 delete 工具（9 个现存脚本+README 全列）。Qdrant snapshot/delete API v1.19.x 官方文档已 web 核：`POST /collections/{name}/snapshots` 同步建快照 · `POST /collections/{name}/points/delete?wait=true` 支持 PointIdsList/FilterSelector 二选一。

### R2 · 方案生成

40 实证执行流水线：F1 备份硬闸（snapshot API + 下载拷出 host 钉死路径 + sha256 台账 · 无备份禁删）→ F2 dry-run（只读 scroll 全量 id · 与立案计数 8574 及审计证据 e04 id 集双重一致核验 · 不一致 STOP）→ F3 白名单删除（points/delete 显式 id 批次 ≤1000 · wait=true · 逐批台账 · 禁 filter/truncate）→ F4 删后核验（count=0 · check_vector_waterline.py 复跑 verdict=match · 处置报告落盘）→ F5 留档收口。回滚预案（snapshot recover）预写进报告。

### R3 · 反例与边界

最大风险是「误删」与「删了装没删」：无备份开删（FP-2 硬闸）、按旧报告删已漂移的数据（FP-3 双重一致核验）、白名单外溢（FP-6 禁 filter/truncate）、删后核验 FAIL 硬撑绿（FP-5 快照恢复）、顺手把一次性动作落成永久脚本扩大范围（FP-8 STOP）。零落码建议的反方风险（curl 手工多批误粘/漏批）照登，由分批台账 + F4 count=0 兜底。

### R4 · 验收/可测性

六条 TC 全部可实证或机断断言：备份产物存在性+sha256、dry-run 逐集相等 diff 为空、删除请求全为显式 id 批次且并集==S、count=0 与水位报告 verdict=match、判定-证据可回溯+回滚预案预写、git status 白名单+pytest 复证+task lint。

### R5 · 收口

草稿交维护者签三闸（HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 全 pending 未代签）；落码与否建议（零落码 · 理由四条+反方照登）一并交维护者裁定；闸未签禁 40。

### 自检结论（执行者）

**40 实证执行回填（2026-10-18 · 全链 PASS · 本地/compose 口径不得外推生产）**：

- **备份产物**：`backups/local_qdrant_orphan_cleanup_20261018T005320Z/ops_knowledge-7885642805251913-2026-10-18-00-53-20.snapshot`（82,857,984 B · sha256 `270b02bd419d1e4a1a94664bc576844467639b65f3bc4838934d567838692e7f` · 双端一致 · tar 可读 · untracked 留本机不入 git）。
- **dry-run 结论**：|S|=8574 且与上游 e04 基准逐集相等（双向 diff 空集 · e06/e07）→ PASS。
- **分批删除台账**：9 批显式 id（8×1000+574 · operation_id 41–49 · 全 ok · 并集==S · 零 filter/truncate/delete collection · 他 collection 零触碰）→ e08/e09/e10。
- **删后核验计数**：points_count=0（e11）· 水位复跑 `reports/vector_waterline_local_20261018T005534Z.yaml` pg=0/qdrant=0/count_diff=0/verdict=match/dlq empty/degraded=false · 计数对照 8574/0/-8574 → 0/0/0。
- **TC-OC-1..6 勾选结果**：全 PASS（明细见处置报告与 40 invoke）；偏差如实记 1 项：首跑水位未注入 DATABASE_URL degraded 未冒充，注入后复跑全绿，降级报告留档。
- **回滚预案**：未触发；PUT snapshots/recover 命令已预写于处置报告 §5。

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-17 | 10-task 落稿（上游 F3 建议落地 · 本地 Qdrant 8574 孤儿点清理 · **含写动作安全前置钉死**：备份硬闸/dry-run 一致/白名单删除/回滚预案 · 建议零落码一次性 curl 执行 · 三闸 pending 未代签 · 零 git 操作 · 仅新增 untracked 文件） |
| 2026-10-18 | 20-task-audit R1 签收（零阻塞 · nit 2 顺手精化：N1 点级删除工具口径+9 脚本枚举 / N2 备份追加 tar -tf 可读性核验）· 维护者 m01000 授权 00 代录三闸 approved · 落码裁定=零落码 curl → 待派 40 处置棒 |
| 2026-10-18 | 40 实证执行完成：F1 备份硬闸（快照+host 备份 sha256 双端一致+tar 可读）→ F2 dry-run（8574 逐集相等）→ F3 白名单 9 批删除（全 ok）→ F4 删后核验（count=0 · 水位 verdict=match）→ F5 留档（处置报告+40 invoke+证据 e00–e11）；TC-OC-1~6 全 PASS；备份二进制 untracked 留本机；待维护者阅报 CLOSE 裁定 |
| 2026-10-18 | 50 CLOSE（维护者 m01029 授权合并+关账）：PR #272 squash 6ee1f61 已并 · 归档 done/ · 状态行 CLOSED · README 登记 · invoke_20261018_50_close.md 落盘 · 照登：00 清理 worktree 时误删 host 备份副本（服务端快照仍在卷内），已从快照 API 重下载恢复 sha256 逐字符一致 |
