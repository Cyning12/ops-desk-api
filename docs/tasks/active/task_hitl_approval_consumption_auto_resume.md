# Task：hitl-approval-consumption-auto-resume（T2 · D5 批准后自动继续可配置面 · 触发器+行锁认领+补偿扫描）

> **状态**：`draft`  
> **类型**：**SPEC 承接**（SPEC v1 · HG-SPEC-SIGNOFF=approved 2026-10-10）  
> **依据**：`docs/spec/hitl-approval-consumption/SPEC-hitl-approval-consumption_v1.md`（**SPEC 文档当前在 `spec/hitl-approval-consumption` 分支 · 随首个实现 PR 一并带入 master**）——本 task 承接 D5（批准后自动继续可配置面）· Q6/Q7 · FP-8~FP-11 · A9/A10（+ A5/A6/A7/A8 存续面）· R2-N1/R2-N2/R2-N3  
> **分支**：`task/hitl-approval-consumption-auto-resume`（base：`master` · **须含 T1 merge** · 禁止 master 直改）  
> **拆分**：T2（本）**依赖 T1 `task_hitl_approval_consumption_loop.md` merge 进 master 后方可 30**（消费门是 auto resume 全链 A9 前提）；T3 与本 task 无依赖

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `hitl-approval-consumption-auto-resume` |
| **git_branch** | `task/hitl-approval-consumption-auto-resume` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | pytest 单测/集成为主：配置面（env 合法/非法回退 · resume_mode 白名单 400/缺省 inherit）+ 触发器派发断言（auto 派发/manual 不派发/单次 decide 至多一次）+ 恢复路径同源断言（与手动 resume 同一代码路径）+ 行锁认领并发断言（Db store 双连接并发仅一认领 · FOR UPDATE SKIP LOCKED）+ 补偿扫描幂等/补触发断言 + 不循环断言（auto 后仍拦回挂起不再自动触发）+ manual 默认零 diff（无后台任务 · decide 既有测试原样绿）；live HTTP/SSE auto 全链 done{completed} 实录留 40 复跑 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1`（行备注 · 不新增一级模块） |
| **graph_delta** | `docs/_tech_graph/l1/01_modules.md` hitl / lg_rag 两行在册备注（main.py lifespan 挂点随 hitl 行备注说明） |
| **graph_delta_note** | 模块边界不变：hitl 模块内增触发器/认领/补偿扫描（decide 端点可选键 · store 新增只读+行锁方法 · 既有 adecide/_DECIDE diff 空）+ lg_rag 行补 auto 恢复同源说明；main.py lifespan 挂点随 hitl 行备注说明 → G-L1 行备注同步，HG-GRAPH-MODULES 随 30 回写由 00 代录 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | SPEC 承接 task · 机制接线增量无 wiki 条目变更 |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,20,30,40` |
| **invoke_retention_profile** | `default` |
| **experience_capture** | `recommended` |
| **kpi_aggregator** | `CLOSE` |
| **orchestration** | 10 落稿 → 20 R1 → 维护者签 → 30 → 40 → PR+CI 绿 → 图谱回写 → CLOSE |
| **freeze_id** | 无（零新表/零新列 · payload jsonb 增键 · 零新 SSE 事件类型 · 零 alembic） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | **approved** | 20-R1, 30 | 维护者签 · 00 代录 2026-10-10（授权「授权00签收所有过程文档」） · lint PASS |
| HG-AUDIT-R1 | **approved** | 30 | 维护者签 · 00 代录 2026-10-10（授权「授权00签收所有过程文档」） · 依据 R1 审查 PASS（reviews/task_hitl_approval_consumption_auto_resume_audit_R1_20261010.md · N-1~N-3 非阻塞 · N-1 补偿扫描兜 OA 批准单语义明示留 30）· **另：T1 merge 前 30 仍拒开工** |
| HG-GRAPH-MODULES | **approved** | 30 | 维护者签「在册」（hitl/lg_rag 行备注段）· 00 代录 2026-10-10 · 30 回写义务在案 |
| HG-PILOT-OPSDESK-GLAYER | n/a | — | 非物理分层试点 task |

---

## 背景与目标

SPEC v1 §1 第四立案（承 handoff 令与终局文档 §4 :82-83）：v0 链路只覆盖「手动 resume」半环——`decide(approved)` 之后必须人再点一次 `POST /requests/{id}/resume` 图才继续跑（router.py:184-186 「两步钉死」docstring 现状）。终局 §4 :82 裁定「批准后自动继续」做成**可配置**（全局默认 + 可按审批单选「立即执行/稍后手动」），机制 = 触发器（Q6 裁定=进程内后台任务 + PG 行锁认领 + 补偿扫描）+ 无状态恢复纪律（SPEC 设计纪律 6 · 触发器不载状态 · 进程重启零丢失）。

**一句话目标**：在 T1 消费成环之上，把「批准后继续」做成可配置自动/手动两级面——全局 env `OPS_HITL_AUTO_RESUME`（默认 `manual` 现状零 diff）+ decide 载荷可选键 `resume_mode`（inherit/immediate/manual · 白名单 fail-closed 400）；auto 形态下 decide(approved) 持久化成功后派发进程内 asyncio 任务走**与手动 resume 同一条恢复路径**直达 `done{completed}`（A9 · handoff 验收令）；PG 行锁认领防多副本重复触发，启动时+定时补偿扫描兜底进程崩溃/重启丢失（FP-8~FP-11）。

---

## 现状锚点（只读 · 30 必读 · 10 已逐行实读 · base `4d905e0`）

| 锚点 | 实证 |
|------|------|
| `app/ops/hitl/router.py:112-116` | `_DecidePayload`：`decision: Literal["approved","rejected"]`（非法值 Pydantic 挡成 **422** · docstring 明示）+ `note: str = ""`——`resume_mode` 增键的载荷模型锚点（R2-N1 形态钉见钉死契约） |
| `app/ops/hitl/router.py:175-232` | `decide_request`：归属守卫 :193-200 → `store.adecide` :201-206 → 重复 409 :207-215 → 审计 :216-222 → 响应 `resume` 块 :223-232（「两步钉死 · 不自动 resume」现状语义）。**触发器挂点 = :201-216 成功分支之后**（R2-N2） |
| `app/ops/hitl/router.py:235-275` | OA `callback`（HMAC 签名面 · 同 `adecide` 守卫）——**本波不挂触发器**（非范围 · 签名面行为零 diff） |
| `app/ops/hitl/router.py:377-430` | `resume_request` 恢复段：`aget` 404/409 守卫 :393-402 → 空 unlock 409 :404-411 → `_open_event_sink` :412-416 → `resume_hitl_run` :417-423 → `ResumeError` → HTTP 映射 :424-436 → `sink.close` + `_persist_resumed_turns` :437-439。**自动 resume 执行体抽取复用此段**（禁 HTTP 自调） |
| `app/ops/hitl/resume.py:285` | `resume_hitl_run(thread_id, approved, rejected, decided_by, update_sink)`——从事件表/checkpoint 重建喂 `Command(resume=...)`（无状态恢复纪律的既有载体） |
| `app/ops/hitl/router.py:319-374` | `_open_event_sink`（run 归属反查失败显式 error 日志返 None）+ `_persist_resumed_turns`（补落 user/assistant turn）——恢复段两件套复用面 |
| `app/ops/hitl/store.py:127-228` | `DbHitlStore` 既有四方法（acreate/aget/alist/adecide）· **全仓无 `FOR UPDATE`/`SKIP LOCKED` 先例**（10 grep 实证）——行锁认领为本 task 新增机制（新增方法 · 既有方法 diff 空） |
| `app/ops/hitl/persistence.py:61-77` | `get/set/reset_hitl_store` 测试隔离面（行锁断言须 `set_hitl_store(DbHitlStore(...))` 显式装配） |
| `app/main.py:12-16` | lifespan 现仅 `log_tracing_startup()` + `yield`——补偿扫描挂点（启动时扫 + 周期任务 + shutdown cancel 纪律） |
| `app/ops/lg_rag/event_store.py:26-142` | 既有只读面：`persist_run_event`/`run_owner`/`last_seq`/`assert_run_owned`/`load_events_after`/`thread_owner`/`list_thread_activity_page`/`fetch_events_for_threads`——**无 run 终态谓词**（补偿扫描「run 未终态」判定需新增只读查询 · 30 裁定留痕） |
| `tests/conftest.py` + 8 个 `TestClient` 测试文件 | `test_hitl.py`/`test_hitl_resume.py`/`test_hitl_resume_events.py`/`test_hitl_pending_decide.py`/`test_chat_ws.py`/`test_chat_router.py`/`test_admin_capability_observability.py` 等经 TestClient 触发 lifespan——**manual 默认下扫描任务零创建**否则全局面炸（实操坑 · 钉死契约） |
| 多副本先例 | `docs/tasks/done/task_multi_replica_verify.md`（双进程 pytest+部署实测形态 · FP-8 并发断言基建参照） |
| T1 前置 | `task_hitl_approval_consumption_loop.md`（消费门 + unlock 回填 · **未 merge 则 A9 全链不可达**：无消费→恢复后仍再拦；无 D2→resume 409） |

---

## 钉死契约（30 不得静默改义）

| 项 | 钉死 |
|----|------|
| **配置面（Q7）** | 全局 env `OPS_HITL_AUTO_RESUME` ∈ {`manual`（默认 · 现状语义零 diff）, `auto`} · **非法值回退 `manual`**（fail-closed）；审批单级覆盖：decide 端点请求载荷增**可选键** `resume_mode` ∈ {`inherit`, `immediate`, `manual`}（缺省=`inherit` 用全局默认）。有效模式求解：`immediate`→auto · `manual`→manual · `inherit`→全局 env |
| **R2-N1 · 400/422 形态钉实现路径** | `resume_mode` 字段类型钉 **`str`（缺省 `"inherit"`）· 禁 `Literal`/`Enum`**——Pydantic 校验失败会返回 **422**，而 SPEC FP-10/A10 钉死未知值 **400**；端点内手工白名单校验 → 未知值 `raise HTTPException(400)`。`decision` 字段既有 `Literal`/422 形态**一行不动**（:115）；`_DecidePayload` docstring 须注明两字段错误形态差异（decision 非法=422 既有 · resume_mode 未知=400 SPEC 钉死）。**载荷缺键 = inherit · 既有调用不带该键行为同现状零 diff** |
| **R2-N2 · 触发器挂点** | `router.py` `decide_request` **成功分支**（`adecide` 返回非 None 后 · :201-216 段）：decision=approved 且有效模式=auto → 派发进程内 asyncio 后台任务。**`store.py` `adecide`/`_DECIDE` git diff 为空**（SPEC A7 存续 · 触发器不落 store 层）；**OA `callback`（:235-275）本波不挂触发器**（签名面行为零 diff · 载荷无 `resume_mode` 面 · 非范围） |
| **恢复路径同源（无状态恢复纪律）** | 自动 resume 走**与手动 resume 同一条恢复路径**：抽取复用 `resume_request` 恢复段（`_open_event_sink` → `resume_hitl_run` → `sink.close` → `_persist_resumed_turns`）· **禁止 HTTP 自调** · 禁止第二条恢复实现；一律从事件表/DB 重建（触发器不载状态 · 进程内 asyncio 任务句柄不落盘 · SPEC 设计纪律 6 红线） |
| **派发不阻响应** | decide 端点语义在先：`adecide` 持久化成功即 200 语义成立；后台任务派发失败/执行失败只落台账，**不改变 decide 已返回的结果**；响应 `resume` 块在 auto 形态下注明已触发自动恢复（manual 形态字面零 diff） |
| **R2-N3 · 行锁锚点与并发断言基建** | `DbHitlStore` **新增**认领方法（建议 `aclaim_approved_for_resume` · 既有四方法 diff 空）：`SELECT … FOR UPDATE SKIP LOCKED` · 条件 status=approved ∧ decided_at 未过 TTL ∧ 同 run 无未决 pending；**认领窗口内再查一次判定**后派发。并发断言基建（FP-8）：Db store 双连接/双协程并发认领**仅一成功**（真 PG fixture 形态承 `test_hitl_resume.py` 真 PG 段与 task_multi_replica_verify 先例）；**InMemory store 无行锁语义**——行锁断言仅 Db 组，InMemory 以 resume 状态机守卫幂等断言覆盖（非 pending/unlocked 态重入无副作用），**禁拿 InMemory 做行锁假断言** |
| **补偿扫描兜底** | `main.py` lifespan（:12-16）挂：启动时扫一次 + 周期任务（周期 env 建议 `OPS_HITL_AUTO_RESUME_SCAN_INTERVAL_SECONDS` 默认 60 · 域 [5,3600] 非法回退）。「已批准未恢复」操作定义钉：status=approved ∧ decided_at 未过 TTL ∧ **run 无终态** ∧ **同 run 无未决 pending**（第四条件防 FP-11 循环：auto resume 后仍被拦会产生新 pending → 扫描自然跳过）。行锁认领后补触发。**manual 模式下扫描任务零创建**（TestClient 8 文件 lifespan 面零 diff · 见 B1）；shutdown 须 cancel 周期任务（任务泄漏坑） |
| **单次 decide 一次触发（FP-11）** | 单次 decide 成功分支至多派发一次；自动 resume 后仍被拦（单据过期/键不匹配 → 新挂起新 pending）→ 回挂起态**等人** · 不再自动触发；判定逻辑零改（D1 消费门语义不变 · T1 面） |
| **off/manual 零 diff（SPEC A6 本 task 面）** | `OPS_HITL_AUTO_RESUME` 缺省/非法=manual：无后台任务 · 无扫描 · decide 响应 `resume` 块字面不变 · 既有 decide 测试原样绿；`LG_RAG_DELEGATION_TOKEN_MODE=off` 时自动 resume 面零触达（无新台账 · 无后台任务行为差） |
| **台账三件套（记动作不记内容）** | `hitl_auto_resume_triggered`（decide 成功分支派发）· `hitl_auto_resume_claimed`（行锁认领成功）· `hitl_auto_resume_compensated`（补偿扫描补触发）；只记 request_id/run_id/resume_mode/decision_by/TTL 余量，**不记参数原值**；`resume_mode` 覆盖记录入台账（FP-10） |
| **T1 语义存续** | D1 消费门/D2 unlock 回填一行不改（本 task 在其上叠加）；deny 判序/Policy 写闸/gateway 闸链 diff 空 |

---

## 范围

- [ ] **F1 · 配置面**：`OPS_HITL_AUTO_RESUME` env 解析（manual 默认 · 非法回退）+ `_DecidePayload` 增 `resume_mode: str = "inherit"` + 端点内白名单 400 校验（R2-N1）+ 有效模式求解助手
- [ ] **F2 · 触发器**：`decide_request` 成功分支派发进程内 asyncio 任务（R2-N2 挂点 · approved ∧ auto 才派发 · 派发/执行失败只落台账不改 decide 结果 · 响应 `resume` 块 auto 注明/manual 字面零 diff）
- [ ] **F3 · 恢复段抽取复用**：`resume_request` 恢复段（sink→resume_hitl_run→turns）抽取为可复用助手，手动端点与自动触发**同源调用**（行为 diff 空 · 禁 HTTP 自调）
- [ ] **F4 · 行锁认领**：`DbHitlStore` 新增 `FOR UPDATE SKIP LOCKED` 认领方法（既有方法 diff 空 · 零新列零迁移）
- [ ] **F5 · 补偿扫描**：lifespan 挂启动时扫 + 周期任务（周期 env + shutdown cancel）；「已批准未恢复」四条件判定（含 run 终态只读查询新增 · 30 裁定留痕）
- [ ] **F6 · 台账三件套**：triggered/claimed/compensated + resume_mode 覆盖记录
- [ ] **F7 · 测试**：验收 TB1–TB8 逐条断言化（含行锁并发 Db 组与 B1 旧测全绿亲跑）
- [ ] **F8 · 图谱同步**：`docs/_tech_graph/l1/01_modules.md` hitl 行（decide 可选键 + 触发器/认领/补偿扫描 + main.py lifespan 挂点说明）与 lg_rag 行（auto 恢复同源说明）在册备注回写（G-L1 · HG-GRAPH-MODULES 随 30 回写由 00 代录）

### 非范围

- ❌ T1 面（D1 消费门/D2 unlock 回填）任何改动——本 task 只叠加；若 30 实证 T1 语义有缺口 → GATE_STOP 回 10，不顺手改
- ❌ T3 strategy env 口
- ❌ `store.py` 既有四方法（acreate/aget/alist/adecide）与 `_DECIDE` SQL 任何改动（diff 空钉死）；resume 状态机/interrupt 机制语义
- ❌ **OA `callback` 签名面挂触发器**（本波不做 · 签名面零 diff · 若维护者要 OA 面 auto 另立 task）
- ❌ MQ/外部调度器/独立轮询工人引入（终局「不需要 MQ」决议 · Q6 双弃在案）
- ❌ UI/前端/SSE 事件类型零新增；新表/新列（认领只读+行锁 · 零 alembic）
- ❌ 自动 resume 的 LLM 结果质量兜底（auto 恢复后 replan 质量属图既有语义 · 本波只保证机制可达）
- ❌ 跨副本触发去重的进程内存缓存（行锁认领即唯一真源 · 无状态恢复纪律）

---

## failure_paths

| # | 触发条件 | 系统行为 | 可重试 | 用户可见 |
|---|----------|----------|--------|----------|
| — | HG-AUDIT-R1 / HG-GRAPH-MODULES pending 即 30；**T1 未 merge 即 30** | **拒开工**（GATE_VERIFY 拦 · T1 依赖见依赖表 · A9 前提不成立） | 是 | 是 |
| FP-8 | 自动 resume 重复触发（decide 重入/多副本并发/触发与扫描同时命中） | PG 行锁认领防重（`FOR UPDATE SKIP LOCKED` · 认领窗口内再查判定）+ resume 状态机守卫幂等（非 pending/unlocked 重入无副作用）· **并发双触发仅一执行断言**（Db 组）；重复 decide 409 原样绿 | 是 | 否 |
| FP-9 | 触发进程崩溃/重启致自动 resume 丢失 | 补偿扫描（启动时+定时）兜底认领补触发；触发器不载状态（无状态恢复纪律）· 断言「重启后已批准未恢复单据被补触发」 | 是 | 否 |
| FP-10 | `resume_mode` 覆盖键滥用/未知值；非法全局 env | 键白名单 + 未知值 **400**（R2-N1 · str+手工校验 · 禁 Literal 变 422）；载荷缺键=inherit；非法全局 env 回退 manual；覆盖记录入台账（decision_by + resume_mode） | 是 | 是（400 detail） |
| FP-11 | 自动 resume 后仍被拦（单据过期/键不匹配） | 单次 decide 最多触发一次；回挂起态等人 · **不循环自动触发**（扫描判定第四条件：同 run 有未决 pending → 跳过）；台账留痕 | 是 | 是（再次 hitl.waiting） |
| 实操-A | `resume_mode` 用 `Literal`/`Enum` 声明 → 未知值变 **422** 而非 SPEC 钉的 400 | R2-N1 形态钉 + TB2 断言（未知值响应 status==400）· 20/40 复核载荷模型字段类型 | 是 | 否 |
| 实操-B | 触发器误挂 `store.adecide` 内（图方便） | 违 SPEC A7「store diff 空」钉 → 20/40 git diff 机械可查；挂点只许 router decide 成功分支 | 是 | 否 |
| 实操-C | InMemory store 做行锁断言（假绿） | InMemory 无锁语义 → 行锁并发断言仅 Db 组（真 PG fixture）；InMemory 只承载状态机幂等断言；验收 TB2 分组明示 | 是 | 否 |
| 实操-D | lifespan 周期任务 shutdown 未 cancel / manual 下误建任务 | manual 默认下扫描任务**零创建**（TestClient 8 文件 lifespan 面零 diff · B1 亲跑）；auto 下 shutdown cancel + 任务句柄模块级管理；泄漏表现=测试进程悬挂/警告 | 是 | 否 |
| 实操-E | 「run 未终态」判定无既有谓词（event_store 只读面无终态查询） | 30 须新增只读查询（事件表 done 帧或等价真源）并在 30 invoke 留裁定（真源选择 + SQL 形态）；禁读进程内存态 · 禁以 checkpoint 存在性近似终态 | 是 | 否 |
| 实操-F | 派发后台任务后 decide 响应才返回 → 客户端时序误判；或派发异常使 decide 5xx | `adecide` 成功即 200 语义成立在先；派发 try/except 只落台账；响应 `resume` 块 manual 字面零 diff / auto 注明已触发 | 是 | 否 |
| 实操-G | `npx spec-wave task lint` / `lint-wiki-delta` 红 | 30 返工修结构 | 是 | 否 |

---

## B1 · 旧测影响面（10 已实扫落盘 · 20-audit 核查清单 · 30 亲跑义务）

| 文件 | 断言面 | 预期 |
|------|--------|------|
| `tests/test_hitl_pending_decide.py` | decide 20 用例（409/404/422/归属过滤/审计） | **原样绿**（载荷增可选键 · 缺键=inherit · manual 默认零 diff）；新增用例独立命名（resume_mode 400/inherit/manual/immediate 面） |
| `tests/test_hitl_resume.py` | resume 19 用例（图替身/真 PG 重启链/ResumeError→HTTP 映射） | 原样绿（恢复段抽取行为 diff 空）；真 PG fixture 为行锁并发断言基建复用面 |
| `tests/test_hitl_resume_events.py` | 恢复段事件落盘/replay cursor | 原样绿（sink 复用同源） |
| `tests/test_hitl.py` / `tests/test_lg_rag_sse_hitl.py` | HITL 路由/SSE 挂起帧面 | 原样绿 |
| `tests/conftest.py` + TestClient 8 文件（`test_chat_ws.py`/`test_chat_router.py`/`test_admin_capability_observability.py` 等） | app lifespan 启动面 | **manual 默认下扫描任务零创建 · 全绿零新增红**（实操-D）；auto 形态测试用例自带 env monkeypatch + store 显式装配隔离 |
| `tests/test_capability_delegation.py` / `test_lg_rag_delegation_wiring.py` | delegation 判定/接线下发面 | 原样绿（T1 面零改） |
| `tests/test_capability_domain_allowlist.py:102-112` | deny 判序钉死 | 原样绿（反回归存续） |

---

## 验收标准

- [ ] 人工闸：HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 全 approved **且 T1 已 merge 进 master** 后方可勾选下列码项
- [ ] **TB1（auto 全链 · SPEC A9 · handoff 验收令）**：`OPS_HITL_AUTO_RESUME=auto`（或单据级 `resume_mode=immediate`）下，plans 含写 tool 的 run → hitl.waiting → pending 可见 → decide(approved) → **无需手动 resume** → 自动恢复 → 终态 `done{completed}`：pytest 集成断言（触发 `hitl_auto_resume_triggered` 台账 + 消费放行 + 终态）；live HTTP/SSE 实录留 40 复跑
- [ ] **TB2（无状态恢复钉死组 · SPEC A10）**：① 恢复路径（手动/自动/补偿扫描）只读事件表+DB——grep/审查断言无进程内存挂起态载体（触发器不载状态）② 补偿扫描幂等断言（重复扫描不重入非 pending 态）③ **行锁认领断言**（Db 组 · 双连接并发认领仅一成功 · InMemory 仅状态机幂等断言 · 禁假断言）④ `resume_mode` 未知值 **400** 断言（非 422 · R2-N1）⑤ 非法全局 env 回退 manual 断言
- [ ] **TB3（防重 · SPEC FP-8）**：并发双 decide（重复 409 原样绿）+ 触发与补偿扫描并发命中同单 → 仅一执行（台账 claimed 计数断言）
- [ ] **TB4（崩溃兜底 · SPEC FP-9）**：模拟 decide 后未派发（或派发任务丢弃）→ 补偿扫描补触发断言（`hitl_auto_resume_compensated` 台账）；进程重启后「已批准未恢复」单据被补触发（真 PG 重启链 fixture 形态承 `test_hitl_resume.py`）
- [ ] **TB5（不循环 · SPEC FP-11）**：auto resume 后仍被拦（构造键不匹配/过期场景）→ 回挂起 + 新 pending 可见 + **无第二次自动触发**（台账 triggered 计数==1 断言）；扫描跳过同 run 有未决 pending 形态断言
- [ ] **TB6（manual/off 零 diff · SPEC A6 本 task 面）**：`OPS_HITL_AUTO_RESUME` 缺省/非法 → decide 响应 `resume` 块字面与 master 一致 · 无后台任务创建（spy 断言）· 无扫描任务（lifespan 面）· B1 全文件原样绿；delegation off 下自动 resume 面零触达
- [ ] **TB7（反回归存续 · SPEC A5/A7 本 task 面）**：`store.py` `adecide`/`_DECIDE` git diff 为空；`registry.py::_match_filter` 与 `policy.py` 闸序段 diff 空；`resume_request` 手动路径行为 diff 空（抽取复用前后对拍）；`test_allow_tags_does_not_waive_deny_write` 原样绿
- [ ] **TB8（工程面 · SPEC A8 本 task 面）**：`pytest tests` 全绿；`ruff check app tests` 触及路径零新增；`./scripts/graph-compile.sh` EXIT=0；图谱 hitl/lg_rag 两行备注回写 + HG-GRAPH-MODULES 00 代录行
- [ ] B1 旧测清单全绿亲跑记录（命令 + 结果）落 40 invoke
- [ ] `npx spec-wave task lint --file docs/tasks/active/task_hitl_approval_consumption_auto_resume.md` PASS；`npx --yes spec-wave@3.0.1 task lint-wiki-delta --target .` PASS

---

## 依赖

| 依赖 | 说明 |
|------|------|
| **T1（硬依赖 · 串行合并）** | `docs/tasks/active/task_hitl_approval_consumption_loop.md` **merge 进 master 后方可 30**——消费门是 auto resume 全链 A9 前提（无消费→恢复后仍再拦 · 无 D2→resume 409）；本 task 分支自 T1 merge 后的 master 切出 |
| SPEC（依据 · signed） | `docs/spec/hitl-approval-consumption/SPEC-hitl-approval-consumption_v1.md`（**当前在 `spec/hitl-approval-consumption` 分支 · 随首个实现 PR 一并带入 master**）——D5 + Q6/Q7 + FP-8~FP-11 + A9/A10 + 设计纪律 6（无状态恢复） |
| 上游路线 | `docs/guides/DESIGN_agent_contribution_endgame_v0_zh.md` §4 :82-83（自动/手动可配置 + 无状态恢复纪律原裁定） |
| handoff 令 | `docs/harness/invokes/by-task/_prompts/PROMPT_00_hitl-consumption-loop-handoff_20261009.md`（「A1 第四段补全实录」验收令=TB1 live 段） |
| 改动面锚点 | `hitl/router.py:112-116,175-232,319-430` · `hitl/resume.py:285` · `hitl/store.py:127-228` · `hitl/persistence.py:61-77` · `main.py:12-16` · `lg_rag/event_store.py:26-142` |
| 并发/多副本先例 | `docs/tasks/done/task_multi_replica_verify.md`（双进程实测形态）· `tests/test_hitl_resume.py` 真 PG fixture |
| 编码规范 | `docs/standards/CODING_BACKEND_L2_v1_zh.md`（P-13 异步一致性 · P-14 零迁移纪律 · P-15 LangGraph 节点约束） |
| 上游任务范式 | `docs/tasks/done/task_testing_write_capability.md`（结构范式 · 40 核验偏差登记=本波立项源） |

---

## 给执行帽的必读列表

1. `AGENTS.md`（新会话启动纪律 + GATE_VERIFY · T1 merge 核验）· 2. 本 task（钉死契约 + B1 + 验收标准 · R2-N1/N2/N3 三钉）· 3. SPEC v1 §1 设计纪律 6 + §2 D5 + §4 Q6/Q7 + §5 FP-8~FP-11 + §6 A9/A10（分支路径同 T1）· 4. `docs/guides/DESIGN_agent_contribution_endgame_v0_zh.md` §4 :81-83 · 5. `docs/standards/CODING_BACKEND_L2_v1_zh.md`（P-13/P-14/P-15）· 6. `hitl/router.py` 全文 + `hitl/resume.py` 全文（恢复段抽取面）· 7. `hitl/store.py` 全文（新增认领方法 · 既有 diff 空）· 8. `main.py:1-30`（lifespan 挂点）· 9. `tests/test_hitl_resume.py`（真 PG fixture 形态）· 10. `docs/tasks/done/task_hitl_approval_consumption_loop.md`（T1 交付形态 · CLOSE 后于 done/）· 11. `docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`

---

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|----|------|------------|----------------------|----------------|
| R0 | 问题=SPEC v1 既定 D5 承接（第四立案 · handoff 验收令 · 终局 §4 两裁定）；需求边界无歧义 | no | — | none |
| R1 | 范围=配置面+触发器+恢复段同源+行锁认领+补偿扫描+台账+测试+图谱；T1 面/store 既有方法/OA 触发/MQ/UI 全非范围；T1 merge 为 30 前置 | no | — | 无 |
| R2 | SPEC Q6（进程内后台任务 · S2 新部署单元/S3 丢通知面双弃）/Q7（全局+单据双级 · S2 一刀切/S3 破零 diff 双弃）裁定存续；新增三钉=**R2-N1 400 形态**（str+手工白名单 · 否 Literal→422）· **R2-N2 挂点**（router decide 成功分支 · 否 store 层违 A7 · 否 OA callback）· **R2-N3 行锁**（Db 新增 FOR UPDATE SKIP LOCKED 方法 · InMemory 禁假断言） | no | — | run 终态判定真源无既有谓词 · 30 裁定留 20/40 复核（实操-E） |
| R3 | 交叉验证：全仓无 FOR UPDATE 先例实证 · TestClient 8 文件 lifespan 面实证（manual 零创建钉）· `_DecidePayload` Literal/422 形态实证 · event_store 只读面无终态谓词实证 · 「已批准未恢复」四条件操作定义（第四条件=防 FP-11 循环的扫描面配套） | no | — | 补偿扫描周期默认值 60s 属建议值 · 30 可在域内调整并留痕 |
| R4 | failure_paths 推演 11 条（FP-8~FP-11 + 实操 A–G · 含 422 漂移/挂点错位/InMemory 假断言/任务泄漏/终态真源/响应时序） | no | — | 无 |
| R5 | 验收口径机断化收敛（TB1–TB8 映射 SPEC A9/A10 + 存续面 · 台账计数/status 码/diff 空/EXIT=0 均可机断） | yes | 三钉各有实证排除岔路 · 锚点逐行实读闭环 · T1 依赖边界清晰 | 见 R2/R3 |

**actual_last_round**：R5 · **early_stop**：yes · **residual_risks**：见 R2/R3

### R0 · 问题框定

SPEC v1 D5 已签收（Q6 触发器三选一裁定=进程内后台任务+行锁+补偿扫描 · Q7 配置面=全局 env+单据级双级）。实读：SPEC v1 全文 + 终局文档 §4 :81-83 + handoff PROMPT（「A1 第四段补全实录」验收令）+ 全部代码锚点（`decide_request` 成功分支形态/`_DecidePayload` Literal 形态/`resume_request` 恢复段/lifespan 现状/store 无行锁先例/event_store 无终态谓词 · master `4d905e0` 逐行复核）。T1 为硬前置：A9 全链的「自动恢复可达 done」以消费放行+unlock 回填为前提，串行合并是机制依赖。

### R1 · 范围钉死

改动面八件（F1–F8）：配置面（env+载荷键+白名单）· 触发器派发 · 恢复段抽取复用 · 行锁认领（Db 新增方法）· 补偿扫描（lifespan）· 台账三件套 · 测试 · 图谱两行备注。划出：T1 面零改（发现缺口 GATE_STOP 回 10 不顺手改）· store 既有四方法与 `_DECIDE` diff 空 · OA callback 不挂触发器 · MQ/外部调度器（终局双弃在案）· UI/SSE · LLM 质量兜底 · 新表新列 · 进程内存去重缓存（行锁即真源）。

### R2 · 方案裁定

**SPEC 裁定存续（不重开）**：Q6=S1 进程内后台任务+PG 行锁认领+补偿扫描（S2 独立轮询工人=P1 零新增服务纪律冲突 · S3 LISTEN-NOTIFY=连接生命周期复杂+丢通知面大+悖「不需要 MQ」精神 · 双弃有机制性理由）；Q7=S1 全局 env+decide 载荷可选键双级（S2 仅全局违终局「可按审批单覆盖」 · S3 仅单据破既有调用零 diff · 双弃）。

**裁定一（R2-N1）· `resume_mode` 未知值 400 的实现路径钉**。实证：`_DecidePayload.decision` 用 `Literal`（router.py:115），Pydantic 校验失败=**422**（docstring 明示）；SPEC FP-10/A10 钉 `resume_mode` 未知值=**400**。岔路：① `Literal["inherit","immediate","manual"]` → 天然 422 · 违 SPEC **否**；② `str` + 端点手工白名单 → 精确 400 · 与 decision 字段形成「422（Pydantic 层 · 既有）/400（业务白名单 · 本键）」双形态——docstring 注明差异防误读 **选定**；③ 自定义 Pydantic validator 抛 `HTTPException` → 校验层抛 HTTP 异常绕 FastAPI 语义 · 晦涩 **否**。

**裁定二（R2-N2）· 触发器挂点=router `decide_request` 成功分支**。岔路：① store `adecide` 内挂 → 违 SPEC A7「store diff 空」+ store 层拿不到 user/resume_mode 台账面 **否**；② router decide 成功分支（`adecide` 返回非 None 后）→ 载荷键/user/审计面齐备 · store 零 diff **选定**；③ OA `callback` 同挂 → 签名面载荷无 `resume_mode` · 行为零 diff 约束下本波不挂（非范围 · 维护者要 OA 面 auto 另立 task）**否（本波）**。

**裁定三（R2-N3）· 行锁锚点与并发断言基建**。实证：全仓无 `FOR UPDATE`/`SKIP LOCKED` 先例（grep 空）→ `DbHitlStore` 新增认领方法（既有四方法 diff 空）；认领窗口内再查判定（防认领后条件已变）。断言基建分组钉：Db 组（真 PG fixture 承 `test_hitl_resume.py` 形态）做并发双认领仅一成功；InMemory 无锁语义只做状态机幂等断言——**禁 InMemory 行锁假断言**（分组边界写进验收 TB2③）。多副本语义承 task_multi_replica_verify 先例（行锁即跨副本唯一真源 · 无进程内存去重）。

**裁定四 · 「已批准未恢复」四条件操作定义**。approved ∧ 未过 TTL ∧ run 无终态 ∧ 同 run 无未决 pending——第四条件是 FP-11 不循环的扫描面配套（auto resume 后仍被拦必产新 pending → 扫描跳过）；「run 无终态」无既有谓词（event_store 只读面实证）→ 新增只读查询为 F5 范围内 · 30 留裁定（实操-E）。

### R3 · 交叉验证

- **挂点形态实证**：`decide_request` :201-216 成功分支后响应在 :223-232 组装——派发点夹在两者间不阻响应；`resume` 块 manual 字面零 diff 可由响应快照对拍机断。
- **lifespan 面实证**：`main.py:12-16` 现仅 `log_tracing_startup()`+yield；TestClient 8 文件经 conftest 触发 lifespan——manual 默认下扫描任务零创建是全局旧测不炸的硬条件（实操-D 钉死）。
- **恢复段同源可行**：`resume_request` :393-439 恢复段依赖仅 row/thread_id/sink——抽取助手后手动端点与自动触发同源调用，行为对拍（TB7）可机断；`_open_event_sink` 归属失败返 None+error 日志的既有语义自动路径原样继承。
- **行锁 SQL 形态**：`ops_hitl_requests` 既有表（db 行图谱 · migration `20260920_hitl_requests`）· `SELECT … FOR UPDATE SKIP LOCKED` 对单行 UPDATE 认领无迁移义务；`decided_at` 为 timestamptz（`_DECIDE` now()）· TTL 比较在 SQL 层或归一后层皆可 · 30 定并留痕。
- **T1 边界复核**：T1 交付面（消费门/unlock 回填/台账 `delegation_approval_consumed`）与本 task 触发面唯一交点=「恢复后重下发的签发判定」——该判定语义归 T1 · 本 task 零改（TB1 仅做全链断言）。

### R4 · failure_paths 推演

SPEC FP-8~FP-11 逐条落机制+断言：重复触发=行锁+状态机双闸（FP-8 · TB3）· 崩溃丢失=补偿扫描（FP-9 · TB4）· 覆盖键滥用=白名单 400+缺键 inherit+非法 env 回退（FP-10 · TB2④⑤）· auto 后仍拦=单次触发+扫描第四条件（FP-11 · TB5）。实操坑七条来自锚点实读：422 形态漂移（A · R2-N1）、挂点错位违 A7（B · diff 机械可查）、InMemory 假断言（C · 分组钉）、lifespan 任务泄漏/manual 误建（D · B1 面）、run 终态真源缺失（E · 30 裁定留痕）、派发阻塞 decide 响应（F · 语义在先钉）、lint 红（G）。

### R5 · 验收口径机断化收敛

TB1–TB8 逐条映射 SPEC A 编号与 FP 断言：台账计数（triggered==1/claimed==1）· HTTP status（400 非 422 · 409 原样）· diff 空（store/registry/policy/手动 resume 对拍）· spy 零调用 · EXIT=0。live 全链（TB1 末段）留 40 复跑（handoff 验收令「A1 第四段补全实录」）。无残留方案分叉（SPEC 裁定存续 + 四新裁定各有实证排除岔路）→ early_stop。

---

### 自检结论（执行者）

**40 核验结论（2026-10-10 · invoke_20261010_40）**：**PASS（带偏差登记 · 可进 PR 队列）**——独立复跑不采信自报：

- **TB1**：pytest 机制段绿 + **live 段复跑达成机制全链**——六 env 组 + `OPS_HITL_AUTO_RESUME=auto` 起服务 :8030，run `dbc0fc74…`：hitl.waiting（unlock=sid 回填）→ pending 可见 → decide(approved) 200 persisted（auto 形态 resume 块 `{required:false, auto_triggered:true}` live 实证）→ **不调 resume** → 台账 `triggered`→`claimed` → 同源恢复执行（解锁 :1 · hitl.resumed 帧 · 恢复完成 replay=:13）；**末段 `done{completed}` 未达成，如实登记**——命中 T1 40 已登记的 replan 重盖章偏差（sid :1→:2 · 无 `delegation_approval_consumed` 台账 · 再拦新 pending :2）。**非 T2 回归 · T2 机制面（decide→自动派发→同源恢复→图继续）live 全达**。
- **TB2–TB7**：39 枚新测抽跑全绿（Db 组 4 枚真 PG 非 skip · SKIP LOCKED 并发断言亲读为真锁语义 · InMemory 组无行锁假断言）；store.py 纯新增 68 行（删除行=0）· registry/policy/nodes/delegation diff 空 · 恢复段抽取同源（`await resume_hitl_run(` 调用点==1 机断钉）。
- **TB8**：全量 1748 passed · 1 skipped · **4 failed=基线环境性**（capability_lookups×3+lg_rag_multi×1 · `delegation no_token` · 与 T1 40 钉案同签名 · 失败文件均非本分支触及 · 零新增红）；ruff 触及六路径零新增（base 3f6a630 影子对拍同绿）；graph-compile EXIT=0（freeze/日期噪音已 checkout 还原）；verify EXIT=0 · task lint PASS · lint-wiki-delta PASS。
- **台账三动作 live 全实证**：triggered/claimed（decide 链）+ compensated（播种「崩溃遗留」approved 单据 · 启动扫描补触发 · ttl_remaining 逐轮递减实证）。
- **40 附带观察（登记上抛 T1/SPEC v2 视野 · 非 T2 归因）**：resume 时 `observe_node` 重放致 `_persist_hitl`（nodes.py:1727 · 落库先于挂起）在 `interrupt()` 返回前为已批准 sid 重建**孤儿 pending**（live 实证 `hitl_5cefb116…:1`）——LangGraph 节点重放语义使然，手动/自动路径同源共有，nodes.py 本 task diff 空。
- 基点注记：本地 master 实指 `94cb1c6`（含 PR #217 T1 close chore），本分支自 `3f6a630` 切出——`git diff master` 混含 T1 归档面，对拍基线以 merge-base `3f6a630` 为准（40 invoke 有实证）。
- HG-GRAPH-MODULES 在册行（T2 行 · 00 代录措辞承 T1 先例形态）实证在案 → 留 00 ratify。


---

## 修订

| 日期 | 说明 |
|------|------|
| 2026-10-10 | 10-task 落稿（骨架先行增量落盘 · SPEC v1 signed 承接 · R0–R5 · HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 全 pending → 30 拒开工） |
