# Task：ops.write 覆盖与能力目录实际行为对账（能力声明 ↔ manifest 一致性 + 端到端实跑常驻覆盖）

> **状态**：`done`（2026-11-06 · 全棒链同日闭环：10 落稿 → lead 签四闸 → 30 实现（lead 验收合并 `039f802`）→ 40 复跑机制面 PASS → 50 CLOSE 归档）
> **类型**：fix / 测试面（ops.write.* 能力目录对账覆盖缺口 · **纯测试面** · 红线=不改实现）
> **上游**：issue [#336](https://github.com/Cyning12/ops-desk-api/issues/336)（backlog 正文 + 维护者 comment [`6678466745`](https://github.com/Cyning12/ops-desk-api/issues/336#issuecomment-6678466745) 令起草 · 补发受理 comment [`6679927635`](https://github.com/Cyning12/ops-desk-api/issues/336#issuecomment-6679927635) · 受理依据 = 维护者 2026-11-06 13:40 授权（lead 代行签收与验收））
> **分支**：10/00 走 `agent/catalog-reconcile-task-e848e9dbbf56`（本 PR · 部署绑定要求末段=工单名）· 30 实分支预登记 `fix/ops-write-catalog-reconcile`（待闸签收后另行授权）
> **10 注**：2026-11-06 · 承 issue #336 维护者 comment `6678466745` 令起草 fix task（**10 帽活** · 只产 task 档 + 10 invoke + lint PASS + PR · 禁改业务码）· 设计闸决策点 = **覆盖形态**（一致性机检 vs 端到端实跑 vs 两者）× **双口径**（intent 准入实际行为 vs spec 目录声明 · 维护者补发令 `6679927635`）· **四闸已签**（2026-11-06 · lead 签认 · 签认依据 = issue #336 comment `6678466745` + `6679927635` + 2026-11-06 13:40 授权 · **设计闸裁决 = 案③两者**：案①机检打底（CI 常驻·双向漂移秒红）+ 案②端到端补强（真闸链驱动·补行为层实证）× A1 双口径——缺口在双向×双口四格，单一形态必留空格）· **30 授权随 issue 评论下发**（另令 · 未至前 NO-GO 30）

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `ops-write-catalog-reconcile` |
| **git_branch** | `agent/catalog-reconcile-task-e848e9dbbf56`（10 起草 PR 分支 · 部署绑定末段=工单名；30 执行分支预登记 `fix/ops-write-catalog-reconcile`） |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 红测先行 · 负样本端到端（维护者令第 2 条「红测先行写进 test_strategy · 负样本按所选形态定」+ 补发令「红测负样本端到端」）：30 按 HG-OPS-WRITE-COVERAGE-DESIGN 签认形态落测试面——①一致性机检面 = 目录声明 ↔ manifest 文件 ↔ catalog 注册规格的逐字段对账断言（先红 = 现状无常驻对账面 · 构造漂移即红 · 后绿 = 对账断言落地）；②端到端实跑面 = 负样本经真实闸链驱动（intent → Policy 写闸 → HITL 审批 → resume 单路径 → 执行 → 审计串链），禁直造状态直调（同链单测盲区教训：`_worker_state` 丢 `run_id` 由 live 才暴露）；两形态若同签（案③）则两族红测皆先红后绿 |
| **code_quality_bar** | `L2_backend`（涉码面=纯新增测试；既有实现零改动红线） |
| **graph_change_layer** | `none`（预期：纯测试面增量 · 无路由/表/事件类型/一级模块面；若 30 实扫出现图谱面须先回闸再动） |
| **graph_delta** | `n/a` |
| **graph_delta_note** | 模块边界不变（测试文件增量 · 非 G-L0/L1/L2 业务模块改动）；不触发图谱同步义务（承 AGENTS.md：仅新增路由/表/事件类型须同步）；HG-GRAPH-MODULES 以 `none` 口径随档签认 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 契约真值在 workspace contracts / freeze；本波零 wiki 面 |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,20,30,40` |
| **invoke_retention_profile** | `default` |
| **experience_capture** | `recommended` |
| **kpi_aggregator** | `CLOSE` |
| **orchestration** | 10 落稿（PR #354 `fd0fbbe` · task 档 + 10 invoke）→ lead 签四闸（PR #354 review `5797443083` · 20-R1 审查文）→ 30 实现（PR #355 `039f802` · 两族对账测试 19 枚 · 六条件全过）→ **40 复跑机制面 PASS**（worktree @ `039f802` 独立复跑：19 + 114 + 全量 2102 passed 零新增红 · 漂移反向实证 10/10 · verify 闸据恢复 PASS）→ 50 CLOSE（active→done 归档 + CLOSE 档 + 双 README · 关账 PR 待 lead 验收） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | approved | 20-R1, 30 | lead 签认 2026-11-06（PR #354 review `5797443083` · 签认依据 = issue #336 comment `6678466745` + `6679927635` + 2026-11-06 13:40 授权）：题面/背景/现状锚点表/A1 锚点语义专节/钉死契约七条齐备，红线照录 |
| HG-AUDIT-R1 | approved | 30 | lead 签认 2026-11-06（同上 review）：实扫诚实（建设期测试≠对账面的区分清晰） |
| HG-GRAPH-MODULES | approved | 30 | lead 签认 2026-11-06（同上 review）：`none` 口径（纯测试面） |
| **HG-OPS-WRITE-COVERAGE-DESIGN** | approved | **30** | **设计闸 · lead 签认 2026-11-06**（同上 review）· **裁决 = 案③两者**：案①一致性机检打底（CI 常驻 · 双向漂移秒红）+ 案②端到端实跑补强（真闸链驱动 · 补「声明有·行为无」的行为层实证）× A1 双口径；理由 = 缺口恰在双向×双口四个格子，单一形态必留两个空格；案③两族并落成本可控（对账对象首枚仅 `ops.write.run_note`）· 30 只执行签认形态（案③ · 两族红测皆先红后绿），不自裁（FP-5） |

---

## 背景与目标

issue #336（backlog，来源 #323 40 invoke 增强/收尾清单）：**SPEC v0.1 注册的 ops.write.* 能力缺专属测试覆盖——能力目录对账面缺口**。维护者定性（comment `6678466745`）：`ops.write.run_note` **capability_catalog 有、manifest v1.0 三读全绿**，但「能力声明↔manifest 一致性」和「端到端实跑」都**没有覆盖到它**。要求补测试覆盖（**纯测试面**）；红线=**不改实现**。

**现状锚点（只读 · 30 必读 · 10 已扫 2026-11-06）——ops.write.* 能力全链与既有覆盖面**：

| 主题 | 路径 · 锚点 | 现状 |
|------|-------------|------|
| 能力声明（spec 目录口径②） | `app/ops/capability/manifests/ops.write.v1.yaml`（v1.0 · stage-w D1 落盘） | 仓内 **唯一** `ops.write.*` 注册能力 = `ops.write.run_note`（run 备注/审计便签 · `tenant_scoped: true` · `hitl.required: true` + snapshot_fields · 顶层 `idempotency_key: "{{request_id}}"` · output_fields/output_schema · reversible 四字段） |
| 三层显式打开 | manifest 不进默认加载面（`OPS_CAPABILITY_EXTRA_MANIFESTS` 显式加载）+ `OPS_CAPABILITY_ALLOW_WRITE_TAGS=run_note` 独立写 tag 放行（只豁免 deny_write 一层 · deny_high_risk 永不豁免） | 加载≠可见≠可写：三道准入判据各自独立（可达 ≠ 默认可达） |
| 执行体（intent 准入口径①） | `app/ops/capability/defaults.py::ops_write_run_note` + `note_store.py`（DB IO 集中） | 真落笔 adapter：tenant 只取 ctx · `approval_id` 落便签行串链 · 幂等 store claim + 落笔表 `(tenant_id, idempotency_key)` 唯一约束双保险 |
| 准入闸链（intent 准入口径①） | SPEC v0.1：intent → Policy 写闸 → HITL 审批挂起 → decide(approved) → resume 单路径 → 执行 → span `approval_id` 审计串链 | loader V13：write 级 `tenant_scoped` 强制（mock 特例清单不扩容）；跨租户 fail-closed 对外 404 |
| 既有测试面 | `tests/test_stage_w_write_expand.py`（16 枚 · A1 机制全链 / V13 四断言 / FP-4 双形态 / A3 租户隔离 / A2 负样本组 / A5 grep）+ `tests/test_fix_worker_state_send_run_id.py` + `tests/test_fix_planner_args_schema.py` | **建设期竖切测试**：钉死「接进来时是对的」，**非对账面**——无「目录声明 ↔ 实际行为」双向漂移检测；manifest 字段以测试内断言零散钉住，非全量逐字段对账 |
| live 实证链 | stage-w 40 invoke 八段实录（`invoke_20261105_40_verify.md`）+ fix-worker-state 40 + fix-planner-args 40 | **一次性人工核验**，非常驻测试覆盖；三波 live 均带 env 前置专配（非默认面） |
| 缺口 | 「能力声明↔manifest 一致性」无常驻对账断言；「端到端实跑」无常驻专属测试面（#336 正文机制） | 目录声明与实际准入行为漂移（声明有·行为无 / 行为有·声明无）无任何测试会红 |

**结论（10 档）**：缺陷 = 能力目录对账覆盖缺口（测试面 · 非码面缺陷）：`ops.write.run_note` 已在目录声明全绿，但声明↔行为双口径无常驻对账。stage-w 16 测为建设期机制测试，#336 题面要求的对账面（双口径 · 双向漂移检测）为真实缺口。**覆盖形态（案①/案②/案③）留设计闸 HG-OPS-WRITE-COVERAGE-DESIGN**，10 档不越权定形态。本 task = 对账覆盖落地竖切：按签认形态落测试面 + 红线对拍。

---

## A1 锚点语义（本档定义 · 维护者令「A1 锚点语义见 task 档」）

> issue #336 补发令 `6679927635` 指定：设计闸决策点以 **intent 准入 vs spec 目录双口径**为对账框架，**A1 锚点语义在本档钉死**，后续 20/30/40 各棒引用 A1 时以本节为唯一真源。

**A1 = ops.write.* 能力目录对账锚点**。语义三要素：

1. **双口径**：对账必须在两条口径上同时成立——
   - **口径① intent 准入**：运行时受控写闸链的**实际行为**（能力被 invoke 时真实发生的准入判序：加载在场 → 可见性放行（写 tag 白名单）→ Policy 写闸 → HITL 审批挂起 → 审批命中消费 → resume 单路径续跑 → 执行落笔 → 审计串链）；
   - **口径② spec 目录**：能力**声明面**（manifest 文件注册规格 × SPEC v0.1 设计纪律 × catalog 可见性端点声明）。
2. **双向漂移即缺陷**：任一方向漂移皆判缺口——**声明有·行为无**（目录声明了某行为断言，实际准入链无对应实证）与**行为有·声明无**（实际准入链出现声明面未登记的行为/字段/判据），两类漂移在对账测试下都必须**红**。
3. **对账可机断**：每条对账断言必须落到具体锚（文件 + 键路径 / 函数 / 事件名 / SSE 帧键），禁「语义级口头对账」；对账集本身随 ops.write.* 能力集扩展（当前对账对象 = `ops.write.run_note` 一枚 · R0 实扫校正，新增 ops.write.* 能力时同锚复用）。

**红线继承 A1 语义**：凡以 A1 为锚的测试面改动——**fail-closed 判据永不放宽**（对账只增断言不删断言；负样本禁改成放行）；**SSE 事件表零 diff**（对账不得经新增/改形 SSE 事件类型达成）；**改码面收敛**（对账落点=纯测试面，实现一行不动）。

---

## 10 钉死契约（承 issue #336 维护者令 · freeze 后升格 · 30 不得静默改义）

| 项 | 钉死 |
|----|----------------|
| **决策点属闸** | 覆盖形态（案①一致性机检 / 案②端到端实跑 / 案③两者 × 双口径裁决）是 **HG-OPS-WRITE-COVERAGE-DESIGN 的决策**，30 只执行签认形态，禁自裁（FP-5） |
| **不改实现** | #336 正文红线：`app/` 实现一行不动（含 registry/policy/gateway/lg_rag/defaults/note_store/manifest loader）；对账只经测试面达成（FP-4） |
| **A1 双口径对账** | 对账断言按 A1 语义落双口径：声明有·行为无 → 红；行为有·声明无 → 红；断言锚到具体文件/键/事件（A1 语义见专节） |
| **fail-closed 不放宽** | 负样本断言禁「改断言适配实现」；对账只增不删；既有 16 测等旧断言零放宽适配（FP-2） |
| **SSE 事件表零 diff** | `lg-rag-sse-v1` 不破：不新增/不改 SSE `event_type` 与帧形态；对账不得借 SSE 面落新事件（FP-3） |
| **红测先行** | 30 新测一律先红后绿：先在对账面下构造漂移/负样本实证红，后落断言转绿；负样本端到端（经真实闸链驱动 · 禁直造状态直调） |
| **闸表四列契约 + 纯 pending 纪律** | 30 不得破坏人工闸四列契约；10/20 档不得代签任何 human_gate |

---

## 范围（竖切 · 四闸齐后才 30）

- [ ] **D-rec-1 · 对账测试面**（30 执行 · 以 HG-OPS-WRITE-COVERAGE-DESIGN 签认为准）：按签认形态落常驻测试——①案①：spec 目录声明 ↔ `ops.write.v1.yaml` 注册规格 ↔ catalog 注册面（加载后的 `CapabilitySpec`）逐字段对账断言集，断言锚 A1 双口径；②案②：端到端实跑族（正样本全链达成 + 负样本组按 A1 语义构造），经真实 intent→审批→resume→执行路径驱动；③案③：两族并落。对账对象首枚 = `ops.write.run_note`；断言须覆盖三层显式打开各判据（加载在场 / tag 放行 / 审批必挂）与幂等·租户封闭·审计串链声明。
- [ ] **D-rec-2 · 旧测影响面实扫**：既有测试族（stage-w 16 测 / capability 族 / manifest 族）grep 影响面如实登记（零适配亦如实列出）；适配不得放宽既有断言（钉死契约六）。
- [ ] **D-rec-3 · 偏差与基线登记**：既有本地产能红基线复核（承 40 先例 · master 干净树对拍 · 零新增红口径）+ 环境性偏差照登。

### 非范围

- ❌ 覆盖形态（案①/②/③）的自行裁定（决策点是闸的 · FP-5）
- ❌ `app/` 任何实现改动（#336 正文红线=不改实现 · registry/policy/gateway/lg_rag/defaults/note_store/manifest loader 一行不动 · FP-4）
- ❌ SSE 事件表 / 帧形态 / `event_store` 写入面（`lg-rag-sse-v1` freeze · FP-3）
- ❌ manifest 文件本体改动（`ops.write.v1.yaml` 声明面是**对账基准**，非改动对象）
- ❌ 新 ops.write.* 能力注册（本 task 只对账现有能力 · 新增能力另案）
- ❌ 既有测试断言放宽 / 删除（FP-2）
- ❌ spec-wave 上游 / `task lint` 规则本体改动（机检确需扩展 → 停下报另案）
- ❌ web 仓 / iOS / 平台项

---

## failure_paths

| # | 触发条件 | 系统行为 | 可重试 | 用户可见 |
|---|----------|----------|--------|----------|
| FP-1 | 四闸任一 pending 即 30 | **拒开工** | 是（签闸后） | 是 |
| FP-2 | 对账测试试图放宽/删除既有断言以适配现状（fail-closed 放宽面） | **拒合并**：红测先行纪律破——负样本被改成放行即 A1 语义破（fail-closed 不放宽） | 否 | 是 |
| FP-3 | 对账经新增/改形 SSE 事件类型或帧达成 | **拒合并**：`lg-rag-sse-v1` freeze 破（SSE 事件表零 diff） | 否 | 是 |
| FP-4 | 30 实扫出现 `app/` 实现改动（含 registry/policy/gateway/lg_rag/defaults/note_store/manifest loader） | **拒合并**：改码面破（#336 正文红线=不改实现 · 对账必须纯测试面达成） | 否 | 是 |
| FP-5 | 30 自行裁定覆盖形态（案①/②/③ 或双口径权重）而未按 HG-OPS-WRITE-COVERAGE-DESIGN 签认 | **拒开工/拒合并**：决策点属闸 | 是（签闸后） | 是 |
| FP-6 | 对账断言脱离 A1 锚（口头语义级断言 · 无文件/键/事件锚） | **退回 30**：A1 语义要求对账可机断（锚到具体面） | 是 | 否 |
| FP-7 | 负样本直造状态直调（不经真实闸链驱动） | **退回 30**：单测盲区教训（`_worker_state` 丢 `run_id` 仅 live 暴露）——直调用例自带全 state，覆盖不到编排链丢键面 | 是 | 否 |
| FP-8 | 对账只测单口径（只声明面或只行为面） | **退回 30**：A1 双口径语义破（漂移两方向皆须红） | 是 | 否 |
| FP-9 | manifest 本体被改动以对齐测试（把基准改成迁就断言） | **拒合并**：对账基准被污染——断言必须迁就真值，真值不得迁就断言 | 否 | 是 |
| FP-10 | 闸表四列契约破坏 / 人工闸代签 | **拒合并**：record 杠杆破 | 否 | 是 |

---

## 验收标准

- [ ] HG-OPS-WRITE-COVERAGE-DESIGN 签认覆盖形态落闸表行（案①/②/③ + 双口径裁决依据），30 按签认形态交付
- [ ] 对账测试面先红后绿：红证据（对账面下构造漂移即红）与绿证据（断言落地转绿）双留痕
- [ ] 负样本端到端：经真实 intent → Policy → HITL → resume → 执行路径驱动（禁直造状态直调 · FP-7）
- [ ] A1 双口径对账：声明有·行为无 / 行为有·声明无 两方向漂移皆有断言会红（FP-8）
- [ ] 红线对拍零命中：`git diff` 对拍 `app/`（含 registry/policy/gateway/lg_rag/defaults/note_store/manifest loader）零 diff；SSE 事件表零 diff（FP-3/FP-4）
- [ ] 既有测试零放宽：stage-w 16 测 / capability 族 / manifest 族断言零删零松（FP-2）；关联回归全绿 + 全量 `pytest tests` 零新增红（既有红基线如实登记）
- [ ] `ruff check app tests` 触及路径零新增；`./scripts/graph-compile.sh` EXIT=0；`npx --yes spec-wave task lint --file <本档>` PASS（零 warn）；`npx --yes spec-wave task lint-wiki-delta --target .` PASS
- [ ] 40 复跑（留 40）：独立复跑不采信 30 自报（worktree @ 30 出货 commit）——对账断言独立转绿 + 红线对拍零命中 + 漂移构造反向实证（对账断言真的会红）

---

## 依赖

| 依赖 | 说明 |
|------|-----|
| 缺陷源 | issue [#336](https://github.com/Cyning12/ops-desk-api/issues/336)（正文：ops.write.* 三能力缺专属测试面 · 纯测试面 · 红线=不改实现 · 立项令 = comment [`6678466745`](https://github.com/Cyning12/ops-desk-api/issues/336#issuecomment-6678466745) 四要求 + 补发令 [`6679927635`](https://github.com/Cyning12/ops-desk-api/issues/336#issuecomment-6679927635)） |
| 上游证据链 | #323 40 invoke 增强/收尾清单（`docs/harness/invokes/by-task/stage-w-write-expand/`） |
| 对账基准面 | [`ops.write.v1.yaml`](../../app/ops/capability/manifests/ops.write.v1.yaml)（v1.0 声明 · 只读基准）· SPEC v0.1（`docs/spec/stage-w-write-expand/SPEC-stage-w-write-expand_v0.md` · 设计纪律六条 + D1–D4）· [`defaults.py`](../../app/ops/capability/defaults.py) `ops_write_run_note`（行为面）· `note_store.py` |
| 既有测试面 | [`test_stage_w_write_expand.py`](../../tests/test_stage_w_write_expand.py)（16 枚建设期测试 · 对账面缺口对照组）· [`test_capability_manifest.py`](../../tests/test_capability_manifest.py)（manifest 加载族） |
| live 实证链 | stage-w 40 invoke 八段实录（八段判据 = 对账正样本的 live 参照系） |
| freeze 参照 | SSE `lg-rag-sse-v1`（事件表 · 零 diff 红线） |
| 编码规范 | `docs/standards/CODING_BACKEND_L2_v1_zh.md`（测试码适用） |

---

## 给执行帽的必读列表

1. `AGENTS.md`（启动纪律 · 四闸扫描）
2. 本 task（A1 锚点语义专节 · 钉死契约 · 闸 · 非范围 · failure_paths）
3. issue #336 全文（题面 + 维护者立项令四要求 + 补发令）
4. `app/ops/capability/manifests/ops.write.v1.yaml`（对账基准 · 只读）· `docs/spec/stage-w-write-expand/SPEC-stage-w-write-expand_v0.md`（声明面真值）
5. [`test_stage_w_write_expand.py`](../../tests/test_stage_w_write_expand.py)（既有覆盖面 · 对账缺口对照）· stage-w 40 invoke（八段 live 参照系）
6. `docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`（闸据消费形态）· `docs/harness/templates/TASK_TEMPLATE.md`（闸表四列契约）

---

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|----|------|------------|----------------------|----------------|
| R0 | 缺陷 = 能力目录对账覆盖缺口（测试面 · 非码面）：`ops.write.run_note` 目录声明全绿但「声明↔manifest 一致性」与「端到端实跑」无常驻对账覆盖；实扫校正 #336 正文「三能力」= 仓内当前唯一 `ops.write.*` 注册能力 `ops.write.run_note`（manifest 全仓 grep · 2026-11-06） | no | — | 「三能力」字面与实扫（一枚）不符：按题面语义（对账覆盖缺口）落档，对账锚 A1 设计为能力集可扩展；若维护者所指另两能力在仓外/未注册面 → 20-R1 或设计闸澄清 |
| R1 | 范围 = 对账测试面（按签认形态）+ 旧测影响面实扫 + 偏差基线登记；非范围九条锁定（形态自裁/实现改动/SSE/manifest 本体/新能力注册/断言放宽/spec-wave 上游/web·iOS）；决策点属闸钉死 | no | — | none |
| R2 | 设计闸三案对比（HG-OPS-WRITE-COVERAGE-DESIGN 决策点）：**案①一致性机检**（声明↔manifest↔注册规格逐字段对账 · 快·稳·全机断 · 风险=覆盖不到运行时行为漂移 · 锚 A1 口径②偏重）/ **案②端到端实跑**（正负样本真实闸链驱动 · 实证最强 · 风险=环境依赖 DB·成本高 · 锚 A1 口径①）/ **案③两者**（机检打底 + 端到端补强 · 覆盖最全 · 工作量最大）；双口径权重与组合形态留维护者裁决，10 档不预断（FP-5/FP-8） | no | — | 三案对 A1 双口径的覆盖不均（①偏声明面 · ②偏行为面），取舍是维护者裁决面 |
| R3 | failure_paths 锚既有语义：四闸拒开工（FP-1）/ 三红线（fail-closed FP-2 · SSE FP-3 · 改码面 FP-4）/ 决策点属闸（FP-5）/ A1 锚漂移（口头断言 FP-6 · 直造状态 FP-7 · 单口径 FP-8）/ 基准污染（FP-9）/ 闸表契约（FP-10） | no | — | none |
| R4 | 可测性：红测先行 + 负样本端到端（维护者令第 2 条）——负样本 = A1 语义下「声明有·行为无」（如声明了幂等双保险但单测路径绕过 DB 约束）与「行为有·声明无」（如准入链出现未登记判据）漂移构造，经真实闸链驱动；先红 = 现状无常驻对账面必红，后绿 = 断言落地；40 反向实证（断言真的会红）留 40 | no | — | 端到端族环境依赖（DB `ops_capability_notes` · 承 stage-w `_DB_MARK` skipif 先例）；live 面留 40 |
| R5 | 起草落稿 · A1 锚点语义专节钉死 · 四闸 pending · NO-GO 20/30 · lint PASS 出货待审 · 30 待闸签收后另行授权（维护者令 + 2026-11-06 13:40 授权 · lead 代行签收与验收） | no | — | 无 |

**actual_last_round**：R5 · **early_stop**：no · **residual_risks**：①「三能力」字面与实扫一枚之差（见 R0 · 设计闸可澄清）；②三案双口径权重待 HG-OPS-WRITE-COVERAGE-DESIGN 裁决（见 R2）

### R0 · 问题框定

issue #336 由维护者立项（backlog · 来源 #323 40 invoke 收尾清单）：ops.write.* 能力缺专属测试覆盖。10 档实扫（2026-11-06）：仓内 `ops.write.*` 唯一注册能力 = `ops.write.run_note`（`ops.write.v1.yaml` 单枚 · 全仓 grep 无其他 ops.write.* id）；既有 16 测（stage-w 建设期）覆盖机制链但**非对账面**——无声明↔行为双向漂移检测；live 八段实录为一次性人工核验非常驻覆盖。题面（维护者 comment `6678466745`）：capability_catalog 有、manifest v1.0 三读全绿，但「能力声明↔manifest 一致性」与「端到端实跑」都没有覆盖到它。

### R1 · 范围/非范围

范围三件套（对账测试面 / 旧测影响面实扫 / 偏差基线登记）收敛为最小竖切；非范围把「会被顺手扩大」的面全部锁死：形态自裁（FP-5）、`app/` 实现改动（FP-4 · #336 正文红线）、SSE 面（FP-3）、manifest 本体（对账基准非改动对象 · FP-9）、新能力注册、断言放宽（FP-2）、spec-wave 上游、web/iOS。

### R2 · 方案对比（设计闸决策点 · HG-OPS-WRITE-COVERAGE-DESIGN）

- **案① 一致性机检**：spec 目录声明 ↔ `ops.write.v1.yaml` ↔ 加载后 `CapabilitySpec` 逐字段对账（加载期/静态断言 · 含三层显式打开各判据在场性）。优点：快、稳、全机断、零环境依赖。风险：只锚 A1 口径②（声明面），运行时行为漂移（口径①）覆盖不到——如「声明 hitl.required 但实际 invoke 未挂审批」机检看不见。
- **案② 端到端实跑**：正样本（全链达成 · 八段 live 参照系的测试化）+ 负样本组（未放行 tag → 不可见/被拒；审批未命中 → 执行零落笔；幂等重放 → 不双写；租户谓词缺失 → 拒），经真实闸链驱动。优点：A1 双口径的行为面实证最强。风险：DB 环境依赖、成本高、墙钟长。
- **案③ 两者**：机检打底（声明面全字段）+ 端到端补强（行为面关键链）。覆盖最全，工作量最大；双口径权重（哪些断言归机检、哪些必须端到端）是裁决面。

### R3 · 边界/失败路径

FP-1~FP-10 逐条锚既有语义：四闸拒开工 / fail-closed 不放宽 / SSE 零 diff / 改码面收敛（不改实现）/ 决策点属闸 / A1 锚三裂口（口头断言 · 直造状态 · 单口径）/ 基准污染 / 闸表契约。核心新增 = FP-6~FP-9 四条 A1 语义专属闸：对账必须锚定可机断、必须真实链驱动、必须双口径、基准只读。

### R4 · 验收/可测性

维护者令第 2 条：红测先行写进 test_strategy，负样本按所选形态定。补发令明确「红测负样本端到端」。本档 test_strategy_note 按签认形态分流：机检面负样本 = 构造声明-注册漂移（改副本 manifest 字段 → 对账断言红）；端到端面负样本 = A1 双口径漂移场景经真实闸链驱动。先红证据 = 现状无常驻对账面（漂移构造无任何断言拦截），后绿 = 断言落地。40 反向实证：对账断言在漂移构造下真的会红（防「恒绿假对账」）。

### R5 · 签收就绪

task 档落稿（含 A1 锚点语义专节）· 10 invoke 落盘 · 四闸 pending · NO-GO 20/30 · lint PASS 后出 PR 待审 · 30 改码须待闸签收后另行授权（issue #336 维护者令 · 受理依据 = 2026-11-06 13:40 授权 · lead 代行签收与验收）。

---

### 自检结论（执行者）

> **hat 10（10 起草）** · 已落稿：task 档 + 10 invoke · 未改 `app/` / `tests/` · 未签任何 human_gate（四闸 pending · NO-GO 20/30）。

| 命令 | 退出码 | 摘要 |
|------|--------|------|
| `npx --yes spec-wave@3.5.0 task lint --file docs/tasks/active/task_ops_write_catalog_reconcile.md` | 0 | LINT: PASS（2026-11-06 · 10 起草自检） |
| `npx --yes spec-wave@3.5.0 task lint-wiki-delta --target .` | 0 | LINT-WIKI-DELTA: PASS（scope all · 本档 wiki_delta 预填） |

> **hat 30（30 实现 · 案③两者）** · 30 授权 = issue #336 comment `6680378035`（六交付条件）· 交付 = 两族对账测试（`tests/test_ops_write_catalog_reconcile.py` 19 枚）+ 闸表签认回填 · `app/` 零 diff。

| 命令 | 退出码 | 摘要 |
|------|--------|------|
| `.venv/bin/pytest tests/test_ops_write_catalog_reconcile.py -q` | 0 | **19 passed**（族①机检 13 + 族②端到端 6：漂移矩阵 10 例 + args 负样本 3 例为参数化） |
| 红证据：漂移矩阵脚本（invoke 留痕） | — | 10/10 漂移被拦（loader V1/V2/V8/adapter 4 枚 + 对账断言红 6 枚）· args 负样本 3/3 fail-closed（args_schema_invalid · 零落笔） |
| `.venv/bin/pytest tests/test_stage_w_write_expand.py tests/test_capability_manifest.py tests/test_capability_testing_write.py tests/test_write_approval_gate.py tests/test_capability_idempotency.py tests/test_capability_reversibility.py tests/test_fix_planner_args_schema.py tests/test_fix_worker_state_send_run_id.py -q` | 0 | **114 passed**（旧测影响面 grep 实扫 4 族引用 run_note · 零适配零放宽） |
| `.venv/bin/ruff check app tests` | 0 | All checks passed!（I001 自修 1 枚） |
| `./scripts/graph-compile.sh` | 0 | done（EXIT=0） |
| `git diff origin/master...HEAD --name-only \| grep -v '^docs/'` | 空 | **app/ 零 diff**（红线对拍 · 纯测试面达成） |

**对账实扫发现（偏差登记 · A1 双向漂移实证）**：成功路径 adapter 出键 `receipt`（抓取载荷）未在 `output_fields` 声明（行为有·声明无）；`duplicate_of` 为**重放路径条件出键**，成功路径永不出（声明有·行为无）。两偏差已在测试内精确钉死并登记，声明面对齐（manifest output_fields 增补/路径条件标注）建议另案裁决——本 task 改码面禁动实现与基准（FP-4/FP-9）。

**环境注记**：本机 venv 补装 `pytest-asyncio`（pyproject 已声明 · requirements.txt 无 pytest 系 · CI skip 绿面不受影响）；真 PG `opsdesk_test` 本地可达，DB 用例真跑非 skip。

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-11-06 | 10 落稿：承 issue #336 维护者 comment `6678466745` 令起草 fix task（10 帽活 · 只产 task 档 + 10 invoke + lint PASS + PR · 禁改业务码）· 补发令 `6679927635` 四要求全落：设计闸 HG-OPS-WRITE-COVERAGE-DESIGN 决策点 = 覆盖形态三案（一致性机检/端到端实跑/两者 × intent 准入 vs spec 目录双口径）/ 红测负样本端到端入 test_strategy / 三红线入 failure_paths（A1 锚点语义本档专节钉死 · fail-closed 不放宽 FP-2 · SSE 零 diff FP-3 · 改码面收敛 FP-4）+ A1 专属闸 FP-6~FP-9 · R0–R5 全轮 · R0 实扫校正「三能力」= 仓内唯一 ops.write.* 能力 run_note · 四闸 pending · NO-GO 20/30 · 30 待闸签收后另行授权 |
| 2026-11-06 | 四闸签认回填（lead 代录 · PR #354 review `5797443083` · 设计闸裁决 = **案③两者**）+ 30 实现（授权令 = issue #336 comment `6680378035` · 六条件全过）：两族对账测试 `tests/test_ops_write_catalog_reconcile.py` 19 枚（族①机检 13 + 族②端到端 6）· 漂移矩阵 10/10 被拦红证据 + args 负样本 3/3 fail-closed 实证 · 全量 2102 passed 零新增红（master 基线同 4 红 worktree 独立复证）· **对账实扫发现漂移 2 枚**（偏差① receipt 行为有·声明无 / 偏差② duplicate_of 声明有·行为无 · 测试内精确钉死 · 声明面对齐建议另案）· app/ 零 diff · ruff / graph-compile / task lint 双 PASS · 30 invoke 落档 |
| 2026-11-06 | 40 复跑 + 50 CLOSE（40 令 = issue #336 comment `6681442245`「30 已验收合并（039f802）· 全绿则关账」· 依据 13:40 多选授权）：**40 机制面 PASS**——独立复跑不采信 30 自报（worktree `/tmp/verify40-recon` @ `039f802`：新测 19 / 关联 114 / 全量 2102 passed 零新增红 · master 基线同 4 红复证 · 漂移反向实证 10/10 · ruff / graph-compile / verify 四闸 approved 全绿）· **20-R1 审查文 + 20 invoke 补档**（30 期遗漏 · verify 闸据恢复 · 非自签 · source = PR #354 review `5797443083`）· 50 CLOSE：active→done 归档 + CLOSE 档 `docs/tasks/close/close_ops_write_catalog_reconcile_20261106.md` + 双 README + 40/50 invoke · 关账 PR 待 lead 验收 |
