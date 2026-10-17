# CLOSE：prod-vector-waterline-check（生产向量水位/对账核查 · 只读脚本 + runbook + 报告模板 + 13 桩测）（2026-10-17）

> **task**：[../done/task_prod_vector_waterline_check.md](../done/task_prod_vector_waterline_check.md)（已归档 done/）
> **类型**：运维核查资产（只读脚本 + runbook + 核查报告模板 · **不改管线/配置/数据** · `graph_change_layer=none`）
> **关账日期**：2026-10-17 · 帽位：CLOSE（50 · 三 task 批量关账 · 分支 `close/active-batch-20261017-pm` · 授权链：维护者 2026-10-17 m00238「授权00签收后续文档，开始下面的任务」· 00 代录 · 20 R1 书面审经授权豁免）
> **开账残留（不关门的两项 · 详见 §四/§七）**：TC-WL-5 本地/compose 亲跑未走（40 轨遗留）· TC-WL-8 生产执行待维护者（HG-PROD-READONLY-ACCESS 保持 pending）

---

## 一 · 任务信息

| 项 | 值 |
|----|----|
| task_slug | `prod_vector_waterline_check` |
| 依据 | 路线 `../ops-desk-workspace/docs/05-plan/04-agent-completion-roadmap_v1_zh.md` §P1-RAG「生产向量水位与对账 **待人工**」（2026-09 进度注） |
| 背景 | RAG 基础设施（`ops_knowledge_chunks` 表 / 入库管线 / 默认 `RAG_VECTOR_BACKEND=qdrant` / 影子写 DLQ / compose Qdrant v1.19.0）已落地，唯生产水位无实证：Qdrant collection 条数 vs PG 行数是否一致、DLQ 是否积压、最近 ingest 水位到哪里，均无回答手段 |
| 目标 | 交付**只读**核查脚本（三断面：PG↔Qdrant 对账 / DLQ 深度 / ingest 水位）+ 降级三态（不冒充）+ runbook + 报告模板 + CI 桩测；**生产执行面归维护者**（HG-PROD-READONLY-ACCESS），证据与处置分离 |
| 分支 | `task/prod-vector-waterline-check`（worktree `t-prod-waterline`） |
| 帽链 | 10-task → 20-task-audit R1 签收零阻塞（授权豁免 · 址A 落盘）→ 三闸 approved（00 代录 · m00238）+ HG-PROD-READONLY-ACCESS 保持 pending（仅阻生产执行）→ 30 交付 E1–E5（`invoke_20261017_30_executor.md`）→ PR #263 → **CLOSE（本档 · 40 轨未走照登）** |

## 二 · 交付

| 环节 | 实证 |
|------|------|
| PR | [#263](https://github.com/Cyning12/ops-desk-api/pull/263) · **MERGED 2026-10-17T05:50:21Z · squash commit `ea65d3d`** |
| E1 核查脚本 | `scripts/check_vector_waterline.py`（366 行）：只读连接 PG + Qdrant → 三断面（PG 行数 + ingest 水位 + DLQ 深度/最老年龄 · Qdrant count + scroll 全量 id 差集）→ YAML 报告落 `reports/vector_waterline_*.yaml`；报告不落连接串/凭证（`database_url_set` 布尔 + 剥离凭证 qdrant_url）· disclaimer 写死「本地/compose 产物不得当生产证据」 |
| E2 降级三态 | Qdrant 不可达 → exit 0 + PG 单侧 + 报告 `qdrant_face.status=no_evidence`「Qdrant 面无实证」（含原因）· PG 不可达/env 缺失 → 同理单侧 + 标注 · 双侧均不可达 → **exit 2 + stderr 显式错误 + 零报告**（不出半份冒充报告） |
| E3 runbook | `docs/guides/RUNBOOK_prod_vector_waterline_v1_zh.md`（81 行）：前置条件（HG-PROD-READONLY-ACCESS + env 清单表）/ 执行步骤（prod + local）/ 报告解读 / 降级判读四节齐备 |
| E4 报告模板 | `reports/vector_waterline_TEMPLATE.yaml`（61 行）：PG 面（row_count + ingest_waterline）/ Qdrant 面（points_count）/ 对账双向差集（计数+抽样）/ DLQ 面（depth/oldest_age_seconds/verdict）/ degradation 标注位 |
| E5 CI 桩测 | `tests/test_check_vector_waterline.py`（356 行 · **13 测全绿**）：FakePgConn + StubQdrantClient（写方法记账）· 聚合/差集方向/降级三态断言 + 只读断言（write_calls==[] + 全 SQL SELECT 词边界扫描）+ CLI 子进程双不可达 exit 2 |
| 关键实定 | **ingest 水位口径 = `max(ops_knowledge_chunks.embedded_at)`**（表无 created_at/updated_at · `alembic/versions/20260808_rag_chunks.py:46` 表结构亲读 · task「30 按表结构实定」授权 · runbook §3 标注） |
| invokes | `docs/harness/invokes/by-task/prod-vector-waterline-check/`（10_task_draft / 20_task_audit_r1 / 30_executor · 40 缺位照登 · 本批 CLOSE 纪律不另立 50 invoke） |
| 审查文 | 址A `docs/harness/reviews/task_prod_vector_waterline_check_audit_R1_20261017.md`（签收零阻塞 · 授权豁免） |
| **CLOSE 增量** | task 档归档 done/ · 本档落盘（**本批纪律：仅新增 `docs/tasks/close/close_*.md` · 零 git 操作 · 不改其他任何文件**） |

## 三 · 核验结论（验收终态摘要 · TC-WL-1–TC-WL-8 逐项）

| 验收项 | 结果 | 实证 |
|--------|------|------|
| TC-WL-1 脚本落地 + 桩测 | ✅ | `scripts/check_vector_waterline.py` 落地；`uv run pytest tests/test_check_vector_waterline.py -q` → **13 passed**（聚合/差集方向/降级三态/只读断言 + CLI 子进程双不可达 exit 2） |
| TC-WL-2 降级行为实证 | ✅ | 桩模拟 Qdrant 不可达 → exit 0 + PG 单侧 + 报告 `qdrant_face.status=no_evidence`「Qdrant 面无实证」；PG env 缺失同理单侧；双不可达 → exit 2 + stderr 显式错误 + 零报告 |
| TC-WL-3 runbook 四节 | ✅ | `docs/guides/RUNBOOK_prod_vector_waterline_v1_zh.md`：前置条件（闸 + env 清单表）/ 执行步骤（prod + local）/ 报告解读 / 降级判读四节齐备 |
| TC-WL-4 报告模板 | ✅ | `reports/vector_waterline_TEMPLATE.yaml` 含 PG 面 / Qdrant 面 / 对账双向差集（计数+抽样）/ DLQ 面（depth/oldest_age_seconds/verdict）/ 降级标注位 |
| TC-WL-5 本地/compose 亲跑 | ⏳ **未走（40 轨遗留）** | 40 轨未执行，本地 compose（Qdrant v1.19.0）亲跑真实报告未产出——**照登：无实证**；命令见 runbook §2，残留移交维护者 checklist（§七） |
| TC-WL-6 零越界 | ✅ | git status 仅 7 个新增路径（scripts/tests/docs/reports）；`app/ops/rag/**` · `alembic/**` · `docker-compose.yml` **零 diff**；ruff 触及路径 All checks passed；全量 pytest 1831 passed / 4 failed 均基线环境性（真库/API key/双进程），零新增红 |
| TC-WL-7 task lint | ✅（本 CLOSE 补实证） | 30 invoke 未摘录 lint 输出字面（照登：无实证字面）；**本 CLOSE 复跑 done/ 档**：`npx --yes spec-wave task lint --file docs/tasks/done/task_prod_vector_waterline_check.md` → **EXIT=0 · LINT: PASS** |
| TC-WL-8 生产执行（维护者） | ⏳ **待维护者** | **HG-PROD-READONLY-ACCESS 保持 pending**（需生产只读访问：PG 只读账号 + Qdrant 只读端点/凭证）；生产核查未跑 · `reports/vector_waterline_prod_*.yaml` 报告位留空**未伪造**（FP-7 纪律遵守）；不占 30/40 验收 |

**CLOSE 质量钉复跑（本帽 · 2026-10-17 · 分支 `close/active-batch-20261017-pm` 归档后仓态）**：

- `npx --yes spec-wave verify --target .` → **EXIT=0 · VERIFY: PASS**（裸 verify · 仓级 reviews 扫描 · 4 条存量基线豁免命中留痕 · 2026-10-11 授权 m01606/m00255 在案）。
- `npx --yes spec-wave task lint --file docs/tasks/done/task_prod_vector_waterline_check.md` → **EXIT=0 · LINT: PASS**（兼 TC-WL-7 补实证）。

## 四 · 偏差与 nit（如实照登）

1. **TC-WL-5 本地/compose 亲跑未走（40 轨遗留）**：40 帽未执行，本地 compose（`docker compose up -d db qdrant` · Qdrant v1.19.0）亲跑出真实报告的实证缺口残留——照登：无实证；脚本确定性已由 13 桩测 + 降级三态 CLI 子进程断言覆盖，残余风险 = 真实 compose 组网/驱动兼容未验。补走命令见 runbook §2，产物 `reports/vector_waterline_*.yaml`（本地标识 ·  disclaimer 防误当生产证据）。
2. **HG-PROD-READONLY-ACCESS pending（设计内 · 非阻塞）**：task 状态行明文「仅阻生产执行不阻脚本交付」；生产执行 = 维护者动作（TC-WL-8），签闸后按 runbook 跑核查 → `reports/vector_waterline_prod_*.yaml` 回填 → 路线 §P1-RAG「待人工」消解或上抛差集处置 task。报告位留空未伪造（FP-7）。
3. **差集处置另 task（FP-6 钉死）**：脚本只记录差集方向与抽样，不修数据/不重放 DLQ；若生产核查出差集，处置动作须另立 task。
4. **桩测开发期三处自身 bug（已修 · 留痕）**：`_fake_connect` 误挂 `@contextmanager` · 只读扫描 `'CREATE'` 子串误判 `created_at`（改词边界扫描）· 漏 `import re` / 未用 `import pytest`——均 30 过程内修复，最终 13 绿。
5. **TC-WL-7 字面缺录（已补）**：30 自检称「lint 结果见 30 invoke 验证记录」但该 invoke 未摘录输出字面；本 CLOSE 复跑 done/ 档 LINT: PASS 补实证（§三）。
6. **40 轨未走照登**：orchestration 原列 40 本地/compose 核验；本批交付由 30 → PR 直连，40 invoke 缺位，TC-WL-5 随之上抛为维护者 checklist 项（§四.1 同一缺口）。

## 五 · 签录（闸态表与审查文链）

| 闸 / 环节 | 状态 | 文档 / 实证 |
|-----------|------|------------|
| HG-TASK-DRAFT | **approved** | 2026-10-17 维护者授权 00 代录（m00238） |
| HG-AUDIT-R1 | **approved** | 同上（20 R1 书面审经授权豁免） |
| HG-GRAPH-MODULES | **approved** | 同上（全局真值 approved · `docs/_tech_graph/l1/01_modules.md:63` · `graph_change_layer=none`） |
| HG-PROD-READONLY-ACCESS | **pending（设计内保持）** | 仅阻生产执行（TC-WL-8 维护者动作）· 脚本交付不依赖本闸 · 待维护者签 |
| 20 R1 审查 | **签收零阻塞（书面审豁免）** | 址A `docs/harness/reviews/task_prod_vector_waterline_check_audit_R1_20261017.md` |
| invokes | — | `by-task/prod-vector-waterline-check/`（10/20/30 · 40 缺位照登） |
| 合并 | **MERGED** | PR [#263](https://github.com/Cyning12/ops-desk-api/pull/263) · squash `ea65d3d` · 2026-10-17T05:50:21Z |

## 六 · 资源清理

- **本 CLOSE 不删任何东西**（本批纪律零 git 操作）：分支 `task/prod-vector-waterline-check`（已 squash 合入 master `ea65d3d` · 删除安全 · 远端一并清）、worktree `t-prod-waterline`、本批 CLOSE 分支 `close/active-batch-20261017-pm` 移交 00/维护者统一清理。

## 七 · 维护者验收 checklist 与后续建议

### 维护者验收 checklist（00 代录 · 授权链同上 · 需人抽验/执行项）

- [ ] **桩测抽验**：`uv run pytest tests/test_check_vector_waterline.py -q` → 13 passed；`uv run ruff check scripts/check_vector_waterline.py tests/test_check_vector_waterline.py` → All checks passed。
- [ ] **只读纪律抽验**：脚本全文无 INSERT/UPDATE/DELETE/DDL 与 Qdrant 写 API（桩测只读断言已钉：write_calls==[] + 全 SQL SELECT 词边界扫描）；runbook 前置条件节只读账号语义写死。
- [ ] **（可选）补 TC-WL-5 本地实证**：`docker compose up -d db qdrant` 后按 runbook §2 亲跑脚本 → `reports/vector_waterline_*.yaml` 落盘（本地标识 · 非生产证据）。
- [ ] **TC-WL-8 生产执行（核心遗留）**：签 HG-PROD-READONLY-ACCESS（PG 只读账号 + Qdrant 只读端点/凭证）→ 按 runbook 跑生产核查 → `reports/vector_waterline_prod_*.yaml` 回填 → 路线 §P1-RAG「待人工」消解；若出差集/DLQ 积压 → 上抛处置 task（FP-6：本 task 只出证据不处置）。

### 后续建议

1. **生产核查排期**：TC-WL-8 是路线 §P1-RAG「待人工」的消解动作本身，建议维护者优先排期；脚本/模板/runbook 已使执行成本 = 填数 + 跑一条命令。
2. **差集/DLQ 处置预案（另案待命）**：若生产核查出差集或 DLQ 积压，处置（补嵌/重放/清理）须另立 task，勿在本资产上顺手扩面。
3. **监控接线（非范围在案）**：多副本/租约/告警接线属非范围，如核查常态化再立监控 task。

## 八 · 修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-17 | CLOSE 落稿（50 close 棒 · 三 task 批量关账 · 分支 `close/active-batch-20261017-pm`）：九节沿仓内先例 · 验收终态承 30 invoke TC-WL-1/2/3/4/6 实证（13 桩测 · 降级三态 · 禁区零 diff）+ TC-WL-7 由本档复跑补实证（done/ 档 LINT: PASS）· 质量钉复跑（verify EXIT=0 PASS）· TC-WL-5 40 轨遗留 / TC-WL-8 HG-PROD-READONLY-ACCESS pending 待维护者 / 水位口径 max(embedded_at) 实定 / 桩测三处自修 bug 如实照登 · 维护者 checklist 00 代录（授权链 m00238） |

## 九 · 附录

### 关键路径

| 类别 | 路径 |
|------|------|
| task（已归档） | `docs/tasks/done/task_prod_vector_waterline_check.md` |
| CLOSE 档 | `docs/tasks/close/close_prod_vector_waterline_check_20261017.md`（本档） |
| 交付资产 | `scripts/check_vector_waterline.py`（366 行 · 只读三断面）· `tests/test_check_vector_waterline.py`（356 行 · 13 桩测）· `docs/guides/RUNBOOK_prod_vector_waterline_v1_zh.md`（81 行）· `reports/vector_waterline_TEMPLATE.yaml`（61 行） |
| 审查文（址A） | `docs/harness/reviews/task_prod_vector_waterline_check_audit_R1_20261017.md` |
| invokes | `docs/harness/invokes/by-task/prod-vector-waterline-check/`（10_task_draft / 20_task_audit_r1 / 30_executor） |
| 代码锚点（只读） | `app/ops/rag/backend.py:27,38-39` · `app/ops/rag/shadow_write.py` · `app/ops/rag/ingest.py:152-170` · `alembic/versions/20260813_qdrant_dlq.py` · `alembic/versions/20260808_rag_chunks.py:46`（水位口径实定依据）· `docker-compose.yml:20-30,69-73` |
| 上游/先例 | 路线 `../ops-desk-workspace/docs/05-plan/04-agent-completion-roadmap_v1_zh.md` §P1-RAG · `reports/qdrant_reconcile_20260813T125801Z.yaml`（本地对账形状先例）· `docs/tasks/done/task_qdrant_migration.md` |

### CLOSE 复跑命令留痕

```bash
npx --yes spec-wave verify --target . > /tmp/verify_close_batch_pm.log 2>&1; echo "EXIT=$?"   # EXIT=0 · VERIFY: PASS
npx --yes spec-wave task lint --file docs/tasks/done/task_prod_vector_waterline_check.md     # EXIT=0 · LINT: PASS（兼 TC-WL-7 补实证）
```
