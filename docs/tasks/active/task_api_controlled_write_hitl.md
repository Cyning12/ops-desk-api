# Task：阶段 W · api 受控写 + HITL（写类 capability 走 Policy + 审批闸 · decide/resume 接合 auto-resume · tenant_scope 下推一致）

> **状态**：`active`（2026-10-30 · **四闸全 approved · GO 30**：HG-TASK-DRAFT / HG-AUDIT-R1（20-R1 PASS）/ HG-GRAPH-MODULES / HG-STAGE-W-DESIGN（首条写能力=testing.write.echo · 令牌复用 PR #223 既有模型）· 均 00 代录）
> **类型**：feature / 受控写 + HITL
> **上游**：`docs/discussions/2026-09-17_interview_gaps_adoption_and_landing_v0.md` §8（阶段序 H→T→W→P）· workspace `docs/05-plan/05_post_h_stage_brief_v1_zh.md`（H α 验收 A–F · E 已预留 span `approval_id`）· workspace `docs/05-plan/06_stage_t_second_tenant_prep_v0_zh.md`（阶段 T 实态）
> **分支**：`task/api-controlled-write-hitl`（base：`master`）
> **前置**：H α（PR #138）· H β（PR #141）· 阶段 T Fixture 轨（PR #142 · `f048c57` ∈ master）· web 租户上下文（web PR #76）均已 MERGED；hitl-auto-resume 已合（PR #223）
> **10 注**：2026-10-30 · 维护者令「起草阶段 W · api 侧 task 壳」· 仅落壳 + lint + invoke · **禁止**改 `app/`；task_slug 采维护者建议 `api-controlled-write-hitl` 不调整

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `api-controlled-write-hitl` |
| **git_branch** | `task/api-controlled-write-hitl` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 单测：写类 capability Policy 闸（write/irreversible 必过审批 · deny_write fail-closed 负样本）+ HITL decide/resume 接合 auto_resume（resume_mode 三值 · 单一恢复路径）+ 写路径 tenant_scope 下推与跨租户写负样本（对外 404）；不连真外网 / 不写生产数据 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1`（预估 · 以 30 实扫为准） |
| **graph_delta** | `docs/_tech_graph/l1/01_modules.md`（capability / hitl 模块条目备注「阶段 W 受控写 · 审批闸接通」）· 不新增一级模块 |
| **graph_delta_note** | 模块边界不变（进程内注册表 + 既有 hitl 面）；仅模块内增量 → G-L1 同步；若 30 实扫涉及 flow/事件流再升 G-L2 备注 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 契约真值在 workspace contracts / web freeze；本仓可薄改 capability SPEC 备注（若涉） |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,20,30,40` |
| **invoke_retention_profile** | `default` |
| **experience_capture** | `recommended` |
| **kpi_aggregator** | `CLOSE` |
| **orchestration** | 10 落稿 → 20 R1 审查 → 维护者签 `HG-TASK-DRAFT`/`HG-AUDIT-R1`/`HG-GRAPH-MODULES`/`HG-STAGE-W-DESIGN` → 30 → 40 → CLOSE；web 审批 UX 另 task（可后合） |
| **freeze_id** | 无（默认**零改** `lg-rag-sse-v1` SSE 事件表；web 冻结契约 `hitl-browser-decide-v1` 消费语义保持稳定） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | **approved** | 20-R1, 30 | 2026-10-30 维护者签收（00 代录）· 解锁 20-R1；30 仍须其余三闸齐 |
| HG-AUDIT-R1 | **approved** | **30** | 2026-10-30 维护者签（00 代录）· 依据：20-R1 审查文 `docs/harness/reviews/task_api_controlled_write_hitl_audit_R1_20261030.md` PASS 零 blocker · M1/N1 已闭环回填 |
| HG-GRAPH-MODULES | **approved** | **30** | 2026-10-30 维护者签（00 代录）· 口径：预估 G-L1 薄增量、不新增一级模块；20-R1 抽验 `docs/_tech_graph/l1/01_modules.md` capability(:34)/hitl(:39) 条目在 · 30 交付时按实增量回签确认 |
| **HG-STAGE-W-DESIGN** | **approved** | **30** | 2026-10-30 维护者设计签收（00 代录）：① 首条写能力 = `testing.write.echo`（极窄 opt-in）② Intent/confirmation 载荷复用既有 hitl 载荷最小化、不扩 hitl 表结构（若 30 实扫需扩 → 走修订表回填）③ 审批令牌复用 hitl-auto-resume（PR #223）既有模型，身份/时效/范围不新建 |

---

## 背景与目标

讨论稿 §8 钉死阶段序 **H→T→W→P 串行**：「写不能早于租户封闭——无 T，写的爆炸半径是串租户改数」。现 H（α/β）与 T（Fixture 轨 + web 联调）均已 CLOSE，进入条件「T 跨租户负样本门禁达标」已满足；W 的剩余进入条件 = **审批与令牌设计签收**（本 task `HG-STAGE-W-DESIGN` 承载）。

W 的定义（§8.1）：**首条极窄写能力；结构化 Intent + confirmation + Policy；幂等与审计**。**不做**：自动改码合 PR；跳过 HITL。

本仓既有面已备好挂钩点：H α 验收 E 已在 span 预留 `approval_id`（`app/ops/capability/gateway.py:1318`）；capability 类型系统有 `side_effect ∈ {none, read, write, irreversible}` 与 `WRITE_SIDE_EFFECTS`、Policy `deny_write`/`allow_write_tags_any`、write 幂等键加载期强制；HITL 面（`app/ops/hitl/`）decide/resume/callback/OA-HMAC 齐备，auto-resume（T2 · PR #223）已合且 resume_mode 三值可配；web 冻结契约 `hitl-browser-decide-v1`（`ops-desk-web/src/api/hitl.ts`）只承接 api 语义。阶段 T freeze 的 F1–F6 租户契约对写路径同样生效。

本 task 交付 **api 侧最小竖切**：写类 capability 走 Policy + 审批闸（无审批不执行）→ HITL decide/resume 与 auto-resume 接合 → 写路径 tenant_scope 下推一致性 → 审计/观测串链（`approval_id` 落 span）。**刻意不做** web 页、不做 Registry 服务化。

---

## 现状锚点（只读 · 30 必读 · 10 已扫）

| 主题 | 路径 · 锚点 | 现状 |
|------|-------------|------|
| 写判定词表 | `app/ops/capability/types.py` · `SIDE_EFFECTS` / `WRITE_SIDE_EFFECTS` · `side_effect` 字段 | write/irreversible 分类已有；Policy 挂点 = side_effect（types.py:7-12 注释钉死「写操作闸（与 HITL）的唯一挂钩点」） |
| Policy 写闸 | `app/ops/capability/registry.py:120-121` · `deny_write` / `allow_write_tags_any` | deny_write 拦写；豁免只放一层 · `deny_high_risk` 永不豁免 |
| 审批串链 | `app/ops/capability/gateway.py:1318` · span `approval_id` 预留 | **预留未启用**（H α 验收 E）；W 落值 |
| HITL 端点面 | `app/ops/hitl/router.py` · pending / decide / resume / callback / requests | decide 两步钉死（默认不自动 resume）· `resume_mode ∈ {inherit, immediate, manual}`（router.py:203-207 白名单 · 未知值 **400**）· 重复已决 409 · 未知/跨用户 404 |
| auto-resume | `app/ops/hitl/auto_resume.py` · `OPS_HITL_AUTO_RESUME` ∈ {manual（默认）, auto} | PG 行锁认领（FOR UPDATE SKIP LOCKED）· 补偿扫描兜底 · 恢复**单路径** `router._execute_decided_resume`（禁 HTTP 自调 · 禁第二条实现） |
| 恢复驱动 | `app/ops/hitl/resume.py` · `resume_hitl_run` | Command(resume=…) 喂 checkpoint；`stranded_checkpoint` 竞态已有只读就绪探针 |
| 租户上下文 | `app/ops/tenant_context.py` + 阶段 T 迁移 `alembic/versions/20260918_tenant_readonly.py` | F1–F6：session 真源 + `X-Ops-Tenant-Id` 一致否则 403 · 跨租户对外 404 · A=`ops-desk-pilot` / B=`ops-desk-pilot-b` |
| 测试写能力 | `docs/tasks/done/task_testing_write_capability.md`（PR #209） | 已有非只读测试 capability 作 HITL 可审对象（罐头 adapter 零 IO） |
| web 冻结契约 | `../ops-desk-web/src/api/hitl.ts` · `hitl-browser-decide-v1` | web 只承接禁改：decide 400/404/409/422 语义 · resume 复用 · OA 签名面零触碰 |

---

## 10 钉死契约（草案 · freeze 后升格；30 不得静默改义）

| 项 | 钉死（草案） |
|----|----------------|
| **写判定** | `side_effect ∈ WRITE_SIDE_EFFECTS`（write / irreversible）的能力调用**必须**过 Policy 写闸 + HITL 审批闸；无审批直接执行 = 缺陷（fail-closed） |
| **审批对象** | HITL request 承载写 intent（结构化：capability_id + args 摘要 + tenant_id + 幂等键）；批准后置已决、走**既有** resume 单路径续跑 |
| **resume 单路径** | 复用 `router._execute_decided_resume`；接合 `auto_resume`（全局 env 默认 manual = 现状零 diff）；**禁止**第二条恢复实现 / HTTP 自调 |
| **消费语义稳定** | web `hitl-browser-decide-v1` 契约语义**不得改**：decide 未知 resume_mode → 400 · 重复已决 → 409 · 未知/跨用户 → 404 · 非法 decision → 422；OA 签名面零触碰 |
| **租户下推** | 写路径同受 F1–F6：`tenant_id` 以 session 为真源、头不一致 403；跨租户写 **fail-closed 对外 404**；审批 intent 与执行均带 tenant_scope |
| **幂等与审计** | write manifest 幂等键强制（既有 V1 不变）；span `approval_id` 落值串链（H α E 预留启用）；审批决策/执行结果可审计 |
| **SSE 零改** | 不新增/不改 SSE `event_type`；复用既有 `hitl.waiting` / `done{status}` 叙事 |
| **首条写能力** | 极窄、低爆径；候选方向（30 前由 00 与维护者在 `HG-STAGE-W-DESIGN` 钉死）：既有 testing 写能力升格为受控写样例，或单租户内无害写（如 issue 备注）；**禁**自动改码/合 PR 类 |

---

## 范围（同 task 竖切 · 四闸齐后才 30）

- [ ] **W0 · Policy 审批闸接通**：写类 capability（side_effect=write/irreversible）调用 → Policy 判序 → 未批准即挂起（HITL pending · interrupt）；负样本：无审批直接写被拒
- [ ] **W1 · HITL decide/resume 接合**：审批（decide approved）→ 复用既有 resume 单路径续跑写执行；`resume_mode` 三值与 auto_resume 触发器/补偿扫描语义保持；OA 面不动
- [ ] **W2 · tenant_scope 下推一致**：写 intent / 审批 / 执行全链带 tenant_id；跨租户写负样本（A 会话写 B 资源 → 对外 404）；头/session 不一致 → 403
- [ ] **W3 · 观测与审计**：span `approval_id` 落值（gateway.py:1318 预留启用）；审批决策 + 写执行结果可串链审计
- [ ] **W4 · 首条极窄写能力竖切**：按 `HG-STAGE-W-DESIGN` 签收选型落地一条端到端（intent → confirmation → Policy → HITL → 执行 → 审计）可演示写能力
- [ ] **W5 · 图谱薄备注**：G-L1 capability / hitl 模块条目一句；不新增一级模块；`app/ops/chat/graph.py` 既有叙事不扩改

### 非范围

- **web UI**（审批台/确认单前端另 task · `hitl-browser-decide-v1` 仅保持消费语义稳定）
- **阶段 P 平台项**：服务化 Registry、完整本体治理、多 Agent 委派平台
- **改 SSE freeze**（`lg-rag-sse-v1` 事件表 / idle keepalive / 旧 chat 410 叙事）
- **生产 P 轨数据**：生产种子/真租户数据另轨（workspace `07` §4），本 task 只用 Fixture/测试面
- 自动改码 / 自动提 PR / 自动合并（属 Coding Agent 线，非本产品 · §8.3）
- OA 签名面（HMAC）改造；iOS

---

## failure_paths

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----------|----------|--------|----------|
| `HG-TASK-DRAFT` / `HG-AUDIT-R1` / `HG-GRAPH-MODULES` / `HG-STAGE-W-DESIGN` pending 即 30 | **拒开工** | 是 | 是 |
| 无审批直接执行写类 capability | Policy + 审批闸 fail-closed · 拒 / 挂起 pending | 是（补审批） | 是（等待授权帧） |
| 契约 freeze 被静默改（`hitl-browser-decide-v1` 消费语义 / F1–F6 / SSE 事件表） | 20/40 审查拒收 · 退回 | 是 | 否 |
| 第二条 resume 实现 / HTTP 自调恢复 | 审查拒收（单路径红线 · auto_resume 模块 docstring 钉死） | 是 | 否 |
| 跨租户写（A 写 B 资源） | fail-closed · 对外 **404** · 对内 `tenant_scope_denied` · 不泄漏存在性 | 否 | 是（安全空/错） |
| 租户头与 session 不一致 | **403**（F1=C 硬门） | 否（改客户端） | 是 |
| decide 未知 `resume_mode` / 重复已决 / 未知单据 | 400 / 409 / 404（语义与 freeze 一致） | 按码 | 是 |
| 写执行中断后进程重启 | 补偿扫描兜底恢复（事件表/DB 重建 · 无进程内存态） | 是（自动） | 否 |
| 审批后写执行失败（下游错误） | 失败可观测（span + 事件）· 审批记录不丢 · 幂等键防重 | 是（按幂等键） | 是 |
| 误改 SSE event_type / 新增事件 | 审查拒收 | 是 | 否 |
| 无跨租户写负样本却宣称验收 | 40/verify 拒收 | 是 | 否 |

---

## 验收标准

- [ ] 人工闸：`HG-TASK-DRAFT` · `HG-AUDIT-R1` · `HG-GRAPH-MODULES` · `HG-STAGE-W-DESIGN` 均 approved 后方可勾选下列码项
- [ ] W0：写类 capability 未经审批不得执行（Policy 判序负样本单测绿：write/irreversible 无审批 → 拒/挂起）
- [ ] W1：decide(approved) → resume 续跑写执行全链测绿；resume_mode 三值 + auto_resume manual/auto 行为与既有语义逐条一致（含补偿扫描）；无第二条恢复路径
- [ ] W2：写路径 tenant_scope 下推；跨租户写负样本（A→B 对外 404）单测绿；头/session 不一致 403 回归绿
- [ ] **行为变更影响面（M1 · 20-R1）**：W0 给写类 capability 新挂审批闸属策略门语义变更——30 交付时须 grep 既有 `side_effect=write/irreversible` 调用与断言面并**逐条标注处理方式**（保留 / 改断言 / 负样本化）；实测影响面温和（write 现状 default `deny_write` 裁剪 · `testing.write.echo` 仅 opt-in），本项要求「逐条标注」而非预设大改
- [ ] W3：span `approval_id` 在审批串链落值（观测断言）；审批 → 执行 → 结果可审计
- [ ] W4：首条极窄写能力端到端（intent → confirmation → Policy → HITL decide → resume → 执行 → 审计）fixture 轨可演示 + 自动化断言
- [ ] `hitl-browser-decide-v1` 消费语义回归：decide 400/404/409/422 · pending 列表字段族不变（web 契约对照测）
- [ ] `ruff` 触及路径绿；`pytest` 本波相关 + 既有 capability/hitl/tenant 回归绿
- [ ] `./scripts/graph-compile.sh` 绿（G-L1 薄备注同步）；不新增 G-L1 一级模块
- [ ] SSE 事件表零 diff（`lg-rag-sse-v1` freeze 不破）
- [ ] `npx spec-wave task lint --file docs/tasks/active/task_api_controlled_write_hitl.md` PASS

---

## 依赖

| 依赖 | 说明 |
|------|------|
| 阶段决议 | `docs/discussions/2026-09-17_interview_gaps_adoption_and_landing_v0.md` §8（H→T→W→P 串行 · W 定义与进入条件） |
| H α 简报 | `../ops-desk-workspace/docs/05-plan/05_post_h_stage_brief_v1_zh.md`（验收 A–F · E=`approval_id` 预留） |
| T 实态 | `../ops-desk-workspace/docs/05-plan/06_stage_t_second_tenant_prep_v0_zh.md`（Fixture 轨 CLOSE · 生产 P 轨另轨） |
| 租户契约 freeze | `../ops-desk-workspace/docs/contracts/api-v1-tenant-readonly-context-draft.md`（F1–F6） |
| web HITL freeze | `../ops-desk-web/src/api/hitl.ts`（`hitl-browser-decide-v1` 消费语义） |
| H α / H β / T | `docs/tasks/done/task_capability_contract_hardening.md` · `task_supervisor_budget_h_beta.md` · `task_tenant_readonly_predicate.md` |
| HITL 既有面 | `docs/tasks/done/task_hitl_browser_decide.md` · hitl-auto-resume（PR #223）· `app/ops/hitl/`（router / auto_resume / resume / store / signature） |
| 测试写能力先例 | `docs/tasks/done/task_testing_write_capability.md`（PR #209） |
| 编码规范 | `docs/standards/CODING_BACKEND_L2_v1_zh.md` |

---

## 给执行帽的必读列表

1. `AGENTS.md`
2. 本 task（钉死契约 · 闸 · 非范围 · failure_paths）
3. 讨论稿 §8 + workspace 05/06 + 租户契约 F1–F6
4. `../ops-desk-web/src/api/hitl.ts`（freeze 语义对照）
5. `docs/standards/CODING_BACKEND_L2_v1_zh.md`
6. 代码：`app/ops/capability/{types,registry,gateway,manifest}.py` · `app/ops/hitl/{router,auto_resume,resume,store}.py` · `app/ops/tenant_context.py` · `app/ops/lg_rag/multi/nodes.py`（tool_exec 注入 / observe_node 挂起面）
7. `docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`

---

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|----|------|------------|----------------------|----------------|
| R0 | W = 受控写（审批闸 + Policy + HITL）+ 幂等审计；**不是**自动改码/平台项 | no | — | none |
| R1 | 进入条件盘点：H/T 已 CLOSE ✓；剩「审批与令牌设计签收」→ 新增 `HG-STAGE-W-DESIGN` 闸承载 | no | — | 设计签收周期长则 W 顺延 |
| R2 | 竖切 = W0–W4 同 task（闸→接合→租户→审计→首条能力）；SSE/web freeze 双零改红线 | no | — | 首条写能力选型未定（挂 HG-STAGE-W-DESIGN） |
| R3 | 既有面复用优先：`approval_id` 预留 / side_effect 词表 / resume 单路径均已备 → 30 为「接线」而非「新建」 | yes | 问题面已框死（契约锚点齐）；实现细节（ intent 载荷字段、令牌时效）属 HG-STAGE-W-DESIGN 与 30 实扫，非 10 轮次能钉 | intent 载荷与审批令牌设计若大改既有 hitl 表结构 → 迁移面膨胀（30 实扫后回填） |
| R4 | （未开） | — | early_stop at R3 | — |
| R5 | （未开） | — | early_stop at R3 | — |

**actual_last_round**：R3 · **early_stop**：yes · **residual_risks**：见 R3

### R0 · 问题框定

阶段 W 的核心是「受控」二字：写能力必须过 Policy + 人工审批闸，且可审计、可幂等重放。§8.3 明示「写 = 自动提 PR / 改码合并」非本产品；§8.2「写不能早于租户封闭」——T 已 CLOSE，前提满足。本 task 只框 api 侧最小竖切；web 审批 UX 另 task。

### R1 · 进入条件核对

对照 §8.1 W 行「进入条件 = T 跨租户负样本门禁达标；审批与令牌设计签收」：前者已满足（T Fixture 轨 CLOSE · web PR #76 联调 PASS），后者无现成闸承载 → 本 task 新增 `HG-STAGE-W-DESIGN`（blocks 30），避免设计未签收即写码。

### R2 · 竖切与外置红线

W0–W4 同 task 防半截合入（有闸无接合 = 假受控）。两条 freeze 红线外置钉死：`hitl-browser-decide-v1` 消费语义稳定（web 只承接禁改）+ `lg-rag-sse-v1` SSE 零改——写路径的过程可见性复用既有 `hitl.waiting`/`done{status}` 叙事。

### R3 · 复用优先 · 收敛

实扫确认既有面挂钩点齐备（types.py 写判定词表 · registry.py deny_write · gateway.py:1318 `approval_id` 预留 · hitl router/auto_resume 单路径恢复 · PR #209 测试写能力先例），30 性质为「接线 + 负样本」而非新建子系统。intent 载荷字段与审批令牌（身份/时效/范围）属设计签收项，非 10 轮次可钉 → R3 后 early_stop，残险挂账 HG-STAGE-W-DESIGN 与 30 实扫回填。

### R4 ·（未开 · early_stop）

本轮不展开；待 HG-STAGE-W-DESIGN 签收后由 20-R1 / 30 实扫补足。

### R5 ·（未开 · early_stop）

本轮不展开。

---

### 自检结论（执行者）

> **hat 40** · 未执行（draft 壳 · 四闸 pending · 30 未开工）；待 40 回填。

| 命令 | 退出码 | 摘要 |
|------|--------|------|
| `npx spec-wave task lint --file docs/tasks/active/task_api_controlled_write_hitl.md` | 0 | LINT: PASS（2026-10-30 · 10 起草自检） |

---

## 修订

| 日期 | 说明 |
|------|------|
| 2026-10-30 | 10 起草壳 · 三闸 + HG-STAGE-W-DESIGN pending · NO-GO 20/30 · R0–R3 思考轮（R3 early_stop） |
| 2026-10-30 | 20-R1 结论回填：PASS 无 blocker · M1 补列「行为变更影响面」验收项（逐条标注 write/irreversible 调用与断言面处理方式）· N1 锚点行号修正（router.py:184 → :203-207）· 闸表 status 不动 |
| 2026-10-30 | 四闸全 approved（HG-AUDIT-R1 / HG-GRAPH-MODULES / HG-STAGE-W-DESIGN 维护者签 · 00 代录）· 状态 draft→active · GO 30 |
