# Task：阶段 W 联调缺口修复（HITL TTL 语义补全 + 只读资源面租户谓词）

> **状态**：`active`（2026-11-02 · 四闸全 approved（维护者签 · 00 代录）· 设计四决策钉死（409+approval_expired · freeze 增补 TTL 条 · resume/消费环 · STATUS_EXPIRED 启用）· **GO 30**）
> **类型**：fix / 安全语义补全（HITL TTL · 跨租户只读封闭）
> **上游**：workspace `docs/harness/invokes/by-task/stage-w-e2e-join-acceptance/invoke_20261102_10_c8_evidence_archive.md`（联调实证 F11/F12/F13 · §2 发现清单 · §5 过期态实验）· workspace `docs/contracts/api-v1-tenant-readonly-context-draft.md`（租户契约 F1–F6 · F4 对外 404/对内 `tenant_scope_denied`）
> **分支**：`task/api-w-join-gap-fix`（base：`master`）
> **10 注**：2026-11-02 · 维护者裁决「F12 补 api TTL 过期出口 · F13 只读资源面接租户谓词 · 联调 task 暂不 CLOSE、待修复复测再关」· 本棒仅落壳 + lint · **禁止**改 `app/`

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `api-w-join-gap-fix` |
| **git_branch** | `task/api-w-join-gap-fix` |
| **implement_repo** | `ops-desk-api`（主）+ `ops-desk-web`（仅 onResume 过期 mapping 薄改 · B1 维护者裁决扩范围） |
| **test_strategy** | `required` |
| **test_strategy_note** | api 侧 pytest 红测先行：过期负样本（approved 超 TTL 后 resume 出口语义 · 未过期批准**不误拒**正样本）+ 跨租户负样本（B session 下 issues/pulls/overview 列表为空、详情 404）+ 同租户读不受影响正样本 + 码面锚点核对（grep 谓词存在性）。web 侧（薄改）：Vitest 补 `onResume` 过期 mapping 用例（resume 返过期错误 → 行级提示「审批已过期，请刷新列表」可达）+ 质量门 `pnpm lint && pnpm test && pnpm build` |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1`（预估薄增量 · 以 30 实扫为准） |
| **graph_delta** | api `docs/_tech_graph/l1/01_modules.md`（issues / pulls / overview / hitl 模块条目一句备注「租户谓词 · TTL 闸」）· 不新增一级模块；web 侧 `docs/_tech_graph/l1/01_modules.md` 评估（预计零 diff 或 hitl 模块一句「resume 过期 mapping」· 以 30 实扫为准） |
| **graph_delta_note** | 模块边界不变；仅模块内谓词/守卫增量 → G-L1 同步；web 薄改在既有 HitlApprovalView 内，预计零图谱面 |
| **wiki_delta** | `n/a`（web 侧预计同 `n/a` · 以 30 实扫为准） |
| **wiki_delta_note** | 契约真值在 workspace contracts；freeze `hitl-browser-decide-v1` 增补方案只列于本 task，**freeze 文件本体由维护者签署后另改** |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,20,30,40` |
| **invoke_retention_profile** | `default` |
| **experience_capture** | `recommended` |
| **kpi_aggregator** | `CLOSE` |
| **orchestration** | 10 落稿 → 20 R1 审查 → R1 FAIL 修订 → 20-R2 复审 PASS-WITH-MINOR（M4 闭环=web 仓镜像薄壳）→ 维护者签 `HG-TASK-DRAFT`/`HG-AUDIT-R1`/`HG-GRAPH-MODULES`/`HG-W-FIX-DESIGN` → 30（api 分支 `task/api-w-join-gap-fix` + web 分支 `task/web-hitl-resume-expired-mapping` · **web 侧 30 闸据 = web 仓镜像薄壳 `task_web_hitl_resume_expired_mapping`（同分支名）· 四闸镜像以本 task 闸表为真值不重复签** · 两 PR 均合入后才可联调复测）→ 40 → 联调 task A4②/A5 复测回接（workspace `task_stage_w_e2e_join_acceptance`）→ CLOSE |
| **freeze_id** | `hitl-browser-decide-v1`（**增补评估**：TTL 过期错误出口需入 freeze；本 task 只列方案，freeze 变更须维护者签 · `lg-rag-sse-v1` 默认零改） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | **approved**（2026-11-02 维护者签收 · 00 代录） | 20-R1, 30 | 维护者签收草稿；解锁 20-R1 · 30 仍须 HG-AUDIT-R1 + HG-GRAPH-MODULES + HG-W-FIX-DESIGN 齐 |
| HG-AUDIT-R1 | **approved**（2026-11-02 维护者签 · 00 代录） | **30** | 20-R2 审查文 PASS-WITH-MINOR（`docs/harness/reviews/task_api_w_join_gap_fix_audit_R2_20261102.md` · M4 已闭环=web 镜像薄壳） |
| HG-GRAPH-MODULES | **approved**（2026-11-02 维护者签 · 00 代录） | **30**（条件触发） | G-L1 薄增量口径确认（issues/pulls/overview/hitl 模块一句备注 · 不新增一级模块 · web 侧零图谱 diff） |
| **HG-W-FIX-DESIGN** | **approved**（2026-11-02 维护者签 · 00 代录） | **30** | **四决策已裁决**：① 出口=**409 + `approval_expired`**（detail 中文含「过期」命中 web mapping）② freeze `hitl-browser-decide-v1` **增补 TTL 条**（含 resume 路径渲染语义 · 本闸签署即生效 · freeze 文件本体随 30 棒改）③ 作用面=resume/消费环（decide 不拒超龄 pending · 「批准不过期」不 reopen）④ **启用 `STATUS_EXPIRED`**（过期拒绝时置 `expired` 终态） |

---

## 背景与目标

2026-11-02 阶段 W 双轨联调（workspace `task_stage_w_e2e_join_acceptance` · 本地双栈真人全链）坐实三个码面缺口，证据全锚于 C8 invoke（§1 C6/C7 · §2 发现清单 · §5 实验记录）：

- **F11（defect）**：手动 resume 链零 TTL 闸——`app/ops/hitl/router.py:520 resume_request` → `:473 _preflight_decided_resume` 全文无 ttl/过期引用；批准超 TTL（实验：approved 后 +178s > 90s 短窗）仍可解锁重跑。而自动续跑扫描路径有 TTL 闸（`app/ops/hitl/store.py:116-117 aclaim_approved_for_resume`：`time.time() - decided_at > ttl_seconds → None`）——两条恢复入口语义**不对称**。
- **F12（gap · 契约）**：api hitl 面无「过期」错误出口——`app/ops/hitl/store.py:22 STATUS_EXPIRED` 定义但全仓无人赋值；decide/resume 无过期分支；freeze `docs/tasks/done/task_hitl_browser_decide.md` 无 TTL 条 → web FP-5「审批已过期，请刷新列表」（`ops-desk-web/src/views/HitlApprovalView.vue:111,:153` mapping `/过期|expired/i`）**悬空不可达**，TC9 过期态截图无法诚实复现（联调 A5 挂账根因）。
- **F13（defect · 高）**：只读资源面跨租户泄漏——`app/ops/issues.py:29 list_issues` 全文零 tenant 引用（pulls.py / overview.py 同）；联调 A4 补测②实证：session 切 B（`ops-desk-pilot-b`）后 `GET /api/ops/issues` / `pulls` / `overview` 均返回 A 租户数据（issue `cc227ab1-9117-4631-abad-68e902bb21d6` 等 · DB 实证 `ops_issues` 881 行全 `tenant_id='ops-desk-pilot'`）。范围锚：`docs/tasks/done/task_tenant_readonly_predicate.md:156` 阶段 T 谓词只圈 `app/ops/capability/**` · `lg_rag/multi/nodes.py` · lookup/RAG——**未覆盖非回归**。连带：**P 轨 canary 手测（workspace `docs/05-plan/07_stage_t_data_prep_runbook_v0_zh.md` §4 P2 期望 B 查 A issue 得 404）当前必失败 → F13 修复是 P 轨硬前置**。

本 task 只做两条修复竖切（W-fix-1 = F11+F12 合并设计 · W-fix-2 = F13），把联调 A4②/A5 两个挂账验收回接到可复测状态。

---

## 现状锚点（只读 · 30 必读 · 10 已扫）

| 主题 | 路径 · 锚点 | 现状 |
|------|-------------|------|
| TTL 闸（已有） | `app/ops/hitl/store.py:116-117`（`aclaim_approved_for_resume` 内 `time.time() - float(decided_at) > ttl_seconds → None`） | 仅服务自动续跑扫描（`auto_resume.py:104-108` 引 `nodes._approval_consumption_ttl_seconds`） |
| TTL 旋钮 | `app/ops/lg_rag/multi/nodes.py:307`（`ENV_APPROVAL_CONSUMPTION_TTL_SECONDS="OPS_HITL_APPROVAL_CONSUMPTION_TTL_SECONDS"`）· `:328`（默认 3600 · `[1,86400]` 越界回退） | 单一旋钮 · 消费闸 T1 同用 |
| 手动 resume 链（无闸） | `app/ops/hitl/router.py:473 _preflight_decided_resume` · `:520 resume_request` | 全文零 ttl/过期 引用（F11 现场） |
| 过期态死码 | `app/ops/hitl/store.py:22 STATUS_EXPIRED = "expired"` | 定义无人赋值（`app/ops/memory/service.py:221` 系另一域） |
| web FP-5 等待侧 | `../ops-desk-web/src/views/HitlApprovalView.vue:111`（`审批已过期，请刷新列表` · 位于 `decideErrorText`，仅 `onDecide` catch `:150` 调用）· `:153`（decide 失败联动刷新）· **`onResume` catch `:173-180` 无 `/过期|expired/i` mapping**（409 透传「续跑失败：{message}」`:176` · 其余状态码泛化「续跑失败（网络/服务异常），可重试」`:179`） | decide 错误路径渲染已存在；**resume 错误路径过期 mapping 缺失（B1 实证 · 20-R1 抽验坐实）→ 本 task 扩范围补** |
| F13 泄漏面 | `app/ops/issues.py:29 list_issues` · `app/ops/pulls.py` · `app/ops/overview.py` | 三处全文零 tenant 引用（10 已 grep 实证） |
| 租户真源 | `app/ops/deps.py:43-45`（`request.state.ops_tenant_id = session.tenant_id or "ops-desk-pilot"`）· `app/ops/tenant_context.py`（F1=C · `current_tenant_or_default()` :24-26 回落 TENANT_A） | session 为真源 · 头不一致 403（`lg_rag/router.py:376-384`） |
| 谓词先例 | `docs/tasks/done/task_tenant_readonly_predicate.md`（capability/lg_rag/RAG 租户谓词模式 · :156 范围锚） | 本 task 对齐其模式，不另造 |
| 联调证据 | `../ops-desk-workspace/docs/harness/invokes/by-task/stage-w-e2e-join-acceptance/invoke_20261102_10_c8_evidence_archive.md` | F11/F12/F13 全锚 · A4②/A5 挂账 · §7 建议 #5/#9/#10 |

---

## 10 钉死契约（草案 · HG-W-FIX-DESIGN 签收后升格；30 不得静默改义）

| 项 | 钉死（草案） |
|----|----------------|
| **TTL 语义** | 「**批准不过期，执行权过期**」不变：`adecide` 对超龄 pending 不拒（人随时可以下决定）；**执行权**（resume 恢复 + T1 消费）对超 TTL approved 拒 |
| **过期出口** | 手动 resume（`router.py:520`）对超 TTL approved 返**明确过期错误**（状态码/文案由 HG-W-FIX-DESIGN 钉：建议 `410 Gone` 或 `409 + approval_expired` 明细，文案含「过期」以命中 web FP-5 mapping）；自动扫描与手动链**同一 TTL 判据**（复用 `nodes._approval_consumption_ttl_seconds` · 禁第二旋钮）；**配套 web 薄改（B1 维护者裁决扩范围）**：`HitlApprovalView.vue` `onResume` catch（:173-180）补 `/过期|expired/i` mapping，文案与 decide 路径同（`审批已过期，请刷新列表`） |
| **单据终态** | 过期拒绝时单据置 `expired`（启用 `store.py:22 STATUS_EXPIRED`）或维持 approved + 错误出口——二选一由 HG-W-FIX-DESIGN 钉死；禁止静默重规划开新单而不告知（联调 F7 轰炸环的过期变体） |
| **freeze 路径** | `hitl-browser-decide-v1` 增补 TTL 条（过期错误出口语义）须走契约闸由维护者签；本 task 不动 freeze 文件 |
| **F4 谓词口径** | 只读面（issues/pulls/overview）接租户谓词：list 查询过滤 `tenant_id == 当前租户`（跨租户得**空列表**）；详情/单资源命中跨租户 → 对外 **404**（不泄漏存在性）· 对内 `tenant_scope_denied`；租户真源 = `request.state.ops_tenant_id`（deps.py:43-45 既有接线） |
| **不误伤** | 同租户读行为零变化（正样本回归）；`tenant_id=''` 历史行（若有）处置策略由 30 实扫提出并回填修订表（默认从严：视同当前租户外 · 列表不可见；**偏离从严默认须维护者签**，30 不得自主裁量） |
| **SSE 零改** | 不新增/不改 SSE `event_type`（`lg-rag-sse-v1` 不破） |

---

## 范围（同 task 竖切 · 四闸齐后才 30）

- [ ] **W-fix-1 · HITL TTL 语义补全（F11+F12）**：手动 resume 链接 TTL 闸（与 `store.py:116-117` 对称）；过期错误出口落地（状态码/文案按 HG-W-FIX-DESIGN）；单据终态策略落地；`STATUS_EXPIRED` 启用或移除（按设计钉死）；自动/手动两入口 TTL 判据同源
- [ ] **W-fix-1-web · web resume 错误路径过期映射（B1 维护者裁决扩范围 · 薄改）**：`ops-desk-web` `src/views/HitlApprovalView.vue` `onResume` catch（:173-180）补 `/过期|expired/i` mapping（与 decide 路径 `decideErrorText:111` 同文案「审批已过期，请刷新列表」）；web 分支 `task/web-hitl-resume-expired-mapping` 独立 PR
- [ ] **W-fix-2 · 只读资源面租户谓词（F13）**：`app/ops/issues.py` · `pulls.py` · `overview.py` 接租户谓词（F4 口径：跨租户列表空集 · 详情 404 · 对内 `tenant_scope_denied`）；同租户读零变化

### 非范围

- **web 其余业务码**（除范围条 W-fix-1-web 列明的 `onResume` 过期 mapping 薄改外一律不动；decide 路径 `decideErrorText` 已有 mapping 不改）
- **改 SSE freeze**（`lg-rag-sse-v1` 事件表 / idle keepalive）
- **freeze 文件本体修改**（`hitl-browser-decide-v1` 增补由维护者签后另走契约闸）
- **联调 task CLOSE**（workspace `task_stage_w_e2e_join_acceptance` · 本 task 修复合入 + 复测后由维护者拍板）
- **其余联调发现**：F1/F2/F3/F5/F6/F7/F8/F9/F10/N-R2-1/守卫真空（invoke §2）——另行立项（N-R2-1 resume 租户上下文丢失为下一高优 · 本 task 不含）
- 阶段 P 平台项 · P 轨生产数据（07 §4 另轨）

---

## failure_paths

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----------|----------|--------|----------|
| 四闸任一 pending 即 30 | **拒开工** | 是 | 是 |
| **误拒未过期批准**（TTL 闸判据错 · 正样本挂） | 红测拦截（未过期 approved resume 须成功）· 30 返修 | 是 | 否 |
| **谓词误伤同租户读**（过滤条件错把本租户行滤掉） | 红测拦截（同租户列表/详情正样本）· 30 返修 | 是 | 否 |
| **freeze 变更未签即改义**（过期出口语义偏离 HG-W-FIX-DESIGN 钉死值） | 20/40 审查拒收 · 退回 | 是 | 否 |
| 过期出口文案不含「过期」关键词，或 web `onResume` mapping 未落地 | web 行级过期提示不可达（api mapping 不命中 / web 无 mapping）· 40 拒收 | 是（改文案 / 补 mapping） | 否 |
| 双入口 TTL 判据不同源（手写第二处秒数/第二旋钮） | 审查拒收（单一旋钮红线） | 是 | 否 |
| 跨租户详情泄漏存在性（404 文案含 hint） | 审查拒收（F4 不泄漏语义） | 是 | 否 |
| 修复合入但未回接联调 A4②/A5 复测 | 联调 task 保持挂账 · **拒 CLOSE** | 是（补复测） | 是 |

---

## 验收标准

- [ ] 人工闸：`HG-TASK-DRAFT` · `HG-AUDIT-R1` · `HG-GRAPH-MODULES` · `HG-W-FIX-DESIGN` 均 approved 后方可勾选下列码项
- [ ] W-fix-1：超 TTL approved 的手动 resume → 过期错误出口（状态码/文案与 HG-W-FIX-DESIGN 一致 · 含「过期」字样）负样本测绿；**未过期** approved resume 正样本测绿（不误拒）；自动扫描与手动链 TTL 判据同源（grep 实证同一 `_approval_consumption_ttl_seconds`）
- [ ] W-fix-1：单据终态策略落地（`expired` 启用或维持语义与钉死一致）；decide 对超龄 pending 不拒（「批准不过期」回归测绿）
- [ ] W-fix-2：B session 下 `GET /api/ops/issues` / `pulls` / `overview` 列表为空、A 资源详情 404 负样本测绿；A session 同资源读正样本零变化测绿
- [ ] **回接条款**：修复合入后复测联调 A4②（B 身份 `GET /issues` → 空集 · 锚 workspace invoke §C6 补测口径）与 A5（api 以 `OPS_HITL_APPROVAL_CONSUMPTION_TTL_SECONDS=90` 短窗复现过期态 → **链路：api resume 过期出口 → web `onResume` mapping → FP-5 行级提示「审批已过期，请刷新列表」可达** → 截图补 TC9 材料）；复测证据回填 workspace invoke 与 task 档
- [ ] `hitl-browser-decide-v1` 消费语义回归：decide 400/404/409/422 既有语义零变化（freeze 增补若签则另走契约闸，本 task 不改 freeze 文件）
- [ ] `ruff` 触及路径绿；`pytest` 本波 + 既有 hitl/tenant/issues 回归绿
- [ ] **旧测 grep 影响面**（M3 · 20-R1）：30 交付前列出 `tests/`（api）与 web 测试中编码旧行为的用例清单——resume 无闸即恢复的正样本、跨租户列表返回全量行的断言、`tenant_id=''` fixture 行等——**逐条标注保留 / 修改 / 删除 + 理由**，随 PR 提交；禁止静默改测对齐
- [ ] `./scripts/graph-compile.sh` 绿（G-L1 薄备注同步）；不新增 G-L1 一级模块
- [ ] SSE 事件表零 diff（`lg-rag-sse-v1` 不破）
- [ ] `npx spec-wave task lint --file docs/tasks/active/task_api_w_join_gap_fix.md` PASS

---

## 依赖

| 依赖 | 说明 |
|------|------|
| 联调证据 | `../ops-desk-workspace/docs/harness/invokes/by-task/stage-w-e2e-join-acceptance/invoke_20261102_10_c8_evidence_archive.md`（F11/F12/F13 实证锚） |
| 联调 task（被阻塞） | `../ops-desk-workspace/docs/tasks/active/task_stage_w_e2e_join_acceptance.md`（A4②/A5 挂账 · **本 task 阻塞其 CLOSE**） |
| 租户契约 freeze | `../ops-desk-workspace/docs/contracts/api-v1-tenant-readonly-context-draft.md`（F1–F6 · F4 口径） |
| 谓词先例 | `docs/tasks/done/task_tenant_readonly_predicate.md`（:156 范围锚 · 谓词模式） |
| HITL 既有面 | `docs/tasks/done/task_hitl_browser_decide.md`（freeze · 无 TTL 条）· `app/ops/hitl/{router,store,auto_resume,resume}.py` |
| P 轨前置 | `../ops-desk-workspace/docs/05-plan/07_stage_t_data_prep_runbook_v0_zh.md` §4 P2（canary 手测期望 404 · 依赖 W-fix-2） |
| 编码规范 | `docs/standards/CODING_BACKEND_L2_v1_zh.md` |
| web 镜像薄壳（M4 闭环） | `../ops-desk-web/docs/tasks/active/task_web_hitl_resume_expired_mapping.md`（分支 `task/web-hitl-resume-expired-mapping` · **web 侧 30 的 GATE_VERIFY 闸据** · 四闸镜像以本 task 闸表为真值 · 不重复签） |

---

## 给执行帽的必读列表

1. `AGENTS.md`
2. 本 task（钉死契约 · 闸 · 非范围 · failure_paths）
3. workspace invoke `invoke_20261102_10_c8_evidence_archive.md`（§2 F11/F12/F13 · §5 过期态实验 · §7 #5/#9/#10）
4. 代码：`app/ops/hitl/{router,store,auto_resume,resume}.py` · `app/ops/{issues,pulls,overview}.py` · `app/ops/deps.py` · `app/ops/tenant_context.py` · `app/ops/lg_rag/multi/nodes.py`（TTL 旋钮）
5. `docs/tasks/done/task_tenant_readonly_predicate.md`（谓词模式）
6. `docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`

---

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|----|------|------------|----------------------|----------------|
| R0 | 本 task = 两个已实证缺口的修复竖切（F11+F12 合并 · F13）；不是新特性 | no | — | none |
| R1 | 范围切分：N-R2-1/F7/F9 等其他发现另行立项，不塞本 task（防范围膨胀失焦） | no | — | N-R2-1 高优被排后 |
| R2 | F11 与 F12 合并设计（同修 resume 链 TTL 语义 · 一处判据两处出口）；F13 对齐 tenant_readonly 谓词先例不另造 | no | — | 过期出口状态码选型分歧（410 vs 409）挂 HG-W-FIX-DESIGN |
| R3 | 闸设计：新增 HG-W-FIX-DESIGN 承载四决策（出口语义 · freeze 增补 · 作用面收窄 · 单据终态）；其余走常链 | yes | 决策面已框死（出口语义/谓词口径/回接条款均落地为闸或验收项）；实现细节属 30 实扫 | `tenant_id=''` 历史行过滤策略可能影响存量列表可见性（30 实扫回填 · 偏离从严须维护者签） |
| R4 | （未开） | — | early_stop at R3 | — |
| R5 | （未开） | — | early_stop at R3 | — |

**actual_last_round**：R3 · **early_stop**：yes · **residual_risks**：见 R3

### R0 · 问题框定

联调把三个缺口从「疑似」打成「实证」：F11（手动 resume 无 TTL 闸）、F12（无过期出口）、F13（只读面泄漏）。本 task 是修复轨不是设计探索——证据、锚点、期望行为都已钉在 invoke 里，30 的性质是「按钉死值接线 + 负样本」。

### R1 · 范围切分

invoke §2 共 13 项发现，本 task 只取维护者裁决的两项（F11+F12、F13）。N-R2-1（resume 租户上下文丢失）虽高优但独立成题（涉 resume 链路还原语义，与 TTL 正交），混进来会拖垮本 task 的聚焦与验收。其余 UX/噪音类发现（F1/F6/F8/F10 等）归 web/后续批次。

### R2 · 合并设计与谓词先例

F11 与 F12 是同一判据（TTL）在两个入口的缺失：补一处同源判据（复用 `nodes._approval_consumption_ttl_seconds`），手动 resume 接闸即同时解决「不对称」（F11）与「无出口」（F12 的一半）；另一半（decide 侧与终态策略）留 HG-W-FIX-DESIGN。F13 照 `task_tenant_readonly_predicate` 的既有谓词模式接三处只读面，不另造过滤框架。

### R3 · 闸设计 · 收敛

过期出口有四个真决策点（①状态码/文案 · ②freeze 是否增补 · ③作用面收窄——decide 不拒超龄 pending 为已定前提 · ④单据终态 expired 启用与否），都影响契约语义，须维护者签 → 新增 `HG-W-FIX-DESIGN`。其余走 10→20→30→40 常链。残险：`tenant_id=''` 历史行在谓词下的可见性策略，30 实扫后回填修订表（偏离从严须维护者签）。

**R3 增补（2026-11-02 · 20-R1 FAIL 后维护者裁决）**：B1「FP-5 可达性链条断裂」（web 过期 mapping 仅在 decide 错误路径 · `onResume` 无 mapping）→ 裁决**扩范围**：web `HitlApprovalView.vue` `onResume` catch（:173-180）补过期 mapping 列入本 task（W-fix-1-web · 薄改 · 独立 web 分支 PR）；「web 业务码」非范围条相应收窄为「web 其余业务码」。

### R4 ·（未开 · early_stop）

本轮不展开；待 HG-W-FIX-DESIGN 签收后由 20-R1 / 30 实扫补足。

### R5 ·（未开 · early_stop）

本轮不展开。

---

### 自检结论

| 命令 | 退出码 | 摘要 |
|------|--------|------|
| `npx spec-wave task lint --file docs/tasks/active/task_api_w_join_gap_fix.md` | 0 | LINT: PASS（2026-11-02 · 10 M4/N5 闭环同步复跑） |

---

## 修订

| 日期 | 说明 |
|------|------|
| 2026-11-02 | 10 起草壳（维护者裁决：F12 补 api TTL 过期出口 · F13 只读资源面接租户谓词 · 联调 task 暂不 CLOSE 待修复复测）· 四闸 pending · NO-GO 20/30 · R0–R3（R3 early_stop）· 证据锚全引 workspace `invoke_20261102_10_c8_evidence_archive.md` |
| 2026-11-02 | 维护者签收 HG-TASK-DRAFT（00 代录 · 闸表+状态行同步）· GO 20-R1 · 30 仍 NO-GO |
| 2026-11-02 | 10 承接 **20-R1 FAIL 修订**（审查文 `docs/harness/reviews/task_api_w_join_gap_fix_audit_R1_20261102.md` · 维护者裁决 B1 方向=扩范围）：**B1 五处联动**——范围 +W-fix-1-web（web `HitlApprovalView.vue` `onResume` catch :173-180 补 `/过期|expired/i` mapping · 与 decide 路径 :111 同文案）· implement_repo 改双仓 · test_strategy_note 补 web 质量门（Vitest + `pnpm lint/test/build`）· orchestration 写入 web 分支 `task/web-hitl-resume-expired-mapping` 与双 PR 链 · graph/wiki_delta 补 web 侧评估 · 非范围「web 业务码」收窄为「web 其余业务码」· 现状锚点表补 onResume 无 mapping 实证 · 过期出口钉死行+failure_path+A5 验收链同步；**M1** 闸行补决策点④「单据终态语义（`STATUS_EXPIRED` 启用与否）」；**M2** 决策点③收窄（decide 不拒超龄 pending 为已定前提 · ③仅签 resume/消费环出口选型）；**M3** 验收补「旧测 grep 影响面」项；**N3** `tenant_id=''` 处置补「偏离从严默认须维护者签」；R3 轮增补 B1 裁决记录 · 闸表 status 未动 · lint 复跑 PASS |
| 2026-11-02 | 10 承接 **20-R2 PASS-WITH-MINOR 的 M4/N5 闭环**（审查文 `docs/harness/reviews/task_api_w_join_gap_fix_audit_R2_20261102.md`）：**M4**——web 仓镜像薄壳 `task_web_hitl_resume_expired_mapping`（分支 `task/web-hitl-resume-expired-mapping`）落档为 web 侧 30 的 GATE_VERIFY 闸据（四闸镜像 pending · 以本 task 闸表为真值 · 不重复签）· orchestration 与依赖区登记；**N5**——语境滞后三处同步（:3 状态行「GO 20-R1」→「20-R2 PASS-WITH-MINOR · 待维护者签三闸」· :39 HG-AUDIT-R1 说明「20-R1 PASS 后签」→「20-R2 PASS-WITH-MINOR 待签」· :205 自检行注记刷新）；闸表 status 未动（三闸仍 pending · 待维护者签）· lint 复跑 PASS |
| 2026-11-02 | 维护者三闸同签（HG-AUDIT-R1 / HG-GRAPH-MODULES / HG-W-FIX-DESIGN · 00 代录）· 设计四决策：①409+approval_expired（中文含「过期」）②freeze 增补 TTL 条（含 resume 渲染语义）③resume/消费环出口（decide 不 reopen）④启用 STATUS_EXPIRED · 状态 draft→active · GO 30 |
