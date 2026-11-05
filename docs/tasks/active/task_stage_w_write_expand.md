# Task：阶段 W 扩写能力（stage-w-write-expand · 受控写闸链接入第二条真实窄写能力 · Q1 选型留闸）

> **状态**：`draft`（2026-11-05 · 00 拆 task 落稿 · **HG-STAGE-W-EXPAND-DESIGN approved**（2026-11-05 维护者签 S1）· 余三闸 pending（HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES）· **NO-GO 30 直至 20-task-audit 审毕 + 三闸签齐**）
> **类型**：feature / 受控写扩切片
> **上游**：[`SPEC-stage-w-write-expand_v0.md`](../../spec/stage-w-write-expand/SPEC-stage-w-write-expand_v0.md)（v0.1 · HG-SPEC-SIGNOFF **approved** 2026-11-05 维护者人签 · B1 已修订）· issue #323（SPEC 审查与选型签收 · 本档为签收链第 3 棒）· [`task_api_controlled_write_hitl`](../done/task_api_controlled_write_hitl.md)（CLOSE · PR #303）+ 三接合缝 fix（PR #307 join-gap · PR #313/#314 tenant-fix · PR #319 decide-owner-fallback · issue #315 CLOSE）
> **分支**：`task/stage-w-write-expand`（base：`master`；本档落稿于 `agent/stage-w-task-split-dde653139625`）
> **10 注**：2026-11-05 · 00 承 issue #323 签收链拆 task（维护者令）· 仅落 task 档 + SPEC v0.1 正本入 master + invoke 落盘 · **禁止**改 `app/`；Q1 选型三案（S1 仓内落笔 / S2 issue 备注写 / S3 sync 触发写）留 `HG-STAGE-W-EXPAND-DESIGN` task 闸随档裁决（类比 HG-STAGE-W-DESIGN 先例 · SPEC §4 Q1 建议序 S1 先行 · S2 另立独立 SPEC）

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `stage-w-write-expand` |
| **git_branch** | `task/stage-w-write-expand` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | pytest 单测/集成为主（审批闸负样本 + tenant_scope 下推负样本 + 幂等重放 + 审计串链断言 + 反回归对拍）；不连真外网 / 不写生产数据；若 Q1 裁定外部写（S2），契约测用 canned adapter，live 面留 40 复跑；不开新 freeze 面 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1`（行备注预估 · 以 30 实扫为准；不新增一级模块） |
| **graph_delta** | `docs/_tech_graph/l1/01_modules.md` capability 行一句备注「阶段 W 扩写」· 不新增一级模块 |
| **graph_delta_note** | 模块边界不变（进程内注册表 + 既有 hitl 面）；仅模块内增量 → G-L1 同步；若 30 实扫涉及 flow/事件流再升 G-L2 备注；HG-GRAPH-MODULES 随 30 回写回签 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 契约真值在 workspace contracts / web freeze；本波不改 capability SPEC 备注面 |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,20,30,40` |
| **invoke_retention_profile** | `default` |
| **experience_capture** | `recommended` |
| **kpi_aggregator** | `CLOSE` |
| **orchestration** | 10 落稿 → 20-task-audit R1 书面审 → 维护者签 HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES + **HG-STAGE-W-EXPAND-DESIGN**（Q1 选型随档裁决）→ 30 → 40 → PR+CI 绿+merge → 图谱回写 → CLOSE |
| **freeze_id** | 无（SSE `lg-rag-sse-v1` 事件表零改 · web `hitl-browser-decide-v1` 消费语义稳定 · 租户契约 F1–F6 不破；倾向零 alembic——落笔目标若须新表 → Q1/Q3 裁定并在本档修订表回填） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | **pending** | 20-R1, 30 | 壳未经 20-task-audit 书面审与维护者签收 |
| HG-AUDIT-R1 | **pending** | **30** | 20-task-audit R1 审查文未落盘（预期路径 `docs/harness/reviews/task_stage_w_write_expand_audit_R1_<日期>.md`） |
| HG-GRAPH-MODULES | **pending** | **30** | 口径：预估 G-L1 行备注薄增量、不新增一级模块；30 交付时按实增量回写回签确认（D4 承载） |
| **HG-STAGE-W-EXPAND-DESIGN** | **approved** | **Q1 选型签收：S1 仓内落笔型写中签**（Q2 随签：S1 下 env 显式 opt-in 加载面；Q3 随签：若需新表 → 修订表回填 alembic 义务）；S2 留作下一波独立 SPEC；S3 本波不碰 · 维护者 2026-11-05 签（lead 代录，签认依据 = issue #323 维护者「按建议签」+ PR #325 的 lead 选型分析评论 #6650428109） |

---

## 背景与目标

阶段 W api 侧已收口（[`task_api_controlled_write_hitl`](../done/task_api_controlled_write_hitl.md) CLOSE · PR #303 + fix 链 #307/#313/#319）：写类 capability 走 Policy 写闸 + HITL 审批闸（无审批 fail-closed 挂起）→ decide/resume 接合 auto-resume 单路径 → tenant_scope 下推一致 → span `approval_id` 审计串链。但受控写闸链上**只有一条语义 mock 写能力** `testing.write.echo`（罐头纯函数零 IO · 不进默认加载面 · `tenant_scoped: false`）——闸链建成了，生产路径上没有任何真实写能力经审批闸。

本 task 交付（承 SPEC v0.1 §1 一句话目标）：把**第二条、真实、极窄、单租户内无害**的写能力端到端接入既有受控写闸链（intent → Policy → HITL 审批 → resume 单路径 → 执行 → 审计），使阶段 W 从「闸链 + mock 演示」升级为「闸链 + 一条真实业务写竖切」。**具体写能力选型 = Q1 裁定项，挂 `HG-STAGE-W-EXPAND-DESIGN`，30 前必须签收**。

---

## 现状锚点（只读 · 30 必读 · 10 已扫）

| 主题 | 路径 · 锚点 | 现状 |
|------|-------------|------|
| SPEC 正本 | `docs/spec/stage-w-write-expand/SPEC-stage-w-write-expand_v0.md`（v0.1） | HG-SPEC-SIGNOFF approved（2026-11-05）；Q1 三案 / Q2 两案 / Q3 / Q4 + R0–R5 全轮在档，本 task 范围/验收/FP 均承 SPEC 不另裁 |
| 唯一既有写能力 | `app/ops/capability/manifests/testing.v1.yaml`（`testing.write.echo`） | 罐头纯函数零 IO；三层显式打开（`OPS_CAPABILITY_EXTRA_MANIFESTS` 显式加载 + `OPS_CAPABILITY_ALLOW_WRITE_TAGS=testing` 放行）；`tenant_scoped: false` mock 特例 |
| 审批闸编排 | `app/ops/lg_rag/multi/nodes.py`（`tool_exec_node` · PR #303） | 闸链零新建复用面；`blocked_by=capability_write_hitl_required` 语义禁改 |
| 写判定词表 | `app/ops/capability/types.py` · `WRITE_SIDE_EFFECTS` | side_effect 挂点是写闸唯一挂钩点；本波只碰 write 级可逆，不碰 irreversible |
| Policy 判序 | `registry.py::_match_filter`（:112-140 · deny 判序）+ `policy.py` 闸序段 | `deny_high_risk` 在 `deny_write` 前 · **判序段逐字节零 diff**（A5 反回归钉死）· `deny_high_risk` 永不豁免 |
| 审批串链 | `app/ops/capability/gateway.py:1318` · span `approval_id` | PR #303 已落值启用；本波对新能力只验不建（D3） |
| resume 单路径 | `app/ops/hitl/router.py::_execute_decided_resume` + `auto_resume.py` | 禁第二条恢复实现 / HTTP 自调（grep 断言 A5） |
| 租户上下文 | `app/ops/tenant_context.py` + 阶段 T F1–F6 + PR #313 消费守卫 | session 真源 + 头一致 403 · 跨租户对外 404 |
| 图谱 | `docs/_tech_graph/l1/01_modules.md` capability 行 | G-L1 一句备注待 30 回写（D4） |

---

## 10 钉死契约（承 SPEC v0.1 §1 设计纪律 · freeze 后升格；30 不得静默改义）

| 项 | 钉死 |
|----|----------------|
| **闸链零新建** | 复用 PR #303 编排层审批闸（`tool_exec_node`）；不新建第二道闸、不改 `blocked_by=capability_write_hitl_required` 语义 |
| **判序零 diff** | `registry.py::_match_filter` deny 判序（`deny_high_risk` 在 `deny_write` 前）与 `policy.py` 闸序段逐字节零 diff；`deny_high_risk` 永不豁免 |
| **resume 单路径** | 复用 `router._execute_decided_resume`；禁第二条恢复实现 / HTTP 自调 |
| **租户封闭** | 新写能力 `tenant_scoped: true`（与 testing.write.echo 的 false 形成对照）；写 intent / 审批 / 执行全链带 tenant_id；跨租户写 fail-closed 对外 404（F1–F6 存续） |
| **显式打开纪律** | 新能力默认不进默认加载面（沿 testing.v1.yaml 三层显式打开先例：manifest env 显式加载 + 写 tag 显式放行），默认零 diff |
| **幂等** | 写 manifest 顶层 `idempotency_key` 声明位强制（loader V1 纪律）；重放不双写 |
| **加载期断言（Q4 · v0.1 B1 修订口径）** | 30 加加载期断言：「除 mock 特例清单（`testing.write.echo`，以 `testing`/`mock` tag 为谓词）外，写能力 `tenant_scoped` 必须为 true；**特例清单不扩容**」 |
| **首条写 tag 独立** | 新能力 `tags` 含独立写 tag，不放行 `testing` tag 复用（SPEC D1） |

---

## 范围（承 SPEC §2 D 块 · 四闸齐后才 30）

- [ ] **D1 · 第二条窄写能力选型与接入**（必做 · **选型挂 Q1 + HG-STAGE-W-EXPAND-DESIGN**）：按 Q1 裁定的一条真实写能力端到端经既有闸链（`side_effect: write` 先 write 级可逆，不碰 irreversible → Policy 写闸 → HITL 审批闸挂起 → decide(approved) → resume 单路径续跑 → 执行 → span `approval_id` 串链审计）；manifest 字段族对齐 builtin.v1.yaml/testing.v1.yaml 范式；`hitl.required: true` 显式声明；能力可见性经 `∩ visible`（strategy builder）与 allowlist 全链照旧——新能力可达 ≠ 默认可达
- [ ] **D2 · 租户下推与负样本**（必做）：新能力 `tenant_scoped: true`；写路径 A 会话写 B 资源 → 对外 404 / 头 session 不一致 403（复用 F1–F6 与 PR #313 消费守卫）；负样本断言：无审批直接执行 fail-closed 挂起 / env 未显式开启时能力不可见 / 幂等重放不双写
- [ ] **D3 · 审计与观测**（必做）：既有 `capability_write_approval_consumed` 台账 + span `approval_id` 串链对新能力原样生效（**只验不建**）；若 30 实扫发现落值缺口 → 本档修订表回填，不静默扩面
- [ ] **D4 · 图谱与文档回写**（必做）：`docs/_tech_graph/l1/01_modules.md` capability 行一句备注（G-L1）；不新增一级模块；HG-GRAPH-MODULES 随 30 回写回签

### 非范围（承 SPEC §3 · 与上游一致）

- ❌ 第三条及更多写能力（本波只扩一条；批量接入属阶段 P/本体治理）
- ❌ irreversible 级写（先 write 级可逆；不可逆写另案）
- ❌ 自动改码 / 自动提 PR / 自动合并（血统不变）
- ❌ web UI / 审批台前端（web 面已 CLOSE；`hitl-browser-decide-v1` 消费语义禁改）
- ❌ SSE 事件表改动（`lg-rag-sse-v1` freeze 不破；复用 `hitl.waiting`/`done{status}` 叙事）
- ❌ 闸链改造：HITL 表结构、decide/resume 状态机、auto-resume 触发器/补偿扫描一行不动（jsonb 载荷增键若必需 → 本档修订表回填）
- ❌ OA 签名面 / iOS / 阶段 P 平台项
- ❌ 生产 P 轨数据（Fixture/测试面 only）

---

## failure_paths（承 SPEC §5 · 裁定照锚既有语义）

| # | 触发条件 | 系统行为 | 可重试 | 用户可见 |
|---|----------|----------|--------|----------|
| FP-1 | 无审批直接执行新写能力 | fail-closed 挂起 pending（既有闸链原样生效）· 负样本断言 | 是（补审批） | 是（等待授权帧） |
| FP-2 | 跨租户写（A 写 B）/ 头 session 不一致 | 对外 404 / 403（F1–F6 + PR #313 消费守卫原样） | 否（改客户端） | 是 |
| FP-3 | env 未显式开启 | 能力不可见（默认加载面零 diff 断言） | 是（显式打开） | 否（安全空） |
| FP-4 | 幂等键重放 | 不双写（幂等键强制度照旧） | 是 | 否 |
| FP-5 | 审批过期（TTL）后执行 | 读时判过期不消费 → 回到挂起态（PR #307 W-fix-1 语义原样） | 是（重新审批） | 是 |
| FP-6（仅 Q1=S2 时启用） | 外部 API 失败 / 超时 / 凭据缺失 | 执行失败可观测（span+事件）· 审批记录不丢 · 按幂等键可重试；**审批 ≠ 执行成功**语义在审计上显式区分 | 是（按幂等键） | 是 |
| FP-7 | 静默改闸链 / 判序 / SSE 事件表 / web 契约 | 20/40 审查拒收退回（红线） | 是 | 否 |
| — | HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES / HG-STAGE-W-EXPAND-DESIGN 任一 pending 即 30 | **拒开工** | 是（签闸后） | 是 |

---

## 验收标准（承 SPEC §6 A1–A8 · 可机验）

- [ ] 人工闸：HG-TASK-DRAFT · HG-AUDIT-R1 · HG-GRAPH-MODULES · **HG-STAGE-W-EXPAND-DESIGN** 均 approved 后方可勾选下列码项（Q1 选型未签 = NO-GO 30）
- [ ] **A1 端到端竖切**：选定写能力 fixture 轨可达「plans 含写 tool → hitl.waiting → pending → decide(approved) → resume（含 auto 模式）→ 执行落笔 → done{completed}」全链自动化断言
- [ ] **A2 负样本组**：无审批 fail-closed；跨租户 404；头/session 403；env 未开启不可见；幂等重放不双写
- [ ] **A2+ 加载期断言（SPEC §4 Q4 · v0.1 口径）**：除 mock 特例清单（`testing.write.echo` · `testing`/`mock` tag 谓词）外，写能力 `tenant_scoped` 必须为 true；特例清单不扩容
- [ ] **A3 租户下推**：写 intent/审批/执行三处 tenant_id 一致（断言 + M1 式影响面逐条标注）
- [ ] **A4 审计串链**：span `approval_id` + `capability_write_approval_consumed` 台账对新能力落值；审批决策与执行结果可串链查询
- [ ] **A5 反回归钉死**：`registry.py::_match_filter` / `policy.py` 闸序段 git diff 为空；PR #303/#307/#313/#319 既有测试原样绿；resume 单路径无第二实现（grep 断言）
- [ ] **A6 freeze 零破**：SSE 事件表零 diff；`hitl-browser-decide-v1` 400/404/409/422 语义回归绿
- [ ] **A7 工程面**：`pytest tests` 全绿（CI 为准）；`ruff` 触及路径零新增；`./scripts/graph-compile.sh` EXIT=0；G-L1 备注回写
- [ ] **A8 lint**：`npx spec-wave task lint` PASS

---

## 依赖

| 依赖 | 说明 |
|------|------|
| SPEC 正本 | [`docs/spec/stage-w-write-expand/SPEC-stage-w-write-expand_v0.md`](../../spec/stage-w-write-expand/SPEC-stage-w-write-expand_v0.md)（v0.1 · signed · Q1–Q4 全裁定项在档） |
| issue #323 | SPEC 审查与选型签收（20-spec-audit R1 → HG-SPEC-SIGNOFF → 本档） |
| 上游 task | [`task_api_controlled_write_hitl`](../done/task_api_controlled_write_hitl.md)（CLOSE · PR #303）· [`task_api_w_join_gap_fix`](../done/task_api_w_join_gap_fix.md)（PR #307）· [`task_api_w_hitl_tenant_fix`](../done/task_api_w_hitl_tenant_fix.md)（PR #313/#314）· [`task_fix_hitl_decide_owner_fallback`](../done/task_fix_hitl_decide_owner_fallback.md)（PR #319） |
| 上游讨论 | `docs/discussions/2026-09-17_interview_gaps_adoption_and_landing_v0.md` §8.1（W 定义「首条极窄写能力」→ 本波扩第二条） |
| 测试写能力先例 | [`task_testing_write_capability`](../done/task_testing_write_capability.md)（PR #209 · 三层显式打开先例） |
| 租户契约 freeze | workspace `docs/contracts/api-v1-tenant-readonly-context-draft.md`（F1–F6） |
| web HITL freeze | `../ops-desk-web/src/api/hitl.ts`（`hitl-browser-decide-v1` 消费语义） |
| 编码规范 | `docs/standards/CODING_BACKEND_L2_v1_zh.md` |
| 图谱 | `docs/_tech_graph/l1/01_modules.md`（capability 行 · D4 回写面） |

---

## 给执行帽的必读列表

1. `AGENTS.md`
2. 本 task（钉死契约 · 闸 · 非范围 · failure_paths）
3. [`SPEC-stage-w-write-expand_v0.md`](../../spec/stage-w-write-expand/SPEC-stage-w-write-expand_v0.md)（范围/非范围/FP/A1–A8/Q1–Q4/R0–R5 真值）
4. `docs/discussions/2026-09-17_interview_gaps_adoption_and_landing_v0.md` §8.1
5. `../ops-desk-web/src/api/hitl.ts`（freeze 语义对照）
6. `docs/standards/CODING_BACKEND_L2_v1_zh.md`
7. 代码：`app/ops/capability/{types,registry,gateway,manifest}.py` · `app/ops/capability/manifests/testing.v1.yaml` · `app/ops/lg_rag/multi/nodes.py`（tool_exec 审批闸）· `app/ops/hitl/{router,auto_resume,resume}.py` · `app/ops/tenant_context.py` · `app/ops/admin/service.py`（S3 候选面）
8. `docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`

---

## 思考轮控制

> 本档为 00 拆 task 产物：R0–R5 思考承 SPEC v0.1 §7（10-spec 已全轮 done · 20-spec-audit R1 复核毕），10-task 不重开思考轮、不另裁；task 层残余未定项唯一 = **Q1 选型**，归口 `HG-STAGE-W-EXPAND-DESIGN`（issue #323 维护者 2026-11-05 令）。

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|----|------|------------|----------------------|----------------|
| R0 | 承 SPEC §7 R0：方向 = 受控写闸链接入第二条真实窄写能力（维护者 2026-11-05 立项令） | no | — | none |
| R1 | 承 SPEC §7 R1：范围 = 一条真实窄写能力接入既有闸链（闸链零新建）；非范围八条锁定 | no | — | none |
| R2 | 承 SPEC §7 R2：Q1 三案（S1/S2/S3）+ Q2/Q3/Q4 技术裁定建议；核心选型留维护者 → **task 闸 HG-STAGE-W-EXPAND-DESIGN** | no | — | Q1 未签则 30 NO-GO |
| R3 | 承 SPEC §7 R3：FP-1~FP-7 逐条锚既有语义（fail-closed / F1–F6 / TTL 读时过期 / 幂等键）；S2 增 FP-6 外部失败面 | no | — | none |
| R4 | 承 SPEC §7 R4：A1–A8 可机验；pytest 不连外网（S2 canned 替身）；live 留 40 | no | — | none |
| R5 | 承 SPEC §7 R5：SPEC 签收毕（HG-SPEC-SIGNOFF approved 2026-11-05）→ 00 拆 task 落稿；task 闸四枚 pending | no | — | 20-task-audit 未审 · Q1 选型未签 |

**actual_last_round**：R5（承 SPEC）· **early_stop**：no · **residual_risks**：Q1 选型未签（HG-STAGE-W-EXPAND-DESIGN）；若 30 实扫须新表 → 修订表回填 alembic 义务；S2 若中签 → env/凭据面与 FP-6 按 SPEC 口径另铺

### R0 · 问题框定（承 SPEC §7 R0）

维护者 2026-11-05 方向裁定「阶段 W 扩写能力」（active 为空时的排期裁定）；磁盘实态实读：W 竖切 + 三 fix CLOSE、active 为空、全仓唯一 write capability = `testing.write.echo`（mock · opt-in · tenant_scoped=false）。task 层问题框定 = 把 SPEC v0.1 落成可执行可验收 task 档，不另开思考。

### R1 · 范围/非范围（承 SPEC §7 R1）

范围 = 一条真实窄写能力接入既有闸链（闸链零新建），D1–D4 同 task 竖切；非范围八条锁定（不多扩 / 不碰 irreversible / 无 web UI / SSE 零改 / HITL 表结构不动 / 无平台项 / 无生产数据 / 无自动改码）。

### R2 · 方案对比（承 SPEC §7 R2）

Q1 三案（S1 仓内落笔 / S2 issue 备注写 / S3 sync 触发写）+ Q2 两案 + Q3/Q4 技术裁定建议均在 SPEC §4；10-spec 建议序 S1 先行、S2 另立独立 SPEC。**核心选型留维护者** → task 闸 HG-STAGE-W-EXPAND-DESIGN（issue #323 维护者 2026-11-05 令 · 类比 HG-STAGE-W-DESIGN 先例），task 档不越权同裁。

### R3 · 边界/失败路径（承 SPEC §7 R3）

FP-1~FP-7 逐条锚既有语义（fail-closed 挂起 / F1–F6 跨租户 404 与头 403 / env 未开启不可见 / 幂等键重放不双写 / TTL 读时过期回挂起 / S2 增 FP-6 外部失败面 / 静默改红线拒收），task 档照承不另裁。

### R4 · 验收/可测性（承 SPEC §7 R4）

A1–A8 可机验照承；pytest 不连真外网（S2 时契约测 canned adapter）；live 面留 40 复跑；task 档补 A2+ 加载期断言验收项（SPEC §4 Q4 v0.1 口径显式化，防 30 漏项）。

### R5 · 签收就绪（承 SPEC §7 R5）

SPEC 签收毕（HG-SPEC-SIGNOFF approved 2026-11-05 · B1 已修订）→ 00 拆 task 落稿（本档）；残余未定项唯一 = Q1 选型（HG-STAGE-W-EXPAND-DESIGN pending）+ 20-task-audit 未审 → 四闸全 pending，NO-GO 20/30。

---

### 自检结论（执行者）

> **hat 10（00 拆 task 派发）** · 已落稿：task 档 + SPEC v0.1 正本（merge `spec/stage-w-write-expand` `fa83be6`）+ 10 invoke 落盘 · 未改 `app/` / `alembic/` / `tests/` · 未签任何 human_gate（四闸 pending · Q1 留 HG-STAGE-W-EXPAND-DESIGN）。

| 命令 | 退出码 | 摘要 |
|------|--------|------|
| `npx spec-wave@3.5.0 task lint --file docs/tasks/active/task_stage_w_write_expand.md` | 0 | LINT: PASS（2026-11-05 · 10 起草自检 · 零 warn） |
| `npx spec-wave@3.5.0 task lint-wiki-delta --target .` | 0 | LINT-WIKI-DELTA: PASS（scope all · scanned 206 · missing 0 · issues 0） |

---

## 修订

| 日期 | 说明 |
|------|------|
| 2026-11-05 | 10 落稿：00 承 issue #323 签收链拆 task（承 SPEC v0.1 · HG-SPEC-SIGNOFF approved）· 四闸 pending（HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES / HG-STAGE-W-EXPAND-DESIGN）· NO-GO 20/30 · Q1 选型留闸随档裁决 · R0–R5 承 SPEC §7 |
