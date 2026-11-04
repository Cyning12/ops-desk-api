# Task：decide 归属反查对无帧 run 的兜底（sync invoke 面 HITL 审批链断点修复）

> **状态**：`active`（2026-11-04 · 10 起草 + 20-R1 自签审查随档 · 四闸 approved（00 代录 · 依据 issue #315 维护者评论 #6623212135 B+C 签认 + #6623253310 全程委托自签）· **GO 20/30 · 出货后 lead 复审验收并决策 merge（#6623253310）**）
> **类型**：fix / 契约兜底（HITL 归属反查末位兜底 + 文档行为差异声明）
> **上游**：issue [#315](https://github.com/Cyning12/ops-desk-api/issues/315)（sync invoke 无 run 事件帧 → decide 404 · 预存在行为非 #313 引入）· 实测锚 workspace `invoke_20261104_10_c6_retest.md` §5（O1 观察）
> **分支**：`fix/hitl-decide-owner-fallback`（30 用 · 10/00 本档走 `agent/decide-fallback-task-c2838ef4cc6f`）
> **10 注**：2026-11-04 · 维护者签认 **B+C** 方案（不选 A：sync 补帧扩大事件面牵连 #311 冻结面）· 本棒仅落 task 档 + 20-R1 审查文 + invoke · **禁止**改 `app/`

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `fix-hitl-decide-owner-fallback` |
| **git_branch** | `fix/hitl-decide-owner-fallback` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 红测先行：负样本①「sync invoke 触发写闸 → 建单 → decide **不再 404**（200 进入 adecide 语义）」（**维护者红线**）②无帧 + thread 归属他人 → decide 仍 404 不越权 ③无帧 + thread 行缺失 → decide 仍 404（fail-closed）；正样本：SSE 有帧 run 的 decide / pending 行为**逐字节零变化**（事件表仍是第一真源 · 兜底分支不触发）；码面锚点 grep：`_run_owner_of` 兜底分支存在且仅兜 `run_owner` 返 None 一路 · SSE 事件写入面零 diff · freeze 两文件零 diff |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1`（薄增量 · hitl 模块条目一句备注） |
| **graph_delta** | api `docs/_tech_graph/l1/01_modules.md` hitl 模块条目一句备注「decide 归属反查无帧兜底（thread 末位反查 · 事件表仍第一真源）」· 不新增一级模块 |
| **graph_delta_note** | 模块边界不变；仅 hitl 模块内归属反查 helper 增兜底分支 → G-L1 同步一句 |
| **wiki_delta** | `n/a`（行为差异声明落 RUNBOOK 指南 · 非 wiki 面） |
| **wiki_delta_note** | 文档声明目标 = `docs/guides/RUNBOOK_hitl_ops_v1_zh.md` 增补 sync invoke 面差异小节（30 落码时同步） |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,20,30,40` |
| **invoke_retention_profile** | `default` |
| **experience_capture** | `recommended` |
| **kpi_aggregator** | `CLOSE` |
| **orchestration** | 10 落稿 → 20-R1 审查（**自签** · 审查文随档 · 依据 issue #315 评论 #6623253310 全程委托）→ 00 代录四闸 approved → **PR 出货 → lead（维护者代理人）审查验收并决策 merge**（issue #315 评论 #6623253310）→ 30（分支 `fix/hitl-decide-owner-fallback` · GATE_VERIFY 闸据=本档闸表）→ 40 → CLOSE |
| **freeze_id** | `lg-rag-sse-v1`（**零 diff 红线**）· `hitl-browser-decide-v1`（decide 404/409 既有语义不破 · 本 task 不动 freeze 文件） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | approved | 20-R1, 30 | 2026-11-04 00 代录 · 依据 issue #315 评论 #6623212135（10 帽授权 + B+C 签认）+ #6623253310（全程委托自签）· 维护者签收草稿 |
| HG-AUDIT-R1 | approved | **30** | 2026-11-04 00 代录 · 依据同上 · 20-R1 审查文随档 PASS（`docs/harness/reviews/task_fix_hitl_decide_owner_fallback_audit_R1_20261104.md` · §2 八项全 PASS · §3 三决策点已裁决） |
| HG-GRAPH-MODULES | approved | **30**（条件触发） | 2026-11-04 00 代录 · 依据同上 · G-L1 薄增量口径确认（hitl 模块一句备注 · 不新增一级模块） |
| HG-DECIDE-FALLBACK-DESIGN | approved | **30** | 2026-11-04 00 代录 · 依据同上 · 三决策点裁决（审查文 §3）：① 兜底机制源=**thread 末位反查**（弃建单打戳）② 作用面=`_run_owner_of` 单一 helper（不动 `_open_event_sink`）③ 声明=RUNBOOK 增补 sync invoke 面差异小节 + docstring 同步 · 不新增 freeze |

---

## 背景与目标

sync `POST /api/ops/lg-rag/invoke`（mode=supervisor）触发写闸时，拦单正常落库，但 **sync invoke 不落 run 事件帧**（事件帧是 SSE `RunWorker` 路径专属产物），hitl decide 的归属反查（`app/ops/hitl/router.py:240-243` → `event_store.run_owner`）返回 None → decide 返回 **404「申请不存在」**，resume 无从谈起，单据滞留 pending。SSE 路径（`POST /api/ops/lg-rag/stream`）有事件帧，不受影响。实测锚（2026-11-04 复测 · workspace `invoke_20261104_10_c6_retest.md` §5）：invoke 面拦单 `hitl_503224fd719a42c8b0fa`（run `8b4f3caf…`）decide → 404 滞留 pending；同 query 走 SSE → run `c2224431…` 全链正常。**预存在行为，非 PR #313 引入**（#313 修的是 resume 链租户快照/打戳/守卫，与本缺口无因果）。

维护者签认（issue #315 评论 #6623212135）：采用 **B+C**——

- **B**：decide 归属反查对无帧 run 增加兜底——单据 `pending` 且无活动帧时按单据自身线索判定归属；**不选 A**（sync invoke 补落 run 事件帧）——run 事件帧是 SSE 路径专属产物，sync 补帧会扩大事件面并牵连 #311 冻结面。
- **C**：同步在文档声明 sync invoke 面 HITL 审批链的行为差异。
- **红线**：SSE 事件表零 diff（`lg-rag-sse-v1` 不破）；红测负样本须覆盖「sync invoke 触发写闸 → decide 不再 404」。

本 task = 该签认的修复竖切：`_run_owner_of` 末位兜底 + RUNBOOK 行为差异声明，让 sync invoke 面写闸单据的审批链（decide 可达）闭环。

---

## 现状锚点（只读 · 30 必读 · 10 已扫）

| 主题 | 路径 · 锚点 | 现状 |
|------|-------------|------|
| 归属反查 helper | `app/ops/hitl/router.py:152-178 _run_owner_of` | 经 `run_id` 反查事件表 `run_owner`；无帧/失败 → None + error 日志，调用方 404（**兜底落点=本 helper 单一真源**） |
| pending 列表调用 | `app/ops/hitl/router.py:201`（`list_pending` 内 `_run_owner_of`） | owner None → 排除不泄露；sync 面单据**当前不可见**（兜底后对其属主可见——decide 前置必要条件） |
| decide 调用 | `app/ops/hitl/router.py:240-243` | owner None 或 ≠ 本人 → 404「申请不存在」（不泄露存在性 FP-1 口径 · **本 task 红线现场**） |
| 事件表真源 | `app/ops/lg_rag/event_store.py:93-110 run_owner` | run 无帧 → None；事件表 user_id 列 = 历史面归属第一真源（**保持不动**） |
| 恢复链事件 sink | `app/ops/hitl/router.py:382-416 _open_event_sink` | 直引 `run_owner`（**不经 helper**）；无帧 → sink=None → resume 继续执行但不落恢复段事件（:488-489）——**本 task 明确不动** |
| sync invoke 面 | `app/ops/lg_rag/router.py:387-449 invoke_lg_rag` | `run_id=uuid4` 下发 · 全程**零事件帧**；`_prepare_thread`（:330-345）跨用户 thread 404 前置拦截 |
| thread 归属 SoT | `app/ops/lg_rag/thread_store.py:63-89 persist_thread_turns` + `app/db/models.py:291-299 OpsLgRagThread`（`user_id` 非空 · FK ops_users） | dispatch 返回后即落 thread 行（**含 interrupt 场景** · invoke :426 无异常短路）→ 无帧 run 的归属可经 `thread_id` 末位反查 |
| 单据行无 user_id | `app/db/models.py:444+ OpsHitlRequest`（run_id/thread_id/tenant_id · **无 user_id 列**） | 归属只能反查，不能直读（钉戳需迁移——见设计决策①弃项） |
| 文档声明面 | `docs/guides/RUNBOOK_hitl_ops_v1_zh.md`（§1 全链菜谱 · §2 在飞 409 · §3 持久化） | 全文以 SSE 面为默认视角，sync invoke 面 HITL 差异**无声明**（C 的落点） |
| 实测证据 | issue #315 正文 + workspace `invoke_20261104_10_c6_retest.md` §5 | invoke 单 decide 404 滞留 · SSE 对照全链正常 |

---

## 10+20 钉死契约（HG-DECIDE-FALLBACK-DESIGN 三决策 · 30 不得静默改义）

| 项 | 钉死 |
|----|------|
| **① 兜底机制源** | **`run_owner(run_id)` 返 None 时，末位反查单据 `thread_id` → `OpsLgRagThread.user_id`**。理由：invoke 面 `_prepare_thread` 已把跨用户 thread 404 在**建单之前**拦住（router.py:330-345），能走到建单的单据其 thread 必属 run 发起者；dispatch 返回后 `persist_thread_turns` 即落 thread 行（含 interrupt）。**弃项：建单时打 user_id 戳**——需 schema 迁移 + nodes 穿线，超出「decide 反查兜底」薄改授权范围；后续若 revive 另立 task |
| **② 作用面** | 兜底落 `_run_owner_of` **单一 helper** → `GET /pending`（:201）与 `POST /decide`（:240）同源受益（pending 可见是 decide 可达的前置）。**不动 `_open_event_sink`**（resume 链 :400 直引 `run_owner`）：无帧时 sink=None 现状继续（resume 执行不落恢复段事件），sync 面无 replay 消费者，差异由文档声明（③）承载 |
| **③ 文档声明口径** | `docs/guides/RUNBOOK_hitl_ops_v1_zh.md` 增补「sync invoke 面 HITL 审批链行为差异」小节：**invoke 不落 run 事件帧（SSE 专属产物 · 永不补帧）→ 归属反查走 thread 末位兜底 → decide 可达 → resume 执行但无 replay 追帧面（结果经线程历史/再次 invoke 可见）**；`_run_owner_of` docstring 同步一句。不新增 freeze · 不动 freeze 文件 |
| **兜底触发条件** | 严格限定：`run_owner(run_id)` 返 None（**仅无帧/反查失败一路**）；有帧 run 零行为变化——事件表仍是第一真源，thread 反查只作末位兜底，**不前置、不替换** |
| **fail-closed 不变** | thread 行缺失 / thread 归属解析失败 → 维持 None → 调用方 404 语义零变化；**绝不猜 user_id**（helper docstring :157-158 既有铁律不破） |
| **404/409 语义不破** | 兜底只解决「无帧导致的归属不可判定」；未知 id / 归属他人 / 已决重复 decide 的 404/409 语义与 `hitl-browser-decide-v1` 消费语义全量不变 |
| **SSE 零改** | 不新增/不改 SSE `event_type`（`lg-rag-sse-v1` 不破）；事件表写入面（`event_store.append` 一族）零 diff |

---

## 范围（竖切 · 四闸齐后才 30）

- [ ] **D-fix-1 · `_run_owner_of` 无帧兜底**：`run_owner` 返 None 时按单据 `thread_id` 末位反查 `OpsLgRagThread.user_id`；失败/缺失回退 None（fail-closed 不变）；helper docstring 同步声明
- [ ] **D-fix-2 · RUNBOOK 行为差异声明**：`docs/guides/RUNBOOK_hitl_ops_v1_zh.md` 按钉死契约③增补 sync invoke 面小节（触发 → decide 可达 → resume 无 replay 面 → 结果可见路径）

### 非范围

- **sync invoke 补落 run 事件帧**（维护者已裁不选 A：事件面扩大牵连 #311 冻结面）
- **`_open_event_sink` / resume 执行链改动**（sink=None 现状照登；resume 归属直引 `run_owner` 不动）
- **hitl 表加 user_id 列 / 任何 schema 迁移**（弃项 · revive 另立 task）
- **freeze 文件本体**（`lg-rag-sse-v1` / `hitl-browser-decide-v1` 均不动）
- **SSE 路径任何行为变化**（有帧 run 全链零变化）
- **issue #311 冻结面** · **web 仓**
- issue #315 其余观察（如有）另行立项

---

## failure_paths

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----------|----------|--------|----------|
| 四闸任一 pending 即 30 | **拒开工** | 是 | 是 |
| **兜底前置/替换事件表真源**（有帧 run 也走 thread 反查） | 审查拒收（事件表第一真源红线）· 30 返修 | 是 | 否 |
| **兜底越权**（thread 归属他人仍放行 decide / 猜 user_id） | 红测拦截（负样本②）· 审查拒收（fail-closed 铁律） | 是 | 否 |
| **误伤有帧路径**（SSE run 的 decide/pending 行为漂移） | 红测拦截（正样本零变化）· 30 返修 | 是 | 否 |
| **SSE 事件表出现 diff**（`lg-rag-sse-v1` 破） | 审查拒收 · 退回 | 是 | 否 |
| 404/409 既有语义漂移（`hitl-browser-decide-v1` 破） | 审查拒收 · 退回 | 是 | 否 |
| 文档声明缺失或与码面行为不符（C 未落地） | 40 拒收 | 是 | 否 |
| sync 面 thread 行缺失（persist 失败等极端路径） | 兜底返 None → decide 仍 404（fail-closed 如实照登） | 是（补 thread 后重试） | 是（单据滞留可见性由 pending 排除维持现状） |

---

## 验收标准

- [ ] 人工闸：`HG-TASK-DRAFT` · `HG-AUDIT-R1` · `HG-GRAPH-MODULES` · `HG-DECIDE-FALLBACK-DESIGN` 均 approved 后方可勾选下列码项
- [ ] 红测负样本①（**维护者红线**）：sync invoke 触发写闸 → 建单 → `POST /hitl/requests/{id}/decide` **不再 404**（进入 adecide 正常语义；approved/rejected 均验证）
- [ ] 红测负样本②：无帧单据 thread 归属他人 → decide 仍 404（不越权 · fail-closed）
- [ ] 红测负样本③：无帧且 thread 行缺失 → decide 仍 404
- [ ] 正样本：SSE 有帧 run 的 decide / pending 行为零变化（既有 hitl 测全绿 · 新增对拍断言）
- [ ] 码面锚点 grep：`_run_owner_of` 兜底分支仅兜 `run_owner` 返 None 一路；SSE 事件写入面零 diff；freeze 两文件零 diff
- [ ] RUNBOOK 增补小节与码面行为一致（30 截图/摘录对拍）；`_run_owner_of` docstring 已同步
- [ ] `ruff` 触及路径绿；`pytest` 本波 + 既有 hitl 回归绿
- [ ] `./scripts/graph-compile.sh` 绿（G-L1 hitl 模块一句备注同步）；不新增 G-L1 一级模块
- [ ] `npx spec-wave task lint --file docs/tasks/active/task_fix_hitl_decide_owner_fallback.md` PASS

---

## 依赖

| 依赖 | 说明 |
|------|------|
| 缺陷源 | issue [#315](https://github.com/Cyning12/ops-desk-api/issues/315)（正文 + 评论 #6623212135 B+C 签认 · #6623253310 全程委托自签） |
| 实测证据 | workspace `invoke_20261104_10_c6_retest.md` §5（O1 · invoke 单 404 / SSE 对照全链） |
| 归属真源 | `app/ops/lg_rag/event_store.py:93-110 run_owner` · `app/ops/lg_rag/thread_store.py:63-89` · `app/db/models.py:291-299` |
| 改码面 | `app/ops/hitl/router.py:152-178`（helper）· `docs/guides/RUNBOOK_hitl_ops_v1_zh.md` |
| 先例 | `docs/tasks/done/task_hitl_browser_decide.md`（404/409 语义 · FP-1 不泄露口径）· `docs/tasks/active/task_api_w_hitl_tenant_fix.md`（fail-closed / 红测先行模式） |
| 编码规范 | `docs/standards/CODING_BACKEND_L2_v1_zh.md` |

---

## 给执行帽的必读列表

1. `AGENTS.md`
2. 本 task（钉死契约 · 闸 · 非范围 · failure_paths）
3. issue #315 全文（现象 · 判读 · 维护者 B+C 签认与红线）
4. 代码：`app/ops/hitl/router.py:152-178,:201,:240-243,:382-416` · `app/ops/lg_rag/event_store.py:93-110` · `app/ops/lg_rag/router.py:387-449` · `app/ops/lg_rag/thread_store.py:63-89`
5. `docs/guides/RUNBOOK_hitl_ops_v1_zh.md`（文档声明落点）
6. `docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`

---

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|----|------|------------|----------------------|----------------|
| R0 | 本 task = 维护者已签认 B+C 的修复竖切；不是设计探索（方向 A 已裁死） | no | — | none |
| R1 | 机制源取舍：thread 末位反查（零迁移 · invoke 面前置守卫已保证 thread 属主=run 发起者）vs 建单打戳（迁移+穿线超授权）→ 前者入 HG-DECIDE-FALLBACK-DESIGN 决策点① | no | — | thread 行缺失极端路径 decide 仍 404（fail-closed 如实照登） |
| R2 | 作用面切分：兜底落 `_run_owner_of` helper（pending/decide 同源）· `_open_event_sink` 明确不动（sink=None 现状 + 文档声明承载）→ 决策点② | no | — | sync 面 resume 后无 replay 追帧（文档声明即契约 · 非缺陷） |
| R3 | 闸设计：HG-DECIDE-FALLBACK-DESIGN 承载三决策点；C 的声明位置/口径钉为决策点③；其余走 10→20→30→40 常链 | yes | 决策面已框死（机制源/作用面/声明口径均落地为闸或契约行）；实现细节属 30 实扫 | 多用户共用 thread_id 的托管场景下兜底归属=thread 属主（与 persist 守卫同语义 · 如实照登） |
| R4 | （未开） | — | early_stop at R3 | — |
| R5 | （未开） | — | early_stop at R3 | — |

**actual_last_round**：R3 · **early_stop**：yes · **residual_risks**：见 R1/R3

### R0 · 问题框定

issue #315 把缺口从「疑似」打成「实证」：sync invoke 面写闸单据因无事件帧 → 归属反查 None → decide 404 → 审批链断。维护者已签认 B+C 并给出红线，本 task 性质 = 「按签认接线 + 红测负样本」，不是方向探索。

### R1 · 兜底机制源

签认语「按单据自身 run_id 判定归属」落地解读：run_id 本身不带归属（事件表无帧即断），单据行自身携带的可判定线索 = `thread_id` → `OpsLgRagThread.user_id`。invoke 面 `_prepare_thread` 在建单**之前**就已对跨用户 thread 404（router.py:330-345），且 dispatch 返回后 `persist_thread_turns` 即落 thread 行（含 interrupt），故能建单的单据其 thread 属主 = run 发起者。零迁移、薄改、可红测。弃项（建单打 user_id 戳）留痕防 30 漂回。

### R2 · 作用面切分

`_run_owner_of` 是 pending 列表与 decide 的**单一**归属 helper——兜底落此处两入口天然同源，pending 可见也是 decide 可达的前置。`_open_event_sink` 直引 `run_owner` 不经 helper，且 sink=None 时 resume 继续执行（:488-489 现状）——动它即越出「decide 反查兜底」授权，其差异由 C 的文档声明承载。

### R3 · 闸设计 · 收敛

三决策点（机制源 / 作用面 / 声明口径）全影响契约语义 → 收进 HG-DECIDE-FALLBACK-DESIGN 一并签。常链不变。残险照登：thread 行缺失路径维持 404（fail-closed 不是缺陷是语义）；多用户托管 thread 场景兜底归属=thread 属主（与 persist 守卫同语义）。

**R3 增补（2026-11-04 · 00 代录四闸 approved 前）**：维护者评论 #6623253310 全程委托 00 自签本单过程文档——20-R1 审查按委托执行（审查文 `docs/harness/reviews/task_fix_hitl_decide_owner_fallback_audit_R1_20261104.md`），三决策点裁决与四闸代录均依据该评论留痕；出货后由 lead 审查验收并决策 merge。

### R4 ·（未开 · early_stop）

本轮不展开；待 HG-DECIDE-FALLBACK-DESIGN 签收后由 30 实扫补足。

### R5 ·（未开 · early_stop）

本轮不展开。

---

### 自检结论

| 命令 | 退出码 | 摘要 |
|------|--------|------|
| `npx spec-wave task lint --file docs/tasks/active/task_fix_hitl_decide_owner_fallback.md` | 0 | LINT: PASS（2026-11-04 · 10 起草棒） |

---

## 修订

| 日期 | 说明 |
|------|------|
| 2026-11-04 | 10 起草壳（维护者 issue #315 评论 #6623212135 令立项 · B+C 签认 + 红线入档 · HG-DECIDE-FALLBACK-DESIGN 三决策点 · R0–R3（R3 early_stop）· 四闸 pending · NO-GO 20/30）· lint PASS |
| 2026-11-04 | 00 代录四闸 approved（HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES / HG-DECIDE-FALLBACK-DESIGN · 依据 issue #315 评论 #6623212135 + #6623253310 全程委托自签 · 20-R1 审查文 §3 三决策点裁决随档）· draft→active · GO 20/30 · **出货后 lead 复审验收并决策 merge（#6623253310 · merge 与最终验收权仍在人）** |
