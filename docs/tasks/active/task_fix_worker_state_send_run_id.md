# Task：`_worker_state` Send 载荷补 `run_id`（HITL resume 后写审批消费门 fail-closed 再拦修复）

> **状态**：`active`（2026-11-05 · 10 起草落稿 → **四闸 approved**（lead 签认 · PR #331 review `5785422963` + issue #329 comment `6658823187`）→ **30 已授权开工**（issue #329 comment `6658823187` · 分支 `fix/worker-state-send-run-id` · 六交付条件入档）· 出货 PR 待 lead 终审 · 40 复跑照旧）
> **类型**：fix / 缺陷修复（Send 载荷丢键 · 消费门 fail-closed 静默失效）
> **上游**：issue [#329](https://github.com/Cyning12/ops-desk-api/issues/329)（backlog 候选 + 维护者 comment `6658235851` 令按 Harness 流程立项）· 证据 = 40 invoke 偏差登记①（[`invoke_20261105_40_verify.md`](../../harness/invokes/by-task/stage-w-write-expand/invoke_20261105_40_verify.md) §5 · live 全链八段实测 shim 补位实证 · 已实锤）
> **分支**：`fix/worker-state-send-run-id`（30 用 · 10/00 本档走 `agent/run-id-fix-task-cdc1b46e15dc`）
> **10 注**：2026-11-05 · 承 issue #329 维护者令起草 fix task（**10 帽活**）· 仅落 task 档 + 10 invoke + lint PASS + PR · **禁止**改 `app/` / `tests/`——30 改码须待本档人工闸签收后另行授权

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `fix-worker-state-send-run-id` |
| **git_branch** | `fix/worker-state-send-run-id` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 红测先行：负样本（维护者红线）=「resume 后重下发不再被写审批消费门拦截」——经真派发路径（`route_next_subtask` → `_worker_state` 产载荷 → `tool_exec_node`）驱动，断言消费命中 + 真落笔（便签行/回执/幂等 done 三照）；正样本：Send 载荷工人可见键集含 `run_id` 回归钉（`_worker_state` 直调 · 防再发）；delegation on 路径对拍（payload `run_id` 值修复前后一致 · 重复赋值不产生漂移）；旧测 grep 影响面：`test_step_contract.py` worker_state 三测 + `tests/eval/test_capability_redlines.py` R14 段直调 `_worker_state`（断言对象均为 `assigned_subtask` · 预估零影响 · 若实扫发现键集等值断言须适配不放宽）；既有 W 链回归（test_write_approval_gate / test_stage_w_write_expand / hitl 全组）全绿；不连真外网 · live 面留 40 复跑 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `none`（模块内一行载荷补键 · 无路由/表/事件类型/一级模块面） |
| **graph_delta** | `n/a` |
| **graph_delta_note** | 模块边界不变（`lg_rag/multi` 既有模块内 `_worker_state` 增量）；不触发图谱同步义务（承 AGENTS.md：仅新增路由/表/事件类型须同步）；HG-GRAPH-MODULES 以 `n/a` 口径随档签认 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 契约真值在 workspace contracts / web freeze；本波零 wiki 面 |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,20,30,40` |
| **invoke_retention_profile** | `default` |
| **experience_capture** | `recommended` |
| **kpi_aggregator** | `CLOSE` |
| **orchestration** | 10 落稿（本 PR · task 档 + 10 invoke）→ 20-R1 书面审（审查文落盘 `docs/harness/reviews/`）→ 维护者签 **HG-WORKER-STATE-RUN-ID-DESIGN**（两决策点）+ 三常闸（HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES）→ PR 出货待审 → **30 改码须待闸签收后另行授权**（`fix/worker-state-send-run-id` · GATE_VERIFY 闸据=本档闸表）→ 40 → CLOSE |
| **freeze_id** | `lg-rag-sse-v1`（**零 diff 红线**）· `hitl-browser-decide-v1`（web `../ops-desk-web/src/api/hitl.ts` 消费语义 freeze 文件**不动**） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | **approved** | 20-R1, 30 | lead 签认 2026-11-05 · 依据 = PR #331 review `5785422963`（审查通过 · lead · fix task 起草）+ issue #329 comment `6658235851`（立项令） |
| HG-AUDIT-R1 | **approved** | **30** | lead 签认 2026-11-05 · 依据同上——lead PR #331 review `5785422963` 审查通过即 20-R1 书面审记录（流程闸与内容闸一并签） |
| HG-GRAPH-MODULES | **approved** | **30** | lead 签认 2026-11-05 · 依据同上 · `none` 口径签认确认（无图谱面 · 承 no-proxy fix 先例） |
| **HG-WORKER-STATE-RUN-ID-DESIGN** | **approved** | **30** | **两决策点裁决**（lead 2026-11-05 签 · PR #331 review `5785422963` + issue #329 comment `6658823187`）：① 修复落点 = **案 A `_worker_state` 补键**（同源单点 · shim 已验证 · 案 B 覆盖面冗余弃 · 案 C 消费门放宽触碰红线禁）② 回归影响面 = **签收**（delegation on 重复赋值同值兼容 · 旧测键集等值断言适配不放宽 · grep 面 test_step_contract 三测 / R14 直调如实列出） |

---

## 背景与目标

阶段 W 40 复跑 live 全链实测（`invoke_20261105_40_verify.md` §5 偏差登记①）实锤 master 既有潜在缺陷：`_worker_state`（`app/ops/lg_rag/multi/nodes.py:1359-1381`）构造的 Send 载荷**不含 `run_id`**——Send 载荷即工人所见的全部 state，而 `route_next_subtask`（:1660-1669）仅在 `delegation_on and node == "tool_exec"`（委派路径）时补 `payload["run_id"]`。tool_exec 的写执行审批消费门 `_write_execution_approval`（:477）经 `_run_id_of(state)` 取 `run_id` 得空串 → 早退返回 `None`（**fail-closed**）→ 写子任务被「写操作未获人工审批」再拦 → **HITL resume 后重下发永远再被拦**，写能力永远无法完成 resumed 后重试。

- **影响面**：全部写能力（含 `ops.write.run_note` / `testing.write.echo`）；潜伏于 PR #303 时期，前后行为一致（**非近期回归**）。
- **为什么单测从未暴露**：单元测试全部直调 `tool_exec_node`（自带完整 state 含 `run_id`），真派发路径（`_worker_state` 挑键构造载荷）无覆盖。
- **修复形态已验证**：40 live 实测以 shim（`_worker_state` 补 `run_id`）补位后全链八段达成（消费命中 → 真落笔 → 审计串链 → done{status:resumed}）。
- **维护者红线**（issue #329 comment `6658235851`）：消费门 fail-closed 语义**不许放宽**；红测负样本 = resume 后重下发不再被消费门拦截（端到端 · 断言真落笔）。

本 task = 该缺陷的最小修复竖切：Send 载荷补 `run_id` 键 + 回归测试（红测负样本 + 键集钉），让 HITL resume 后的写审批消费闭环真正可达。

---

## 现状锚点（只读 · 30 必读 · 10 已扫）

| 主题 | 路径 · 锚点 | 现状 |
|------|-------------|------|
| 缺陷现场 | `app/ops/lg_rag/multi/nodes.py:1359-1381 _worker_state` | payload 挑键构造仅 5 键（messages / assigned_subtask / subtasks / supervisor_step_count + 两条件键），**无 `run_id`** |
| 派发路径 | `nodes.py:1643-1676 route_next_subtask` | :1666 仅 `delegation_on and node=="tool_exec"` 时补 `payload["run_id"]`（注释已写明丢键后果：验签侧 ctx.run_id 为空 ⇒ 误拒） |
| 写消费门 | `nodes.py:462-532 _write_execution_approval` | :477 `_run_id_of(state)` 空串 → 返 `None`（fail-closed）；命中三元组 `(run_id, subtask_id, capability_id)` + TTL + 租户守卫 |
| 闸点 | `nodes.py:1888-1910 tool_exec_node`（W0 写闸） | `write_approval is None` → `blocked_by=capability_write_hitl_required` + write_intent 挂起（复用既有 HITL 回路） |
| run_id 通道 | `app/ops/lg_rag/state.py:206`（LgRagState.run_id） | 图 state 通道在档（入口签发 · 节点内禁再造 uuid），但 Send 载荷是显式挑键构造 → 通道存在 ≠ 工人可见 |
| `_run_id_of` | `nodes.py:264-265` | `str(state.get("run_id") or "").strip()` · 空串 falsy |
| 单测盲区 | 40 invoke 偏差登记① | 单测全直调 tool_exec（自带全 state）；真派发路径零覆盖——本 task 红测负样本即补此面 |
| 既有先例 | `nodes.py:1377-1380`（supervisor_started_at 条件写键） | 载荷可选键「非空才写」写法在档 · 案 A 子口径参照 |
| 实测证据 | `docs/harness/invokes/by-task/stage-w-write-expand/invoke_20261105_40_verify.md` §5 | live 两轮无 shim 复现（run `fab290e9` / `c02daf71`）→ DBG 包装器实证 state 键集仅 5 枚 → shim 补位后八段全通 |

---

## 10 钉死契约（承 issue #329 维护者红线 · freeze 后升格 · 30 不得静默改义）

| 项 | 钉死 |
|----|----------------|
| **消费门 fail-closed 永不放宽** | `_write_execution_approval` 未命中/读失败/过期/类型不符/租户不符 → 一律返 `None` 语义**逐字节不变**；禁任何 fail-open 化（issue #329 维护者红线） |
| **SSE 事件表零 diff** | `lg-rag-sse-v1` 不破：不新增/不改 SSE `event_type` 与帧形态；`event_store` 写入面零 diff |
| **hitl 消费语义 freeze 不动** | web `../ops-desk-web/src/api/hitl.ts`（`hitl-browser-decide-v1`）freeze 文件**零 diff**；decide 404/409 既有语义全量不变 |
| **resume 单路径** | 复用 `router._execute_decided_resume`；禁第二条恢复实现 / HTTP 自调（grep 断言沿用 A5 形态） |
| **改码面收敛** | 唯一改码面 = `_worker_state` 载荷补 `run_id` 键（落点子口径以 HG-WORKER-STATE-RUN-ID-DESIGN 签认为准）+ 新增回归测试 + 旧测适配（如有）；闸链 / HITL 表 / 状态机 / auto-resume / 委派令牌机制一行不动 |

---

## 范围（竖切 · 四闸齐后才 30）

- [ ] **D-fix-1 · Send 载荷补 `run_id` 键**：`_worker_state` 产物含 `run_id`（落点与写法子口径以设计闸决策点①签认为准；推荐案 A：`_worker_state` 内补键 · 非空才写镜像 supervisor_started_at 先例 · delegation 分支 :1666 重复赋值行保留可留待后续清理）（30 交付）
- [ ] **D-fix-2 · 红测负样本 + 键集回归钉**：①负样本 = 经真派发路径（`route_next_subtask`/`_worker_state` 产载荷 → `tool_exec_node`）resume 后重下发 → 消费门命中 → **真落笔断言**（便签行/回执/幂等 done · 对齐 stage-w A1 审计三照形态）②键集钉 = `_worker_state` 直调断言工人可见载荷含 `run_id`（有值 state）· 空 run_id 不写入（防空串键污染）（30 交付）
- [ ] **D-fix-3 · 旧测适配（条件触发）**：若 30 实扫发现键集等值断言直调 `_worker_state`（`test_step_contract.py` 三测 / `test_capability_redlines.py` R14 段预估断言对象为 `assigned_subtask` 不受影响），适配而非放宽（30 交付 · 以实扫为准）

### 非范围

- ❌ 消费门语义任何改动（fail-closed 红线条款 · 含 fail-open 化 / 判序 / TTL / 租户守卫）
- ❌ HITL 表结构 / decide-resume 状态机 / auto-resume 触发器与补偿扫描一行不动
- ❌ SSE 事件表 / 帧形态 / `event_store` 写入面
- ❌ freeze 文件本体（`lg-rag-sse-v1` 事件表 · web `hitl-browser-decide-v1` `hitl.ts`）
- ❌ 委派令牌机制（Host V1-A）改造——:1666 既有补键行语义不动
- ❌ resume 链第二实现 / HTTP 自调
- ❌ web 仓 / iOS / 平台项
- ❌ 40 invoke 其余观察项（supervisor prompt 未文档化 `args` 字段等——另波 prompt 资产视野 · 非本 task）

---

## failure_paths

| # | 触发条件 | 系统行为 | 可重试 | 用户可见 |
|---|----------|----------|--------|----------|
| FP-1 | 四闸任一 pending 即 30 | **拒开工** | 是（签闸后） | 是 |
| FP-2 | **消费门 fail-closed 被放宽**（未命中改放行 / fail-open 化） | 红测拦截 · 审查拒收退回（维护者红线） | 是 | 否 |
| FP-3 | **SSE 事件表出现 diff**（`lg-rag-sse-v1` 破） | 审查拒收 · 退回 | 是 | 否 |
| FP-4 | **hitl 消费语义 freeze 文件被改**（web `hitl.ts` diff / decide 404·409 语义漂移） | 审查拒收 · 退回 | 是 | 否 |
| FP-5 | **resume 第二实现**（新恢复路径 / HTTP 自调） | grep 断言红 · 审查拒收 | 是 | 否 |
| FP-6 | delegation on 路径行为漂移（payload `run_id` 值变化 / 委派消费门误拒新形态） | 对拍断言红 · 审查拒收 | 是 | 否 |
| FP-7 | run_id 缺失场景语义变化（空 run_id 被写成 `""` 键进入载荷 · 工人误判有 run_id） | 键集钉红（空值不写入口径）· 审查拒收 | 是 | 否 |
| FP-8 | `_worker_state` 其余键静默变动（messages/subtasks 引用拷贝语义漂移等） | 旧测红 · 审查拒收 | 是 | 否 |
| FP-9 | 写能力无审批直跑（修复后回归保障被误读为放行口） | fail-closed 原样拦（负样本组既有断言承接 · 本修复**只**修「有审批但取不到 run_id」一路） | 是（补审批） | 是（等待授权帧） |

---

## 验收标准

- [ ] 人工闸：HG-TASK-DRAFT · HG-AUDIT-R1 · HG-GRAPH-MODULES · **HG-WORKER-STATE-RUN-ID-DESIGN** 均 approved 后方可勾选下列码项
- [ ] 红测负样本（**维护者红线**）：resume 后重下发不再被写审批消费门拦截——经真派发路径驱动（state 由 `_worker_state` 产出 · 非直造全 state），decide(approved) → 重下发 → `capability_write_approval_consumed` 台账 + **真落笔断言**（便签行落值 / 回执 / 幂等 done 三照 · approval_id 串链）
- [ ] 键集回归钉：`_worker_state`（有 run_id state）产物工人可见键集含 `run_id` 且值正确；空 run_id state 产物**不含** `run_id` 键（防空串污染）
- [ ] 正样本对拍：delegation on 路径 payload `run_id` 值修复前后一致（既有委派回归测试全绿）
- [ ] 消费门 fail-closed 语义零变化：未命中 / 读失败 / 过期 / 类型不符 / 租户不符各负样本既有断言全绿（`test_write_approval_gate` 全组）
- [ ] 红线对拍：SSE 事件表零 diff；web `hitl.ts` freeze 零 diff；resume 单路径 grep 断言绿；`registry.py` / `policy.py` 零 diff
- [ ] 旧测 grep 影响面：`test_step_contract.py` worker_state 三测 + `test_capability_redlines.py` R14 段直调面适配（如有）不放宽；`test_stage_w_write_expand.py` 16 枚 + W 链关联回归全绿
- [ ] 工程面：`ruff check app tests` 触及路径零新增；`pytest tests` 零新增红（本地产能既有红基线如实登记）；`./scripts/graph-compile.sh` EXIT=0；`npx spec-wave task lint` PASS
- [ ] 40 复跑销项（条件触发）：live 全链八段**免 shim**复跑达成（原偏差登记①销项）

---

## 依赖

| 依赖 | 说明 |
|------|------|
| 缺陷源 | issue [#329](https://github.com/Cyning12/ops-desk-api/issues/329)（正文 + 维护者 comment `6658235851` 立项令 · 红线与 test_strategy 四要求） |
| 实测证据 | [`invoke_20261105_40_verify.md`](../../harness/invokes/by-task/stage-w-write-expand/invoke_20261105_40_verify.md) §5 偏差登记①（live 两轮复现 + DBG 键集实证 + shim 八段全通） |
| 上游 task | [`task_stage_w_write_expand.md`](./task_stage_w_write_expand.md)（40 PASS 带偏差登记 · PR #327/#328 · 偏差#1 移交本档）· [`task_api_controlled_write_hitl.md`](../done/task_api_controlled_write_hitl.md)（CLOSE · PR #303 · 闸链真源） |
| 改码面 | `app/ops/lg_rag/multi/nodes.py:1359-1381`（`_worker_state` · 落点以闸签为准）+ 新增回归测试 |
| freeze 参照 | SSE `lg-rag-sse-v1`（事件表）· web `../ops-desk-web/src/api/hitl.ts`（`hitl-browser-decide-v1`） |
| 编码规范 | `docs/standards/CODING_BACKEND_L2_v1_zh.md` |
| 先例 | [`task_fix_no_proxy_bracket_ipv6_sanitize.md`](../done/task_fix_no_proxy_bracket_ipv6_sanitize.md)（graph=none 口径先例）· [`task_fix_hitl_decide_owner_fallback.md`](../done/task_fix_hitl_decide_owner_fallback.md)（fix 竖切 + 红测负样本模式先例） |

---

## 给执行帽的必读列表

1. `AGENTS.md`
2. 本 task（钉死契约 · 闸 · 非范围 · failure_paths）
3. issue #329 全文（缺陷机制 · 维护者立项令与红线）
4. [`invoke_20261105_40_verify.md`](../../harness/invokes/by-task/stage-w-write-expand/invoke_20261105_40_verify.md) §5（live 实证链 · shim 形态）
5. 代码：`app/ops/lg_rag/multi/nodes.py:264-265`（_run_id_of）· `:1359-1381`（_worker_state · 缺陷现场）· `:1643-1676`（route_next_subtask 派发）· `:462-532`（写消费门）· `:1857-1910`（tool_exec 闸点）· `app/ops/lg_rag/state.py:185-260`（LgRagState 通道 doc）
6. 测试面：`tests/test_step_contract.py`（worker_state 直调三测）· `tests/eval/test_capability_redlines.py:1622+`（R14）· `tests/test_write_approval_gate.py` · `tests/test_stage_w_write_expand.py`（A1 全链形态参照）
7. `docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`

---

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|----|------|------------|----------------------|----------------|
| R0 | 本 task = 已实锤缺陷（40 live 实证 + shim 验证）的最小修复竖切；非设计探索（修复形态已验证可行） | no | — | none |
| R1 | 范围 = Send 载荷补键 + 红测负样本 + 键集钉；非范围八条锁定（闸链/表/状态机/SSE/freeze/resume 第二实现/委派机制/web 面） | no | — | none |
| R2 | 落点三案：A `_worker_state` 补键（推荐 · 单点真源全派发路径一致 · shim 已验证 · 非空才写镜像 :1377 先例）/ B `route_next_subtask` 无条件补（只修派发路径 · `_worker_state` 直调方仍缺 · 弃项倾向）/ C 消费门放宽（**禁 · fail-closed 红线**）→ 决策点①入闸；回归影响面（delegation 已有 run_id 重复赋值兼容 + 旧测适配口径）→ 决策点②入闸 | no | — | 案 A 下 :1666 delegation 行成冗余（同值幂等 · 保留或清理随闸签） |
| R3 | failure_paths 锚既有语义：fail-closed 永不放宽 / SSE 零 diff / freeze 不动 / resume 单路径 / 空串键污染防（FP-7） | no | — | none |
| R4 | 可测性：负样本必须走真派发路径（`_worker_state` 产载荷）补单测盲区；红测先行（先红后绿）；旧测 grep 影响面项入验收（20-task-audit 行为变更类要求）；live 免 shim 复跑留 40 | no | — | 本地产能既有红基线（diff-whitelist 锚点漂移 / env 依赖 · CI skip 面）如实登记口径沿用 |
| R5 | 起草落稿 · 四闸 pending · NO-GO 20/30；30 改码须待闸签收后另行授权（issue #329 维护者令） | no | — | 无 |

**actual_last_round**：R5 · **early_stop**：no · **residual_risks**：无（见各轮）

### R0 · 问题框定

40 invoke 偏差登记①把缺口从「疑似」打成「live 实锤」：无 shim 两轮复现（run `fab290e9` / `c02daf71`）→ DBG 包装器实证工人 state 键集仅 5 枚无 `run_id` → 锁定丢键面在 `_worker_state`；同参数离进程复现匹配成功；shim 补位后八段全通。缺陷自 PR #303 时期潜伏（前后行为一致 · 非 #327 回归）。本 task 性质 = 按已验证形态接线 + 红测补盲区，不另开方向探索。

### R1 · 范围/非范围

范围三件套（补键 / 红测负样本 + 键集钉 / 条件旧测适配）收敛为最小竖切；非范围把「会被顺手扩大」的面全部锁死：消费门语义（FP-2）、SSE 事件表（FP-3）、web freeze（FP-4）、resume 单路径（FP-5）、委派机制——尤其防「修派发路径」滑成「改闸链」。

### R2 · 方案对比（设计闸两决策点）

- **案 A（推荐）**：`_worker_state` 内补 `run_id` 键（非空才写 · 镜像 :1377 supervisor_started_at 条件写键先例）。优点：单点真源——Send 载荷构造唯一出口，全部派发路径（tool / rag / 未来新增节点类型）一致受益；与 shim 实证形态同面；`_worker_state` 直调测试（step_contract / redlines）可键集钉防再发。代价：无（:1666 delegation 行变冗余同值幂等 · 保留或清理随闸签）。
- **案 B（弃项倾向）**：`route_next_subtask` 把 :1666 补键行移出 delegation 条件。缺点：只修派发路径，`_worker_state` 直调方（测试/未来调用）仍缺键；修复面比案 A 窄但真源仍分裂——载荷构造语义仍在两处。
- **案 C（禁）**：消费门放宽（空 run_id 跳过 / fail-open）。**触碰维护者红线（fail-closed 永不放宽），不入签。**

决策点②回归影响面：delegation on 路径 :1666 已有同值补键 → 案 A 后成重复赋值（幂等无漂移 · 对拍断言钉死）；旧测直调 `_worker_state` 三处断言对象均为 `assigned_subtask` 子树 → 预估零影响，实扫若见键集等值断言则适配不放宽。

### R3 · 边界/失败路径

FP-1~FP-9 逐条锚既有语义：四闸拒开工 / fail-closed 放宽拒收 / SSE 零 diff / freeze 不动 / resume 单路径 / delegation 漂移 / 空串键污染 / 其余键静默变动 / 无审批仍拦（本修复只修「有审批但取不到 run_id」一路——FP-9 防误读为放行口）。

### R4 · 验收/可测性

核心可测性风险 = 重犯单测盲区：负样本必须经真派发路径（`route_next_subtask` 或 `_worker_state` 产载荷直送 `tool_exec_node`），**禁止**直造全 state 调 tool_exec（那正是缺陷藏了 N 轮的原因）。红测先行：先以负样本红（载荷无 run_id → 再拦 → 零落笔）锁定缺陷，修复后绿（消费命中 → 真落笔三照）。行为变更类 task 依 20-task-audit 要求列「旧测 grep 影响面」验收项。live 免 shim 八段复跑留 40 销偏差登记①。

### R5 · 签收就绪

task 档落稿 · 四闸 pending · NO-GO 20/30；10 invoke 落盘 `docs/harness/invokes/by-task/fix-worker-state-send-run-id/`；lint PASS 后出 PR 待审；30 改码须待闸签收后**另行授权**（issue #329 维护者令）。

---

### 自检结论（执行者）

> **hat 10（10 起草）** · 已落稿：task 档 + 10 invoke · 未改 `app/` / `tests/` · 未签任何 human_gate（四闸 pending · NO-GO 20/30）。

| 命令 | 退出码 | 摘要 |
|------|--------|------|
| `npx spec-wave task lint --file docs/tasks/active/task_fix_worker_state_send_run_id.md` | 0 | LINT: PASS（2026-11-05 · 10 起草自检） |

---

## 修订

| 日期 | 说明 |
|------|------|
| 2026-11-05 | 10 落稿：承 issue #329 维护者 comment `6658235851` 令起草 fix task（10 帽活 · 只产 task 档 + invoke + lint PASS + PR · 禁改业务码）· 缺陷机制/影响面/证据承 40 invoke 偏差登记① · HG-WORKER-STATE-RUN-ID-DESIGN 两决策点（修复落点三案 A 推荐/B/C 禁 · 回归影响面）· 维护者四红线入 failure_paths（SSE 零 diff / freeze 不动 / resume 单路径 / fail-closed 永不放宽）· 红测负样本（真派发路径 · 真落笔断言）入 test_strategy · R0–R5 全轮 · 四闸 pending · NO-GO 20/30 |
| 2026-11-05 | **四闸 approved + 30 授权**：lead 签认（PR #331 review `5785422963` 审查通过 · 设计闸裁决案 A + 回归影响面签收）· issue #329 comment `6658823187` 30 授权（分支 `fix/worker-state-send-run-id` · GATE_VERIFY 闸据=本档闸表）· 六交付条件：①红测先行可见红→绿（真派发路径 · 消费命中+真落笔三照）②旧测适配清单随 PR（适配不放宽）③改码面唯一（仅 `_worker_state` 补键+新测+旧测适配）④四红线零 diff 对拍 ⑤ruff+pytest 全量+graph-compile 绿 ⑥PR 说明逐条对照验收标准 · draft→active · GO 30 · 出货 PR 待 lead 终审 · 40 复跑照旧 |
