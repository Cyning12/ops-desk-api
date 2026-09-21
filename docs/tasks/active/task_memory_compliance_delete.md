# Task：记忆合规物理删除权（service 层 purge_by_user 按 (tenant,user) 全 status 整行 DELETE + 动作级审计记动作不记内容）· POST /admin/memory/purge（AdminSyncAuth 对齐 · dry_run 默认 true + expected_count 双闸门：缺→400 / 不等→409 零删除）· 删除后确定性召回零命中+向量通路零命中+表行全 status 零残留+越 tenant/user 零影响断言化 + 变异检验三条（memory-compliance-delete）

> **状态**：`signed`（2026-09-22 · R1 PASS 零阻塞 · HG-TASK-DRAFT/HG-AUDIT-R1=approved（维护者授权 00 代录）· 可 30）  
> **类型**：feature（新增管理面不可逆删除能力 · **无 alembic 义务**（零新表零列 · 审计落既有 logger 面 · SPEC §4 A1 裁决）· **有图谱义务按实判**（新 admin 路由 `POST /admin/memory/purge` 落 admin 行备注 + 人签记录新行留 00 代录位 · 不新增一级模块/表/SSE 事件 · 偏离回炉条款见闸表与 graph_delta_note））  
> **上游 SPEC**：`docs/spec/memory-compliance-delete/SPEC-memory-compliance-delete_v1.md`（**signed** · HG-SPEC-SIGNOFF=approved 2026-09-22 · a65ce3b · S1 同步物理删除 + A1 日志审计 + 默认干跑双闸门签收锁死）  
> **分支**：`task/memory-compliance-delete`（**禁止 master/main 直改 · 禁止 push**）  
> **10 注**：2026-09-22 · 本棒由 00 委派 10-task 帽 Agent 执行；HG-TASK-DRAFT / HG-AUDIT-R1 落稿时待签（10 帽不签）

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `memory-compliance-delete` |
| **git_branch** | `task/memory-compliance-delete` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 干跑/实删对拍断言（干跑零行变化 · 响应 echo dry_run 标志）· 双闸门断言（缺 expected_count → 400 · 计数不等 → 409 零删除 · 计数等 → 200 且 deleted==expected_count）· 删除后断言（确定性召回零命中 · 向量通路零命中（MEMORY_FACTS_VECTOR_RECALL_ENABLED=true + mock embedder）· 表行零残留含全部 status）· 越 tenant/user 谓词断言（跨 tenant 调用影响 0 行 · 他 tenant/他 user 夹具行逐行不动）· 审计留痕断言（caplog 动作级日志存在 · 字段含 tenant/user/dry_run/affected · 不含 key/value 内容）· 幂等断言（重复实删影响 0 行）· **变异检验三条**（谓词可检 / 全量可检 / 审计可检 · 见验收「变异检验」）· 全量 pytest 绿（基线 **1333 collected** 真跑）+ ruff 零新增 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | **有图谱义务按实判**（SPEC §2 D4）：新增 admin 路由 `POST /admin/memory/purge`（`app/ops/admin/` 既有一级模块内 · 零新开一级模块）——`admin` 行备注（首个 admin 面不可逆写端点 · AdminSyncAuth · 默认干跑 + 双闸门）+ `api` 行注册备注 + 人签记录**新行留 00 代录位**（随 30 交付落盘 · llm-layer-hardening/session-summary-fallback 先例）；**不新增一级模块/表/SSE 事件类型**（**本帽真读复核**见闸表 HG-GRAPH-MODULES 行与 R1） |
| **graph_delta** | 有（admin 行备注新路由 + api 行注册备注 + 人签新行 · 零新一级模块） |
| **graph_delta_note** | **回炉补闸条款**：若 30 阶段实现形态偏离预判（新增一级模块 · 新增表/列触发 alembic · 新增 SSE 事件类型 · 新建 DB 审计表 · 改逻辑状态机/write/revoke/sweep/recall 既有语义等 SPEC §3 非范围项），**不得沿用本裁定**——退回 10-spec 修订 SPEC + 10-task 补闸 + `docs/_tech_graph/` 如实登记后方可续 30 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 契约真值在 SPEC `memory-compliance-delete`；`app/ops/memory/README.md` 模块说明同步属 D4 范围项非 wiki |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,20,30,40` |
| **invoke_retention_profile** | `default` |
| **experience_capture** | `recommended` |
| **kpi_aggregator** | `CLOSE` |
| **orchestration** | 单 task 直通：10 落稿 → 20-task-audit → HG-AUDIT-R1 人签 → 30（承 SPEC §8 序：D4 图谱 → D1 purge 函数 → D2 admin 路由 → D3 断言 · 状态机/recall/revoke 既有语义零改动）→ 40（干跑对拍 + 双闸门三态 + 两通路零命中 + 越域零影响 + 变异检验三条）→ CLOSE |
| **freeze_id** | 无（不改 `lg-rag-sse-v1` / `lg-rag-http-v1` / `lc-evidence-http-v1`；SSE 零新事件类型；新 admin HTTP 路由非 freeze 面） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | approved | 20-R1, 30 | 2026-09-22 · 00 验收 10-task 稿通过（维护者本窗授权 00 签收过程文档 · 原话留痕 SPEC 状态行） |
| HG-AUDIT-R1 | approved | **30** | 2026-09-22 · 20-task-audit R1 PASS 零阻塞零退回（`docs/harness/reviews/task_memory_compliance_delete_audit_R1_20260922.md` · B1 抽 5 亲跑 · 双闸门三态可执行）· 维护者本窗授权 00 代录签收 |
| HG-GRAPH-MODULES | approved | **30** | 2026-09-22 本帽**真读** `docs/_tech_graph/l1/01_modules.md`：模块表已建置（bootstrap 签 2026-07-16 · 签录链完整至 :92 security-input-isolation 行）；`admin` 行 :30（`app/ops/admin/**` → db · Bearer 机读 token + cookie maintainer 双口径）· `memory` 行 :28（ops_memory_facts · **无对外 HTTP 端点**——purge 是 memory 首个对外入口但落在 admin 模块内 · 零新开一级模块）· `api` 行 :20（router.py 注册面）均在表。SPEC §2 D4 判**有图谱义务按实判**：`admin` 行备注（`POST /admin/memory/purge` 首个 admin 面不可逆写端点 · AdminSyncAuth · 默认干跑 + expected_count 双闸门）+ `api` 行注册备注 + 人签记录**新行留 00 代录位**（随 30 交付落盘 · llm-layer-hardening/session-summary-fallback/security-input-isolation 先例）——义务钉在 D4 验收，**不新增一级模块/表/SSE 事件**故不阻塞 30 开工形态预判。**若 30 形态偏离 → 回炉补闸**（见 graph_delta_note，不得沿用本裁定） |
| HG-PILOT-OPSDESK-GLAYER | n/a | 物理分层试点改码 | 本 task 不涉物理分层试点 |

---

## 背景与目标

现状（SPEC §1 实扫锁死 · 2026-09-22 本帽复核一致）：P0 状态机（active/superseded/revoked/expired）全部为**逻辑失效**，物理删除未做（service.py docstring :7 明示「失效走状态机，**不物理删**」——本帽复核）；企业合规场景（用户行使删除权）需要按 user 物理删除的能力——删除权缺位意味着 revoked 行连内容带 embedding 永久留表，恰是合规面不可逆缺口。SPEC **时机裁定：现在做，但落地形态取保守双闸门**（用户令队列推进 + revoke_by_key 前置就绪证明 tenant+user 谓词纪律与审计日志形态已稳定 + 保守形态兜住「真实流量前」顾虑：管理面默认干跑，实删须先干跑取计数、再携 matching expected_count 双闸门提交）。

一句话目标（SPEC 锁死）：为 ops_memory_facts 提供**按 (tenant_id, user_id) 的整行物理删除**能力：service 层幂等 `purge_by_user`（**全 status 行整行删除** · embedding 列随行消失）+ admin 面入口 `POST /admin/memory/purge`（AdminSyncAuth 对齐 · **默认干跑 + expected_count 双闸门**：缺 → 400 · 不等 → 409 零删除）+ 动作级审计留痕（`logger.info` 记动作不记内容 · revoke 先例同形）；删除后**召回/向量两通路零命中 + 表行零残留（全 status）+ 越 tenant/user 零影响**全部断言化；逻辑状态机语义零改动。

设计纪律（30 不得违反 · 承 SPEC §1/§2/§4 签收锁死）：

1. **S1 同步物理删除**（SPEC §4 裁决 · 不重演）：单条 `DELETE ... WHERE tenant_id+user_id` 单事务原子执行——不存在半删中间态；幂等天然成立（重复实删第二次影响 0 行）；两通路零残留 = 行零残留（embedding 是表内列 · 向量 SQL 查表本身）。
2. **双闸门铁律**：`dry_run` 默认 true（盲发只读 · 干跑前后表行计数逐字节对拍）；实删（dry_run=false）必须 `expected_count` 与当前匹配计数一致——缺 → 400 · 不等 → 409 零删除（调用方重新干跑）；「删多少」是显式对账不是盲发。
3. **谓词铁律**：DELETE 谓词含且仅含 tenant_id+user_id（revoke_by_key :176-177 纪律钉死 · 跨 tenant = 0 行）；越域防线全在断言层 + 变异检验①（删后不可恢复如实定性）。
4. **审计记动作不记内容**（SPEC §4 A1 裁决）：`logger.info("memory purge_by_user tenant=%s user=%s dry_run=%s affected=%d", ...)`——无 key/value（revoke :159-162/:197-200 先例同形）；实删/干跑/幂等 0 行全含；落既有 logger 面零新表。
5. **诚实定性**：双闸门防不住「计数碰巧相等的错目标」（expected_count 只锁范围数量不锁主体正确性 · SPEC §7 ① 残余风险如实承认）；同计数内容替换竞态不可区分（管理面低频操作可接受 · §7 ②）；审计落日志面不可机查台账（§7 ③ · 合规要求机查台账时回 10-spec 升级 A2）。
6. **计数守恒纪律**：PurgeReport 字段族 `dry_run/scanned/deleted/by_status/elapsed_s/recorded_at`（backfill 报告先例）；实删 `deleted==scanned` · 干跑 `deleted==0`；干跑/实删同谓词同计数口径（口径漂移 = 409 误拒，灰度期暴露）。

---

## 现状锚点（只读 · 30 必读 · 10 已扫 · 承 SPEC §1 并复核）

| 主题 | 路径 · 锚点 | 现状 |
|------|-------------|------|
| revoke 语义（**纪律沿用对象 D1**） | `app/ops/memory/service.py` | `revoke_by_source`（:134-163 本帽复核）/ `revoke_by_key`（:166-201）：均 `UPDATE ... SET status='revoked'` **逻辑失效**——只动 active 行、幂等（重复 0 行）、审计 `logger.info` 记动作与影响行数（**记动作不记内容**先例 :159-162/:197-200）；`revoke_by_key` 必带 tenant+user 谓词（跨 tenant = 0 行 · :176-177 docstring 钉死）；docstring :7 明示「失效走状态机，**不物理删**」——物理删除零既有实现可复用，只有纪律可沿用 |
| strip 先例（**D2 对齐对象**） | `app/ops/memory/service.py:110-115` | `write_fact` 对 tenant_id/user_id/key 一律 `.strip()`（本帽复核）——请求体 tenant/user 空串/空白 strip 后空 = 400 对齐此先例 |
| session 纪律（**D1 对齐对象**） | `app/ops/memory/service.py:10-11` | docstring：传入 session 调用方持事务只 flush；不传自开 `AsyncSessionLocal` 并 commit（对齐 thread_store 先例）——purge 沿用 |
| AdminSyncAuth（**D2 对齐对象**） | `app/ops/deps.py:86-116` | `require_admin_sync`（本帽复核）：Bearer `OPS_ADMIN_SYNC_TOKEN`（`secrets.compare_digest` 比对 :98 · token 空则 Bearer 路径禁用 :97-103 · 禁写日志 docstring :93）或 cookie maintainer 角色（:105-111 · 非 maintainer 403）；已挂 admin/sync.py :32、admin/capability.py 5 处、hitl/router.py 共 8 处——admin 面鉴权口径唯一且成熟 |
| admin 错误纪律（**D2 对齐对象**） | `app/ops/admin/sync.py:35-45` | 异常 rollback + `logger.exception` + HTTPException 500（本帽复核 · 500 不静默先例同形） |
| admin 路由注册面（**D2 落点**） | `app/ops/router.py:4-5/:24-25` | 注册 `admin_sync_router` + `admin_capability_router`（本帽复核）；`app/ops/admin/` 目录 ls 实证：`__init__/capability/schema/service/sync/sender` **无 memory.py**（新增义务）；**admin 面目前零写操作路由**，本 purge 是首个不可逆写端点 |
| ops_memory_facts 模型（**D1/D3 断言对象**） | `app/db/models.py` | `embedding` 列（:558-560 · Vector(1024) nullable deferred=True · P1 向量召回用）；`supersedes` 自引用 FK `ondelete="SET NULL"`（:545-549 · 只在同 (tenant,user,key) 内置链）；status CHECK 四值（:500-503）；整行物理 DELETE 天然覆盖 embedding 列——**向量残留 = 行残留，两通路同源一张表** |
| 向量通路（**D3 断言对象**） | `app/ops/memory/service.py:266-528` | `_VECTOR_RECALL_SQL`（:281-289）裸 SQL 查 ops_memory_facts 表本身（cosine `<=>` · 必带 tenant/user/active/未过期谓词）；`_vector_top_m` ORM 补取再次带全谓词（:461-469 双保险）；向量失败回退确定性 + span `memory_vector_degraded`（:494-501）——行不在即零命中 |
| 干跑/报告字段族先例（**D1 输出对齐对象**） | `scripts/memory_embedding_backfill.py` + `reports/memory_embedding_backfill/backfill_*.yaml` | `status/dry_run/scanned/skipped/failed/failed_ids/elapsed_s/recorded_at` 字段族 + **计数守恒**（:72 注释钉死）；`reports/qdrant_migrate/reconcile_p1_*.yaml` 双侧计数对账先例 |
| 审计面现状 | 全仓 grep `audit` | **零 DB 审计表、零审计模块**；唯一审计形态 = memory service `logger.info` 动作日志（SPEC §1 实扫 · 本帽复核一致）——审计落既有日志面是唯一与现状一致的选项（A1 裁决） |
| 模块说明（**D4 文档落点**） | `app/ops/memory/README.md` | **存在**（本帽 ls 实证）——补 purge 语义与双闸门纪律 |
| 命名冲突扫 | `grep -rn 'purge_by_user\|PurgeReport\|admin/memory'` app/ tests/ evals/ docs/_tech_graph/ | **零命中**（2026-09-22 本帽真跑 · 全仓 purge 命中仅 Dockerfile apt-get 与 SPEC 文档 · 新函数名/路由路径/报告类名无冲突） |
| 测试基线 | `python -m pytest tests --collect-only -q` | **1333 collected**（2026-09-22 本帽真跑）；相关面用例计数见 B1 清单 |
| alembic 义务 | 无 | 零新表零列 · 纯 DELETE + 只读计数；审计落既有 logger 面不落新表（SPEC §4 A1 裁决）；迁移 diff 为空入验收断言 |

---

## 钉死契约（自 SPEC §2/§4 锁死；30 不得静默改义）

| 项 | 钉死 |
|----|------|
| **落点（D1）** | `app/ops/memory/service.py` 新增 `purge_by_user(tenant_id, user_id, *, dry_run=True, session=None) -> PurgeReport`（既有模块内 · **零新开一级模块** · 与 write/revoke/sweep/recall 同 module docstring 纪律面） |
| **删除语义（D1）** | `DELETE FROM ops_memory_facts WHERE tenant_id=:t AND user_id=:u`——**全 status 行整行删除**（active/superseded/revoked/expired 无差别 · embedding 列随行消失）；谓词含且仅含 tenant_id+user_id（锚点断言 · 变异检验①兜底） |
| **干跑语义（D1 铁律）** | `dry_run=True`（**默认**）：同谓词 `SELECT count(*) + count by status`，**零写**（前后计数对拍断言）；实删与干跑同谓词保证计数口径一致 |
| **审计留痕（D1）** | `logger.info("memory purge_by_user tenant=%s user=%s dry_run=%s affected=%d", ...)`——**记动作不记内容**（无 key/value · revoke :159-162 同形）；实删/干跑/幂等 0 行全含（caplog 断言 · 变异检验③兜底） |
| **幂等（D1）** | DELETE 天然幂等：重复实删第二次 `deleted==0`（与 revoke 幂等语义同形 · 断言化） |
| **事务（D1）** | 单条 DELETE 语句单事务原子执行（无半删中间态）；session 纪律沿用模块先例（传入 session 调用方持事务只 flush · 不传自开 `AsyncSessionLocal` 并 commit · :10-11 docstring） |
| **返回（D1）** | `PurgeReport` dataclass：`dry_run/scanned(=匹配行数)/deleted/by_status/elapsed_s/recorded_at`（backfill 报告字段族 · **计数守恒**：实删 `deleted==scanned` · 干跑 `deleted==0`） |
| **路由（D2）** | `POST /admin/memory/purge`（新文件 `app/ops/admin/memory.py` · `app/ops/router.py` 注册 · tags=["admin"] · `/api/ops` 前缀下 `/api/ops/admin/memory/purge`） |
| **鉴权（D2）** | `_user: OpsUser | None = AdminSyncAuth`（admin/sync.py :32 先例逐字对齐 · **零新鉴权面**）；未授权 → 401/403 且表行零变化（断言） |
| **请求体（D2）** | `{tenant_id, user_id, dry_run: bool = true, expected_count: int \| None = null}`；tenant/user 空串/空白 strip 后空 → 400（service.py :110-115 strip 先例对齐） |
| **双闸门（D2 铁律）** | ① **默认干跑**：`dry_run` 缺省/显式 true → 只返回计数报告零写（响应 echo `dry_run` 标志）；② **实删须范围确认**：`dry_run=false` 时 `expected_count` 必填（缺 → 400 零删除），与当前匹配计数**不等 → 409 零删除**（调用方重新干跑）；计数等 → 200 实删且 `deleted==expected_count` |
| **错误纪律（D2）** | 500 不静默：异常 rollback + `logger.exception` + HTTPException（admin/sync.py :35-45 先例同形） |
| **竞态语义（D2）** | expected_count 不等即拒（dry-run 后有新写入/其他删除 → 计数漂移 → 409）；**同计数内容替换**（时间窗内同数新行换旧行）不可区分 → 列残余风险（SPEC §7 ② · 管理面低频操作可接受） |
| **图谱（D4）** | `admin` 行备注（POST /admin/memory/purge 首个 admin 面不可逆写端点 · 双闸门）+ `api` 行注册备注 + HG-GRAPH-MODULES 人签记录新行（**00 代录位** · 随 30 交付落盘）；`./scripts/graph-compile.sh` 绿；零 alembic（迁移 diff 为空断言）；零新表/零一级模块/零 SSE 事件（偏离 → 回炉补闸 + SPEC 回炉） |
| **文档（D4）** | `app/ops/memory/README.md`（存在 · 本帽实证）补 purge 语义（双闸门 · 幂等 · 审计不记内容）+ service docstring 补「物理删除走管理面 purge」；admin 面文档补端点；不回改 done/归档历史文档 |
| **安全** | 无新凭证面（复用 OPS_ADMIN_SYNC_TOKEN / maintainer cookie）；无新网络面/对外端点（admin 前缀既有）；**首个 admin 面不可逆写端点**——双闸门 + 审计断言为本 task 核心否决面；审计日志不含 fact 内容（无 PII 泄漏面）；干跑为只读面；tenant/user 由请求体显式传入但只在 AdminSyncAuth 通过后才生效（admin/capability.py「替别人看一眼」先例同形态） |

---

## 范围（单 task 直通 · SPEC §2 D1–D4）

- [ ] **D1 · service 层物理删除（必做 · 核心 · S1 同步物理删除）**：`app/ops/memory/service.py` 新增 `purge_by_user(tenant_id, user_id, *, dry_run=True, session=None) -> PurgeReport`；DELETE 谓词含且仅含 tenant_id+user_id；全 status 整行删除；`dry_run=True` 默认零写（count + count by status）；审计 `logger.info` 记动作不记内容（含幂等 0 行）；单事务原子；`PurgeReport` 字段族 + 计数守恒
- [ ] **D2 · 管理面入口（必做 · AdminSyncAuth 对齐 · 双闸门）**：新文件 `app/ops/admin/memory.py` + router.py 注册；`_user: OpsUser | None = AdminSyncAuth`；请求体 `{tenant_id, user_id, dry_run=true, expected_count=null}`；默认干跑零写 echo 标志；实删缺 expected_count → 400 · 计数不等 → 409 零删除 · 计数等 → 200；tenant/user 空白 strip 后空 → 400；500 不静默（rollback + logger.exception）
- [ ] **D3 · 删除后断言（必做 · 验收否决面）**：确定性召回零命中（`recall_active` 返回空 · 事前有 active 行夹具）；向量通路零命中（`MEMORY_FACTS_VECTOR_RECALL_ENABLED=true` + mock embedder → `recall_with_vector` 返回空）；表行零残留（`count(*) WHERE tenant+user == 0` **全 status**）；越域零影响（他 tenant 同 user / 同 tenant 他 user 夹具行逐行不动 · 跨 tenant purge `deleted==0`）；审计存在（caplog 字段含 tenant/user/dry_run/affected · 不含 key/value）
- [ ] **D4 · 图谱 / 文档（必做 · 按实判）**：零 alembic（迁移 diff 为空断言）；`docs/_tech_graph/` admin 行备注 + api 行注册备注 + HG-GRAPH-MODULES 人签新行（00 代录位）；graph-compile 绿；memory 模块说明 + service docstring 同步

**竖切结论**：D1–D4 同 task 一次提交（SPEC §8 序：D4 图谱 → D1 purge 函数 → D2 admin 路由 → D3 断言收口）；purge 函数不配双闸门入口 = 能力无触发面；不配删除后断言 = 违反「先把坏了能发现装上」；耦合面小（一个函数 + 一个路由 + 注册行 + 测试/图谱/文档），单 PR 可控。

### 非范围

- ❌ **删除其它业务表数据**（ops_threads/ops_runs/checkpoints/ops_users 等任何表 · 本 task 只覆盖 ops_memory_facts）
- ❌ **DSR 全流程自动化**（删除权请求的受理/核验/多表编排/SLA 工单 · 另案）
- ❌ **改逻辑状态机**（active/superseded/revoked/expired 语义 · write/revoke/sweep/recall 行为零改动 · revoke 仍是运行期纠错唯一入口，purge 只走管理面）
- ❌ **用户自助端点**（非 admin 面的任何删除入口 · 本波仅管理面 + 双闸门）
- ❌ **批量/全表 purge**（无 tenant 级、无全表级、无定时 purge worker · 最小粒度 = 单 (tenant,user)）
- ❌ **RAG 知识库/Qdrant 数据删除**（`ops_memory_facts` embedding 是表内列随行删除；知识库 chunks/Qdrant 集合删除另案）
- ❌ **Langfuse/trace 侧数据删除**（观测面数据生命周期另案）
- ❌ **新建 DB 审计表**（SPEC §4 A1 裁决落既有日志面 · 若未来合规要求机查审计台账 → 回 10-spec 修订）
- ❌ 前端/管理台 UI（本波纯 API 面）
- ❌ 历史文档回改

---

## failure_paths

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----------|----------|--------|----------|
| `HG-AUDIT-R1` 未签即 30 | **拒开工** | 是 | 是 |
| B1 旧测影响面未落盘/未逐条处置即 30 交付 | **拒收**（闸前置 · 30 逐条执行处置并在提交说明逐条回填） | 是 | 是 |
| 验收缺干跑对拍/双闸门三态/两通路零命中/越域零影响/审计 caplog/幂等/变异检验三条任一 | **拒收**（防空真规则） | 是 | 是 |
| **误删**（范围确认缺失/错填 tenant/user → 删错人） | **不可逆错**；防线三层：① dry_run 默认 true（盲发只读）；② 实删必须 expected_count 与当前匹配计数一致否则 409 零删除；③ 审计日志记动作可追查。残余：计数碰巧相等且确为错目标 → 双闸门不可防（SPEC §7 ① · 管理面人工操作纪律兜底：先干跑核对计数再实删） | 否（删后不可恢复 · 防在闸前） | 是 |
| **越 tenant / 越 user 删除**（谓词漏带 → 跨域行被删） | **不可逆 + 静默错**；DELETE 必带 tenant+user 双谓词（revoke_by_key :176-177 纪律钉死）；D3 断言他 tenant/他 user 夹具行逐行不动、跨 tenant 调用影响 0 行；变异检验①兜底（临时去谓词 → 断言必挂） | 是（修谓词 · 已删不可恢复故防线全在断言层） | 是 |
| **删一半中断**（进程崩溃/DB 断连 mid-delete） | 单条 DELETE 语句单事务原子执行——**不存在半删中间态**（要么全删要么全留）；异常 rollback + logger.exception + 500（admin/sync.py :35-45 先例）；重入安全：重跑删剩余行（幂等 · 第二次起影响 0 行） | 是（重发请求） | 是 |
| **审计缺位**（删除执行了但无留痕） | **静默错**；审计日志在 purge 函数内强制记录（实删/干跑/幂等 0 行全含 · revoke :159-162 先例同形）；D3 caplog 断言审计字段存在且不含内容；变异检验③兜底（临时去日志 → 断言必挂） | 是（补日志） | 否 |
| **向量通路残留**（行删了 embedding 还留在某处） | embedding 是表内列（models.py :558-560 · 无独立向量库存储 memory facts），整行 DELETE 随行消失；向量 SQL 查表本身（:281-289）——行不在即零命中；D3 向量通路零命中断言 + 变异检验②（只删 active 行 → 零残留断言必挂） | 是 | 否 |
| **dry_run 标志误用**（dry_run=true 却真删 / 响应不 echo 标志致调用方误判） | 干跑路径零写（对拍断言：干跑前后表行计数逐字节一致）；响应 echo `dry_run` 字段；实删/干跑同谓词同计数口径（口径漂移 = 409 误拒，灰度期暴露） | 是（修代码） | 是 |
| **expected_count 竞态**（dry-run 后实删前有新写入/其他删除） | 计数不等 → 409 零删除 + 调用方重新干跑；同计数内容替换（时间窗内同数新行换旧行）不可区分 → SPEC §7 ②（管理面低频操作可接受） | 是（重新干跑） | 是 |
| **未授权调用** | AdminSyncAuth 既有语义：Bearer 比对 `secrets.compare_digest`（token 空则 Bearer 路径禁用）/ cookie maintainer 角色，否则 401/403；未授权请求零删除（断言） | 是（带凭证重试） | 是 |
| **supersedes 自引用 FK 悬挂** | `supersedes` FK `ondelete="SET NULL"`（models.py :545-549）且只在同 (tenant,user,key) 内置链（service :56-82 谓词）——整用户删除同语句覆盖父子行，无跨域悬挂面；D3 表行零残留断言覆盖（残留为零则悬挂为空真） | — | 否 |
| 身份/租户语义漂移 | 本波零新增身份语义：tenant/user 由请求体显式传入但**只在 AdminSyncAuth 通过后才生效**；admin/capability.py「替别人看一眼」先例同形态（管理面显式接受主体参数有先例） | — | 否 |

---

## 验收标准

- [ ] 人工闸：HG-AUDIT-R1 approved 后方可勾选下列码项（HG-GRAPH-MODULES 模块表已建置 approved · 本 task 图谱新签义务（admin 行备注 + api 行注册备注 + 人签新行 00 代录位）随 30 交付落盘；**若 30 偏离预判（新增一级模块 / 新增表列触发 alembic / 新增 SSE 事件类型 / 新建 DB 审计表 / 改状态机与 recall/revoke 既有语义）→ 回炉补闸**，见闸表与 graph_delta_note）

### D1 · service 层 purge（映射 SPEC §6-D1）

- [ ] `purge_by_user(tenant_id, user_id, *, dry_run=True, session=None)` 落 `app/ops/memory/service.py`；DELETE 谓词含且仅含 tenant_id+user_id（锚点断言）
- [ ] 全 status 整行删除：夹具含 active/superseded/revoked/expired 四态行 + 非 NULL embedding 行 → 实删后全部消失
- [ ] `dry_run=True`（默认）：表行零变化（前后计数对拍断言）· 返回 `scanned==匹配数, deleted==0, by_status` 计数守恒；实删 `deleted==scanned`
- [ ] 幂等：重复实删第二次 `deleted==0`；干跑/实删同谓词（计数口径一致断言）
- [ ] 审计日志：实删/干跑/幂等 0 行均产生 `memory purge_by_user` 动作日志，字段含 tenant/user/dry_run/affected，**不含** key/value（caplog 断言）

### D2 · 管理面入口（映射 SPEC §6-D2）

- [ ] `POST /admin/memory/purge` 注册且挂 `AdminSyncAuth`；未授权 → 401/403 且表行零变化
- [ ] 默认干跑：缺省 `dry_run` → 200 + 计数报告 + 表行零变化；响应 echo `dry_run`
- [ ] 双闸门：`dry_run=false` 缺 `expected_count` → 400 零删除；计数不等 → 409 零删除；计数等 → 200 实删成功且 `deleted==expected_count`
- [ ] 请求体 tenant/user 空串/空白 → 拒绝（strip 后空 = 400 · service.py :110-115 strip 先例对齐）

### D3 · 删除后断言（否决面 · 映射 SPEC §6-D3）

- [ ] 召回通路：实删后 `recall_active(tenant, user)` 返回空
- [ ] 向量通路：`MEMORY_FACTS_VECTOR_RECALL_ENABLED=true` + mock embedder → `recall_with_vector` 返回空
- [ ] 表行：`count(*) WHERE tenant+user == 0`（全 status 含 superseded/revoked/expired——逻辑失效行同样物理消失，不留「已失效但内容还在」的合规漏洞）
- [ ] 越域：他 tenant 同 user / 同 tenant 他 user 夹具行逐行不动；跨 tenant purge 调用 `deleted==0`

### D4 · 图谱 / 文档（映射 SPEC §6-D4）

- [ ] 零 alembic（迁移 diff 为空断言）；`docs/_tech_graph/l1/01_modules.md`：admin 行备注（POST /admin/memory/purge 首个 admin 面不可逆写端点 · 双闸门）+ api 行注册备注 + HG-GRAPH-MODULES 人签记录新行（00 代录）；`./scripts/graph-compile.sh` 绿；零新增表/一级模块/SSE 事件（偏离 → 回炉补闸 + SPEC 回炉）
- [ ] 文档：`app/ops/memory/README.md` 补 purge 语义（双闸门 · 幂等 · 审计不记内容）+ service docstring 补「物理删除走管理面 purge」

### 变异检验（不验收空真规则 · 映射 SPEC §6-变异检验）

- [ ] ① **谓词可检**：临时去掉 DELETE 的 tenant_id 谓词 → 「他 tenant 行不动」断言必挂；恢复后全绿
- [ ] ② **全量可检**：临时只删 `status='active'` 行（留 superseded/revoked/expired）→ 表行零残留断言必挂；恢复后全绿
- [ ] ③ **审计可检**：临时去掉 purge 审计日志 → caplog 断言必挂；恢复后全绿

### 工程（映射 SPEC §6-工程）

- [ ] **闸前置**：30 开工前旧测影响面清单已落盘且逐条有处置（回归/改编理由）——清单见下「旧测影响面清单（B1）」，30 逐条执行处置并在提交说明逐条回填
- [ ] 全量 `pytest tests` 绿（基线 **1333 collected** · 2026-09-22 本帽真跑；**无既有用例删除**，新增守护用例数如实入 40 记录）；`ruff check app tests` 绿（零新增告警口径）
- [ ] 生产路径 diff 白名单：`git diff master -- app/` 只含 service.py purge 函数 + admin/memory.py 新路由 + router.py 注册行 + 测试/图谱/文档

### 旧测影响面清单（B1 · 2026-09-22 10-task 实扫落盘）

> 扫描口径（真跑）：`ls tests/ | grep -iE 'memory|admin|auth'`（命中 11 文件：memory×7 / admin×3 / auth×1）· `grep -rn 'purge_by_user\|PurgeReport\|admin/memory' app/ tests/ evals/ docs/_tech_graph/`（**零命中**——新函数名/路由路径/报告类名无冲突；全仓 purge 命中仅 Dockerfile apt-get 与 SPEC 文档）· `grep -rn 'revoke_by_key\|revoke_by_source\|recall_active\|recall_with_vector\|MEMORY_FACTS_VECTOR_RECALL_ENABLED' tests/`（守护用例锚点逐个定位）· `grep -rn 'AdminSyncAuth\|require_admin_sync' tests/`（override 先例 3 文件）· 各文件 `def test_` 计数（memory_service_db 13 / memory_gate 15 / memory_injection 23 / memory_vector_p1 9 / memory_extract_p1 14 / memory_embedding_backfill 15 / memory_time_decay_tz 6 / admin_sync 10 / admin_capability_observability 12 / auth 10 · 均真跑）· `python -m pytest tests --collect-only -q`（=**1333**）。本波行为变更源裁定：**service.py purge 函数（纯新增）+ admin/memory.py 新路由（纯新增）+ router.py 注册行**；write/revoke/sweep/recall/向量召回/AdminSyncAuth 语义零改动（非范围钉死）——purge 是**纯新增能力零既有行为变更**，影响面以**回归**为主、**改编为零**（实扫确认：无任何既有用例依赖「ops_memory_facts 行不可物理删除」或「admin 面无写路由」的反向断言），**无测试删除**。处置三态：**回归**（不受影响，全量重跑确认）/ **改编**（本清单无）/ **删除**（本清单无）。

| # | 锚点 | 旧测/调用点现状 | 本波影响 | 处置 |
|---|------|----------------|----------|------|
| 1 | `tests/test_memory_service_db.py` 13 用例（revoke_by_source 零命中+幂等+审计 :133-163 · revoke_by_key 语义 :329-361 · 跨 tenant 隔离 :250-251 · 变异检验 revoke 消失 :365+） | 状态机/revoke/recall 守护（真 PostgreSQL · `mf-test-%` 租户夹具自清理）；revoke 审计 caplog 断言形态（:341 `"revoke_by_key" in caplog.text and "affected=1"`）= purge 审计断言**直接先例** | purge 纯新增不改 write/revoke/recall 语义（非范围钉死）→ 既有用例零改动全绿；purge 断言为新增（见 #10） | 回归（零改动）+ 新增 purge service 断言（新增义务 · 见 #10） |
| 2 | `tests/test_memory_vector_p1.py` 9 用例（向量融合召回 :122+ · revoke 后向量零命中 :238-244 · 开关非法值 warning :313-319） | 向量通路守护（mock embedder 先例 :234 fake embedder） | 向量召回语义零改动 → 零改动全绿；向量通路零命中断言为新增（见 #10 · mock embedder 先例直接复用） | 回归（零改动）+ 新增向量零命中断言（新增义务 · 见 #10） |
| 3 | `tests/test_memory_embedding_backfill.py` 15 用例（报告字段族 · 计数守恒 :72 注释钉死面 · 干跑模式 :106/:220） | 干跑/对账报告先例守护 | backfill 语义零改动；PurgeReport 字段族对齐其先例（钉死契约）→ 零改动全绿 | 回归（零改动） |
| 4 | `tests/test_memory_gate.py`（15）· `tests/test_memory_injection.py`（23 · off 对拍 :34/:45 先例）· `tests/test_memory_extract_p1.py`（14）· `tests/test_memory_time_decay_tz.py`（6） | 写入闸/注入装配/离线抽取/衰减守护 | 与本波正交（purge 不触闸/装配/抽取/衰减路径）→ 零改动全绿 | 回归（零改动） |
| 5 | `tests/test_admin_sync.py` 10 用例（无 cookie 401 :14-15 · viewer 403 :22-23 · Bearer 正/误/空 token :110-143 · 幂等重放 :73-77）· `tests/test_auth.py` :116-148（admin sync 鉴权三例） | AdminSyncAuth 既有语义守护（401/403/Bearer 三态） | 新路由复用同一 AdminSyncAuth 零新鉴权面 → 既有用例零改动全绿；新路由 401/403 断言沿用同形态（见 #10） | 回归（零改动）+ 新增 purge 路由鉴权断言（新增义务 · 见 #10） |
| 6 | `tests/test_admin_capability_observability.py` 12 用例 | `dependency_overrides[require_admin_sync] = lambda: None`（:31-35）= admin 路由测试 override **先例形态**；BASE = `/api/ops/admin/capability`（:27）路由前缀先例 | 新路由测试沿用同 override 形态（钉死契约 · 见 #10）；既有用例零改动 | 回归（零改动）+ 新增沿用 override 先例（见 #10） |
| 7 | `tests/test_hitl_resume.py`（:313/:319）· `tests/test_hitl_resume_events.py`（:180/:186） | AdminSyncAuth override 先例另两处 | 与 purge 路由正交 → 零改动全绿 | 回归（零改动） |
| 8 | `tests/test_graph.py`（:43）· `tests/test_issues.py`（:28/:60/:85）· `tests/test_pulls.py`（:28/:59）· `tests/test_admin_sync_sender.py` | admin sync 调用/sender 守护 | 与 purge 路由正交（sync payload 面零改动）→ 零改动全绿 | 回归（零改动） |
| 9 | `tests/eval/test_memory_preference_redline.py`（recall_active mock :61）· `tests/test_input_isolation_wiring.py`（recall_active mock :256） | evals/装配面 recall mock 守护 | purge 不触装配/evals 路径 → 零改动全绿 | 回归（零改动） |
| 10 | 新增义务：purge service 单测（干跑对拍零写 / 全 status 四态+embedding 行整删 / 幂等 deleted==0 / 审计 caplog 含 tenant/user/dry_run/affected 不含 key/value / 越 tenant·越 user 零影响 / 干跑实删同谓词口径）· admin 路由测（默认干跑 echo / 双闸门 400·409·200 三态 / 401·403 零删除 / 空白 tenant/user 400 / 500 不静默）· 删除后三断言（recall_active 空 · recall_with_vector 空（mock embedder）· 表行全 status 零残留）· 变异检验三条 | 当前不存在（`purge_by_user`/`PurgeReport`/`admin/memory` 全仓零命中实证） | 本波新增守护测试（工程验收项）；collected 自 1333 增加，新增数入 40 记录 | 新增（30 实现 · 40 核验） |
| 11 | alembic 链 | 本波**无迁移义务**（零新表零列 · 审计落既有 logger 面 · SPEC §4 A1 裁决） | 迁移 diff 为空断言入 D4 验收 | 无（零迁移钉死） |

---

## 依赖

| 依赖 | 说明 |
|------|------|
| SPEC | `docs/spec/memory-compliance-delete/SPEC-memory-compliance-delete_v1.md`（signed · HG-SPEC-SIGNOFF=approved 2026-09-22 · a65ce3b · S1 同步物理删除 + A1 日志审计 + 双闸门签收锁死） |
| 上游手册 | `../ops-desk-workspace/docs/08-interview/07_agent-memory-prompt-module-landscape_v1_zh.md`（手册 L7 删除权行 · §3.4 第三类「成熟度标志」时机裁定） |
| 编码规范 | `docs/standards/CODING_BACKEND_L2_v1_zh.md` |
| 图谱 | `docs/_tech_graph/l1/01_modules.md`（HG-GRAPH-MODULES 真值 · 2026-09-22 真读核验 · admin 行 :30 / memory 行 :28（无对外 HTTP 端点）/ api 行 :20 / 签录链至 :92） |
| 改造对象 | `app/ops/memory/service.py`（purge_by_user 新增）· `app/ops/admin/memory.py`（新增 · 目录实证无此文件）· `app/ops/router.py`（:4-5/:24-25 注册面） |
| 先例 · revoke 纪律 | `app/ops/memory/service.py:134-201`（revoke_by_source/revoke_by_key：逻辑失效 · tenant+user 谓词钉死 :176-177 · 幂等 · 审计记动作不记内容 :159-162/:197-200）· :10-11 session 纪律 · :110-115 strip 先例 |
| 先例 · AdminSyncAuth | `app/ops/deps.py:86-116`（require_admin_sync：compare_digest :98 · token 空 Bearer 禁用 :97-103 · maintainer 403 :105-111）· `app/ops/admin/sync.py:32`（挂法逐字对齐）· :35-45（500 不静默） |
| 先例 · 干跑报告字段族 | `scripts/memory_embedding_backfill.py` + `reports/memory_embedding_backfill/backfill_*.yaml`（字段族 + 计数守恒 :72 注释）· `reports/qdrant_migrate/reconcile_p1_*.yaml`（双侧计数对账） |
| 先例 · admin 路由测试 | `tests/test_admin_capability_observability.py:31-35`（require_admin_sync override 形态）· `tests/test_admin_sync.py:110-143`（Bearer 三态） |
| 先例 · 向量零命中断言 | `tests/test_memory_vector_p1.py:234-244`（mock embedder + revoke 后向量零命中形态） |
| 测试锚点 | `tests/test_memory_service_db.py` · `tests/test_memory_vector_p1.py` · `tests/test_admin_sync.py` · `tests/test_admin_capability_observability.py` · `tests/test_auth.py` |
| 格式基准 | `docs/tasks/done/task_security_input_isolation.md`（signed → done 五棒全通 · PR #161 · 本 task 格式对齐此） |

---

## 给执行帽的必读列表

1. `AGENTS.md`
2. 本 task（钉死契约 · 闸 · 非范围 · B1）
3. SPEC `docs/spec/memory-compliance-delete/SPEC-memory-compliance-delete_v1.md`（§1 锚点+时机裁定 / §2 D1–D4 / §3 非范围 / §4 方案裁决 S1+A1 / §5 failure_paths / §6 验收 / §7 residual）
4. `docs/standards/CODING_BACKEND_L2_v1_zh.md`
5. 代码：`app/ops/memory/service.py`（docstring :1-12 · :56-82 supersedes 谓词 · :110-115 strip · :134-201 revoke 双函数 · :266-528 向量通路）· `app/ops/deps.py:86-116`（AdminSyncAuth）· `app/ops/admin/sync.py`（:28-45 挂法+错误纪律先例）· `app/ops/admin/capability.py`（:60-76 「替别人看一眼」先例）· `app/ops/router.py`（:1-30）· `app/db/models.py:490-562`（ops_memory_facts 模型）
6. 先例：`tests/test_memory_service_db.py:329-361`（revoke_by_key 幂等/跨 tenant/caplog 审计范式）· `tests/test_memory_vector_p1.py:234-244`（mock embedder 向量零命中范式）· `tests/test_admin_capability_observability.py:31-62`（admin override + 鉴权断言范式）· `tests/test_admin_sync.py:110-163`（Bearer 三态范式）
7. 测试：`tests/test_memory_service_db.py` · `tests/test_memory_vector_p1.py` · `tests/test_admin_sync.py` · `tests/test_admin_capability_observability.py` · `tests/test_auth.py`
8. `docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`

---

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|----|------|------------|----------------------|----------------|
| R0 | SPEC signed（HG-SPEC-SIGNOFF=approved 2026-09-22 · a65ce3b）；范围 D1–D4 承 SPEC §2 不重开辩论；本帽实扫复核：分支正确（`task/memory-compliance-delete`）· service.py docstring :7「不物理删」/ :10-11 session 纪律 / :110-115 strip / revoke_by_source :134-163 / revoke_by_key :166-201（谓词 :176-177 · 审计 :197-200）· deps.py AdminSyncAuth :86-116（compare_digest :98 · token 空禁用 :97-103）· admin/sync.py :32/:35-45 · models.py CHECK :500-503/supersedes :545-549/embedding :558-560 · router.py :4-5/:24-25 · admin/ 目录无 memory.py（ls 实证）· memory/README.md 存在 · 命名冲突扫零命中 · pytest 基线 **1333 collected**（真跑）——SPEC §1 锚点全部复核一致 | no | — | none |
| R1 | 开工闸：HG-TASK-DRAFT / HG-AUDIT-R1 落稿时待签（10 帽不签 · blocks 30 未放行）· HG-GRAPH-MODULES=approved（模块表已建置 · **真读** `01_modules.md`：admin 行 :30 · memory 行 :28（无对外 HTTP 端点 · purge 首个对外入口落 admin 模块内）· api 行 :20 · 签录链至 :92）+ **新签义务**（admin 行备注 + api 行注册备注 + 人签新行 00 代录位随 30 交付落盘）+ 偏离回炉补闸条款 · HG-PILOT-OPSDESK-GLAYER=n/a | no | — | 无 |
| R2 | 竖切：D1–D4 同 task 一次提交（承 SPEC §8 序：D4 图谱 → D1 purge → D2 admin 路由 → D3 断言）；方案对比继承 SPEC §4 两组裁决（S1 同步物理删除弃 S2 软删+异步 purge · A1 落既有 logger 面弃 A2 新审计表），不重演 | no | — | 无 |
| R3 | failure_paths **13 条** = SPEC §5 十条翻四列 + 过程三（闸未签拒开工 · B1 闸前置拒收 · 缺断言/变异检验拒收）；两不可逆错（误删/越 tenant）防线全在闸前与断言层（双闸门 + 谓词断言 + 变异检验），删后不可恢复如实定性；删一半中断由单语句原子性消除；审计缺位静默错有 caplog 断言 + 变异检验③兜底 | no | — | 无 |
| R4 | 验收 **22 条**全否定性断言化逐块映射 SPEC §6（人工闸 1 / D1×5 / D2×4 / D3×4 / D4×2 / 变异检验×3 / 工程×3）；B1 实扫 **11 行**落盘（回归×9 · 改编×0 · 新增×1 · 迁移无×1 · 删除×0）；关键实证：`purge_by_user`/`PurgeReport`/`admin/memory` 全仓零命中（无命名冲突）· 无任何既有用例依赖「行不可物理删除」反向断言 → 改编面为零钉死 | no | — | 双闸门防不住计数碰巧相等的错目标（承 SPEC §7 ① · 管理面人工纪律兜底如实承认） |
| R5 | 可交 20-task-audit；与 SPEC 实质差异为零（B1 / 闸行留痕 / 基线数 / 锚点行号复核均为过程化落地）；HG-TASK-DRAFT 与 HG-AUDIT-R1 落稿时待签 | no | — | ① 双闸门只锁数量不锁主体（承 SPEC §7 ①）；② 同计数内容替换竞态（承 SPEC §7 ②）；③ 审计日志面不可机查台账（承 SPEC §7 ③ · 合规要机查台账时回 10-spec 升级 A2）；④ 删除权受理/核验（谁有权替用户发起）不在本 task（承 SPEC §7 ④ · DSR 编排另案） |

**actual_last_round**：R5 · **early_stop**：no · **residual_risks**：见 R4/R5

### R0 · 问题框定

SPEC 已签收（S1 同步物理删除 + A1 日志审计 + 默认干跑双闸门锁死），本 task 只做可执行化拆解：P0 状态机全为逻辑失效，物理删除零既有实现只有纪律可沿用（SPEC §1 实扫锁死）。本帽实扫复核：分支 `task/memory-compliance-delete` 正确；`revoke_by_source`（:134-163）/`revoke_by_key`（:166-201）均为 `UPDATE ... SET status='revoked'` 逻辑失效（docstring :7 明示不物理删）；tenant+user 谓词纪律（:176-177）与审计记动作不记内容先例（:159-162/:197-200）在位；session 纪律（:10-11）与 strip 先例（:110-115）在位；AdminSyncAuth（deps.py:86-116 · compare_digest :98 · token 空 Bearer 禁用 :97-103 · maintainer 403 :105-111）与挂法先例（admin/sync.py:32）、500 不静默先例（:35-45）逐行复核一致；ops_memory_facts 模型 CHECK 四值（:500-503）/ supersedes FK SET NULL（:545-549）/ embedding deferred 列（:558-560）复核一致；router.py :4-5/:24-25 注册面复核；`app/ops/admin/` ls 实证**无 memory.py**（新增义务）；`app/ops/memory/README.md` 存在（D4 文档落点）；`purge_by_user`/`PurgeReport`/`admin/memory` 全仓**零命中**（无命名冲突）；pytest 基线 **1333 collected**（真跑）。SPEC §1 锚点复核**零语义偏差**。

### R1 · 开工闸

HG-TASK-DRAFT / HG-AUDIT-R1 落稿时待签（10 帽不签 · blocks 30 未放行 → **30 拒开工**）；HG-GRAPH-MODULES **真读** `docs/_tech_graph/l1/01_modules.md` 核验：模块表已建置（bootstrap 签 2026-07-16 · 签录链完整至 :92 security-input-isolation 行）；`admin` 行（:30 · `app/ops/admin/**` → db · Bearer 机读 token + cookie maintainer 双口径）· `memory` 行（:28 · ops_memory_facts · **无对外 HTTP 端点**——purge 是 memory 首个对外入口但落在 admin 模块内 · 零新开一级模块）· `api` 行（:20 · router.py 注册面）均在表。SPEC §2 D4 判**有图谱义务按实判**：admin 行备注（POST /admin/memory/purge 首个 admin 面不可逆写端点 · 双闸门）+ api 行注册备注 + 人签记录**新行留 00 代录位**（随 30 交付落盘 · llm-layer-hardening/session-summary-fallback/security-input-isolation 先例）——不新增一级模块/表/SSE 事件，义务钉 D4 验收不阻塞 30 开工形态预判；**回炉补闸条款**钉死（偏离 → 退 10-spec + 补闸 + 图谱如实登记）。HG-PILOT-OPSDESK-GLAYER=n/a。

### R2 · 竖切

D1–D4 是不可拆语义单元：purge 函数不配双闸门入口 = 能力无触发面（SPEC 保守形态裁定落空）；不配删除后断言 = 违反「先把坏了能发现装上」；不配图谱登记 = admin 面首个不可逆写端点无真值留痕。耦合面小（一个函数 + 一个路由文件 + 注册行 + 测试/图谱/文档），单 PR 不巨型。实现序承 SPEC §8：D4 图谱 → D1 purge 函数 → D2 admin 路由 → D3 断言收口。方案对比不重演，直接继承 SPEC §4 两组裁决（S1 同步物理删除弃 S2 软删+异步 purge：alembic 新列+worker 基础设施 vs 收益≈零且与非范围冲突 · A1 落既有 logger 面弃 A2 新审计表：全仓无先例且信息无增量且触发 alembic 义务）。

### R3 · 失败语义

SPEC §5 十条失败面全收并翻四列：两不可逆错（误删 / 越 tenant）防线全在闸前与断言层——删后不可恢复如实定性（不虚假承诺可挽回）；删一半中断由单语句单事务原子性消除（无中间态）；审计缺位为静默错有 caplog 断言 + 变异检验③兜底；向量通路残留由「embedding 是表内列随行删除 + 向量 SQL 查表本身」结构性消除 + D3 断言 + 变异检验②兜底；dry_run 误用由对拍断言 + echo 标志钉死；expected_count 竞态 409 拒 + 同计数内容替换不可区分列残余风险；未授权零删除断言；supersedes 自引用 FK 同语句覆盖父子行无悬挂面。补过程三行：闸未签拒开工 · B1 未落盘拒收 · 缺干跑对拍/双闸门三态/两通路零命中/越域/审计/幂等/变异检验三条任一拒收（防空真规则）。

### R4 · 可测性

验收 **22 条**全部可执行断言：谓词锚点断言 · 全 status 四态+embedding 行整删 · 干跑对拍零写+计数守恒 · 幂等 deleted==0 · 审计 caplog 含字段不含内容 · 双闸门 400/409/200 三态 · 401/403 零删除 · 空白 400 · recall_active 空 · recall_with_vector 空（mock embedder）· 表行全 status 零残留 · 越域逐行不动+跨 tenant 0 行 · 零 alembic diff 为空 + 图谱三处登记 + graph-compile 绿 · 文档同步 · 变异检验三条 · pytest/ruff/diff 白名单。B1 实扫落盘 **11 行**：回归×9 · **改编×0**（purge 纯新增零既有行为变更 · 无既有用例依赖「行不可物理删除」反向断言）· 新增×1（守护测试义务 #10）· 迁移无×1（#11 零 alembic 钉死）· **删除×0**。

### R5 · 交付判定

可交 20-task-audit：与 SPEC 实质差异为零（B1 实扫落盘 / 闸行留痕 / pytest 基线数 / 锚点行号复核均为过程化落地，无范围/验收/非范围语义偏移）；HG-TASK-DRAFT 与 HG-AUDIT-R1 落稿时待签（10 帽不签）；残余风险四条承 SPEC §7 如实携带（双闸门只锁数量不锁主体 · 同计数内容替换竞态 · 审计日志面不可机查台账 · 删除权受理核验另案），无新增风险。

### 自检结论

本稿：范围/非范围/验收/failure_paths 逐块映射 SPEC（§2→范围 · §3→非范围 · §5→failure_paths+过程三 · §6→验收 22 条）；钉死契约自 SPEC §2/§4 锁死不重开辩论；B1 实扫落盘 11 行处置三态齐全；闸表四行（HG-TASK-DRAFT 落稿时待签 · HG-AUDIT-R1 落稿时待签 blocks 30 · HG-GRAPH-MODULES 模块表已建置 approved+新签义务 · HG-PILOT-OPSDESK-GLAYER n/a）；R0–R5 全轮无 early_stop；可交 20-task-audit。

**40 核验结论（2026-09-22 · PASS 22/22）**：全量 pytest 1345 passed/3 failed/1 skipped（collected 1349=1333+16 真跑复核；3 红经 git worktree @ origin/master 10d72e7 + 同 .env 实证为基线环境性：capability proxy urllib + chat_ws×2）；谓词防线读码成立（`_purge_predicate` 含且仅含 tenant+user · count/DELETE 共用同一谓词对象 → 干跑/实删同口径结构性保证）；双闸门三态亲跑（400 零删除 / 409 零删除 detail.current_count / 200 deleted==expected · 重放→409）；审计 caplog 断言记动作不记内容亲核（字段含 tenant/user/dry_run/affected · 无 key/value 参数位）；AdminSyncAuth 挂载逐字对齐 admin/sync.py:32；变异检验①40 亲复（去 tenant 谓词 → 2 failed → 还原 16/16 绿 · 工作树净 · ②③采信 30 留痕）；ruff 57=基线 57（worktree 对拍）；graph-compile 绿（graph.json 时间戳漂移已还原）；alembic diff=0；diff 白名单无越界；B1 抽 5 行亲跑全符；图谱 admin/api 行备注 + HG-GRAPH-MODULES 新行 ratify（741f585）真读核验。证据全文：`docs/harness/invokes/by-task/memory-compliance-delete/invoke_20260922_40_verify_memory_compliance_delete.md`。

---

## 修订记录

| 日期 | 摘要 |
|------|------|
| 2026-09-22 | 10-task 落稿（SPEC signed a65ce3b 后 · 本棒由 00 委派 10-task 帽 Agent 执行）：锚点逐个复核（revoke 逻辑失效纪律沿用 · AdminSyncAuth :86-116 · admin/sync.py :32/:35-45 · models :500-560 · router :4-5/:24-25 · admin/ 无 memory.py · memory/README.md 存在 · 命名冲突零命中 · 基线 1333 collected 真跑）；验收 22 条断言化映射 SPEC §6；failure_paths 13 条（SPEC §5 十条 + 过程三）；B1 实扫 11 行（回归×9 · 改编×0 · 新增×1 · 迁移无×1 · 删除×0）；HG-GRAPH-MODULES 真读核模块表（admin :30 / memory :28 / api :20 · 签录链至 :92）+ 新签义务 00 代录位 + 偏离回炉条款；HG-TASK-DRAFT / HG-AUDIT-R1 落稿时待签 |
| 2026-09-22 | 40 核验 **PASS（22/22 亲核）**：pytest 1345/3/1（3 红 worktree @ 10d72e7 实证基线环境性）· 谓词防线读码（含且仅含 tenant+user · 同谓词同口径）· 双闸门三态+重放 409 亲跑 · 审计 caplog 记动作不记内容亲核 · AdminSyncAuth 逐字对齐 · 变异①亲复（2 挂→还原绿 · 树净）· ruff 57=基线 · graph-compile 绿（漂移还原）· alembic diff=0 · B1 抽 5 行+图谱 ratify 741f585 真读全符 · invoke：`invoke_20260922_40_verify_memory_compliance_delete.md` |
