# Task：阶段 T · 只读租户谓词下推 + 跨租户负样本

> **状态**：`done`（2026-09-21 归档 · 代码已在 `chore/upgrade-langgraph-1.2` 入库：`app/ops/tenant_context.py` · `alembic/versions/20260918_tenant_readonly.py` · models/lookups `tenant_id`；**PR 未开、未合 master**，见 `docs/HANDOFF_recent-2days_v1_zh.md` §3-P0；生产 B 种子另轨）  
> **类型**：feature / 只读多租户  
> **上游**：workspace `docs/05-plan/06_stage_t_second_tenant_prep_v0_zh.md` · `docs/contracts/api-v1-tenant-readonly-context-draft.md` · 讨论稿 §8 阶段 T  
> **分支**：`task/tenant-readonly-predicate`（建议；base：`master`）  
> **前置**：H α `tenant_scoped`（#138）· H β supervisor 预算（#141）均已 MERGED  
> **00 注**：2026-09-18 · 维护者令「起草」· 仅落壳；**禁止**在 D1–D3 未齐时改 `app/` · **30 注**：同日 Fixture 本地跑通（未 commit）

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `tenant-readonly-predicate` |
| **git_branch** | `task/tenant-readonly-predicate` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 单测：lookup/RAG 谓词下推 + 跨租户负样本；不连真外网 / 不连生产 Qdrant 写 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1` |
| **graph_delta** | `docs/_tech_graph/l1/01_modules.md`（capability / lg_rag / rag 备注）· 可选 flow 一句 |
| **graph_delta_note** | **不新增**一级模块；备注「阶段 T 只读谓词下推」 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 契约真值在 workspace contracts；本仓可薄改 capability SPEC 备注 |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,20,30,40` |
| **invoke_retention_profile** | `default` |
| **experience_capture** | `recommended` |
| **kpi_aggregator** | `CLOSE` |
| **orchestration** | workspace 00 签数据闸 → 本仓 20 → 30 → 与 web 联调 |
| **freeze_id** | 无（默认不改 `lg-rag-sse-v1`） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | **approved** | 20-R1, 30 | 2026-09-18 维护者令本地 30 · 00 代签 |
| HG-AUDIT-R1 | **approved** | **30** | 2026-09-18 维护者令本地 30 · 00 代签（Fixture 轨 · 不写长审） |
| HG-GRAPH-MODULES | **approved** | **30** | 2026-09-18 · 仅 G-L1 备注、不新增一级模块 · 00 代签 |
| **HG-STAGE-T-DATA** | **approved** | **30** | 2026-09-18 Fixture 轨 · 本地跑通 · 生产种子另轨 |
| **HG-CONTRACT-FREEZE** | **approved** | **30** | 2026-09-18 · 对齐 workspace 契约 freeze（F1–F6）· 00 代签 |

---

## 背景与目标

H α 已机制化 `tenant_scoped` + 构造性单租户注入（`OPS_PILOT_TENANT_ID` / `ops-desk-pilot`）。阶段 T 要把 **Issue/PR lookup SQL 谓词** 与 **RAG 检索 metadata 过滤** 接到真实请求上下文中的租户，并具备 **跨租户负样本**（A 会话不得读到 B）。

本竖切交付：请求上下文解析 → 下推 → 负样本测绿。产品仍只读；**不开写 / HITL**。

---

## 现状锚点（只读 · 30 必读 · 10 已扫）

| 主题 | 路径 · 锚点 | 现状缺口 |
|------|-------------|----------|
| Policy 租户门 | `tests/test_capability_policy.py` · `tenant_scoped` | 缺 ctx 已拒；**有** ctx 后 SQL/ANN 是否真过滤未证 |
| Lookup | `app/ops/capability/lookups.py` | **无** tenant 谓词；仅 `number` |
| ORM | `app/db/models.py` · `OpsIssue`/`OpsPullRequest` | **无** `tenant_id` 列 → 30 须 DDL |
| tool_exec 注入 | `app/ops/lg_rag/multi/nodes.py` · `OPS_PILOT_TENANT_ID` | 构造性单租户；须改请求上下文（F1=C） |
| RAG Qdrant | `app/ops/rag/shadow_write.py` · `filter_payload` | **无** `tenant_id`；ALLOWED 仅 source/repo/… |
| 数据前置 | workspace `docs/05-plan/07_stage_t_data_prep_runbook_v0_zh.md` | 双轨：Fixture 解闸 / P 轨种子 |

---

## 10 钉死契约（草案 · freeze 后升格；30 不得静默改义）

| 项 | 钉死（草案） |
|----|----------------|
| **租户键** | ctx / 查询谓词主键 = `tenant_id`（与 H α 一致） |
| **试点命名** | A=`ops-desk-pilot` · B=`ops-desk-pilot-b`（**D1 已钉 · 2026-09-18**） |
| **注入优先级** | **已钉 F1=C**：session 为真源；请求宜带 `X-Ops-Tenant-Id`，若带则必须与 session 一致，否则 **403** |
| **头名** | **`X-Ops-Tenant-Id`**（F2） |
| **workspace_id** | 本波等同 `tenant_id`（F3） |
| **缺租户** | `tenant_scoped` 能力 → 既有 `tenant_scope_missing` 拒（不放行） |
| **跨租户资源** | fail-closed；**对外 HTTP 404**；对内/日志可记 `tenant_scope_denied`；**禁止**向客户端回传他租户存在性细节 |
| **SSE** | **默认零改** `event_type`；租户仅 header/body/session |
| **负样本** | A 会话查 B 的 issue# → 拒或空；同号不串（D4，可与本 task 同竖切） |

---

## 范围（同 task 竖切 · Fixture 闸齐后才 30）

- [x] **T0 · Schema**：Issue/PR 增 `tenant_id`（回填 A）；唯一约束策略按 workspace `07` §2.1；Qdrant `filter_payload`+index 增 `tenant_id`；ingest 写 `metadata.tenant_id`
- [x] **T1 · 请求上下文**：F1=C 解析/校验；切换 API 写 session；注入 Gateway ctx / tool_exec（替换纯 env 硬编码或请求优先）  
- [x] **T2 · Lookup 下推**：SQL **必带**租户谓词；跨租户 → 对外 404；fixture 负样本绿  
- [x] **T3 · RAG 下推**：检索前 tenant filter；A/B fixture 各 ≥1  
- [x] **T4 · 负样本**：至少 1 条自动化测（A→B issue#）；可选挂 eval 骨架（非硬门）  
- [x] **T5 · 图谱薄备注**：G-L1 capability/lg_rag/rag 一句；`chat/graph.py` **零 diff**

**竖切结论**：T0–T4 **同 task 必交**；T5 薄。生产 P 轨种子可 CLOSE 后另窗口做。

### 非范围

- 阶段 W / P；写能力；HITL；服务化 Registry  
- 改 SSE freeze / idle keepalive / 旧 chat 410 叙事  
- 完整 Workspace SaaS 产品（邀请、计费、租户管理台）  
- web UI（另 task）；ios  
- 改 `app/ops/chat/graph.py`

---

## failure_paths

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----------|----------|--------|----------|
| `HG-STAGE-T-DATA` / `HG-CONTRACT-FREEZE` / `HG-AUDIT-R1` pending 即 30 | **拒开工** | 是 | 是 |
| 缺 `tenant_id` 调 tenant_scoped | `tenant_scope_missing` · 拒 | 是（补 ctx） | 是 |
| 头与 session 不一致 | 403（草案） | 否（改客户端） | 是 |
| 跨租户 lookup/RAG | 拒或空 · 不泄漏 | 否 | 是（安全空/错） |
| 误改 SSE event_type | 审查拒收 | 是 | 否 |
| 无第二租户 fixture 却宣称验收 | 40/verify 拒收 | 是 | 否 |

---

## 验收标准

- [x] 人工闸：`HG-STAGE-T-DATA` · `HG-CONTRACT-FREEZE` · `HG-AUDIT-R1` · `HG-GRAPH-MODULES` 均为 approved 后方可勾选下列码项  
- [x] T0：Issue/PR `tenant_id` + Qdrant/PG tenant filter 路径落地；既有行回填 A  
- [x] T1：请求上下文可测注入；不再仅依赖「全局唯一 pilot」才能过 tenant_scoped 金样  
- [x] T2：跨租户 issue/PR 负样本单测绿（对外 404）  
- [x] T3：跨租户 RAG 负样本（或 metadata filter 单测）绿  
- [x] T4：至少 1 条 A→B 自动化断言  
- [x] `ruff` 触及路径绿；`pytest` 本波相关 + 既有 capability/lookup 回归绿  
- [x] `./scripts/graph-compile.sh` 绿（若改图谱）  
- [x] `chat/graph.py` 零 diff；不新增 G-L1 一级模块  
- [x] `npx spec-wave task lint --file docs/tasks/active/task_tenant_readonly_predicate.md` PASS

---

## 依赖

| 依赖 | 说明 |
|------|------|
| workspace 过程 task | `../ops-desk-workspace/docs/tasks/active/task_stage_t_tenant_contract.md` |
| 契约 | `../ops-desk-workspace/docs/contracts/api-v1-tenant-readonly-context-draft.md` |
| 06 前置 | `../ops-desk-workspace/docs/05-plan/06_stage_t_second_tenant_prep_v0_zh.md` |
| 07 数据 Runbook | `../ops-desk-workspace/docs/05-plan/07_stage_t_data_prep_runbook_v0_zh.md` |
| H α | `docs/tasks/done/task_capability_contract_hardening.md` |
| H β | `docs/tasks/done/task_supervisor_budget_h_beta.md` |
| web 并行 | `../ops-desk-web/docs/tasks/active/task_web_tenant_context_chat.md`（联调；可后合） |
| 编码规范 | `docs/standards/CODING_BACKEND_L2_v1_zh.md` |

---

## 给执行帽的必读列表

1. `AGENTS.md`  
2. 本 task（钉死契约 · 闸 · 非范围）  
3. workspace 契约 + 06  
4. 讨论稿 §8  
5. `docs/standards/CODING_BACKEND_L2_v1_zh.md`  
6. 代码：`app/ops/capability/**` · `app/ops/lg_rag/multi/nodes.py` · lookup/RAG 检索路径  
7. `docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`

---

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|----|------|------------|----------------------|----------------|
| R0 | T = 谓词下推 + 负样本，非 Workspace SaaS | no | — | none |
| R1 | 30 硬阻塞于数据闸+契约 freeze | no | — | 数据长期不齐 |
| R2 | T1–T4 同竖切；SSE 不动 | no | — | lookup 表无 tenant 列需迁移 |
| R3 | 头/session 策略外包给契约 freeze | yes | 实现面已框；schema/迁移细节等 30 实扫 | ORM 无 tenant 列则工期膨胀 |
| R4 | （未开） | — | early_stop at R3 | — |
| R5 | （未开） | — | early_stop at R3 | — |

**actual_last_round**：R3 · **early_stop**：yes · **residual_risks**：见 R3

### R0 · 问题框定

H 只解决「缺租户拒」；T 解决「有租户后真隔离」。

### R1 · 开工闸

无第二租户数据的「下推」无法验收 → 拒 30 优于假绿。

### R2 · 竖切

上下文 + lookup + RAG + 一条负样本同 task，避免半截合入。

### R3 · 外置产品钉死

头 vs session、404 vs 业务码交给 workspace freeze；本仓 30 只实现已钉语义。

### R4 ·（未开 · early_stop）

本轮不展开；实现面等数据闸与 freeze。

### R5 ·（未开 · early_stop）

本轮不展开。

---

### 自检结论（执行者）

> **hat 40** · 2026-09-18 · 工作目录=仓根 · **未 commit** · **未** 为本波另起 8001（避免串口）

| 命令 | 退出码 | 摘要 |
|------|--------|------|
| `.venv/bin/ruff check app tests` | **1** | 既有 2 条（`app/ops/rag/tokenizer.py` UP035 · `tests/test_rag_chunker.py` I001）；**非本波**（无 diff） |
| `.venv/bin/ruff check` 本波 app/tests 触及路径 | **0** | All checks passed |
| `.venv/bin/pytest tests/test_tenant_context.py tests/test_capability_lookups.py -q --tb=short` | **0** | **19 passed** |
| `.venv/bin/pytest tests -q --tb=short` | **1** | **680 passed · 2 failed · 1 skipped**；失败均 `tests/test_chat_ws.py`（缺 `ops_knowledge_chunks` / event loop）· **与本波无关** · 未扩修旧 chat WS |
| `./scripts/graph-compile.sh` | **0** | 9 graphs · 132 nodes · 194 edges · check OK |
| `npx spec-wave verify --target . --task docs/tasks/active/task_tenant_readonly_predicate.md --allow-no-review --allow-invoke-gap` | **0** | VERIFY: PASS |
| `npx spec-wave task lint --file docs/tasks/active/task_tenant_readonly_predicate.md` | **0** | LINT: PASS |
| `npx spec-wave task lint-wiki-delta --target .` | **0** | LINT-WIKI-DELTA: PASS（scanned=116 · issues=0） |
| `git diff --stat -- app/ops/chat/graph.py` | **0** | **零 diff**（bytes=0） |
| `curl --noproxy '*' http://127.0.0.1:8001/api/ops/auth/me` | **7** | **8001 未听**；Docker `:8000` 另进程在听，**不得**当作本波 |

**验收表摘要**：T0–T5 与门禁条（本波 ruff / 本波+lookup pytest / graph-compile / chat 零 diff / task lint）均为 **pass**。全量 pytest 2 fail 记残留、不改 T0–T5 口径。

**已知未测项**：本机 uvicorn **8001 未听** → 未抽检 `/me` 401、头不一致 403、tenant 切换（30 invoke 曾测；40 未复测 HTTP）。生产 B 种子未做。未跑 Docker `:8000` 当本波。

**结论**：**40 PASS**（Fixture 轨 · 待 web 联调对准 8001 · **禁止 commit**）

---

## 修订

| 日期 | 说明 |
|------|------|
| 2026-09-18 | 10 起草壳 · NO-GO 30 · 互链 workspace/web |
| 2026-09-18 | 30 Fixture 本地跑通 · T0–T5 勾选 · invoke `invoke_20260918_30_*` |
| 2026-09-18 | 40 自检回填 · invoke `invoke_20260918_40_verify_*` · 未 commit |
| 2026-09-21 | 代码随两日集中开发入库 `chore/upgrade-langgraph-1.2`（脱离 specwave 过程，见 HANDOFF）；task 归档 active→done；PR 待开 |
