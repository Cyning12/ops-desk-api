# SPEC：记忆合规物理删除权（v1）

> **状态**：`signed`（HG-SPEC-SIGNOFF=**approved** · 2026-09-22 · 维护者授权 00 本窗代录签收 · 原话「此spec完成后继续把完成后续spec，一个个进行，每次PR到main通过CI后自动merge」承前令「授权00签收所有过程文档」）
> **track**：`feature`（新增管理面不可逆删除能力 · **本波无 alembic 义务** · 图谱义务有按实判见 §2 D4）
> **上游**：`../ops-desk-workspace/docs/08-interview/07_agent-memory-prompt-module-landscape_v1_zh.md`（手册 L7 删除权行 · §3.4 第三类「成熟度标志」）
> **格式基准**：`docs/spec/security-hardening/SPEC-security-hardening_v1.md`（signed · 2026-10-13）
> **下游**：人签 SPEC → 00 出 task → 20-task-audit → HG-AUDIT-R1 → 30 实现
> **Open Folder（实现）**：`ops-desk-api/`

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **spec_slug** | `memory-compliance-delete` |
| **invoke_slug** | `memory-compliance-delete` |
| **test_strategy** | `required` |
| **test_strategy_note** | 干跑/实删对拍断言（干跑零行变化 · 响应 echo dry_run 标志）· 双闸门断言（缺 expected_count → 400 · 计数不等 → 409 零删除）· 删除后三断言（确定性召回零命中 · 向量通路零命中 · 表行零残留含全部 status）· 越 tenant/user 谓词断言（跨 tenant 调用影响 0 行 · 原行不动）· 审计留痕断言（动作级日志存在 · 不含内容）· 幂等断言（重复实删影响 0 行）· 变异检验三条（见 §6）· 全量 pytest 绿 |
| **Open Folder（实现）** | `ops-desk-api/` |
| **默认分支** | `task/memory-compliance-delete` |
| **graph_change_layer（建议）** | **有图谱义务按实判**：新增 admin 路由 `POST /admin/memory/purge`（`app/ops/admin/` 既有一级模块内 · 零新开一级模块）——须落 `docs/_tech_graph/` 路由面 + HG-GRAPH-MODULES 行（30 前须 approved）。零新表/零新列/零 SSE 事件类型。若 30 形态偏离（新表/新一级模块/新事件）→ 回 10-spec 修订 |

### 人工闸（SPEC 阶段）

| human_gate_id | status | 说明 |
|---|---|---|
| **HG-SPEC-SIGNOFF** | pending | 维护者签收本 SPEC 后方可 00 出 task / 30 改码（人签，不由 10-spec 代签） |
| **HG-GRAPH-MODULES** | pending | 新增 admin 路由落 `docs/_tech_graph/` 路由面；30 前须 approved |

---

## 1. 背景与目标

P0 状态机（active/superseded/revoked/expired）全部为**逻辑失效**，物理删除未做（P0 §3 非范围预留）。企业合规场景（用户行使删除权）需要按 user 物理删除的能力。占位注「有合规要求/真实流量前不做」（手册 §3.4 第三类「成熟度标志」）。

### 时机裁定（手册 §3.4 第三类 → 现在做的理由与保守形态）

**裁定：现在做，但落地形态取保守双闸门。** 理由：① **用户令队列推进**——维护者把本 slug 从占位表取出立项（排序依据「缺了会不会造成不可逆/静默的错」：删除权缺位意味着 revoked 行连内容带 embedding 永久留表，恰是合规面不可逆缺口）；② **前置已全部就绪**——revoke_by_key 先例（memory-preference-profile 刚交付）证明 tenant+user 谓词纪律与审计日志形态已稳定，物理删除是其语义延伸而非新地基；③ **保守形态兜住「真实流量前」的顾虑**——管理面默认干跑（dry_run=true），实删须先干跑取计数、再携 matching `expected_count` 双闸门提交，计数不等 409 零删除；无用户自助端点、无批量全表面、无定时 purge worker。即「能力实现，触发面收到最小」。

### 现状（2026-10-13 实扫 · 锚点逐个核）

| 锚点 | 实扫结论 |
|---|---|
| `app/ops/memory/service.py` revoke 语义 | `revoke_by_source`（:134-163）/ `revoke_by_key`（:166-201）：均为 `UPDATE ... SET status='revoked'` **逻辑失效**——只动 active 行、幂等（重复调用 0 行）、审计 `logger.info` 记动作与影响行数（**记动作不记内容**先例 :159-162/:197-200）、`revoke_by_key` 必带 tenant+user 谓词（跨 tenant = 0 行，:176-177 docstring 钉死）。docstring :7 明示「失效走状态机，**不物理删**」——物理删除是本 SPEC 新增能力，无既有实现可复用，只有纪律可沿用 |
| `app/ops/admin/` 鉴权先例 | `AdminSyncAuth`（deps.py :86-116 `require_admin_sync`）：Bearer `OPS_ADMIN_SYNC_TOKEN`（`secrets.compare_digest` 比对 · token 为空则 Bearer 路径禁用 · 禁写日志）或 cookie maintainer 角色；已挂 `admin/sync.py`（:32）、`admin/capability.py`（:80/:165/:218/:230/:257）、`hitl/router.py` 共 8 处——**admin 面鉴权口径唯一且成熟**，本 SPEC 直接对齐零新鉴权面 |
| admin 路由实扫 | `app/ops/router.py` :4-5/:24-25 注册 `admin_sync_router` + `admin_capability_router`；admin/capability.py 展示只读自检面（runtime/metrics · Principal 按待观测主体构造 :60-76 「替别人看一眼」先例——管理面操作显式接受 tenant/user 参数有先例）；**admin 面目前零写操作路由**，本 purge 是 admin 面首个不可逆写端点 |
| `ops_memory_facts` 模型 | models.py :490-562：`embedding` 列（:558-560 · Vector(1024) nullable **deferred=True** · P1 向量召回用）；`supersedes` 自引用 FK `ondelete="SET NULL"`（:545-549 · 只在同 (tenant,user,key) 内置链，见 service :56-82 谓词）；status CHECK 四值（:500-503）；召回索引 (tenant,user,key,status)（:510-516）。整行物理 DELETE 天然覆盖 embedding 列——**向量残留 = 行残留，两通路同源** |
| 审计面现状 | 全仓 grep `audit`：**零 DB 审计表、零审计模块**；唯一审计形态 = memory service 的 `logger.info` 动作日志（revoke_by_source/revoke_by_key 先例）+ capability/task_writer 注释引用评审文。审计落既有日志面是唯一与现状一致的选项（方案对比见 §4） |
| 向量通路 | service.py P1（:266-528）：`_VECTOR_RECALL_SQL`（:281-289）裸 SQL 查 `ops_memory_facts` 表本身（cosine `<=>` · 必带 tenant/user/active/未过期谓词）；`_vector_top_m` ORM 补取**再次**带全谓词（:461-469 双保险）；向量失败回退确定性 + span `memory_vector_degraded`（:494-501）。**向量与确定性两通路同查一张表**——物理删行后两通路零残留是同一件事的两个观察面，断言须分别覆盖 |
| 干跑/对账报告先例 | `scripts/memory_embedding_backfill.py` + `reports/memory_embedding_backfill/backfill_*.yaml`：`status/dry_run/scanned/skipped/failed/failed_ids/elapsed_s/recorded_at` 字段族 + **计数守恒** `embedded+skipped+failed==scanned`（:72 注释钉死）+ 退出码语义（0=pass/1=partial/2=前置失败）；`reports/qdrant_migrate/reconcile_p1_*.yaml`：双侧计数对账（pg_count vs qdrant_count · count_diff=0 判 pass）。本 SPEC 干跑响应沿用此字段族与守恒纪律 |

### 一句话目标

为 ops_memory_facts 提供**按 (tenant_id, user_id) 的整行物理删除**能力：service 层幂等 `purge` 函数 + admin 面入口（AdminSyncAuth 对齐 · **默认干跑 + expected_count 双闸门**）+ 动作级审计留痕（记动作不记内容）；删除后**召回/向量两通路零命中 + 表行零残留 + 越 tenant 零影响**全部断言化；逻辑状态机语义零改动。

---

## 2. 范围

### D1 · service 层物理删除（必做 · 核心）

| 项 | 约定 |
|---|---|
| 落点 | `app/ops/memory/service.py` 新增 `purge_by_user(tenant_id, user_id, *, dry_run=True, session=None) -> PurgeReport`（既有模块内 · 零新开一级模块；与 write/revoke/sweep/recall 同 module docstring 纪律面） |
| 删除语义 | `DELETE FROM ops_memory_facts WHERE tenant_id=:t AND user_id=:u`——**全 status 行整行删除**（active/superseded/revoked/expired 无差别 · embedding 列随行消失）；必带 tenant+user 双谓词（revoke_by_key :176-177 纪律钉死 · 跨 tenant = 0 行） |
| 干跑语义 | `dry_run=True`（**默认**）：同谓词 `SELECT count(*) + count by status`，零写；实删与干跑同谓词保证计数口径一致 |
| 审计留痕 | `logger.info("memory purge_by_user tenant=%s user=%s dry_run=%s affected=%d", ...)`——**记动作不记内容**（无 key/value · revoke 先例 :159-162 同形）；含幂等 0 行调用 |
| 幂等 | DELETE 天然幂等：重复实删第二次影响 0 行（与 revoke 幂等语义同形 · 断言化） |
| 事务 | 单条 DELETE 语句单事务原子执行；session 纪律沿用模块先例（传入 session 调用方持事务只 flush · 不传自开 `AsyncSessionLocal` 并 commit · service.py :10-11 docstring 先例） |
| 返回 | `PurgeReport` dataclass：`dry_run/scanned(=匹配行数)/deleted/by_status/elapsed_s/recorded_at`（backfill 报告字段族 · 计数守恒：实删 `deleted==scanned` · 干跑 `deleted==0`） |

### D2 · 管理面入口（必做 · AdminSyncAuth 对齐 · 双闸门）

| 项 | 约定 |
|---|---|
| 路由 | `POST /admin/memory/purge`（新文件 `app/ops/admin/memory.py` · `app/ops/router.py` 注册 · tags=["admin"]） |
| 鉴权 | `_user: OpsUser | None = AdminSyncAuth`（admin/sync.py :32 先例逐字对齐 · 零新鉴权面） |
| 请求体 | `{tenant_id, user_id, dry_run: bool = true, expected_count: int | None = null}` |
| 双闸门 | ① **默认干跑**：`dry_run` 缺省/显式 true → 只返回计数报告零写；② **实删须范围确认**：`dry_run=false` 时 `expected_count` 必填（缺 → 400），与当前匹配计数**不等 → 409 零删除**（调用方重新干跑）——dry-run→confirm 两段式把「删多少」变成显式对账而不是盲发 |
| 竞态语义 | expected_count 不等即拒（dry-run 后有新写入/其他删除 → 计数漂移 → 409）；**同计数内容替换**（时间窗内同数新行换旧行）不可区分，列 §7 残余风险（管理面低频操作可接受） |
| 响应 | 200 + PurgeReport JSON（echo `dry_run` 标志 · by_status 计数）；400 缺 expected_count；409 计数不等；401/403 鉴权失败（AdminSyncAuth 既有语义） |
| 错误纪律 | 500 不静默：异常 rollback + `logger.exception` + HTTPException（admin/sync.py :35-45 先例同形） |

### D3 · 删除后断言（必做 · 验收否决面）

| 断言 | 形态 |
|---|---|
| 召回通路零残留 | 实删后 `recall_active(tenant, user)` 返回空（单测 · 事前有 active 行夹具） |
| 向量通路零残留 | `MEMORY_FACTS_VECTOR_RECALL_ENABLED=true` + mock embedder 下 `recall_with_vector` 返回空；向量 SQL 查表本身，行不在即零命中（embedding 列随行删除 · 无独立向量库残留面） |
| 表行零残留 | `count(*) WHERE tenant_id=:t AND user_id=:u == 0`（**全 status** 含 superseded/revoked/expired——逻辑失效行同样物理消失，不留「已失效但内容还在」的合规漏洞） |
| 越 tenant 拒绝 | 他 tenant 同 user_id / 同 tenant 他 user_id 夹具行**逐行不动**；跨 tenant 调用影响 0 行（revoke_by_key 谓词纪律同断言形态） |
| 审计存在 | 实删与干跑均产生动作级日志（caplog 断言 · 字段含 tenant/user/dry_run/affected · **不含** key/value 内容） |

### D4 · 图谱 / 文档（必做 · 按实判）

- **alembic 义务：无**（零新表零新列 · 纯 DELETE + 只读计数；审计落既有 logger 面不落新表——方案对比 §4 A 面裁决）。
- **图谱义务：有（按实判）**。新增 admin 路由 `POST /admin/memory/purge` 落 `docs/_tech_graph/` 路由面 + HG-GRAPH-MODULES 行（30 前须 approved）；不新增一级模块/表/SSE 事件类型；`./scripts/graph-compile.sh` 绿。若 30 形态偏离 → 回 10-spec 修订。
- 文档同步：`app/ops/memory/README.md`（若存在该模块说明）或 service docstring 补 purge 语义与双闸门纪律；admin 面文档补端点；不回改 done/归档历史文档。

---

## 3. 非范围

- ❌ **删除其它业务表数据**（ops_threads/ops_runs/checkpoints/ops_users 等任何表 · 本 SPEC 只覆盖 ops_memory_facts）
- ❌ **DSR 全流程自动化**（删除权请求的受理/核验/多表编排/SLA 工单 · 另案）
- ❌ **改逻辑状态机**（active/superseded/revoked/expired 语义 · write/revoke/sweep/recall 行为零改动 · revoke 仍是运行期纠错唯一入口，purge 只走管理面）
- ❌ **用户自助端点**（非 admin 面的任何删除入口 · 本波仅管理面 + 双闸门）
- ❌ **批量/全表 purge**（无 tenant 级、无全表级、无定时 purge worker · 最小粒度 = 单 (tenant,user)）
- ❌ **RAG 知识库/Qdrant 数据删除**（`ops_memory_facts` embedding 是表内列随行删除；知识库 chunks/Qdrant 集合删除另案）
- ❌ **Langfuse/trace 侧数据删除**（观测面数据生命周期另案）
- ❌ **新建 DB 审计表**（方案对比 §4 A 面裁决落既有日志面 · 若未来合规要求机查审计台账 → 回 10-spec 修订）
- ❌ 前端/管理台 UI（本波纯 API 面）
- ❌ 历史文档回改

---

## 4. 方案对比（R2）

### 删除执行形态（D1 · 核心裁定）

| 方案 | 做法 | 收益 | 代价 | 裁决 |
|---|---|---|---|---|
| **S1 · 同步物理删除（本 SPEC）** | service 层单事务 `DELETE ... WHERE tenant+user`，管理面同步调用返回计数 | 语义最直接（删除权 = 行不在）；单语句原子（无删一半中间态）；幂等天然成立；两通路零残留 = 行零残留，断言链最短；单用户行数有界（闸限标量值 + top-N 召回预算），同步删除无时延/锁风险 | 不可逆（由 D2 双闸门 + D3 断言兜） | **推荐** |
| S2 · 软删标记 + 异步 purge worker | 新增 `purged` 态/标记列 → 后台 worker 定期物理清 | 删除请求快返；误删有挽回窗 | ** alembic 新列 + worker 基础设施**（队列/调度/失败重试面全新增）；状态机 CHECK 要扩（改逻辑状态机 = 非范围冲突）；软删窗口期内内容仍在表 = 合规语义打折；单用户行数有界，异步化收益≈零 | 弃（成本全在基础设施 · 收益为零 · 与非范围冲突） |

### 审计留痕落点（D1/D4 · 裁定）

| 方案 | 做法 | 收益 | 代价 | 裁决 |
|---|---|---|---|---|
| **A1 · 落既有 logger 面（本 SPEC）** | `logger.info` 动作级日志（tenant/user/dry_run/affected/recorded_at · **不记内容**）——revoke_by_source/revoke_by_key 既有先例同形 | 与全仓唯一审计形态一致（实扫：零 DB 审计表零审计模块）；零 alembic；日志管道（采集/轮转/告警）既有 | 日志轮转后不可机查台账（列 §7 残余风险 · 合规要求机查台账时回 10-spec 升级 A2） | **推荐** |
| A2 · 新建审计表（如 ops_memory_purge_audits） | alembic 新表 · 删除同事务插审计行 | 台账可机查可 JOIN；事务内同生共死 | 全仓无任何 DB 审计表先例，为单端点引入新表 + 新模型 + 迁移面不成比例；「记动作不记内容」纪律下表内容 = 日志内容同信息，无增量价值 | 弃（现状无先例 · 信息无增量 · 触发 alembic 义务） |

---

## 5. 边界 / 失败路径 / 安全（failure_paths）

| 触发 | 行为 | 可重试 |
|---|---|---|
| **误删**（范围确认缺失/错填 tenant/user → 删错人） | **不可逆错**；防线三层：① dry_run 默认 true（盲发只读）；② 实删必须 `expected_count` 与当前匹配计数一致否则 409 零删除——「删多少」显式对账；③ 审计日志记动作可追查。残余：计数碰巧相等且确为错目标 → 双闸门不可防，列 §7 ①（管理面人工操作纪律兜底：先干跑核对计数再实删） | N（删后不可恢复 · 防在闸前） |
| **越 tenant / 越 user 删除**（谓词漏带 → 跨域行被删） | **不可逆 + 静默错**；DELETE 必带 tenant+user 双谓词（revoke_by_key :176-177 纪律钉死）；D3 断言他 tenant/他 user 夹具行逐行不动、跨 tenant 调用影响 0 行；变异检验 ① 兜底（临时去谓词 → 断言必挂） | Y（修谓词 · 已删不可恢复故防线全在断言层） |
| **删一半中断**（进程崩溃/DB 断连 mid-delete） | 单条 DELETE 语句单事务原子执行——**不存在半删中间态**（要么全删要么全留）；异常 rollback + logger.exception + 500（admin/sync.py :35-45 先例）；重入安全：重跑删剩余行（幂等 · 第二次起影响 0 行） | Y（重发请求） |
| **审计缺位**（删除执行了但无留痕） | **静默错**；审计日志在 purge 函数内强制记录（实删/干跑/幂等 0 行全含 · revoke :159-162 先例同形）；D3 caplog 断言审计字段存在且不含内容；变异检验 ③ 兜底（临时去日志 → 断言必挂） | Y（补日志） |
| **向量通路残留**（行删了 embedding 还留在某处） | embedding 是表内列（models.py :558-560 · 无独立向量库存储 memory facts），整行 DELETE 随行消失；向量 SQL 查表本身（:281-289）——行不在即零命中；D3 向量通路零命中断言 + 变异检验 ②（只删 active 行 → 零残留断言必挂） | Y |
| **dry_run 标志误用**（dry_run=true 却真删 / 响应不 echo 标志致调用方误判） | 干跑路径零写（对拍断言：干跑前后表行计数逐字节一致）；响应 echo `dry_run` 字段；实删/干跑同谓词同计数口径（口径漂移 = 409 误拒，灰度期暴露） | Y（修代码） |
| **expected_count 竞态**（dry-run 后实删前有新写入/其他删除） | 计数不等 → 409 零删除 + 调用方重新干跑；同计数内容替换（时间窗内同数新行换旧行）不可区分 → 列 §7 ②（管理面低频操作可接受） | Y（重新干跑） |
| **未授权调用** | AdminSyncAuth 既有语义：Bearer 比对 `secrets.compare_digest`（token 空则 Bearer 路径禁用）/ cookie maintainer 角色，否则 401/403；未授权请求零删除（断言） | Y（带凭证重试） |
| **supersedes 自引用 FK 悬挂** | `supersedes` FK `ondelete="SET NULL"`（models.py :545-549）且只在同 (tenant,user,key) 内置链（service :56-82 谓词）——整用户删除同语句覆盖父子行，无跨域悬挂面；D3 表行零残留断言覆盖（残留为零则悬挂为空真） | — |
| 身份/租户语义漂移 | 本波零新增身份语义：tenant/user 由请求体显式传入但**只在 AdminSyncAuth 通过后才生效**；admin/capability.py :60-76「替别人看一眼」先例同形态（管理面显式接受主体参数有先例） | — |

安全：无新凭证面（复用 OPS_ADMIN_SYNC_TOKEN / maintainer cookie）；无新网络面/对外端点（admin 前缀既有）；**首个 admin 面不可逆写端点**——双闸门 + 审计断言为本 SPEC 核心否决面；审计日志不含 fact 内容（无 PII 泄漏面）；干跑为只读面。

---

## 6. 验收标准（task 直接可用）

### D1 · service 层 purge

- [ ] `purge_by_user(tenant_id, user_id, *, dry_run=True, session=None)` 落 `app/ops/memory/service.py`；DELETE 谓词含且仅含 tenant_id+user_id（锚点断言）
- [ ] 全 status 整行删除：夹具含 active/superseded/revoked/expired 四态行 + 非 NULL embedding 行 → 实删后全部消失
- [ ] `dry_run=True`（默认）：表行零变化（前后计数对拍断言）· 返回 `scanned==匹配数, deleted==0, by_status` 计数守恒
- [ ] 幂等：重复实删第二次 `deleted==0`；干跑/实删同谓词（计数口径一致断言）
- [ ] 审计日志：实删/干跑/幂等 0 行均产生 `memory purge_by_user` 动作日志，字段含 tenant/user/dry_run/affected，**不含** key/value（caplog 断言）

### D2 · 管理面入口

- [ ] `POST /admin/memory/purge` 注册且挂 `AdminSyncAuth`；未授权 → 401/403 且表行零变化
- [ ] 默认干跑：缺省 `dry_run` → 200 + 计数报告 + 表行零变化；响应 echo `dry_run`
- [ ] 双闸门：`dry_run=false` 缺 `expected_count` → 400 零删除；计数不等 → 409 零删除；计数等 → 200 实删成功且 `deleted==expected_count`
- [ ] 请求体 tenant/user 空串/空白 → 拒绝（strip 后空 = 400 · service.py :110-115 strip 先例对齐）

### D3 · 删除后断言（否决面）

- [ ] 召回通路：实删后 `recall_active(tenant, user)` 返回空
- [ ] 向量通路：`MEMORY_FACTS_VECTOR_RECALL_ENABLED=true` + mock embedder → `recall_with_vector` 返回空
- [ ] 表行：`count(*) WHERE tenant+user == 0`（全 status）
- [ ] 越域：他 tenant 同 user / 同 tenant 他 user 夹具行逐行不动；跨 tenant purge 调用 `deleted==0`

### D4 · 图谱 / 文档

- [ ] 零 alembic（迁移 diff 为空断言）；`docs/_tech_graph/` 补 `POST /admin/memory/purge` 路由行 + HG-GRAPH-MODULES=approved；`./scripts/graph-compile.sh` 绿；零新表/零一级模块/零 SSE 事件（偏离 → 本 SPEC 回炉）
- [ ] 文档：memory 模块说明补 purge 语义（双闸门 · 幂等 · 审计不记内容）

### 变异检验（不验收空真规则）

- [ ] ① 谓词可检：临时去掉 DELETE 的 tenant_id 谓词 → 「他 tenant 行不动」断言必挂；恢复后全绿
- [ ] ② 全量可检：临时只删 `status='active'` 行（留 superseded/revoked/expired）→ 表行零残留断言必挂；恢复后全绿
- [ ] ③ 审计可检：临时去掉 purge 审计日志 → caplog 断言必挂；恢复后全绿

### 工程

- [ ] 全量 `pytest tests` 绿；`ruff check app tests` 绿；生产路径 diff 只含：service.py purge 函数 + admin/memory.py 新路由 + router.py 注册行 + 测试/图谱/文档

---

## 7. 思考轮控制（10-spec）

| 轮 | 结论摘要 | 状态 |
|---|---|---|
| R0 | 上游手册 L7 删除权行 + §3.4 第三类；实扫确认/纠正占位：① revoke_by_source/revoke_by_key 均为逻辑失效（docstring :7 明示不物理删），物理删除零既有实现、纪律可沿用（tenant+user 谓词 · 幂等 · logger 审计记动作不记内容）；② AdminSyncAuth 唯一鉴权口径已挂 8 处，admin 面目前零写操作路由——本 purge 是首个不可逆写端点；③ embedding 是表内列（deferred）· 向量 SQL 查表本身——两通路同源一张表，行零残留即两通路零残留；④ 全仓零 DB 审计表零审计模块，logger 是唯一审计形态；⑤ backfill/qdrant_migrate 报告字段族与计数守恒纪律为干跑输出真值先例 | done |
| R1 | 范围 = D1 service purge / D2 admin 双闸门入口 / D3 删除后三断言 / D4 图谱文档；非范围 = 其它业务表 · DSR 自动化 · 状态机改动 · 用户自助端点 · 批量/定时 purge · RAG/Qdrant/Langfuse 删除 · 新审计表 · 前端 UI（占位原文沿用并据实扫扩列） | done |
| R2 | 执行形态两案：选 **S1 同步物理删除**（弃 S2 软删+异步 purge：alembic 新列+worker 基础设施 vs 收益≈零 · 且扩状态机 CHECK 与非范围冲突）；审计落点两案：选 **A1 落既有 logger 面**（弃 A2 新审计表：全仓无先例 · 「记动作不记内容」下表=日志同信息无增量 · 触发 alembic 义务；合规要机查台账时回 10-spec 升级） | done |
| R3 | failure_paths 10 条；两不可逆错（误删/越 tenant）防线全在闸前与断言层（双闸门 + 谓词断言 + 变异检验），删后不可恢复如实定性；删一半中断由单语句原子性消除（无中间态）；审计缺位为静默错有 caplog 断言 + 变异检验兜底；supersedes 自引用 FK 同语句覆盖父子行无悬挂面 | done |
| R4 | 验收全为可执行断言：干跑对拍 · 双闸门 400/409/200 三态 · 两通路零命中 + 表行零残留（全 status）· 越域零影响 · 审计字段存在且不含内容 · 幂等 0 行；变异检验三条（谓词/全量/审计各一）；全量 pytest 绿 | done |
| R5 | SPEC draft-complete 可交人签（闸表 HG-SPEC-SIGNOFF 落稿时待签）；签后 00 出 task（slug `memory-compliance-delete` · failure_paths 沿用 §5 · HG-GRAPH-MODULES 有义务（新路由）· 无 alembic）；**时机裁定落 §1：现在做（用户令队列推进 + 前置就绪）· 保守形态（默认干跑 + 双闸门 + 零自助/批量/定时面）** | done |
| early_stop | no | — |
| residual_risks | ① **双闸门防不住「计数碰巧相等的错目标」**——expected_count 只锁范围数量不锁主体正确性；管理面人工纪律（先干跑核对再实删）兜底，删除不可逆如实承认；② 同计数内容替换竞态：dry-run→实删时间窗内同数新行换旧行不可区分（管理面低频操作可接受）；③ 审计落日志面不可机查台账：日志轮转后追溯依赖日志管道留存期——合规要求机查审计台账时回 10-spec 升级新表方案（A2 弃选理由失效条件即此）；④ 删除权受理/核验（「谁有权替用户发起」）不在本 SPEC——AdminSyncAuth 只鉴权操作者身份，DSR 流程编排另案 | 签收时知悉 |

---

## 8. 下一棒

1. **维护者**：审本 SPEC → 签 `HG-SPEC-SIGNOFF=approved`
2. **00**：起草 `docs/tasks/active/task_memory_compliance_delete.md`（范围 §2 D1–D4 · failure_paths 沿用 §5 · 人工闸表：HG-GRAPH-MODULES 有义务（新路由）· 变异检验三条入验收 · 无 alembic · 铁律：dry_run 默认 true · 实删双闸门（expected_count 匹配否则 409 零删除）· DELETE 必带 tenant+user 谓词 · 审计记动作不记内容 · 全 status 整行删除）
3. **20-task-audit**：书面审 → 维护者签 `HG-AUDIT-R1`
4. **30**：`task/memory-compliance-delete` 分支实现（D4 图谱 → D1 purge 函数 → D2 admin 路由 → D3 断言 · 状态机/recall/revoke 既有语义零改动）
5. **40**：验收（含变异检验三条）→ PR（与 memory-facts-p0/p1 · security-input-isolation 同模式）

### 下一棒可复制 Prompt（20-spec-audit 预审 / 00 起草 task）

```text
你是 ops-desk-api 仓（/Users/cyning/Desktop/Ops-desk/ops-desk-api）的 <20-spec-audit ｜ 00>。
SPEC：docs/spec/memory-compliance-delete/SPEC-memory-compliance-delete_v1.md（draft-complete · HG-SPEC-SIGNOFF 待签）。
<20-spec-audit>：书面审范围/非范围/验收/failure_paths 与 R0–R5 思考轮（重点：时机裁定（§3.4 第三类为何现在做）· S1 同步删除 vs S2 软删+异步 purge 裁决 · A1 日志审计 vs A2 新表裁决 · 双闸门可执行性 · 误删不可逆诚实定性），结论落盘 docs/harness/reviews/，不代签人闸。
<00>：待维护者签 HG-SPEC-SIGNOFF=approved 后，按 SPEC §8 起草 docs/tasks/active/task_memory_compliance_delete.md（D1–D4 · failure_paths 沿用 SPEC §5 · HG-GRAPH-MODULES 有义务（新路由）· 无 alembic · 铁律：dry_run 默认 true、实删 expected_count 双闸门、DELETE 必带 tenant+user 谓词、审计记动作不记内容、全 status 整行删除）。
```

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-10-12 | 占位稿（范围草案 + 锚点 + 验收方向 + 接续指引） |
| 2026-10-13 | 10-spec 补全：锚点逐个实扫（service.py revoke 语义——逻辑失效不物理删、谓词/幂等/logger 审计纪律可沿用 · AdminSyncAuth 唯一鉴权口径已挂 8 处、admin 面零写路由先例缺位 · ops_memory_facts 模型 embedding deferred 列 + supersedes 自引用 FK · 全仓零 DB 审计表 · 向量通路两通路同查一张表 · backfill/qdrant_migrate 干跑对账报告先例）；**时机裁定**（§3.4 第三类 → 现在做：用户令队列推进 + revoke_by_key 前置就绪；保守形态：默认干跑 + expected_count 双闸门 + 零自助/批量/定时面）；**S1 同步物理删除裁定**（vs S2 软删+异步 purge · S2 触发 alembic+worker 且与非范围冲突）；**A1 日志审计裁定**（vs A2 新审计表 · 全仓无先例且信息无增量）；track 裁定 `feature`（无 alembic · 图谱义务有按实判：新 admin 路由）；failure_paths 10 条（误删/越 tenant 两不可逆错防线全在闸前 · 删一半中断单语句原子消除）；R0–R5 回填；HG-SPEC-SIGNOFF 保持待签 |
