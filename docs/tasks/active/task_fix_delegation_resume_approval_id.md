# Task：`delegation` resume 对称清理 `approval_id`（与主路径 resume 清理口径对齐）

> **状态**：`implementing`（2026-11-06 · 四闸 approved · 30 已授权 · 六交付条件在案）
> **类型**：fix / 缺陷修复（delegation resume 未对称清理 approval_id · 与主路径语义不齐）
> **上游**：issue [#334](https://github.com/Cyning12/ops-desk-api/issues/334)（backlog 正文 + 维护者 comment `6662721599` 令立项 · comment `6664735511` 30 授权 · 受理依据 = 窗口授权 2026-11-05 22:26 → 2026-11-06 07:00 · lead 代行签收与验收）
> **分支**：`fix/delegation-resume-approval-id`（30 本档 · 10/00 走 `agent/approval-id-fix-task-be209a5f60c8` · PR #341 已合入 `c162d1d`）
> **10 注**：2026-11-05 · 承 issue #334 维护者令起草 fix task（10 帽活）· 仅落 task 档 + lint PASS + PR · PR #341 已验收合并
> **30 注**：2026-11-06 · 维护者 comment `6664735511` 30 授权（签认依据 = PR #341 review `5789202776` lead 签 · 窗口授权）· 六交付条件：①红测先行可见红→绿（负样本 = delegation resume 后 approval_id 已清 + 真落笔 + 消费闭环三照 · 端到端）②旧测适配不放宽随 PR ③改码面唯一收敛（nodes.py :2162+:2177 单点 · 承 review 裁决）④四红线零 diff 对拍 ⑤ruff + pytest + graph-compile 全绿 ⑥PR 说明逐条对照 · 出货即 30 invoke 落档待审

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `fix-delegation-resume-approval-id` |
| **git_branch** | `fix/delegation-resume-approval-id` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 红测先行：负样本（维护者红线）=「delegation resume 后 approval_id 已清」——delegation on 路径 tool 子任务签发审批拦下（`delegation_issue_hitl_required`）→ decide(approved) → **真 resume**（`resume_hitl_run` · 经 `_execute_decided_resume` 同源单路径）→ replan 重下发，**端到端断言** resume 后 approval_id 残留面已清（承载面 = 30 红测先行定位：工人可见 Send 载荷 / graph state / 审计面，**禁直造全 state 直调**——经真派发路径 `route_next_subtask`/`_worker_state` 产载荷）；正样本对拍：主路径（delegation off · `capability_write_hitl_required` 闸）resume 后同口径已清、零漂移（对称性对拍 · 防修成 delegation-only 特殊分支）；放行面承接：delegation 消费命中 `delegation_approval_consumed` 台账 + 真落笔 approval_id 串链三照（便签行/回执/span）不变；既有消费门 fail-closed 负样本组（`test_write_approval_gate` / `test_hitl_approval_consumption`）全绿不放宽；A5 grep 断言（resume 单路径）承接；不连真外网 · live 面留 40 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `none`（预期：resume 链对称清理小修 · 无路由/表/事件类型/一级模块面；若 30 实扫出现图谱面须先回闸再动） |
| **graph_delta** | `n/a` |
| **graph_delta_note** | 模块边界不变（`lg_rag/multi` 既有 resume/消费链内增量）；不触发图谱同步义务（承 AGENTS.md：仅新增路由/表/事件类型须同步）；HG-GRAPH-MODULES 以 `n/a` 口径随档签认 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 契约真值在 workspace contracts / freeze；本波零 wiki 面 |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,20,30,40` |
| **invoke_retention_profile** | `default` |
| **experience_capture** | `recommended` |
| **kpi_aggregator** | `CLOSE` |
| **orchestration** | 10 落稿（本 PR · task 档）→ 20-R1 书面审（审查文落盘 `docs/harness/reviews/`）→ 维护者签 **HG-DELEGATION-RESUME-APPROVAL-ID-DESIGN**（清理落点与 resume 单路径兼容性）+ 三常闸（HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES）→ PR 出货待审 → **30 改码须待闸签收后另行授权**（`fix/delegation-resume-approval-id` · GATE_VERIFY 闸据=本档闸表）→ 40 → CLOSE |
| **freeze_id** | `lg-rag-sse-v1`（**零 diff 红线**：SSE 事件表/帧形态）· `hitl-browser-decide-v1`（web `../ops-desk-web/src/api/hitl.ts` 消费语义 freeze 文件**不动**） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | **approved** | 20-R1, 30 | 维护者签认（issue #334 comment `6662721599` 令立项 · 签认依据 = PR #341 review `5789202776` + 窗口授权 2026-11-05 22:26 指令 · lead 代行 2026-11-05） |
| HG-AUDIT-R1 | **approved** | **30** | lead 签认 2026-11-05 · 依据同上——lead PR #341 review `5789202776` 审查通过即 20-R1 书面审记录（审查文 [`task_fix_delegation_resume_approval_id_audit_R1_20261106.md`](../harness/reviews/task_fix_delegation_resume_approval_id_audit_R1_20261106.md) 随 30 分支出货落盘） |
| HG-GRAPH-MODULES | **approved** | **30** | lead 签认 2026-11-05 · 依据同上 · `none` 口径签认确认（无图谱面 · 承 no-proxy fix 先例）· 若 30 实扫出图谱面须回签 |
| **HG-DELEGATION-RESUME-APPROVAL-ID-DESIGN** | **approved** | **30** | **设计闸裁决（PR #341 review `5789202776`）**：**案 A 路径**——对称清理单点落 `nodes.py :2162+:2177`，一次 cleanup 主/委/审三态收敛；改码面收敛红线内；兼容语义显性化零行为变化 · resume 单路径兼容性：清理动作必须落在既有单链内，禁第二实现/旁路 |

---

## 背景与目标

issue #334（backlog）：**delegation 路径 resume 时未对称清理 approval_id，与主路径语义不齐**（来源：#323 stage-w 40 invoke 实测证据链 · `docs/harness/invokes/by-task/stage-w-write-expand/`）。维护者定性：小修——对齐 resume 清理口径；红线 = resume 单路径 / SSE 事件表零 diff。

两条拦截类 HITL 路径的 resume 收敛点（只读锚点 · 30 必读 · 10 已扫）：

- **主路径**（`capability_write_hitl_required` · delegation off）：tool 子任务写闸未命中 → 挂起 → decide(approved) → resume → `_apply_hitl_decision` 剪旧结果/解锁/轮数归零 → replan 重下发 → `_write_execution_approval` 消费命中 → `cap_ctx["approval_id"]` 注入 → 真落笔三照串链（issue #334 所称「主路径清理口径」）。
- **delegation 路径**（`delegation_issue_hitl_required` · delegation on）：supervisor stamping 签发审批拦下 → 挂起 → decide(approved) → resume → 同走 `_apply_hitl_decision` → replan → `_delegation_issue_block_reason` 内 `_approval_consumed` 消费放行签发 → `route_next_subtask` 重签发令牌派发 → tool_exec 写闸再消费（`_WRITE_CONSUMABLE_BLOCKED_BY` 含 delegation 类）→ 执行。

**缺陷**：resume 决策应用后，delegation 路径存在 approval_id 残留面未按主路径同口径清理（确切承载面 = 30 红测负样本先行定位——工人可见 Send 载荷 / graph state / 审计面之一或其组合；10 档不预断）。语义不齐的后果：resume 重放面携 stale approval_id，与「授权效力 = 读取时刻的活状态、resume 后按活状态重取」的既有契约相悖，构成审计串链与重放语义的漂移面。

本 task = 该缺陷的最小修复竖切：delegation resume 对称清理 approval_id（落点以设计闸签认为准）+ 红测负样本（端到端断言）+ 主/Delegation 对称性对拍，让两条拦截类路径的 resume 清理口径一致。

---

## 现状锚点（只读 · 30 必读 · 10 已扫）

| 主题 | 路径 · 锚点 | 现状 |
|------|-------------|------|
| resume 决策应用点 | `app/ops/lg_rag/multi/nodes.py:2299-2353 _apply_hitl_decision` | resume 值解释统一出口：解锁 `hitl_unlocked_ids` + 剪 approved 步旧结果（`SubtaskResultBatch replace`）+ 轮数归零 + `hitl_interrupt` 换 `resumed` 形态；**两条拦截类路径同源经过**——对称清理的天然候选落点 |
| resume 单路径 | `app/ops/hitl/router.py:493-533 _execute_decided_resume` · `app/ops/hitl/resume.py:303-378 resume_hitl_run` | 手动 resume 端点 / T2 auto-resume / 补偿扫描**同源自重用此链**（禁第二实现 · 禁 HTTP 自调 · A5 grep 断言钉死） |
| delegation 签发门 | `app/ops/lg_rag/multi/nodes.py:555-582 _delegation_issue_block_reason` · 调用点 `:1289-1300`（supervisor stamping） | 签发审批口径判定；命中 `_approval_consumed` 即放行签发（None）；未命中 → `_delegation_blocked_terminal`（`blocked_by=delegation_issue_hitl_required` + 租户戳） |
| delegation 消费门 | `app/ops/lg_rag/multi/nodes.py:418-460 _approval_consumed` | 只消费 delegation 类单据（`blocked_by` 守卫）；**fail-closed**；**不写回单据状态**（授权效力 = 读取时刻活状态） |
| 写闸（含 delegation 类） | `app/ops/lg_rag/multi/nodes.py:462-533 _write_execution_approval` | `_WRITE_CONSUMABLE_BLOCKED_BY` 收 capability_write + delegation 两类；命中返行 → 调用方注入 `approval_id`；租户守卫 fail-closed |
| approval_id 注入/串链 | `app/ops/lg_rag/multi/nodes.py:1964-1969`（cap_ctx）· `app/ops/capability/gateway.py:1318`（span 预留启用）· `app/ops/capability/defaults.py:169-177,215`（真落笔 adapter） | W3 审计串链：消费命中 → Host 单次写放行 + approval_id 注入 → capability span metadata / 回执 / 便签行三照 |
| 派发路径 | `app/ops/lg_rag/multi/nodes.py:1643-1680 route_next_subtask` · `_worker_state :1359-1381` · `_issue_delegation_token :584-616` | Send 载荷 = 工人可见全部 state（挑键构造 · `run_id` 键已由 fix-worker-state-send-run-id 补齐）；delegation on 逐子任务重签发新例（旧 nonce 作废 · 禁续期） |
| 挂单守卫 | `app/ops/lg_rag/multi/nodes.py:2128-2160 _approved_fresh_for_subtask` · 调用点 `:2236` | 同三元组已有新鲜 approved 单据 ⇒ 跳过建单（防 resume 重放孤儿 pending）；镜像消费语义 · 同一实现复用 |
| freeze 面 | SSE `lg-rag-sse-v1` · web `../ops-desk-web/src/api/hitl.ts` `hitl-browser-decide-v1` | 事件表/帧形态/freeze 文件零 diff 红线 |
| 先例 | fix-worker-state-send-run-id（PR #331/#332/#340 · `docs/tasks/done/task_fix_worker_state_send_run_id.md`） | 同链 resume 修复先例：真派发路径红测负样本 + 键集钉 + 四红线 failure_paths + 设计闸两决策点形态 |

---

## 10 钉死契约（承 issue #334 维护者红线 · freeze 后升格 · 30 不得静默改义）

| 项 | 钉死 |
|----|----------------|
| **resume 单路径** | 复用 `router._execute_decided_resume` → `resume_hitl_run` → `_apply_hitl_decision` 既有单链；清理动作必须落在该链内——**禁**第二条恢复实现 / HTTP 自调 / 旁路清理线程（A5 grep 断言沿用） |
| **SSE 事件表零 diff** | `lg-rag-sse-v1` 不破：不新增/不改 SSE `event_type` 与帧形态；`event_store` 写入面零 diff |
| **消费门 fail-closed 永不放宽** | `_approval_consumed` / `_write_execution_approval` 未命中/读失败/过期/类型不符/租户不符 → 一律 `False`/`None` 语义**逐字节不变**；禁任何 fail-open 化；**「不写回单据状态」契约不动**（清理 ≠ 改单据状态） |
| **改码面收敛** | 唯一改码面 = 对称清理落点（以 HG-DELEGATION-RESUME-APPROVAL-ID-DESIGN 签认为准）+ 新增回归测试 + 旧测适配（如有）；闸链 / HITL 表结构 / decide-resume 状态机 / auto-resume / 委派令牌机制 / 写闸判定序 一行不动 |
| **hitl 消费语义 freeze 不动** | web `../ops-desk-web/src/api/hitl.ts`（`hitl-browser-decide-v1`）freeze 文件**零 diff**；decide 404/409 既有语义全量不变 |

---

## 范围（竖切 · 四闸齐后才 30）

- [ ] **D-fix-1 · delegation resume 对称清理 approval_id**：resume 决策应用后按主路径同口径清理 approval_id 残留面（**落点与写法子口径以设计闸决策点①签认为准**；倾向案 A：`_apply_hitl_decision` 统一应用点对称清理——两条拦截类路径同源经过、单点真源、天然不破 resume 单路径；确切残留承载面由 30 红测负样本先行定位后回填本节）（30 交付）
- [ ] **D-fix-2 · 红测负样本 + 对称性对拍**：①负样本（维护者红线）= delegation on 路径签发审批拦下 → decide(approved) → **真 resume** → 重下发，端到端断言 resume 后 approval_id 已清（经真派发路径 · 非直造 state）②对称对拍 = 主路径（delegation off · capability_write 闸）resume 后同口径已清零漂移 + delegation 放行面承接（`delegation_approval_consumed` 台账 + 真落笔三照 approval_id 串链不变）（30 交付）
- [ ] **D-fix-3 · 旧测适配（条件触发）**：若 30 实扫发现既有断言锚在 resume 后 approval_id 残留形态（grep 面：delegation 消费/ resume / write 闸测试族），适配而非放宽（30 交付 · 以实扫为准）

### 非范围

- ❌ 消费门语义任何改动（fail-closed 红线条款 · 含 fail-open 化 / 判序 / TTL / 租户守卫 / `blocked_by` 单据类守卫）
- ❌ 「不写回单据状态」契约破坏（清理动作改 hitl 单据行状态 = 禁 · 案 C 不入签）
- ❌ HITL 表结构 / decide-resume 状态机 / auto-resume 触发器与补偿扫描一行不动
- ❌ SSE 事件表 / 帧形态 / `event_store` 写入面
- ❌ freeze 文件本体（`lg-rag-sse-v1` 事件表 · web `hitl-browser-decide-v1` `hitl.ts`）
- ❌ 委派令牌机制（Host V1-A）改造——签发/验签/nonce 作废语义不动
- ❌ resume 链第二实现 / HTTP 自调 / 清理旁路线程
- ❌ web 仓 / iOS / 平台项
- ❌ supervisor planner string-args（`args_schema_invalid`）——已立 #339 另波跟踪，非本 task

---

## failure_paths

| # | 触发条件 | 系统行为 | 可重试 | 用户可见 |
|---|----------|----------|--------|----------|
| FP-1 | 四闸任一 pending 即 30 | **拒开工** | 是（签闸后） | 是 |
| FP-2 | **resume 第二实现**（新恢复路径 / HTTP 自调 / 清理旁路线程） | A5 grep 断言红 · 审查拒收退回（红线） | 是 | 否 |
| FP-3 | **SSE 事件表出现 diff**（`lg-rag-sse-v1` 破） | 审查拒收 · 退回 | 是 | 否 |
| FP-4 | **消费门 fail-closed 被放宽**（未命中改放行 / fail-open 化 / 判序漂移 / TTL 或租户守卫松动） | 红测拦截 · 审查拒收退回（红线） | 是 | 否 |
| FP-5 | **改码面外溢**（闸链 / HITL 表 / 状态机 / auto-resume / 委派令牌 / 写闸判定序被碰） | 红线对拍 diff 非空 · 审查拒收 | 是 | 否 |
| FP-6 | **清理动作写回单据状态**（破坏「不写回单据状态」契约 · 案 C 形态） | 审查拒收 · 退回 | 是 | 否 |
| FP-7 | 修成 delegation-only 特殊分支（主路径口径被改义 / 两路径清理口径再分裂） | 对称性对拍红 · 审查拒收 | 是 | 否 |
| FP-8 | resume 后 stale approval_id 仍未清（负样本红未转绿即出货） | 红测拦截 · 审查拒收 | 是 | 否 |
| FP-9 | 无审批直跑被误放行（把「清理残留」误读成「放行口」） | fail-closed 原样拦（消费门负样本组既有断言承接 · 本修复**只**清残留、不动放行判定） | 是（补审批） | 是（等待授权帧） |

---

## 验收标准

- [ ] 人工闸：HG-TASK-DRAFT · HG-AUDIT-R1 · HG-GRAPH-MODULES · **HG-DELEGATION-RESUME-APPROVAL-ID-DESIGN** 均 approved 后方可勾选下列码项
- [ ] 红测负样本（**维护者红线**）：delegation resume 后 approval_id 已清——delegation on 签发审批拦下 → decide(approved) → 真 resume（`resume_hitl_run` · 经 `_execute_decided_resume` 同源单路径）→ 重下发，端到端断言已清（先红后绿可见 · 承载面以 30 定位回填）
- [ ] 对称性对拍：主路径（delegation off · capability_write 闸）resume 后同口径已清、修复前后零漂移；两路径清理口径一致（无 delegation-only 特殊分支）
- [ ] 放行面承接不回归：delegation 消费命中 `delegation_approval_consumed` 台账 + 真落笔三照 approval_id 串链（便签行/回执/span）与修复前一致
- [ ] 消费门 fail-closed 语义零变化：未命中 / 读失败 / 过期 / 类型不符 / 租户不符 / `blocked_by` 类守卫各负样本既有断言全绿（`test_hitl_approval_consumption` / `test_write_approval_gate` 全组）
- [ ] 红线对拍：SSE 事件表零 diff；web `hitl.ts` freeze 零 diff；resume 单路径 A5 grep 断言绿；闸链 / HITL 表 / 状态机 / auto-resume / 委派令牌 / 写闸判定序零 diff
- [ ] 旧测 grep 影响面适配（如有）不放宽；delegation 消费 / resume / write 闸测试族关联回归全绿
- [ ] 工程面：`ruff check app tests` 触及路径零新增；`pytest tests` 零新增红（本地产能既有红基线如实登记 · 环境纪律承先例显式空值中和）；`./scripts/graph-compile.sh` EXIT=0；`npx spec-wave task lint` PASS
- [ ] 40 复跑（live 面 · 条件触发）：delegation on live 全链 resume 实测 · 清理口径对称达成

---

## 依赖

| 依赖 | 说明 |
|------|------|
| 缺陷源 | issue [#334](https://github.com/Cyning12/ops-desk-api/issues/334)（正文 + 维护者 comment `6662721599` 立项令：task 档四要素 / 红测负样本 / 四条红线 / lint PASS 出货） |
| 上游证据链 | #323 stage-w 40 invoke：`docs/harness/invokes/by-task/stage-w-write-expand/invoke_20261105_40_verify.md`（live 全链八段实测 · delegation on/off 双路径证据面） |
| 同链先例 | [`task_fix_worker_state_send_run_id.md`](../done/task_fix_worker_state_send_run_id.md)（CLOSE · PR #331/#332/#340 · 同 resume 链 · 真派发路径红测负样本 + 设计闸两决策点形态先例）· [`task_hitl_approval_consumption_loop.md`](../done/task_hitl_approval_consumption_loop.md)（D1 消费门 · unlock 空形态回填 · resume 不 409 契约） |
| 改码面（预期） | `app/ops/lg_rag/multi/nodes.py`（`_apply_hitl_decision` 或闸签落点 · 以闸签为准）+ 新增回归测试 |
| freeze 参照 | SSE `lg-rag-sse-v1`（事件表）· web `../ops-desk-web/src/api/hitl.ts`（`hitl-browser-decide-v1`） |
| 编码规范 | `docs/standards/CODING_BACKEND_L2_v1_zh.md` |
| 另波跟踪 | issue #339（supervisor planner string-args · 非本 task） |

---

## 给执行帽的必读列表

1. `AGENTS.md`
2. 本 task（钉死契约 · 闸 · 非范围 · failure_paths）
3. issue #334 全文（缺陷定性 · 维护者立项令与红线）
4. 代码：`app/ops/lg_rag/multi/nodes.py:2299-2353`（_apply_hitl_decision · resume 决策统一应用点）· `:418-460`（_approval_consumed）· `:462-533`（_write_execution_approval）· `:555-582`（_delegation_issue_block_reason）· `:1289-1300`（stamping 委派拦截）· `:1643-1680`（route_next_subtask 派发）· `:1964-1969`（cap_ctx approval_id 注入）· `app/ops/hitl/router.py:493-533`（_execute_decided_resume · resume 单路径）· `app/ops/hitl/resume.py:303-378`（resume_hitl_run）
5. 测试面：`tests/test_hitl_approval_consumption.py`（TA/TB 全组 · delegation 消费 + resume 成环形态）· `tests/test_write_approval_gate.py`（W 组 · 写闸负样本）· `tests/test_fix_worker_state_send_run_id.py`（同链真派发路径红测形态参照）· `tests/test_hitl_resume.py`（resume 单路径 harness）
6. `docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`

---

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|----|------|------------|----------------------|----------------|
| R0 | 本 task = 维护者 issue #334 定性的对称性缺陷小修（非设计探索）：delegation 路径 resume 未按主路径同口径清理 approval_id，语义不齐 | no | — | 确切残留承载面（载荷/state/审计面）10 档未实锤 · 30 红测先行定位 |
| R1 | 范围 = 对称清理落点 + 红测负样本 + 对称对拍 + 条件旧测适配；非范围九条锁定（消费门语义/不写回契约/闸链/表/状态机/SSE/freeze/委派机制/resume 第二实现/web 面） | no | — | none |
| R2 | 清理落点三案：A `_apply_hitl_decision` 统一应用点对称清理（**倾向** · 两条拦截类路径同源经过 · 单点真源 · 天然不破 resume 单路径）/ B delegation 消费侧局部清理（只修 delegation 面 · 若残留面在 state/载荷则够不着 · 弃项倾向）/ C 单据面写回清理（**禁** · 破「不写回单据状态」契约）→ 决策点①入闸；resume 单路径兼容性（清理动作必须落在既有单链内 · 禁旁路）→ 决策点②入闸 | no | — | 案 A 倾向基于链式收敛推演（无 shim/live 实证）· 30 红测定位后若残留面在载荷层须回评落点 |
| R3 | failure_paths 锚既有语义：四红线（resume 单路径 FP-2 / SSE 零 diff FP-3 / fail-closed 永不放宽 FP-4 / 改码面收敛 FP-5）+ 禁写回契约（FP-6）+ 对称性再分裂（FP-7）+ 负样本未绿出货（FP-8）+ 误读放行口（FP-9） | no | — | none |
| R4 | 可测性：负样本必须走真派发路径 + 真 resume（禁直造 state 直调——单测盲区是 #334 同源教训）；红测先红后绿；对称对拍防修成 delegation-only 分支；live 面留 40 | no | — | 本地产能既有红基线（diff-whitelist 锚点漂移 / env 依赖）如实登记口径沿用 |
| R5 | 起草落稿 · 四闸 pending · NO-GO 20/30；30 改码须待闸签收后另行授权（issue #334 维护者令 · 窗口授权至 2026-11-06 07:00） | no | — | 无 |

**actual_last_round**：R5 · **early_stop**：no · **residual_risks**：残留承载面待 30 红测定位（见 R0/R2）

### R0 · 问题框定

issue #334 由维护者定性（backlog · 小修）：delegation 路径 resume 时未对称清理 approval_id，与主路径语义不齐；来源 #323 stage-w 40 invoke 实测证据链。与 fix-worker-state-send-run-id（同链已实锤缺陷）不同，本档 10 未做 live 复现：残留承载面（工人可见 Send 载荷 / graph state / 审计面）以 30 红测负样本为执行规格先行定位。task 性质 = 对齐 resume 清理口径的对称性小修，非方向探索。

### R1 · 范围/非范围

范围四件套（清理落点 / 红测负样本 + 对称对拍 / 条件旧测适配）收敛为最小竖切；非范围把「会被顺手扩大」的面全部锁死：消费门语义与「不写回单据状态」契约（FP-4/FP-6）、SSE 事件表（FP-3）、web freeze、resume 单路径（FP-2）、委派令牌机制、写闸判定序——尤其防「清残留」滑成「改闸链」或「放行口」（FP-9）。

### R2 · 方案对比（设计闸两决策点）

- **案 A（倾向）**：`_apply_hitl_decision`（resume 决策统一应用点）内对 delegation 拦截类按主路径同口径对称清理 approval_id 残留。优点：主/delegation 两条拦截类路径（`capability_write_hitl_required` / `delegation_issue_hitl_required`）resume 后**同源经过**该函数——单点真源，清理口径天然一致，无 delegation-only 特殊分支；不破 resume 单路径（动作就在单链内）。代价/前提：需 30 红测确认残留承载面可达该点（若残留实际生在 Send 载荷构造层，须回评落点并报闸）。
- **案 B（弃项倾向）**：delegation 消费侧局部清理（`_approval_consumed` 命中后 / 签发门放行分支）。缺点：只修 delegation 面，主路径口径仍各自表述；若残留面在 state/载荷层则够不着；清理口径分裂风险（FP-7）。
- **案 C（禁）**：单据面写回清理（改 hitl 单据行状态）。**破坏「不写回单据状态」既有契约（授权效力 = 读取时刻活状态），不入签。**

决策点② resume 单路径兼容性：清理动作必须落在 `_execute_decided_resume` → `resume_hitl_run` → `_apply_hitl_decision` 既有单链内——禁第二实现 / HTTP 自调 / 清理旁路线程（A5 grep 断言承接）。

### R3 · 边界/失败路径

FP-1~FP-9 逐条锚既有语义：四闸拒开工 / resume 第二实现 / SSE 零 diff / fail-closed 放宽 / 改码面外溢 / 写回契约破坏 / 对称性再分裂 / 负样本未绿出货 / 误读放行口（本修复只清残留，不放行判定）。

### R4 · 验收/可测性

核心可测性风险 = 重犯单测盲区：负样本必须经**真派发路径**（`route_next_subtask`/`_worker_state` 产载荷）+ **真 resume**（`resume_hitl_run`）驱动，禁直造全 state 直调（同 #334 同源教训：缺陷藏 N 轮正因单测全走捷径）。红测先行：先以负样本红（resume 后 approval_id 残留未清）锁定缺陷，修复后绿。对称对拍（主路径零漂移）防修成 delegation-only 分支。live delegation on 全链留 40。

### R5 · 签收就绪

task 档落稿 · 四闸 pending · NO-GO 20/30；lint PASS 后出 PR 待审；30 改码须待闸签收后**另行授权**（issue #334 维护者令 · 窗口授权 2026-11-05 22:26 → 2026-11-06 07:00）。

---

### 自检结论（执行者）

> **hat 10（10 起草）** · 已落稿：task 档 · 未改 `app/` / `tests/` · 未签任何 human_gate（四闸 pending · NO-GO 20/30）。

| 命令 | 退出码 | 摘要 |
|------|--------|------|
| `npx spec-wave task lint --file docs/tasks/active/task_fix_delegation_resume_approval_id.md` | 0 | LINT: PASS（2026-11-05 · 10 起草自检） |

---

## 修订

| 日期 | 说明 |
|------|------|
| 2026-11-05 | 10 落稿：承 issue #334 维护者 comment `6662721599` 令起草 fix task（10 帽活 · 只产 task 档 + lint PASS + PR · 禁改业务码）· 缺陷定性（delegation resume 未对称清理 approval_id）与四红线（resume 单路径 / SSE 事件表零 diff / 消费门 fail-closed 永不放宽 / 改码面收敛）承 issue 正文 · 设计闸 HG-DELEGATION-RESUME-APPROVAL-ID-DESIGN 两决策点（清理落点三案 A 倾向/B/C 禁 · resume 单路径兼容性）· 红测负样本（delegation resume 后 approval_id 已清 · 端到端断言）入 test_strategy · R0–R5 全轮 · 四闸 pending · NO-GO 20/30 |
| 2026-11-06 | **四闸 approved 代录 + 30 授权入档**（签认依据 = PR #341 review `5789202776` lead 签 + issue #334 comment `6664735511` + 窗口授权 2026-11-05 22:26 指令）：设计闸裁决 = **案 A 路径**（对称清理单点落 `nodes.py :2162+:2177` · 一次 cleanup 主/委/审三态收敛 · 兼容语义显性化零行为变化）· 30 六交付条件入档（红测负样本+三照端到端 / 旧测适配不放宽 / 改码面唯一收敛 / 四红线零 diff / ruff+pytest+graph-compile 全绿 / PR 逐条对照 + 30 invoke 落档）· PR #341 已合入 `c162d1d` · 30 开工（GATE_VERIFY 闸据 = 本档闸表） |
