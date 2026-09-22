# task 审查 · memory-compliance-delete · R1（20-task-audit）

| 项 | 内容 |
|----|------|
| **日期** | 2026-09-22 |
| **帽** | 20-task-audit（书面审 · 不实现代码 · 不代签人闸） |
| **被审对象** | `docs/tasks/active/task_memory_compliance_delete.md`（10-task 落稿 · commit a2dc8dd · 状态 draft） |
| **对照基准** | `docs/spec/memory-compliance-delete/SPEC-memory-compliance-delete_v1.md`（**signed** · HG-SPEC-SIGNOFF=approved 2026-09-22 · commit a65ce3b · S1 同步物理删除 + A1 日志审计 + 默认干跑双闸门签收锁死） |
| **分支** | `task/memory-compliance-delete`（本帽 `git branch --show-current` 复核一致） |
| **invoke 快照** | `docs/harness/invokes/by-task/memory-compliance-delete/invoke_20260922_20_task_audit_memory_compliance_delete.md`（required_invoke_hats=10,20,30,40 含 20 · 同批落盘） |

---

## 结论

**通过（内容零阻塞）**：范围 D1–D4 / 非范围 10 条 / failure_paths 13 条 / 验收 22 条 / R0–R5 思考轮与 SPEC 实质**零差异**；B1 11 行抽 5 条亲跑属实（10 个测试文件用例计数全对）；pytest 基线 **1333 collected** 复跑一致；`purge_by_user`/`PurgeReport`/`admin/memory` 全仓 grep 复核**零命中**；双闸门三态（缺→400 · 不等→409 零删除 · 等→200）可测性核验成立；变异检验三条可执行性核验成立；不可逆操作安全网（干跑默认对拍 / 审计 caplog / 越 tenant 逐行不动）全部断言化到位；HG-GRAPH-MODULES 亲读 `docs/_tech_graph/l1/01_modules.md` 复核成立；代码锚点 14 处逐行实核一致。

**流程闸（与内容分列）**：`HG-TASK-DRAFT` = pending · `HG-AUDIT-R1` = **pending（blocks 30）**——两闸均待维护者签，本帽不签；闸签前 30 拒开工（`npx spec-wave verify` 机跑印证 BLOCKED）。本审查文**不附 30 Prompt**，文末仅维护者签闸清单。

**签收**：20-task-audit R1 书面审通过，内容面可交维护者签闸。

---

## 逐项核对（对照 SPEC signed · a65ce3b）

### 1. 范围（SPEC §2 D1–D4）

- **D1 · service 层物理删除**：`purge_by_user(tenant_id, user_id, *, dry_run=True, session=None) -> PurgeReport` 落 `app/ops/memory/service.py`；DELETE 谓词含且仅含 tenant_id+user_id；全 status 整行删除；dry_run 默认 true 零写；审计 logger.info 记动作不记内容；单事务原子；PurgeReport 字段族 + 计数守恒——逐字对应 SPEC §2-D1 七行表 ✓
- **D2 · 管理面入口**：`POST /admin/memory/purge`（新文件 `app/ops/admin/memory.py` + router.py 注册 · tags=["admin"]）；`_user: OpsUser | None = AdminSyncAuth` 逐字对齐 admin/sync.py :32；请求体 `{tenant_id, user_id, dry_run=true, expected_count=null}`；双闸门三态 + 空白 strip 400 + 500 不静默——对应 SPEC §2-D2 ✓
- **D3 · 删除后断言**：确定性召回零命中 / 向量通路零命中（开关 true + mock embedder）/ 表行零残留（全 status）/ 越域零影响（逐行不动 + 跨 tenant deleted==0）/ 审计存在（caplog 含字段不含内容）——对应 SPEC §2-D3 五断言表 ✓
- **D4 · 图谱/文档**：零 alembic（迁移 diff 为空断言）· admin 行备注 + api 行注册备注 + 人签新行 00 代录位 · graph-compile 绿 · 零新表/一级模块/SSE 事件 · memory README + service docstring 同步——对应 SPEC §2-D4 ✓
- 竖切结论与实现序（D4 → D1 → D2 → D3）承 SPEC §8，方案对比（S1/A1 裁决）不重演 ✓

### 2. 非范围（SPEC §3）

SPEC §3 十条全收（其它业务表 / DSR 自动化 / 改状态机 / 用户自助端点 / 批量全表 purge / RAG·Qdrant 删除 / Langfuse 删除 / 新建 DB 审计表 / 前端 UI / 历史回改），task 逐条对应零增减 ✓。

### 3. 验收断言化（SPEC §6）

task 验收 **22 条** = 人工闸行 1 + D1×5 + D2×4 + D3×4 + D4×2 + 变异检验×3 + 工程×3，逐块映射 SPEC §6 标注齐备（SPEC §6 本体 18 条 + task 工程条扩三条 B1 闸前置/pytest+ruff/diff 白名单 + 人工闸行）✓。关键断言化质量抽核：

- 谓词锚点断言（含且仅含 tenant_id+user_id）✓ · 全 status 四态 + 非 NULL embedding 行整删夹具 ✓
- 干跑对拍（前后计数逐字节一致）+ 计数守恒（实删 deleted==scanned · 干跑 deleted==0）✓
- 双闸门三态各自独立断言（缺 expected_count→400 零删除 · 不等→409 零删除 · 等→200 且 deleted==expected_count）✓
- 未授权 401/403 **且表行零变化**（不只验状态码）✓ · 空白 tenant/user strip 后空→400 ✓
- 审计 caplog 字段含 tenant/user/dry_run/affected **且不含 key/value**（双向断言）✓
- 越域双向：他 tenant 同 user / 同 tenant 他 user 夹具行**逐行不动** + 跨 tenant purge deleted==0 ✓
- 变异检验三条均为「临时破坏 → 断言必挂 → 恢复全绿」句式，防空真规则钉死 ✓

### 4. failure_paths（SPEC §5）

task **13 条** = SPEC §5 十条逐条翻四列（误删 / 越 tenant·越 user / 删一半中断 / 审计缺位 / 向量通路残留 / dry_run 标志误用 / expected_count 竞态 / 未授权调用 / supersedes 自引用 FK 悬挂 / 身份租户语义漂移）+ 过程三条（HG-AUDIT-R1 未签拒开工 · B1 未落盘拒收 · 缺断言/变异检验拒收防空真规则）✓。两不可逆错（误删 / 越 tenant）防线全在闸前与断言层、删后不可恢复**如实定性**（可重试列标「否」不虚假承诺）✓；残余风险四条（双闸门只锁数量不锁主体 / 同计数内容替换竞态 / 审计日志面不可机查台账 / 删除权受理核验另案）承 SPEC §7 如实携带 ✓。

### 5. R0–R5 思考轮

全轮无 early_stop ✓；actual_last_round=R5 回填 ✓。R0 实扫复核留痕详实（分支/docstring/谓词/审计/鉴权/模型/注册面/目录/命名扫/基线逐项）；R1 闸态四条闭合；R2 竖切理由承 SPEC 不重演；R3 失败语义 13 条闭合；R4 可测性 22 条 + B1 处置三态（回归×9 · 改编×0 · 新增×1 · 迁移无×1 · 删除×0）；R5 与 SPEC 实质差异为零自述成立，残余四条承 SPEC §7 ✓。自检结论与正文一致 ✓。

### 6. 闸表

| 闸 | task 表值 | 本帽复核 |
|----|-----------|----------|
| HG-TASK-DRAFT | pending（blocks 20-R1, 30） | 一致 · 待维护者签 |
| HG-AUDIT-R1 | **pending**（blocks **30**） | 一致 · 待维护者签 · **本审查文不附 30 Prompt**（`npx spec-wave verify` 机跑印证 30 拒开工） |
| HG-GRAPH-MODULES | approved（模块表已建置）+ 新签义务 + 回炉补闸条款 | 亲读复核成立（见抽查节） |
| HG-PILOT-OPSDESK-GLAYER | n/a | 一致（本 task 不涉物理分层试点） |

新签义务留 **00 代录位**（随 30 交付落盘）有先例支撑：01_modules.md :88（prompt_asset_roadmap_p1）· :89（llm-layer-hardening）· :91（session-summary-fallback）· :92（security-input-isolation）✓。偏离回炉补闸条款在 graph_delta_note + 闸表 + 验收人工闸行三处钉死 ✓。

---

## 重点抽查（本帽亲跑）

### B1 11 行抽 5 条实核（全对）

| # | task 声称 | 本帽亲跑 | 结果 |
|---|-----------|----------|------|
| #1 | test_memory_service_db.py **13** 用例 · revoke_by_key 语义 :329-361 · caplog 先例 :341 · 跨 tenant :250-251 · 变异 :365+ | 计数=13 · :329 `test_revoke_by_key_semantics(caplog)` 实位 · :341 `"revoke_by_key" in caplog.text and "affected=1"` 逐字在位 · :250-251 跨 tenant 断言实位 · :365 `test_mutation_wrong_preference_pollutes_then_revoke_by_key_erases` 实位 | ✓ |
| #2 | test_memory_vector_p1.py **9** 用例 · mock embedder :234 · revoke 后向量零命中 :238-244 · 开关非法值 :313-319 | 计数=9 · :234 fake embedder 调用实位 · :238-244 revoke→recall_with_vector 零命中断言实位 · :310-319 env 非法值 warning caplog 实位 | ✓ |
| #3 | test_memory_embedding_backfill.py **15** 用例 | 计数=15 | ✓ |
| #5 | test_admin_sync.py **10**（401 :14-15 · 403 :22-23 · Bearer :110-143 · 幂等 :73-77）· test_auth.py **10**（:116-148） | 两文件计数=10/10 · :13-16 无 cookie 401 实位 · :19-24 viewer 403 实位 · :110 Bearer token monkeypatch 实位 · :73-78 幂等重放实位 · test_auth.py :116 admin_sync 401 实位 | ✓ |
| #6 | test_admin_capability_observability.py **12** · override :31-35 · BASE :27 | 计数=12 · :33 `dependency_overrides[require_admin_sync] = lambda: None` 逐字在位 · :27 BASE 实位 | ✓ |

补核 B1 扫描口径：`ls tests/ | grep -iE 'memory|admin|auth'` = **11 文件**（memory×7 / admin×3 / auth×1）与 B1 一致 ✓；其余文件计数（gate 15 / injection 23 / extract_p1 14 / time_decay_tz 6）亲跑全对 ✓；「无既有用例依赖行不可物理删除反向断言 → 改编面为零」与 purge 纯新增事实互证成立 ✓。

### pytest 基线复跑

`python -m pytest tests --collect-only -q` = **1333 tests collected**（2026-09-22 本帽真跑 · 与 task :78/:190/:249 基线一致）✓

### purge_by_user / PurgeReport 全仓零命中复核

`grep -rn 'purge_by_user\|PurgeReport\|admin/memory' app/ tests/ evals/ docs/_tech_graph/` = **零命中**（exit 1 亲跑）✓——新函数名/路由路径/报告类名无冲突，B1#10「当前不存在」实证成立。

### 代码锚点逐行实核（14 处全对）

| 锚点 | task 声称 | 本帽实核 | 结果 |
|------|-----------|----------|------|
| service.py docstring「不物理删」 | :7 | :7「失效走状态机…不物理删」逐字在位 | ✓ |
| service.py session 纪律 | :10-11 | :10-11 docstring 逐字在位 | ✓ |
| service.py strip 先例 | :110-115 | :110-112 tenant/user/key .strip() 实位（落在声称区间内） | ✓ |
| revoke_by_source | :134-163 · 审计 :159-162 | def :134 · logger.info :160-162 实位 | ✓ |
| revoke_by_key | :166-201 · 谓词 :176-177 · 审计 :197-200 | def :166 · :176-177「必带 tenant+user 谓词（跨 tenant = 0 行）」逐字在位 · logger.info :198-200 实位 | ✓ |
| deps.py require_admin_sync | :86-116 · compare_digest :98 · token 空禁用 :97-103 · maintainer 403 :105-111 | def :86 · :98 compare_digest 实位 · :97-103 空 token 401 实位 · :106-111 maintainer 403 实位 · AdminSyncAuth :116 | ✓ |
| admin/sync.py 挂法+错误纪律 | :32 · :35-45 | :32 `_user: OpsUser \| None = AdminSyncAuth` 逐字在位 · :39-45 rollback+logger.exception+500 实位 | ✓ |
| models.py status CHECK | :500-503 | :500-503 四值 CHECK 实位 | ✓ |
| models.py supersedes FK | :545-549 | :545-549 `ondelete="SET NULL"` 实位 | ✓ |
| models.py embedding 列 | :558-560 | :558-560 Vector nullable deferred=True 实位 | ✓ |
| router.py 注册面 | :4-5/:24-25 | :4-5 import · :24-25 include_router 实位 | ✓ |
| admin/ 目录无 memory.py | ls 实证 | ls = __init__/capability/schema/sender/service/sync · 无 memory.py | ✓ |
| memory/README.md 存在 | ls 实证 | 存在 | ✓ |
| capability.py「替别人看一眼」 | :60-76 | :63-66 docstring「用途就是替别人看一眼」逐字在位 | ✓ |

### 双闸门语义可测性

- 三态各自可区分可执行：缺 expected_count（dry_run=false）→ 400 **且零删除**；计数不等 → 409 **且零删除**；计数等 → 200 且 `deleted==expected_count`——每态均带表行侧断言，不只验状态码 ✓
- 干跑默认：缺省 dry_run → 200 + 计数报告 + 表行零变化 + 响应 echo dry_run 标志（防调用方误判）✓
- 锚点先例真实：Bearer 三态（test_admin_sync.py :110-143）· override 形态（test_admin_capability_observability.py :31-35）· 500 不静默（admin/sync.py :35-45）全部实位可复用 ✓
- 可测性结论：双闸门 400/409/200 三态 + 401/403 零删除 + 空白 400 形态可执行、先例锚点真实 ✓

### 变异检验三条可执行性

- ① 谓词可检：临时去 tenant_id 谓词 → 「他 tenant 行不动」断言必挂——越域断言为逐行不动双向夹具，破坏谓词后他 tenant 行必被动，断言必挂成立 ✓
- ② 全量可检：临时只删 active 行 → 表行零残留（全 status）断言必挂——D3 表行断言明确含 superseded/revoked/expired，留非 active 行则 count>0 必挂成立 ✓
- ③ 审计可检：临时去审计日志 → caplog 断言必挂——审计断言要求实删/干跑/幂等 0 行三路径全有日志，去日志后 caplog 空必挂成立 ✓
- 三条均为「破坏 → 必挂 → 恢复全绿」闭环句式，与既有变异检验先例（test_memory_service_db.py :365+）同形态可执行 ✓

### 不可逆操作安全网断言化

- **干跑默认**：dry_run 缺省 true · 干跑前后表行计数对拍断言 · 响应 echo 标志——盲发只读兜底断言化 ✓
- **实删双闸门**：expected_count 显式对账（缺→400 · 不等→409 零删除）——「删多少」显式对账非盲发 ✓
- **审计**：caplog 字段存在 + 不含 key/value 双向断言 + 变异检验③兜底 ✓
- **越 tenant/user**：夹具行逐行不动 + 跨 tenant 调用 deleted==0 + 变异检验①兜底 ✓
- **诚实定性**：双闸门防不住「计数碰巧相等的错目标」列残余风险（SPEC §7 ①）· 删后不可恢复在 failure_paths 可重试列标「否」——不虚假承诺 ✓

### HG-GRAPH-MODULES 亲读复核（01_modules.md）

- `admin` 行 **:30**：`app/ops/admin/** → db` · Bearer 机读 token + cookie maintainer 双口径逐字在位 ✓
- `memory` 行 **:28**：P0 备注含「**无对外 HTTP 端点**」逐字在位——purge 是 memory 首个对外入口但落在 admin 模块内、零新开一级模块的裁定与图谱真值一致 ✓
- `api` 行 **:20**：router.py 注册面行实位 ✓
- 签录链完整至 **:92**（security-input-isolation · 2026-09-22）· bootstrap 签 2026-07-16（:55）✓
- 00 代录位先例 :85/:86/:88/:89/:90/:91/:92 多处在案 ✓
- 复核结论：task 闸表 HG-GRAPH-MODULES=approved（模块表已建置）+ 新签义务（admin 行备注 + api 行注册备注 + 人签新行 00 代录位）+ 回炉补闸条款——全部与图谱真值一致 ✓

---

## 非阻塞观察（记录备查 · 不构成退回）

1. **AdminSyncAuth 挂载点计数漂移**：task 锚点与 SPEC §1 称「已挂…共 8 处」，本帽 grep 实核当前 **10 处**（admin/sync.py :32 ×1 + admin/capability.py :80/:165/:218/:230/:257 ×5 + hitl/router.py :66/:90/:242/:336 ×4）——hitl 面实 4 处，计数自 SPEC 实扫后有漂移；「admin 面鉴权口径唯一且成熟」实质结论不受影响，30 阶段挂法对齐 admin/sync.py :32 先例即可。
2. task 工程验收「生产路径 diff 白名单」口径为 `git diff master -- app/`，本仓主干实际以 PR 合并到 main（AGENTS.md 口径 · 承 security-input-isolation R1 同款观察）；30/40 阶段执行时按实际主干分支名取值即可，不影响断言语义。

---

## 闸态汇总

- `HG-TASK-DRAFT` = **pending**（blocks 20-R1, 30 · 待维护者/00 验收代录）
- `HG-AUDIT-R1` = **pending**（blocks **30** · 本审查 R1 通过待人签 · 本帽不签）
- `HG-GRAPH-MODULES` = approved（模块表已建置 · 本帽亲读复核成立）+ 新签义务随 30 交付落盘（00 代录位）+ 偏离回炉补闸
- `HG-PILOT-OPSDESK-GLAYER` = n/a

---

## 维护者签闸（20 后 · 30 前）

- [ ] 已读 R1 审查结论（本文）
- [ ] 在 task 人工闸表将 HG-TASK-DRAFT 改为 approved（维护者 · 日期）
- [ ] 在 task 人工闸表将 HG-AUDIT-R1 改为 approved（维护者 · 日期）
- [ ] commit task 文档或确认已签
- [ ] 再下发 Harness 30 Prompt

30 Agent 将以 task 表为准；pending 时必须拒开工（见 TEMPLATE_30_gate_stop.md）。
