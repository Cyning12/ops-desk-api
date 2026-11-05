# Task：write ticket 拉起幂等守卫（`reset_worker_seen_surface` 后首轮巡检不重复拉起）

> **状态**：`in_progress`（10 起草壳 PR #345 已合 `ec87535` · **四闸 approved**（签认依据 = PR #345 review `5792245814` lead 签 + 窗口授权 2026-11-05 22:26 指令）· **30 已授权交付**（issue #335 comment `6669768156` 六条件 · 出货 PR 待审））
> **类型**：fix / 缺陷修复（write ticket 拉起幂等缺口 · worker 重启后 seen 面重置无守卫）
> **上游**：issue [#335](https://github.com/Cyning12/ops-desk-api/issues/335)（backlog 正文 + 维护者 comment `6668554143` 令立项 · 受理依据 = 窗口授权 2026-11-05 22:26 → 2026-11-06 07:00 · lead 代行签收与验收）
> **分支**：10/00 走 `agent/idempotency-fix-task-4b3782da80c4`（本 PR · 部署绑定末段=工单名）· 30 实分支预登记 `fix/seen-surface-idempotency`（待闸签收后另行授权）
> **10 注**：2026-11-06 · 承 issue #335 维护者令起草 fix task（**10 帽活** · 只产 task 档 + 10 invoke + lint PASS + PR · 禁改业务码）· 30 改码待闸签收后另行授权
> **30 注**：2026-11-06 · 维护者 comment `6669768156` 30 授权（六交付条件）· **设计闸决策点①裁决**（引用本评论）：探针实证承载面 = **nodes.py 拉起链双点**——`_join_subtasks` 巡检派发面（孪生步重复派发：重复拉起噪音 + 建单风险）+ `_persist_hitl` 建单面（精确 sid 去重对孪生 sid 不可见 ⇒ **重复建单实证**：同 run 同写意图库面 2 笔 + 写闸拦截行 2 条）——裁决 = **案 A ∪ 案 B 同链双点半卫**（10 档 R2 单点倾向修正 · 锚点留痕纪律）：①巡检层守卫 `_write_blocked_call_keys`——同写意图在途写单步被孪生时继承在途终态（`replay_of` 溯源 · 不派发不消费 · 留痕 `write_ticket_twin_inherited`）；②建单层守卫 `_write_intent_live_key`（status 位：库面 live 写单按 (capability_id, args_summary) 索引 · pending 全量 + approved 未过期）——命中 ⇒ `arelocate_linkage` 存量单连接域迁附当前步并带回（不新建 · 留痕 `hitl_write_intent_attached`）；与 `already`（seen_surface 位）合成 **status ∧ seen_surface 双条件**（决策点②签认语义落地）。改码面唯一 = `nodes.py` 拉起链 + `hitl/store.py` 增量方法（Protocol/InMemory/Db/Null · 无表结构/语义面变更）+ 新测 3 枚；守卫共用既有 `LG_RAG_WRITE_REPLAY_GUARD_ENABLED` 单开关（关 = master 基线零 diff）；**消费门（`_write_execution_approval`/`_match_fresh_approved`）/ resume 单路径 / SSE / worker freeze 一行不动**

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `fix-seen-surface-idempotency` |
| **git_branch** | `agent/idempotency-fix-task-4b3782da80c4`（10 起草 PR 分支 · 部署绑定要求末段=工单名；30 实分支预登记 `fix/seen-surface-idempotency`） |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 红测先行：负样本（维护者红线）=「`reset_worker_seen_surface` 后首轮巡检不重复拉起存量 write ticket」——经**真巡检/派发路径**驱动（禁直造 state 直调 · 同链单测盲区教训），先红（重置 seen 面后首轮巡检重复拉起实证）后绿（守卫落地后不重复拉起 · 端到端断言：存量 write ticket 建单/拉起动作恰一次、无第二次拉起、overlap 警告台账零新增）；正样本对拍：无重置的常规巡检轮次拉起行为与修复前零漂移；既有消费门 fail-closed 负样本组（`test_write_approval_gate` / `test_hitl_approval_consumption`）全绿不放宽；live 面留 40 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `none`（预期：幂等守卫小修 · 无路由/表/事件类型/一级模块面；若 30 实扫出现图谱面须先回闸再动） |
| **graph_delta** | `n/a` |
| **graph_delta_note** | 模块边界不变（巡检/建单/消费链内增量守卫）；不触发图谱同步义务（承 AGENTS.md：仅新增路由/表/事件类型须同步）；HG-GRAPH-MODULES 以 `none` 口径随档签认 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 契约真值在 workspace contracts / freeze；本波零 wiki 面 |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,20,30,40` |
| **invoke_retention_profile** | `default` |
| **experience_capture** | `recommended` |
| **kpi_aggregator** | `CLOSE` |
| **orchestration** | 10 落稿（本 PR · task 档 + 10 invoke）→ 20-R1 书面审（审查文落盘 `docs/harness/reviews/`）→ 维护者签 **HG-WRITE-TICKET-IDEMPOTENCY-DESIGN**（修复落点 + ticket 幂等键语义双决策点）+ 三常闸（HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES）→ PR 出货待审 → **30 改码须待闸签收后另行授权**（`fix/seen-surface-idempotency` · GATE_VERIFY 闸据=本档闸表）→ 40 → CLOSE |
| **freeze_id** | `lg-rag-sse-v1`（**零 diff 红线**：SSE 事件表/帧形态） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | **approved** | 20-R1, 30 | lead 签认 2026-11-05 · 依据 = PR #345 review `5792245814`（APPROVED）+ 窗口授权 2026-11-05 22:26 指令 + #335 comment `6668554143` |
| HG-AUDIT-R1 | **approved** | **30** | lead 签认 2026-11-05 · 依据同上——lead PR #345 review `5792245814` 审查通过即 20-R1 书面审记录（审查文随 30 PR 出货落盘 `docs/harness/reviews/` · 承 lead review 明示） |
| HG-GRAPH-MODULES | **approved** | **30** | lead 签认 2026-11-05 · 依据同上 · `none` 口径签认确认（无图谱面 · 承 no-proxy/delegation 先例；若 30 实扫出图谱面须回签） |
| **HG-WRITE-TICKET-IDEMPOTENCY-DESIGN** | **approved** | **30** | **设计闸 · lead 签认 2026-11-05 · 依据同上**（维护者 comment `6668554143` 令设）· **双决策点照留**：决策点① = 修复落点——30 红测探针实证后裁决（候选案 A 巡检层守卫=倾向 / B 建单拉起层 / C 只压警告=禁 · 见 R2）；决策点② = ticket 幂等键语义 = **status / seen_surface 双条件位**（库面真实状态位 ∧ worker seen 面位 · 缺一不可 · 签认留档 · 见 R2） |

---

## 背景与目标

issue #335（backlog）：**`reset_worker_seen_surface` 后首次巡检重复拉起存量 write ticket（幂等缺口）**——worker 重启后 seen 面重置无幂等守卫，触发 overlap_warning 噪音（来源：#323 stage-w 40 invoke 实测证据链 · `docs/harness/invokes/by-task/stage-w-write-expand/`）。维护者定性：小修——补幂等守卫消警告；红线 = worker freeze 不动语义 + 四红线（resume 单路径 / SSE 事件表零 diff / 消费门 fail-closed 永不放宽 / 改码面收敛）。

**10 档实扫声明（如实留痕）**：仓内 grep 未检到字面符号 `reset_worker_seen_surface` / `overlap_warning`（`app/` `tests/` `scripts/` `docs/` 零命中）——维护者用的是机制命名（seen 面 = worker 进程内「已拉起/已见」去重面；重置 = worker 重启后该面归零）。缺陷的精确承载面（巡检循环 / 拉起点 / 警告台账键名）以 **30 红测探针**为执行规格先行定位，设计闸决策点①据此裁决（承 delegation 先例「锚点修正如实留痕」纪律）。

同链相关机制（只读锚点 · 10 已扫 · 30 必读）：

- **建单层既有 DB 幂等先例**：`_persist_hitl`（`app/ops/lg_rag/multi/nodes.py:2180-2240`）建单前去重**不能只看 state**（interrupt 挂起时 return 值不进 checkpoint，恢复重跑会重复建单）——真相在 store，幂等键 = `(run_id, subtask_id)` 级三元组；`_approved_fresh_for_subtask`（:2142-2182）以新鲜 approved 单据抑制重复建单（镜像 `_approval_consumed` 匹配语义 · fail-open + `hitl_persist_guard_read_failed` 台账）。
- **写闸 / 消费门**：`_write_execution_approval`（:462-533 · fail-closed · delegation 类查命中不重复消费）· `_approval_consumed`（:418-460 · fail-closed · 不写回单据状态）。
- **巡检形态先例**：HITL auto-resume 补偿扫描（`app/ops/hitl/auto_resume.py:233-296`）= 周期巡检 + **启动首轮立即执行**（worker 重启后首轮即扫 · 与本缺陷「reset 后首轮巡检」同形态）；行锁认领防并发双触发。
- **resume 单路径**：`app/ops/hitl/router.py:493-533 _execute_decided_resume` → `app/ops/hitl/resume.py:303-378 resume_hitl_run` → `app/ops/lg_rag/multi/nodes.py:2299-2353 _apply_hitl_decision`（手动 / T2 auto-resume / 补偿扫描同源单链）。

本 task = 该缺陷的最小修复竖切：**write ticket 拉起的幂等守卫**（重置 seen 面后首轮巡检不重复拉起存量单据）+ 红测负样本（端到端断言）+ 常规路径零漂移对拍。

---

## 范围（竖切 · 四闸齐后才 30）

- [x] **D-fix-1 · 幂等守卫**（30 已交付 2026-11-06 · 裁决 = 案 A ∪ B 双点半卫 · 见 30 注）：①巡检层 `_write_blocked_call_keys` + 孪生继承（`write_ticket_twin_inherited` 留痕）②建单层 `_write_intent_live_key`（status 位）+ `arelocate_linkage` 迁附带回（`hitl_write_intent_attached` 留痕）· 双条件 = status ∧ seen_surface（决策点②落地）。
- [x] **D-fix-2 · 红测负样本 + 常规对拍**（30 已交付 2026-11-06 · **先红后绿实证**）：负样本（维护者红线）= 真链挂起 → checkpoint 重建（seen 面重置 · 前置断言 `hitl_requests` 必空）→ 重规划孪生 → 首轮巡检（真 join/persist）→ **修复前红**：库面 2 笔同写意图票 + 写闸拦截行 2 条（`run-…:1`/`:2` 双拉起实证）→ **修复后绿**：库面恰一笔（存量 T1 迁附孪生步）· 拦截行零新增 · 孪生步不派发（`replay_of` 溯源）。常规对拍 2 枚：同 sid 重放 attach 既有语义零漂移 + 成功孪生 replay-guard 面零漂移。
- [x] **D-fix-3 · 旧测适配**（30 实扫 2026-11-06：**零适配**）：写闸 / 消费门 / 保号 / resume / delegation / stage-w 全组 122 枚断言对象均不锚「孪生写步建单」形态——实扫零影响如实列出，无适配发生。

### 非范围

- ❌ 消费门语义任何改动（`_approval_consumed` / `_write_execution_approval` fail-closed · 判序 · TTL · 租户守卫 · `blocked_by` 类守卫 · 「不写回单据状态」契约）
- ❌ resume 单路径（禁第二实现 / HTTP 自调 / 旁路线程 · A5 grep 断言承接）
- ❌ SSE 事件表 / 帧形态 / `event_store` 写入面（`lg-rag-sse-v1` freeze）
- ❌ worker freeze / 生命周期语义（issue #335 正文红线：worker freeze 不动语义）
- ❌ HITL 表结构 / decide-resume 状态机 / auto-resume 触发器与补偿扫描周期参数
- ❌ 委派令牌机制 · 闸链 · 写闸判定序
- ❌ **只压警告不修幂等**（把 overlap_warning 降噪/静默当修复 = 治标不治本 · 禁）
- ❌ web 仓 / iOS / 平台项

---

## failure_paths

| # | 触发条件 | 系统行为 | 可重试 | 用户可见 |
|---|----------|----------|--------|----------|
| FP-1 | 四闸任一 pending 即 30 | **拒开工** | 是（签闸后） | 是 |
| FP-2 | **resume 第二实现**（新恢复路径 / HTTP 自调 / 旁路线程） | A5 grep 断言红 · 审查拒收退回（红线） | 是 | 否 |
| FP-3 | **SSE 事件表出现 diff**（`lg-rag-sse-v1` 破） | 审查拒收 · 退回（红线） | 是 | 否 |
| FP-4 | **消费门 fail-closed 被放宽**（未命中改放行 / fail-open 化 / 判序漂移 / TTL 或租户守卫松动） | 红测拦截 · 审查拒收退回（红线） | 是 | 否 |
| FP-5 | **改码面外溢**（闸链 / HITL 表 / 状态机 / auto-resume / 委派令牌 / 写闸判定序 / worker freeze 面被碰） | 红线对拍 diff 非空 · 审查拒收 | 是 | 否 |
| FP-6 | **幂等键语义被削成单条件**（只看 seen 面位 → 重启重置后照样重复拉起 = 本缺陷未修；只看库面 status 位 → 正常新单被误判重复、永久拒拉起） | 红测负样本/对拍红 · 审查拒收 | 是 | 是（重复拉起噪音 / 单据传不上去） |
| FP-7 | 负样本未转绿即出货（reset 后首轮巡检仍重复拉起） | 红测拦截 · 审查拒收 | 是 | 否 |
| FP-8 | **只压 overlap_warning 噪声**（日志降级/静默/去重显示）而未补幂等守卫 | 审查拒收 · 退回（治标不治本 · 同消警告≠修缺陷先例口径） | 是 | 否 |
| FP-9 | 幂等守卫被做成**放行口**（把「已拉起过」误用为「免审批放行」） | fail-closed 原样拦（守卫只判重、不动放行判定；消费门负样本组既有断言承接） | 是（补审批） | 是（等待授权帧） |
| FP-10 | 守卫读失败（库面/状态读异常） | **fail-closed**：视为「不可判重」→ 不重复拉起方向上保守（宁可本轮不拉起等下轮，不可重复拉起）；读异常留痕台账（钉死键名 · 30 回填） | 是（下轮巡检） | 否（巡检日志可见） |

---

## 验收标准

- [x] 人工闸：HG-TASK-DRAFT · HG-AUDIT-R1 · HG-GRAPH-MODULES · **HG-WRITE-TICKET-IDEMPOTENCY-DESIGN** 均 approved（签认依据 = PR #345 review `5792245814` + issue #335 comment `6669768156` + 窗口授权）
- [x] 红测负样本（**维护者红线**）：reset seen 面（checkpoint 重建 · seen 面重置前置断言）→ 首轮巡检 → 端到端断言存量 write ticket 拉起恰一次（**先红**：库面 2 笔 + 双拦截行实证 → **后绿**：恰一笔 + 零新增 · `tests/test_fix_seen_surface_idempotency.py`）
- [x] 幂等键语义 = status / seen_surface 双条件位落地（决策点②签认口径逐条对照：status 位 = `intent_live` 库面索引（capability_write 类 · 带 write_intent · pending 全量 + approved 未过期 TTL 同口径）· seen_surface 位 = `already` 本轮面；双条件缺一不可注释显性化 · FP-6 两形态：不同 args ⇒ 不同 intent 键不合并（args_summary 决定性序列化）· 同 args 跨 sid ⇒ 合并（本修复语义））
- [x] 常规对拍：无重置巡检轮次（同 sid 重放 attach / 成功孪生 guard-skip）与修复前零漂移（2 枚对拍绿）
- [x] 四红线零 diff 对拍：resume 单路径（`router.py`/`resume.py` **零 diff**）· SSE 事件表零 diff（`event_store`/`sse_*` 零 diff）· 消费门 fail-closed 既有负样本组全绿（`test_write_approval_gate` / `test_hitl_approval_consumption` 全组）· 改码面收敛（`git diff` 面 = `nodes.py` + `hitl/store.py` 唯一）
- [x] 旧测 grep 影响面适配（零适配如实登记）；巡检 / 建单 / 写闸 / 消费 / resume 测试族关联回归全绿（122 passed）
- [x] 工程面：`ruff check app tests` **All checks passed（零）**；`pytest tests` 全量零新增红（如实登记）；`./scripts/graph-compile.sh` EXIT=0；`npx spec-wave task lint` PASS
- [ ] 40 复跑（live 面 · 待 40）：worker 重启后首轮巡检 live 实测 · 存量 write ticket 单拉起实证

---

## 依赖

| 依赖 | 说明 |
|------|-----|
| 缺陷源 | issue [#335](https://github.com/Cyning12/ops-desk-api/issues/335)（正文 + 维护者 comment `6668554143` 立项令：task 档六要素 / 设计闸双决策点 / 红测负样本 / 四红线入 failure_paths / lint PASS 出货） |
| 上游证据链 | #323 stage-w 40 invoke：`docs/harness/invokes/by-task/stage-w-write-expand/invoke_20261105_40_verify.md`（live 全链实测 · write 闸链证据面） |
| 同链先例 | [`task_fix_delegation_resume_approval_id.md`](../done/task_fix_delegation_resume_approval_id.md)（CLOSE · PR #341/#343 · 同链 · 设计闸两决策点 + 四红线 + 红测端到端形态先例 · **锚点修正如实留痕纪律**）· [`task_fix_worker_state_send_run_id.md`](../done/task_fix_worker_state_send_run_id.md)（CLOSE · PR #331/#332/#340 · 同 resume/派发链） |
| 改码面（预期） | 巡检/拉起链单点（以设计闸签认为准 · 候选锚点见背景节）+ 新增回归测试 |
| freeze 参照 | SSE `lg-rag-sse-v1`（事件表） |
| 编码规范 | `docs/standards/CODING_BACKEND_L2_v1_zh.md` |
| 另波跟踪 | issue #339（supervisor planner string-args · 非本 task） |

---

## 给执行帽的必读列表

1. `AGENTS.md`
2. 本 task（钉死契约 · 闸 · 非范围 · failure_paths · R2 候选案）
3. issue #335 全文（缺陷定性 · 维护者立项令与红线）
4. 代码：`app/ops/lg_rag/multi/nodes.py:418-460`（`_approval_consumed`）· `:462-533`（`_write_execution_approval`）· `:2142-2182`（`_approved_fresh_for_subtask` 建单守卫）· `:2180-2240`（`_persist_hitl` 建单幂等先例）· `:2299-2353`（`_apply_hitl_decision`）· `app/ops/hitl/auto_resume.py:233-296`（补偿扫描 = 巡检形态先例 · 启动首轮立即执行）· `app/ops/hitl/router.py:493-533`（`_execute_decided_resume` · resume 单路径）
5. 测试面：`tests/test_write_approval_gate.py`（写闸负样本组）· `tests/test_hitl_approval_consumption.py`（消费门负样本组）· `tests/test_fix_delegation_resume_approval_id.py`（同链端到端红测形态参照）
6. `docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`

---

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|----|------|------------|----------------------|----------------|
| R0 | 本 task = 维护者 issue #335 定性的幂等缺口小修（非设计探索）：reset seen 面后首轮巡检重复拉起存量 write ticket；维护者机制命名（`reset_worker_seen_surface` / `overlap_warning`）在仓内无字面符号 → 精确承载面留 30 红测探针 | no | — | 承载面（巡检循环/拉起点/警告台账）10 档未实锤 · 30 探针定位 |
| R1 | 范围 = 幂等守卫（落点待闸）+ 红测负样本 + 常规对拍 + 条件旧测适配；非范围十一条锁定（消费门语义/resume 单路径/SSE/worker freeze/表结构/状态机/补偿扫描/委派令牌/只压警告/web 面） | no | — | none |
| R2 | 设计闸两决策点：①修复落点三案——A 巡检层守卫（seen 面重置/重建时并入库面 status 真源 · 重启可恢复 · **倾向**）/ B 建单/拉起层守卫（扩 `_persist_hitl` 类 DB 幂等键至双条件位 · 若承载面在建单侧则直接适用）/ C 只压警告（**禁** · FP-8）；②ticket 幂等键语义 = status/seen_surface 双条件位——status 位（库面真实状态：pending/approved/in-flight）∧ seen_surface 位（worker 本轮已见）；只看 seen 位 = 本缺陷（重启重置即重拉），只看 status 位 = 误杀正常新单（拒拉起）→ 双条件缺一不可，语义裁定入闸 | no | — | 案 A/B 取舍取决于 30 探针实证承载面（巡检层 vs 建单层）· 裁决时须附探针证据 |
| R3 | failure_paths 锚既有语义：四闸拒开工（FP-1）/ resume 第二实现（FP-2）/ SSE 零 diff（FP-3）/ fail-closed 放宽（FP-4）/ 改码面外溢含 worker freeze（FP-5）/ 幂等键削成单条件两形态（FP-6）/ 负样本未绿出货（FP-7）/ 只压警告（FP-8）/ 守卫变放行口（FP-9）/ 守卫读失败 fail-closed 方向（FP-10） | no | — | none |
| R4 | 可测性：负样本必须经真巡检/派发路径驱动（禁直造 state 直调——单测盲区是同链通病）；reset 语义 = 显式 seen 面重置（新 worker 实例/重置钩子 · 以 30 探针实选定承载面为准）；先红后绿；常规对拍防过紧语义；live 面留 40 | no | — | 本地产能既有红基线如实登记口径沿用 |
| R5 | 起草落稿 · 四闸 pending · NO-GO 20/30；lint PASS 后出 PR 待审；30 改码须待闸签收后另行授权（issue #335 维护者令 · 窗口授权至 2026-11-06 07:00） | no | — | 无 |

**actual_last_round**：R5 · **early_stop**：no · **residual_risks**：缺陷精确承载面待 30 红测探针定位（见 R0/R2）

### R0 · 问题框定

issue #335 由维护者定性（backlog · 小修）：`reset_worker_seen_surface` 后首次巡检重复拉起存量 write ticket（幂等缺口），worker 重启后 seen 面重置无幂等守卫，触发 overlap_warning 噪音；来源 #323 stage-w 40 invoke 实测证据链。task 性质 = 补幂等守卫消警告的小修，非方向探索。10 档实扫：字面符号 `reset_worker_seen_surface` / `overlap_warning` 仓内零命中（如实声明，承 delegation 锚点修正先例——10 不臆造锚点），精确承载面以 30 红测探针为执行规格先行定位。

### R1 · 范围/非范围

范围四件套（幂等守卫 / 红测负样本 + 常规对拍 / 条件旧测适配）收敛为最小竖切；非范围把「会被顺手扩大」的面全部锁死：消费门语义与「不写回单据状态」契约、resume 单路径、SSE 事件表、worker freeze 语义、HITL 表结构、auto-resume、委派令牌、写闸判定序——尤其防「补守卫」滑成「改放行口」（FP-9）或「压警告」（FP-8）。

### R2 · 方案对比（设计闸两决策点）

- **决策点① 修复落点**：
  - **案 A（倾向）**：巡检层守卫——seen 面重置/重建时并入库面 status 真源（重启后首轮巡检以「单据库面状态 + seen 位」双条件判重，而非只看内存 seen 面）。优点：直接对症本缺陷（seen 面重置是去重失效根因）；重启后可恢复、不依赖进程内存。代价/前提：需 30 探针确认巡检循环承载面与重置语义实形。
  - **案 B**：建单/拉起层守卫——扩 `_persist_hitl` 类既有 DB 幂等键至双条件位（若承载面在建单侧，DB 幂等键天然重启可恢复）。优点：复用既有建单幂等先例（「真相在 store」教训已制度化）。代价：若缺陷实际在巡检/派发的拉起动作（先于建单），建单守卫够不着。
  - **案 C（禁）**：只压 overlap_warning 噪声（日志降级/静默）。治标不治本，FP-8 拒收。
- **决策点② ticket 幂等键语义 = status / seen_surface 双条件位**：status 位 = 单据在库面的真实状态（pending / approved / in-flight 级）；seen_surface 位 = worker 本轮巡检已见该 ticket。两条件**缺一不可**：只看 seen 位 → 重启重置后重复拉起（= 本缺陷）；只看 status 位 → 正常新单可能被误判「已存在」而永久拒拉起。裁定须明示双条件的判定序与读失败方向（FP-10：读失败 fail-closed——宁可不拉起、不可重复拉起）。

### R3 · 边界/失败路径

FP-1~FP-10 逐条锚既有语义：四闸拒开工 / resume 第二实现 / SSE 零 diff / fail-closed 放宽 / 改码面外溢（含 worker freeze）/ 幂等键单条件化两形态 / 负样本未绿出货 / 只压警告 / 守卫变放行口 / 守卫读失败方向。核心边界 = 守卫只判重、不动放行判定；消警告是幂等补上的**结果**，不是独立交付物。

### R4 · 验收/可测性

核心可测性风险 = 重犯单测盲区：负样本必须经**真巡检/派发路径**驱动，禁直造全 state 直调。reset 语义模拟 = 显式 seen 面重置（新 worker 实例或重置钩子 · 以 30 探针选定承载面为准）。红测先行：先以负样本红（重置后首轮巡检重复拉起）锁定缺陷，修复后绿（拉起恰一次 + overlap 台账零新增）。常规对拍（无重置轮次零漂移）防过紧语义（重置即拒拉起）。live 重启首巡实测留 40。

### R5 · 签收就绪

task 档落稿 · 10 invoke 落盘 · 四闸 pending · NO-GO 20/30；`spec-wave task lint` PASS 后出 PR 待审；30 改码须待闸签收后**另行授权**（issue #335 维护者令 · 窗口授权 2026-11-05 22:26 → 2026-11-06 07:00）。

---

### 自检结论（执行者）

> **hat 10（10 起草）** · 已落稿：task 档 + 10 invoke · 未改 `app/` / `tests/` · 未签任何 human_gate（四闸 pending · NO-GO 20/30）。

| 命令 | 退出码 | 摘要 |
|------|--------|------|
| `npx spec-wave task lint --file docs/tasks/active/task_fix_seen_surface_idempotency.md` | 0 | LINT: PASS（2026-11-06 · 10 起草自检） |

> **hat 30（30 实现）** · 已交付：nodes.py 拉起链双点半卫 + hitl/store.py 增量 `arelocate_linkage`（+225/-1 · 注释显性化裁决依据）+ 新测 3 枚（负样本先红后绿 + 对拍 ×2）· 四闸 approved 承签认档 · 未触碰任何 human_gate。

| 命令 | 退出码 | 摘要 |
|------|--------|------|
| `pytest tests/test_fix_seen_surface_idempotency.py`（负样本 · stash 修复后先红） | 1 | RED 实证：reset 后首轮巡检库面 2 笔同写意图票 + 写闸拦截行双拉起（孪生步 :2 重复拉起） |
| `pytest tests/test_fix_seen_surface_idempotency.py`（修复后） | 0 | 3 passed（负样本恰一笔 + 对拍 ×2 零漂移 · 后绿） |
| `pytest tests/test_fix_seen_surface_idempotency.py tests/test_write_approval_gate.py tests/test_hitl_approval_consumption.py tests/test_hitl_approved_replan_quality.py tests/test_hitl_resume.py tests/test_fix_delegation_resume_approval_id.py tests/test_fix_worker_state_send_run_id.py tests/test_stage_w_write_expand.py` | 0 | 122 passed 零适配 |
| `pytest tests`（全量） | 0* | 2068 passed · 4 failed = master 既有基线同形（diff-whitelist ×2 / embedder env ×1 / dualproc env ×1 · stash 复验 baseline 同 4 枚 · **零新增红**） |
| `ruff check app tests` | 0 | All checks passed（零） |
| `./scripts/graph-compile.sh` | 0 | EXIT=0 |
| `npx spec-wave task lint --file docs/tasks/active/task_fix_seen_surface_idempotency.md` | 0 | LINT: PASS（30 回填后） |
| 红线对拍 `git diff origin/master --stat` | 0 | 改码面唯一 `nodes.py` + `hitl/store.py` · `hitl/router.py`/`resume.py`/`auto_resume.py`/`event_store`/`sse_*`/`capability/gateway.py` 零 diff · 消费门函数（`_approval_consumed`/`_write_execution_approval`/`_match_fresh_approved`）零 diff |

---

## 修订记录

| 日期 | 说明 |
|------|-----|
| 2026-11-06 | 10 落稿：承 issue #335 维护者 comment `6668554143` 令起草 fix task（10 帽活 · 只产 task 档 + 10 invoke + lint PASS + PR · 禁改业务码）· 缺陷定性（reset_worker_seen_surface 后首轮巡检重复拉起存量 write ticket · 幂等缺口）承 issue 正文 · 设计闸 HG-WRITE-TICKET-IDEMPOTENCY-DESIGN 两决策点（①修复落点三案 A 倾向/B/C 禁 · ②ticket 幂等键语义 = status/seen_surface 双条件位）· 红测负样本（reset 后首轮巡检不重复拉起 · 端到端断言）入 test_strategy · 四红线（resume 单路径 / SSE 事件表零 diff / 消费门 fail-closed 永不放宽 / 改码面收敛）+ worker freeze 不动语义入 failure_paths · R0–R5 全轮 · 四闸 pending · NO-GO 20/30 · 10 档实扫声明（字面符号零命中 · 承载面留 30 探针） |
| 2026-11-06 | **四闸 approved 代录 + 30 授权入档**（签认依据 = PR #345 review `5792245814` lead 签 + issue #335 comment `6669768156` + 窗口授权 2026-11-05 22:26 指令）：设计闸决策点②签认 = ticket 幂等键语义 **status/seen_surface 双条件位**照留；决策点①（修复落点）留 30 红测探针实证后裁决并引用 comment `6669768156` · **30 授权六交付条件**（红测先红后绿留 invoke / 常规对拍零漂移 / 改码面唯一落点 / 四红线零 diff 对拍 / ruff+pytest+graph-compile 全绿 CI 4/4 / 20-R1 审查文随 30 PR 落盘）· 30 分支 `fix/seen-surface-idempotency` · PR #345 已 squash 合入 master `ec87535`（10 棒闭环） |
| 2026-11-06 | **30 交付**：设计闸决策点①裁决 = **案 A ∪ 案 B 同链双点半卫**（巡检层孪生继承 + 建单层 status 位迁附 · 10 档 R2 单点倾向经探针修正 · 如实留痕）· 红测负样本先红（库面 2 笔 + 双拦截行）后绿（恰一笔 + 零新增）· 对拍 ×2 零漂移 · 全量套件零新增红 · 改码面 `nodes.py`+`hitl/store.py` 唯一 · 四红线零 diff · 20-R1 审查文随本 PR 落盘 · 30 invoke 落档 |
