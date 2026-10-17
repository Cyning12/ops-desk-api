# Task：prod-vector-waterline-check（生产向量水位/对账核查 · 只读脚本 + runbook + 报告模板）

> **状态**：done（CLOSED 2026-10-17 · PR #263 MERGED squash ea65d3d · mergedAt 2026-10-17T05:50:21Z · CLOSE 档 docs/tasks/close/close_prod_vector_waterline_check_20261017.md）
> **类型**：运维核查资产（只读脚本 + runbook + 核查报告模板 · **不改管线/配置/数据**）  
> **上游**：路线 `../ops-desk-workspace/docs/05-plan/04-agent-completion-roadmap_v1_zh.md` §P1-RAG「生产向量水位与对账 **待人工**」（2026-09 进度注）  
> **分支**：`task/prod-vector-waterline-check`（自 master 新切）  
> **现网默认**：`RAG_VECTOR_BACKEND=qdrant`（compose Qdrant v1.19.0 · 失败降级 pgvector · 影子写/DLQ）

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `prod_vector_waterline_check` |
| **git_branch** | `task/prod-vector-waterline-check` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 脚本单测 CI 确定性（fake/桩 Qdrant 客户端与 PG 会话 · 不连真库）；生产只读执行 = 维护者动作，钉为前置条件/人工闸项 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `none` |
| **graph_delta** | `none` |
| **graph_delta_note** | 核查脚本/runbook/报告模板（scripts/ + docs/guides/ + reports/）；无新模块/无对外契约改动 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 运维真值回写路线 §P1-RAG 进度注属维护者动作；本 task 不改 coding_wiki 正文 |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,20,30,40` |
| **invoke_retention_profile** | `default` |
| **experience_capture** | `recommended` |
| **kpi_aggregator** | `n/a` |
| **orchestration** | 10 落稿 → 20 R1 → 维护者签三闸 → 30（脚本+单测+runbook+模板）→ 40 本地/compose 环境核验 → 维护者持生产只读访问跑核查并回填报告 → CLOSE |
| **freeze_id** | 无 |
| **related_tasks** | [`task_qdrant_migration.md`](../done/task_qdrant_migration.md)（迁移与本地对账先例）· [`task_rag_golden_eval_r4_r5.md`](./task_rag_golden_eval_r4_r5.md)（姊妹 task · 评测轨） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | approved | 20, 30 | 2026-10-17 维护者授权 00 代录（m00238） |
| HG-AUDIT-R1 | approved | 30 | 2026-10-17 维护者授权 00 代录（m00238 · 20 R1 书面审豁免） |
| HG-GRAPH-MODULES | approved | 30 | 2026-10-17 代录：全局真值 approved（01_modules.md:63）· `graph_change_layer=none` |
| HG-PROD-READONLY-ACCESS | pending | 生产执行 | 待维护者签：**需生产只读访问**（PG 只读账号 + Qdrant 只读端点/凭证）为生产核查前置条件；脚本交付本身不依赖本闸 |

---

## 背景与目标

路线 §P1-RAG 基础设施现状（2026-09）：`ops_knowledge_chunks` 表、入库/embed/upsert 管线、默认 `RAG_VECTOR_BACKEND=qdrant`、影子写/DLQ、compose Qdrant v1.19 均已落地；唯「**生产向量水位与对账 待人工**」——Qdrant collection 条数 vs PG 行数是否一致、DLQ 是否积压、最近一次 ingest 水位到哪里，现无实证。

### 现状锚点（只读 · 30 必读 · 10 已扫）

| 主题 | 路径 · 锚点 | 现状 |
|------|-------------|------|
| 后端选择 | `app/ops/rag/backend.py:27` | `RAG_VECTOR_BACKEND` 缺省 `qdrant`，非法值告警回退 qdrant |
| Collection 名 | `app/ops/rag/backend.py:38-39` | `QDRANT_COLLECTION` 缺省 `ops_knowledge` |
| 影子写/DLQ | `app/ops/rag/shadow_write.py` | PG commit 后非阻塞入队；失败进 DLQ 表 `ops_qdrant_dlq (op, point_ids, payload, error, created_at)`；绝不回滚/阻塞 ingest |
| DLQ 表迁移 | `alembic/versions/20260813_qdrant_dlq.py` | op CHECK ∈ {upsert, delete} · created_at 索引 |
| PG 主表 | `app/ops/rag/ingest.py:152-170` · `app/ops/rag/retrieve.py` | `ops_knowledge_chunks` |
| compose 真值 | `docker-compose.yml:20-30, 69-73` | `qdrant/qdrant:v1.19.0` · `RAG_VECTOR_BACKEND` 默认 qdrant · `RAG_QDRANT_SHADOW_WRITE` 默认 true · `QDRANT_URL` |
| 本地对账先例 | `reports/qdrant_reconcile_20260813T125801Z.yaml` | pg_count vs qdrant_count + 抽样向量比对 + topk overlap（**本地**环境产物 · 非生产） |
| runbook 先例 | `docs/guides/RUNBOOK_*.md` | 仓内 runbook 落 `docs/guides/`（无 docs/runbook 目录） |

### 目标

交付**只读**核查脚本 + runbook + 核查报告模板，使维护者持生产只读访问即可一次性回答：① Qdrant `ops_knowledge` collection 条数 vs PG `ops_knowledge_chunks` 行数对账（含差集方向：PG 有 Qdrant 无 / Qdrant 有 PG 无）；② DLQ 深度与最老条目年龄；③ 最近 ingest 水位（PG 侧 max(created_at/updated_at) 口径 30 按表结构实定）。生产执行面由维护者跑。

---

## 范围

- **E1 · 核查脚本**：`scripts/check_vector_waterline.py`（或 30 裁定等价命名）：只读连接 PG + Qdrant → 输出对账结果（PG 行数 / Qdrant points count / 差值与差集抽样 / DLQ 深度与最老年龄 / 最近 ingest 水位）→ YAML 报告落 `reports/vector_waterline_*.yaml`。**只读硬约束**：脚本禁任何 INSERT/UPDATE/DELETE/DDL 与 Qdrant 写 API；连接串只读账号语义在 runbook 写死。
- **E2 · 降级行为**：Qdrant 不可达/凭证缺失 → 脚本**不失败退出冒充**，降级输出 PG 单侧水位 + 报告标注「Qdrant 面无实证」（含原因）；PG 不可达同理降级 Qdrant 单侧 + 标注；两侧均不可达 → 非零退出 + 显式错误。
- **E3 · runbook**：`docs/guides/RUNBOOK_prod_vector_waterline_v1_zh.md`：前置条件（生产只读访问 · env 清单）、执行步骤、报告解读（差集方向含义 / DLQ 积压处置指针，**处置动作另 task**）、降级输出判读。
- **E4 · 报告模板**：`reports/vector_waterline_TEMPLATE.yaml`（执行时间/环境标识/PG 面/Qdrant 面/对账差集/DLQ 面/ingest 水位/降级标注位）。
- **E5 · CI 测试**：`tests/test_check_vector_waterline.py`：桩 Qdrant 客户端 + fake PG 会话 → 双侧面聚合断言 / 差集方向断言 / 降级三态断言（Qdrant 不可达→PG 单侧+标注 · PG 不可达→Qdrant 单侧+标注 · 双不可达→非零显式失败）/ 只读断言（桩上断言零写调用）。

## 非范围

- 改 ingest 管线（`app/ops/rag/ingest.py` / `shadow_write.py` 逻辑零 diff）；改向量库配置或 compose 默认值
- 补历史数据 / 重嵌 / DLQ 重放消费（处置动作另 task，本 task 只出证据）
- 生产执行本身（维护者动作 · HG-PROD-READONLY-ACCESS）；CI 连真库
- 检索质量评测（属 [`task_rag_golden_eval_r4_r5.md`](./task_rag_golden_eval_r4_r5.md) 面）
- 多副本/租约/告警接线（监控另立）

---

## 失败路径

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----------|----------|--------|----------|
| FP-1 HG-AUDIT-R1 pending 即 30 | GATE_VERIFY **拒开工** | 是 | — |
| FP-2 Qdrant 不可达/凭证缺失 | 脚本降级输出 PG 单侧水位 + 报告标注「Qdrant 面无实证」（含错误摘要）；不静默冒充 | 是（修网络/凭证重跑） | 报告标注 |
| FP-3 PG 不可达 | 降级输出 Qdrant 单侧 + 标注「PG 面无实证」 | 是 | 报告标注 |
| FP-4 双侧均不可达 | 非零退出 + 显式错误（不出半份冒充报告） | 是 | stderr + 退出码 |
| FP-5 脚本误含写操作 | E5 只读断言 fail（桩零写调用）；runbook 钉只读账号 | 是 | 测报 |
| FP-6 对账出差集 | 报告如实列差集方向与抽样；**处置另 task**，本 task 不修数据 | — | 报告 |
| FP-7 生产执行无授权访问 | HG-PROD-READONLY-ACCESS pending → 维护者不跑；报告位留空不伪造 | 是 | runbook 前置条件节 |
| FP-8 30 顺手改管线/配置 | 零 diff 契约（`app/ops/rag/**` · `docker-compose.yml`），审查拒收 | 是 | — |

---

## 验收标准

- [ ] **TC-WL-1**：`scripts/check_vector_waterline.py` 落地；`pytest tests/test_check_vector_waterline.py -q` 全绿（聚合/差集方向/降级三态/只读断言，可对命令输出断言）
- [ ] **TC-WL-2**：降级行为实证：桩模拟 Qdrant 不可达 → 报告含 PG 单侧水位 + 「Qdrant 面无实证」标注字段；双不可达 → 非零退出 + stderr 显式错误
- [ ] **TC-WL-3**：runbook `docs/guides/RUNBOOK_prod_vector_waterline_v1_zh.md` 含前置条件（生产只读访问授权 · env 清单）、执行步骤、报告解读、降级判读四节
- [ ] **TC-WL-4**：报告模板含 PG 面（行数/最近 ingest 水位）/Qdrant 面（collection 条数）/对账差集（双向计数+抽样）/DLQ 面（深度/最老年龄）/降级标注位
- [ ] **TC-WL-5**：40 在本地/compose 环境（docker-compose Qdrant v1.19.0）亲跑脚本出真实报告一份落 `reports/vector_waterline_*.yaml`（本地实证 · 非生产）
- [ ] **TC-WL-6**：`app/ops/rag/**` · `alembic/**` · `docker-compose.yml` **零 diff**；`ruff` 触及路径绿；既有 rag 相关测试零新增红
- [ ] **TC-WL-7**：`npx --yes spec-wave task lint --file docs/tasks/active/task_prod_vector_waterline_check.md` 输出含 `LINT: PASS`
- [ ] **TC-WL-8（维护者执行 · 不占 30/40 验收）**：维护者持 HG-PROD-READONLY-ACCESS 授权跑生产核查 → `reports/vector_waterline_prod_*.yaml` 回填 → 路线 §P1-RAG「待人工」消解或上抛差集处置 task

## 依赖

- 路线真值：`../ops-desk-workspace/docs/05-plan/04-agent-completion-roadmap_v1_zh.md` §P1-RAG（「生产向量水位与对账 待人工」）
- 代码锚点（只读）：`app/ops/rag/backend.py` · `app/ops/rag/shadow_write.py` · `app/ops/rag/ingest.py` · `app/ops/rag/retrieve.py` · `alembic/versions/20260813_qdrant_dlq.py` · `docker-compose.yml`
- 本地对账先例（报告形状可仿 · 环境不同勿当生产证据）：`reports/qdrant_reconcile_20260813T125801Z.yaml`
- 脚本/runbook 落位先例：`scripts/rag_ingest.py` · `scripts/rag_smoke.py` · `docs/guides/RUNBOOK_multi_replica_verify_v1.md`
- 编码规范：`docs/standards/CODING_BACKEND_L2_v1_zh.md`
- 姊妹 task（评测轨 · 独立立项）：[`task_rag_golden_eval_r4_r5.md`](./task_rag_golden_eval_r4_r5.md)

## 给执行帽的必读列表

1. 本 task 全文（只读硬约束 · 降级三态 · 非范围三条 · HG-PROD-READONLY-ACCESS 纪律）。
2. 路线 §P1-RAG（`../ops-desk-workspace/docs/05-plan/04-agent-completion-roadmap_v1_zh.md`）。
3. 上列代码锚点原文（禁信转述 · 行号 30 按实校正）。
4. `reports/qdrant_reconcile_20260813T125801Z.yaml`（报告形状先例）。
5. [`task_qdrant_migration.md`](../done/task_qdrant_migration.md)（迁移/对账史）。
6. `docs/standards/CODING_BACKEND_L2_v1_zh.md`。
7. `docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`。

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|---|------|------------|----------------------|----------------|
| R0 | 框定：路线「待人工」缺口=生产水位无实证；交付物=只读脚本+runbook+模板，执行归维护者 | false | — | 生产访问授权节奏 |
| R1 | 证据：backend.py 默认 qdrant · collection=ops_knowledge · DLQ 表 ops_qdrant_dlq · compose v1.19.0 · 本地对账先例在 | false | — | 行号漂移（30 按实校正） |
| R2 | 方案：单脚本三断面（对账/DLQ/ingest 水位）· 降级不冒充 · 报告模板先行 | false | — | Qdrant 客户端版本对齐 |
| R3 | 反例：只读断言防写 · 差集处置另 task · 生产执行不占 CI · 不改管线配置 | false | — | 差集出现时处置需求另立 |
| R4 | 验收：TC-WL-1..8 · 桩测降级三态 · 40 本地 compose 实证 · 生产回填=TC-WL-8 维护者 | false | — | 本地与生产形状差异 |
| R5 | 收口：草稿交 20；四闸 pending 待维护者签；禁 30 | true | 范围/降级/先例已钉死，再轮无新锚点 | 闸未签 |

**actual_last_round**：R5（early_stop）

### R0 · 问题框定

缺口不是「没有管线」，是「生产水位无实证」。本 task 把核查能力资产化（脚本+runbook+模板），生产执行权责归维护者，证据与处置分离。

### R1 · 证据收集

默认后端 qdrant（`backend.py:27`）、collection 缺省 `ops_knowledge`（`backend.py:38-39`）、DLQ 表 `ops_qdrant_dlq`（`shadow_write.py` + `alembic/versions/20260813_qdrant_dlq.py`）、compose Qdrant v1.19.0（`docker-compose.yml`）、本地对账报告先例（`reports/qdrant_reconcile_20260813T125801Z.yaml`）。

### R2 · 方案生成

一个只读脚本覆盖三断面；降级语义按 memory-golden-eval「显式失败不冒充」先例；报告模板先行使生产执行只填数。

### R3 · 反例与边界

最大风险是脚本越权写库——桩断言零写调用 + runbook 钉只读账号双保险；差集只记录不处置；生产访问未授权则报告位留空，禁伪造。

### R4 · 验收/可测性

聚合/差集/降级三态全桩测确定性断言；40 用本地 compose 出真实报告证明脚本真能用；生产回填单列 TC-WL-8 不绑架交付。

### R5 · 收口

草稿交 20 R1；四闸全 pending 待维护者签；闸未签禁 30。

### 自检结论（执行者）

30 执行帽 2026-10-17 回填：

- **TC-WL-1 ✅**：scripts/check_vector_waterline.py 落地；`pytest tests/test_check_vector_waterline.py -q` → 13 passed（聚合/差集方向/降级三态/只读断言 + CLI 子进程双不可达 exit 2）。
- **TC-WL-2 ✅**：桩模拟 Qdrant 不可达 → exit 0 + PG 单侧 + 报告 qdrant_face.status=no_evidence「Qdrant 面无实证」；PG env 缺失同理单侧；双不可达 → exit 2 + stderr 显式错误 + 零报告。
- **TC-WL-3 ✅**：runbook 前置条件（HG-PROD-READONLY-ACCESS + env 清单表）/执行步骤（prod+local）/报告解读/降级判读四节齐备。
- **TC-WL-4 ✅**：reports/vector_waterline_TEMPLATE.yaml 含 PG 面（row_count + ingest_waterline）/Qdrant 面（points_count）/对账双向差集（计数+抽样）/DLQ 面（depth/oldest_age_seconds/verdict）/degradation 标注位。
- **TC-WL-5 ⏳ 40**：本地/compose 亲跑实证，待 40 轨执行（命令见 runbook §2）。
- **TC-WL-6 ✅**：git status 仅 7 个新增路径；app/ops/rag/** · alembic/** · docker-compose.yml 零 diff；ruff 触及路径 All checks passed；全量 pytest 1831 passed / 4 failed 均基线环境性（真库/API key/双进程），零新增红。
- **TC-WL-7**：spec-wave task lint 结果见 30 invoke 验证记录。
- **TC-WL-8 ⏳ 维护者**：HG-PROD-READONLY-ACCESS 保持 pending；生产执行与报告回填属维护者动作，未伪造报告位。
- 关键实定：ingest 水位口径 = max(ops_knowledge_chunks.embedded_at)（表无 created_at/updated_at，alembic/versions/20260808_rag_chunks.py:46 亲读）。

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-17 | 10-task 落稿（生产向量水位/对账核查 · 只读脚本+runbook+模板 · 四闸 pending 待维护者签 · 未 commit） |
| 2026-10-17 | 30 交付：E1 脚本 + E2 降级三态 + E3 runbook + E4 模板 + E5 桩测 13 绿 · ruff 绿 · 禁区零 diff · 自检结论回填（TC-WL-1/2/3/4/6 ✅ · TC-WL-5 待 40 · TC-WL-8 待维护者） |
| 2026-10-17 | CLOSED：PR #263 MERGED squash ea65d3d（2026-10-17T05:50:21Z）· 批量关账 · CLOSE 档 close_prod_vector_waterline_check_20261017.md |
