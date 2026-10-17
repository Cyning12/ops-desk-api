# Task：vector-waterline-local-rerun（TC-WL-5 开账 · 本地/compose 亲跑向量水位核查出真实报告）

> **状态**：draft（10-task 落稿 2026-10-17 · 人工闸全 pending 未代签）
> **类型**：运维实证核查（**零改码 · 40 轨单棒** · 复用既有只读脚本与模板）
> **上游**：[`task_prod_vector_waterline_check.md`](../done/task_prod_vector_waterline_check.md) TC-WL-5（40 轨本地/compose 亲跑）关账时未走，移交维护者开账 —— CLOSE 档 [`close_prod_vector_waterline_check_20261017.md`](../close/close_prod_vector_waterline_check_20261017.md) §四.1 + §七 checklist「（可选）补 TC-WL-5 本地实证」；维护者 2026-10-17 选定先推此件（会话「先 WL-5」指示）
> **分支**：无（零改码 · 零 git 操作纪律；报告产物提交与否由 00/维护者事后裁定）
> **现网默认**：`RAG_VECTOR_BACKEND=qdrant`（compose Qdrant v1.19.0 · 失败降级 pgvector · 影子写/DLQ）

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `vector_waterline_local_rerun` |
| **git_branch** | 无（零改码 · 零 git 操作） |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 机断 + 实证混合：既有桩测 `tests/test_check_vector_waterline.py` 复跑零红（CI 确定性 · 不连真库）+ 本地 compose 真实亲跑出报告（40 实证）；无新代码、无新测试 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `none` |
| **graph_delta** | `none` |
| **graph_delta_note** | 仅运行既有核查脚本产出 reports/ 证据档；无新模块/无对外契约/无配置改动 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 本地实证报告属运维证据留痕；路线 §P1-RAG 进度注回写是 TC-WL-8（生产执行）消解后的维护者动作，非本 task |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,40` |
| **invoke_retention_profile** | `default`（实取 10+40 · 本 task 无 30 改码棒 · 20 按授权） |
| **experience_capture** | `recommended` |
| **kpi_aggregator** | `n/a` |
| **orchestration** | 10 落稿 → 20 R1（按维护者授权取舍）→ 维护者签闸 → 40 亲跑实证 + 报告落盘 + 验收勾选/自检结论回填 → CLOSE |
| **freeze_id** | 无 |
| **related_tasks** | [`task_prod_vector_waterline_check.md`](../done/task_prod_vector_waterline_check.md)（母体 · TC-WL-5 定义 :108 · 30 交付口径 :190）· [`task_qdrant_migration.md`](../done/task_qdrant_migration.md)（迁移与本地对账先例） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | approved | 20, 40 | 2026-10-17 维护者授权 00 代录（会话 m00823「授权 00 代录」· 承 m00238 总授权）· 20 R1 书面审已做（PASS · docs/harness/reviews/task_vector_waterline_local_rerun_audit_R1_20261017.md） |
| HG-AUDIT-R1 | approved | 40 | 2026-10-17 维护者授权 00 代录（m00823）· 审查文同上 PASS 零阻塞 |
| HG-GRAPH-MODULES | approved | 40 | 2026-10-17 维护者授权 00 代录（m00823）· 全局真值 approved（`docs/_tech_graph/l1/01_modules.md:63`）· `graph_change_layer=none` 本 task 零图谱改动 |

> 关联闸照登：母体 task 的 HG-PROD-READONLY-ACCESS 仍 pending（仅阻生产执行 TC-WL-8）；**本 task 零涉生产**，不受其阻、也不消解之。

---

## 背景与目标

母体 task prod-vector-waterline-check 已 CLOSE（PR #263 MERGED squash ea65d3d · 2026-10-17T05:50:21Z），脚本/桩测/runbook/模板四资产齐备且 13 桩测全绿；唯 **TC-WL-5「40 轨本地/compose 亲跑出真实报告」关账时未走**（CLOSE 档 §四.1 照登：无实证；残余风险 = 真实 compose 组网/驱动兼容未验）。本 task 把该移交项开账独立执行：在本地 compose 环境亲跑既有只读脚本，产出一份**真实**本地报告并对模板逐键核验。

### 实证锚点（10 已亲读复核 · 40 必读）

| 主题 | 路径 · 锚点 | 现状（2026-10-17 亲核） |
|------|-------------|--------------------------|
| 核查脚本 | `scripts/check_vector_waterline.py`（366 行） | 在库 · 只读硬约束（PG 全 SELECT :55-59 · Qdrant 仅 count/scroll :131-144）· 降级三态 :307-332 · 报告落 `reports/vector_waterline_<env>_<UTCts>.yaml` :274-281 · 双侧不可达 exit 2 零报告 :325-332 |
| 本地执行命令 | `docs/guides/RUNBOOK_prod_vector_waterline_v1_zh.md` §2 local 形态 :39-43 | `docker compose up -d db qdrant` 后 `DATABASE_URL='postgresql+psycopg://ops:ops_password@127.0.0.1:5432/opsdesk' QDRANT_URL='http://127.0.0.1:6333' uv run python scripts/check_vector_waterline.py --env local` |
| env 清单 | 同上 runbook §1 表 :22-27 | WATERLINE_DATABASE_URL 或 DATABASE_URL（缺则 PG 面降级）· QDRANT_URL 缺省 127.0.0.1:6333 · QDRANT_COLLECTION 缺省 ops_knowledge |
| 报告模板 | `reports/vector_waterline_TEMPLATE.yaml`（61 行 · template_version=v1） | 键集：kind/template_version/recorded_at/environment/executed_by/git_sha/config/status/pg_face/qdrant_face/reconcile/degradation/disclaimer |
| compose 真值 | `docker-compose.yml` qdrant 服务 :22-39 · db 服务 :4-18 | qdrant/qdrant:v1.19.0 · 端口 6333/6334 · healthcheck；db pgvector/pgvector:pg15 · 5432 |
| 容器现状（10 起草时实证） | `docker ps` | `ops-desk-api-qdrant-1` Up 29h **(healthy)** 0.0.0.0:6333-6334 映射 · `ops-desk-api-db-1` Up 29h **(healthy)** 0.0.0.0:5432 映射 —— 两服已在跑，40 可直接复用或按 runbook 重建 |
| 桩测 | `tests/test_check_vector_waterline.py`（356 行 · 13 测） | 在库 · 聚合/差集方向/降级三态/只读断言 + CLI 子进程双不可达 exit 2 |
| 母体关账口径 | `docs/tasks/close/close_prod_vector_waterline_check_20261017.md` §四.1 · §七 checklist | TC-WL-5 照登未走 · 补走命令指 runbook §2 · 产物本地标识非生产证据 |

### 目标

F1：本地 compose 环境亲跑 `scripts/check_vector_waterline.py --env local`（命令逐字取自 runbook §2 local 形态）→ exit 0。F2：真实报告落 `reports/vector_waterline_local_<UTCts>.yaml`（非 TEMPLATE · 非生产），字段对模板逐键核验。F3：40 invoke 留档 + 验收勾选 + 修订记录回填（40 轨单棒）。

---

## 范围

- **F1 · 本地 compose 亲跑**：确认/起服 `docker compose up -d db qdrant`（容器现 healthy 可复用），按 runbook §2 local 形态亲跑 `scripts/check_vector_waterline.py --env local`，实录出口码与 stdout/stderr。
- **F2 · 真实报告核验**：产物 `reports/vector_waterline_local_<UTCts>.yaml` 为脚本实跑生成（非 TEMPLATE 拷贝 · 非生产证据）；按 `reports/vector_waterline_TEMPLATE.yaml` 键集逐键对拍（含 environment=local · disclaimer 原文 · degradation 位照实）。
- **F3 · 留档收口**：40 invoke 落 `docs/harness/invokes/by-task/vector-waterline-local-rerun/`；本档验收勾选 + 自检结论 + 修订记录回填。
- **F4 · 质量三门复跑**：`ruff check` 触及路径绿 · `uv run pytest tests/test_check_vector_waterline.py -q` 13 绿复证 · `npx --yes spec-wave verify --target .` PASS。

## 非范围

- **生产 Qdrant/PG 访问与生产执行**（HG-PROD-READONLY-ACCESS 仍 pending · TC-WL-8 属维护者动作 · 本 task 零涉生产）
- **脚本功能改动**：`scripts/check_vector_waterline.py` 与 `tests/test_check_vector_waterline.py` 零 diff 硬约束；**若实证发现脚本须改码即 STOP，另立 task**
- **collection 数据修补 / 差集处置 / DLQ 重放**：对账出 mismatch 或 DLQ 积压只如实记录并上抛另立处置 task（承 FP-6 母体纪律）
- 改 ingest 管线 / compose 默认值 / 任何配置；新写测试；监控/告警接线

---

## 失败路径

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----------|----------|--------|----------|
| FP-1 闸 pending 即 40 实证 | GATE_VERIFY **拒开工**（真值在本档人工闸表） | 是 | — |
| FP-2 Qdrant 容器不可达/未起 | 脚本降级三态照登：exit 0 + `qdrant_face.status=no_evidence` + notes 含「Qdrant 面无实证：<原因>」；**不假绿**；先 `docker compose up -d qdrant` 待 healthy 再重跑出双侧实证 | 是 | 报告标注 + stderr |
| FP-3 PG 不可达/env 未配置 | 同理降级 Qdrant 单侧 + 「PG 面无实证」照登；不假绿 | 是 | 报告标注 |
| FP-4 双侧均不可达 | exit 2 + stderr 显式错误 + **零报告**；STOP 修连通性后重跑，不出半份冒充 | 是 | stderr + 退出码 |
| FP-5 报告字段缺失/不符模板 | 逐键对拍 FAIL → 回查脚本版本/模板版本；**禁手改报告冒充**；若实证须改脚本 → STOP 另立 task（非范围） | 是 | 40 invoke 实录 |
| FP-6 数据为空 collection/空表 | 如实记 0 水位（row_count=0 / points_count=0 / ingest_waterline.max=null）不伪造；对账 verdict 照实（match/mismatch 皆合法） | — | 报告 |
| FP-7 对账 mismatch / DLQ 积压 | 报告如实列差集方向与 DLQ 深度；**本 task 不处置**，上抛另立处置 task | — | 报告 + 40 invoke |
| FP-8 本地报告误当生产证据 | disclaimer 写死「本地/compose 环境产物不得当作生产证据」+ environment=local 钉死；生产回填仍待 TC-WL-8 | — | 报告 disclaimer |

---

## 验收标准

- [x] **TC-LR-1（机断）**：`docker ps` 实证 `ops-desk-api-db-1` 与 `ops-desk-api-qdrant-1` 均 Up **(healthy)**（或 `docker compose up -d db qdrant` 重建后 healthy）；Qdrant 镜像 = qdrant/qdrant:v1.19.0
- [x] **TC-LR-2（实证）**：按 runbook §2 local 形态亲跑 `QDRANT_URL='http://127.0.0.1:6333' uv run python scripts/check_vector_waterline.py --env local`（含 DATABASE_URL 注入）→ **exit 0**；命令与 runbook 逐字一致（可复现性核验）
- [x] **TC-LR-3（实证+机断）**：真实报告 `reports/vector_waterline_local_<UTCts>.yaml` 落盘（非 TEMPLATE）；按 `reports/vector_waterline_TEMPLATE.yaml` 键集逐键对拍全中：kind=vector_waterline · template_version=v1 · environment=local · executed_by/git_sha 实值 · config 三键（database_url_set 布尔 · qdrant_url 剥离凭证 · qdrant_collection=ops_knowledge）· status 属 {ok,degraded} · pg_face（row_count/ingest_waterline/dlq 四键+verdict）· qdrant_face（points_count/scrolled_ids）· reconcile（status 与双向差集计数+抽样）· degradation 位照实 · disclaimer 含「本地/compose 环境产物不得当作生产证据」
- [x] **TC-LR-4（机断）**：报告真实性核验 —— 任一面 `no_evidence` 时 status=degraded 且 degradation.notes 非空（不假绿）；空表/空 collection 则计数如实为 0 不伪造（FP-6）；对账 verdict 与差集计数自洽（count_diff = pg_count - qdrant_count）
- [x] **TC-LR-5（机断 · 三门）**：`uv run ruff check scripts/check_vector_waterline.py tests/test_check_vector_waterline.py` 绿 · `uv run pytest tests/test_check_vector_waterline.py -q` 13 passed 复证 · `npx --yes spec-wave verify --target .` EXIT=0 · `npx --yes spec-wave task lint --file docs/tasks/active/task_vector_waterline_local_rerun.md` LINT: PASS
- [x] **TC-LR-6（机断 · 零越界）**：`scripts/check_vector_waterline.py` · `tests/` · `app/**` · `alembic/**` · `docker-compose.yml` **零 diff**（git status 仅新增 reports/ 报告 + invokes + 本档改动）；40 invoke 落盘 + 本档勾选/自检结论/修订记录回填

## 依赖

- 母体 task 与关账档：[`task_prod_vector_waterline_check.md`](../done/task_prod_vector_waterline_check.md)（TC-WL-5 定义 :108 · 30 交付口径 :190）· [`close_prod_vector_waterline_check_20261017.md`](../close/close_prod_vector_waterline_check_20261017.md)（§四.1 缺口照登 · §七 checklist 移交口径）
- 资产（只读 · 零 diff）：`scripts/check_vector_waterline.py` · `tests/test_check_vector_waterline.py` · `docs/guides/RUNBOOK_prod_vector_waterline_v1_zh.md`（§1 env 表 · §2 执行步骤 · §4 降级判读）· `reports/vector_waterline_TEMPLATE.yaml` · `docker-compose.yml`
- 本地对账先例（报告形状参照 · 环境不同勿当生产证据）：`reports/qdrant_reconcile_20260813T125801Z.yaml`
- 编码规范：`docs/standards/CODING_BACKEND_L2_v1_zh.md`

## 给执行帽的必读列表

1. 本 task 全文（非范围三条 · 降级照登纪律 · 闸表）。
2. `docs/guides/RUNBOOK_prod_vector_waterline_v1_zh.md` §1–§4 全文（命令逐字取自 §2 local 形态）。
3. `scripts/check_vector_waterline.py` 全文（禁信转述 · 行号 40 按实校正）。
4. `reports/vector_waterline_TEMPLATE.yaml`（逐键对拍基准）。
5. 母体 CLOSE 档 §四/§七（缺口口径与 checklist）。
6. `docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`（GATE_VERIFY 形状 · 本 task 阻塞面 = 40）。

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|---|------|------------|----------------------|----------------|
| R0 | 框定：母体 TC-WL-5 开账 = 本地/compose 亲跑出真实报告；零改码 · 40 单棒 · 零涉生产 | false | — | 闸未签 |
| R1 | 证据：脚本/runbook/模板/桩测/compose 五资产在库亲读 · 容器 db+qdrant 已 healthy 实证 · 命令逐字在 runbook §2 :39-43 | false | — | 容器数据态漂移（照实记录即可） |
| R2 | 方案：runbook 命令亲跑 exit 0 → 报告落盘 → 模板逐键对拍 → 三门复跑 → 勾选回填；降级三态照登不假绿 | false | — | 本地库可能为空（FP-6 如实记 0） |
| R3 | 反例：禁手改报告冒充 · 禁顺手改脚本（须改码即 STOP 另立）· mismatch/DLQ 积压只记录上抛 · 本地报告防误当生产证据 | false | — | 差集出现时处置需求另立 task |
| R4 | 验收：TC-LR-1..6 机断+实证混合（起服/亲跑 exit 0/逐键对拍/真实性/三门/零越界+留档） | false | — | 无 |
| R5 | 收口：草稿待维护者签三闸（全 pending 未代签）；范围极小无新锚点 | true | 资产齐备 + 命令既定 + 容器实证在跑，再轮无新信息 | 闸未签 |

**actual_last_round**：R5（early_stop）

### R0 · 问题框定

母体关账时 TC-WL-5 照登未走，残余风险 = 真实 compose 组网/驱动兼容未验。本 task 不做任何交付物新增，只把「脚本真能在本地 compose 跑通并出真实报告」这一实证缺口补上。

### R1 · 证据收集

五资产在库亲读：脚本 366 行（只读硬约束 :55-59 · 降级三态 :307-332）、runbook §1 env 表 + §2 local 命令 :39-43、模板 61 行键集、桩测 13 绿先例、compose qdrant v1.19.0 :22-39。起草时 `docker ps` 实证 `ops-desk-api-qdrant-1` 与 `ops-desk-api-db-1` 均 Up (healthy)，端口 6333/5432 已映射 —— 亲跑前置条件已现实满足。

### R2 · 方案生成

40 单棒流水线：起服核验 → runbook 命令逐字亲跑（exit 0）→ 报告落盘 → 模板逐键对拍 + 真实性核验（degraded/零水位照实）→ 三门复跑（ruff/pytest/spec-wave）→ 勾选 + invoke + 修订记录回填。

### R3 · 反例与边界

最大风险是「实证不真」：手改报告、降级冒充绿、空数据伪造水位——以逐键对拍（TC-LR-3）+ 真实性核验（TC-LR-4）+ 零 diff（TC-LR-6）三锁钉死。脚本若现 bug 须改码，本 task STOP 另立，不在实证棒顺手修。

### R4 · 验收/可测性

六条 TC 全部可机断或实证断言：exit 码、文件存在性、键集对拍、数值自洽（count_diff = pg_count - qdrant_count）、命令输出（ruff/pytest/spec-wave）、git status 白名单。

### R5 · 收口

草稿交维护者签三闸（HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 全 pending 未代签）；闸未签禁 40。

### 自检结论（执行者）

40 实证 2026-10-17 完成（invoke：docs/harness/invokes/by-task/vector-waterline-local-rerun/invoke_20261017_40_live_rerun.md）：

- **TC-LR-1 PASS**：`docker ps` 实证 db+qdrant 均 Up (healthy) · Qdrant 镜像 qdrant/qdrant:v1.19.0 · 复用未重建。
- **TC-LR-2 PASS**：runbook §2 local 命令逐字亲跑 exit 0。首跑因执行机 shell 代理变量污染（NO_PROXY 含 `[::1]` 触发 httpx `InvalidURL: Invalid port: ':1]'`）Qdrant 面降级 → degraded 报告 123538Z 如实落盘不假绿；探针实证 Qdrant 服务健康（curl HTTP 200）· 非脚本 bug 零改码；剥代理变量后重跑（命令本体逐字不变）exit 0 双侧实证齐全。
- **TC-LR-3 PASS**：真实报告 `reports/vector_waterline_local_20261017T123649Z.yaml` 对模板逐键对拍全中（kind=v1 · environment=local · executed_by=cyning · git_sha=d3fd056 · config 三键 · disclaimer 钉死防误当生产证据）。
- **TC-LR-4 PASS**：降级三态真实生效（123538Z no_evidence→degraded+notes 非空）· 空表如实记 0（row_count=0 · waterline=null · DLQ empty）· 数值自洽（count_diff=0-8574=-8574 · points_count=scrolled_ids=8574）。
- **TC-LR-5 PASS**：ruff EXIT=0 · pytest 13 passed · spec-wave verify EXIT=0 · task lint LINT: PASS。
- **TC-LR-6 PASS**：scripts/tests/app/alembic/docker-compose.yml 零 diff；git status 仅新增报告+invoke+本档+20 审查文。
- **上抛（FP-7 · 本 task 不处置）**：本地 Qdrant 8574 points vs PG 0 行 → verdict=mismatch（Qdrant 独有 8574）· 疑墓碑/脏点或本地 DB 重建清空 · 建议维护者另立处置 task 核查本地数据态。零涉生产。

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-17 | 10-task 落稿（TC-WL-5 开账 · 本地/compose 亲跑实证 · 零改码 40 单棒 · 三闸 pending 未代签 · 零 git 操作） |
| 2026-10-17 | 40 实证完成（TC-LR-1~6 全 PASS · 真实报告 vector_waterline_local_20261017T123649Z.yaml + 降级照登报告 123538Z · mismatch 差集 8574 上抛另立处置 task · 维护者/00 裁定报告产物入 commit 走 PR） |
