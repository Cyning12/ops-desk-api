# Task：阶段 W 联调缺陷修复 II（HITL resume 链租户上下文还原 + delegation 单据租户戳）

> **状态**：`active`（2026-11-03 · 四闸全 approved · 设计三决策已裁决（A+B 组合 / 守卫扩列 / 历史 '' 从严 · PR #312 review 维护者签认）· **GO 30**）
> **类型**：fix / 安全语义补全（跨租户写守卫闭环 · 审计真值）
> **上游**：workspace `docs/harness/invokes/by-task/stage-w-e2e-join-acceptance/invoke_20261102_10_c8_evidence_archive.md`（§2 F3 / N-R2-1 / 守卫真空 · §C6 实证）· workspace 同目录 `invoke_20261103_10_final_acceptance.md` §2（2026-11-03 收尾棒）· workspace backlog `docs/tasks/backlog/backlog_20261030_post_stage_w.md` B2（2026-11-03 标注「联调已坐实 · 待立 fix task」）· 维护者 issue [#311](https://github.com/Cyning12/ops-desk-api/issues/311) 令起草 · PR [#312](https://github.com/Cyning12/ops-desk-api/pull/312)（MERGED 2026-11-03 · squash `04245ef`）
> **分支**：30 棒走部署绑定分支 `agent/hitl-tenant-fix-task-955c1cd011b6`（base：`master` · 名义分支 `task/api-w-hitl-tenant-fix` 让位绑定规则）
> **10 注**：2026-11-03 · 起草 PR #312 合入 · 20-R1 审查 PASS（审查文址A `docs/harness/reviews/task_api_w_hitl_tenant_fix_audit_R1_20261103.md` · 过程档 `docs/harness/invokes/by-task/api-w-hitl-tenant-fix/invoke_20261103_20_r1_audit.md`）· 维护者三闸签认（issue #311 评论 + auth311）+ HG-AUDIT-R1 随审查文落档签 · **30 改码授权生效**（维护者 auth311 六要求）

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `api-w-hitl-tenant-fix` |
| **git_branch** | `agent/hitl-tenant-fix-task-955c1cd011b6`（30 棒 · 部署绑定分支；名义 `task/api-w-hitl-tenant-fix`） |
| **implement_repo** | `ops-desk-api`（唯一） |
| **test_strategy** | `required` |
| **test_strategy_note** | api 侧 pytest **红测先行**：① B 租户负样本——B 身份 approve+resume 后消费日志 `capability_write_approval_consumed.tenant_id` 与 `ops_capability_receipts.tenant_id` 必须 = B（`ops-desk-pilot-b`），回落 A 即红（钉死 N-R2-1 不复发）② delegation 建单负样本——`_persist_hitl` 建 delegation 类单据 `tenant_id` 非空且 = 当前租户（治 `''` 真空 · 联调实扫 40 行）③ 跨租户消费守卫负样本——他租户单据不被本租户消费（fail-closed）④ 同租户正样本——A 租户全链（拦单→批准→resume→消费→回执）行为零变化、resume 正样本不误拒 ⑤ 码面锚点 grep（`resume` 执行体 tenant 还原接线存在性 · 单一真源不另造第二处回落） |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1`（预估薄增量 · 以 30 实扫为准） |
| **graph_delta** | api `docs/_tech_graph/l1/01_modules.md`（hitl 模块条目一句备注「resume 链租户还原 · delegation 单据租户戳」· lg_rag/multi 模块条目一句备注「消费守卫租户口径按 HG-W-TENANT-DESIGN」）· 不新增一级模块 |
| **graph_delta_note** | 模块边界不变；仅模块内守卫/落库字段语义增量 → G-L1 同步 |
| **wiki_delta** | `n/a`（以 30 实扫为准） |
| **wiki_delta_note** | 契约真值在 workspace contracts；本 task 不动 freeze 文件本体 |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,20,30,40` |
| **invoke_retention_profile** | `default` |
| **experience_capture** | `recommended` |
| **kpi_aggregator** | `CLOSE` |
| **orchestration** | 10 落稿（PR #312 合入 `04245ef`）→ 20-R1 审查 PASS（invoke_20261103_20_r1_audit）→ 维护者签 `HG-TASK-DRAFT`/`HG-GRAPH-MODULES`/`HG-W-TENANT-DESIGN`（issue #311 评论 + PR #312 review · auth311 代录）+ `HG-AUDIT-R1` 随审查文落档签 → **GO 30**（部署绑定分支 · 红测先行 · auth311 六要求）→ 40 → 联调 C6 复测回接（workspace `task_stage_w_e2e_join_acceptance` N-R2-1/F3 复测）→ CLOSE |
| **freeze_id** | `lg-rag-sse-v1`（**零改红线**）· `hitl-browser-decide-v1`（**零改红线** · 文件本体不动 · 本 task 无增补提案） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | approved | 20-R1, 30 | 2026-11-03 维护者签（issue #311 评论 + PR #312 review · 起草质量 20-R1 已过 · 00 代录） |
| HG-AUDIT-R1 | approved | **30** | 2026-11-03 维护者签（auth311：20-R1 审查文址A `docs/harness/reviews/task_api_w_hitl_tenant_fix_audit_R1_20261103.md` 落档即签 · 过程档 invokes/by-task/api-w-hitl-tenant-fix/invoke_20261103_20_r1_audit.md · 00 代录） |
| HG-GRAPH-MODULES | approved | **30**（条件触发） | 2026-11-03 维护者签（auth311：G-L1 薄备注 · 无新增一级模块 · 00 代录） |
| **HG-W-TENANT-DESIGN** | approved | **30** | 2026-11-03 维护者签（PR #312 review 三决策点裁决 · auth311 代录）：① resume 链 tenant 来源 = **A+B 组合**——单据 `tenant_id` 为唯一真源做快照还原（对齐守卫 `row.tenant_id` 语义）；手动入口 session 租户存在且 ≠ 单据租户 → 403（对齐 `lg_rag/router.py:376-384` 先例）；auto-scan 无请求上下文 → 纯 A；fail-closed：单据 tenant 为空 → 拒 resume ② delegation 消费守卫 = **扩列纳入租户校验**（T-fix-2 打戳后守卫查非空成立）· 不选豁免文档化 ③ 历史 `tenant_id=''` 40 行 = **默认从严**——一律 fail-closed 拒 resume · 不回填；后续真实 resume 诉求走单独授权的数据修复 |

---

## 背景与目标

2026-11-02 阶段 W 端到端联调（workspace `task_stage_w_e2e_join_acceptance` · C6 跨租户负样本）坐实两个同族缺陷，2026-11-03 终验收尾 invoke §2 与 backlog B2 复确认待立 fix task：

- **缺陷 1 · N-R2-1（defect · 高优先 · 审计失真）**：HITL resume 链零租户引用——`app/ops/hitl/resume.py` 全文零 tenant 引用；resume 执行体（`hitl/router.py:447 _execute_decided_resume` → `resume_hitl_run`）在 HTTP 手动路径（`router.py:619-620 asyncio.create_task(_run_resume_in_background)`）与自动扫描路径（`auto_resume.py:225-227` 同源执行体）均**无人 `set_current_tenant`**——对照：首次 run 入口有（`lg_rag/run_worker.py:120` · `lg_rag/router.py:398`），resume 没有。消费环 `current_tenant_or_default()` 回落默认租户 A（`tenant_context.py:24-26`）。**实证**：B 租户（`ops-desk-pilot-b`）拦单 `hitl_b4c35664bc10412fa561` 经 B 身份真人 approve+续跑后，被 **A 上下文消费**——消费日志 `capability_write_approval_consumed {"tenant_id": "ops-desk-pilot"}`（应 `-b`），回执 `d6bd262904544232` tenant 错标 `ops-desk-pilot`（invoke §C6）。
- **缺陷 2 · F3（gap）+ 守卫真空**：delegation 类审批单租户戳真空——`_persist_hitl`（`lg_rag/multi/nodes.py:2144` 起）tenant 取 `term.get("tenant_id")`（`:2221`），而 delegation 签发路径（`_delegation_issue_block_reason :554` 拦截原因 → terminal term）**不打租户戳**（对照：阶段 W capability_write 闸路径已 stamping · `:1881-1925` `blocked["tenant_id"] = current_tenant_or_default()`）→ DB `tenant_id=''`（联调实扫 `ops_hitl_requests` `''`=40 行）。连带**守卫真空**：消费守卫 `nodes.py:499-504` 仅对 `blocked_by==capability_write*` 类查租户（`:502-503`），**delegation 类跳过租户守卫**（`_WRITE_CONSUMABLE_BLOCKED_BY` `:318-320` 虽含两类，但守卫 tenant 检查只在 capability_write 分支内）→ 跨租户消费 fail-closed 在 delegation 路径无法触发（invoke §2「守卫真空」行）。

两缺陷同族（租户上下文在 resume/建单链断裂）且相互咬合：**若设计选「decide 时快照」（选项 A），delegation 单 `tenant_id=''` 不修则快照无真值可取**——故合并一题同修（invoke §7 #1/#2 建议「可与 N-R2-1 合并设计」· 守卫真空「并入上述 fix task 设计」）。

本 task 把跨租户写守卫在 resume/ delegation 链路由「形同虚设」打回「真实可达」，并把审计真值（消费日志/回执 tenant）恢复到运行上下文真值。

---

## 现状锚点（只读 · 30 必读 · 10 已扫）

| 主题 | 路径 · 锚点 | 现状 |
|------|-------------|------|
| resume 执行体 | `app/ops/hitl/router.py:447 _execute_decided_resume`（→ `resume_hitl_run :462`）· `router.py:514-521 _run_resume_in_background` · `router.py:619-620 create_task` | 手动 resume 异步执行体全文零 tenant 引用 |
| 自动扫描同体 | `app/ops/hitl/auto_resume.py:225-227`（惰性 import `_execute_decided_resume` · 禁 HTTP 自调先例） | 同源缺口：lifespan 扫描上下文同样无租户 |
| 消费环回落 | `app/ops/tenant_context.py:24-26`（`current_tenant_or_default()` → TENANT_A） | N-R2-1 回落点（唯一真源 · 30 不得另造第二处回落） |
| run 入口对照 | `app/ops/lg_rag/run_worker.py:120` · `app/ops/lg_rag/router.py:398,449`（set/reset 成对） | 首次 run 有 tenant · resume 无 —— 不对称本体 |
| 建单打戳 | `app/ops/lg_rag/multi/nodes.py:2144 _persist_hitl` · `:2221 "tenant_id": str(term.get("tenant_id") or "")` | delegation term 无 tenant 键 → `''` |
| 既有 stamping 先例 | `nodes.py:1881-1925`（capability_write 闸 `blocked["tenant_id"] = gate_tenant` · write_intent 随单落库） | delegation 路径对齐此先例 · 不另造形态 |
| 签发审批口径 | `nodes.py:554 _delegation_issue_block_reason` · `:1272` 调用点 | 拦截原因生成处 · 零 tenant 引用 |
| 消费守卫 | `nodes.py:499-504`（仅 capability_write 分支查租户 `:502-503`）· `nodes.py:318-320 _WRITE_CONSUMABLE_BLOCKED_BY`（含 delegation+capability_write） | delegation 类守卫真空现场 |
| 租户真源 | `app/ops/deps.py:43-45`（`request.state.ops_tenant_id = session.tenant_id or "ops-desk-pilot"`）· 头不一致 403 先例 `lg_rag/router.py:376-384` | 选项 B（请求重建）载体 · F1=C session 真源 |
| 联调实证 | workspace `invoke_20261102_10_c8_evidence_archive.md` §C6（单据 `hitl_b4c35664bc10412fa561` · 回执 `d6bd262904544232` 错标）· §2 F3 / N-R2-1 / 守卫真空 · §4 「tenant 上下文：resume 链丢失」行 | 双缺陷全锚 |

---

## 10 钉死契约（HG-W-TENANT-DESIGN 2026-11-03 签认升格 · 30 不得静默改义）

| 项 | 钉死（裁决值） |
|----|----------------|
| **resume tenant 来源（A+B 组合）** | 单据 `tenant_id` 为**唯一真源**——resume 执行体驱动图前按单据快照 `set_current_tenant` 还原（对齐守卫 `row.tenant_id` 语义）；手动入口 session 租户存在且 ≠ 单据 tenant → **403**（对齐 `lg_rag/router.py:376-384` 先例）；auto-scan 无请求上下文 → 纯 A（即仅快照还原）；**fail-closed：单据 tenant 为空 → 拒 resume** |
| **delegation 建单打戳** | `_persist_hitl` delegation 签发路径 tenant 取当前租户上下文（对齐 `:1881-1925` capability_write 既有 stamping 先例）；治 `''` 真空 · 新单不再产 `tenant_id=''` |
| **回执/日志真值** | 消费日志与 `ops_capability_receipts.tenant_id` 取运行上下文真值（快照还原后的 ContextVar）；**禁止回落默认 A 静默错标**（`d6bd262904544232` 场景不复发为硬验收） |
| **守卫口径（扩列）** | delegation 类**纳入** `_WRITE_CONSUMABLE_BLOCKED_BY` 租户校验（T-fix-2 打戳后守卫查非空成立 · `nodes.py:499-504` 扩至两类）；resume 链还原 tenant 后 W2 守卫在两类**真实可达**为硬验收 |
| **历史 40 行（从严）** | 历史 `tenant_id=''` 单一律 fail-closed 拒 resume · **不回填**；后续真实 resume 诉求走单独授权的数据修复 |
| **双 freeze 零改** | 不新增/不改/不删 SSE `event_type`（`lg-rag-sse-v1` 不破）；`hitl-browser-decide-v1` freeze 文件本体不动（本 task 无增补提案 · 若 30 实扫认为需增补另走契约闸） |
| **不误伤** | A 租户全链行为零变化（正样本回归）；同租户 resume 正样本不误拒；自动扫描路径与手动路径**同一** tenant 还原实现（禁第二份） |

---

## 范围（同 task 竖切 · 四闸齐后才 30）

- [ ] **T-fix-1 · N-R2-1 resume 链租户上下文还原**：resume 执行体（`_execute_decided_resume` 唯一执行体 · 手动/自动两入口同源受益）驱动图前按 HG-W-TENANT-DESIGN ①还原 `set_current_tenant`（reset 成对 · 对照 `run_worker.py:120/153` 形态）；消费日志/回执 tenant 错标修复（取运行上下文真值）
- [ ] **T-fix-2 · F3 delegation 单据租户戳**：`_persist_hitl` delegation 签发路径补租户打戳（对齐 capability_write 既有先例）；新单 `tenant_id` 非空且 = 当前租户（红测负样本钉死）
- [ ] **守卫真空收口（按 HG-W-TENANT-DESIGN ②）**：delegation 类消费守卫纳入租户检查 **或** 豁免理由显式文档化——二选一 · 维护者签后落地

### 非范围

- **其余联调发现**：F1/F6/F8/F10/F14/F15（web UX 族 · invoke §2/§2追加 · backlog B10/B11 建议合并 web UX task）· F5（环境噪音）· F7（supervisor 重规划轰炸环）· F9（孤儿单去重纳入已决态）——另行立项
- **W-fix-1/W-fix-2 已修项回归**（`task_api_w_join_gap_fix` · PR #307：TTL 过期出口 / 只读面租户谓词——本 task 不动）
- **改 SSE freeze**（`lg-rag-sse-v1` 事件表 / idle keepalive）
- **`hitl-browser-decide-v1` freeze 文件本体修改**（本 task 无增补提案 · 如需走契约闸另立）
- **历史 `tenant_id=''` 40 行数据回填**（处置口径属 HG-W-TENANT-DESIGN ③ · 回填动作未签不做）
- **web 仓改动**（本 task 纯 api）
- **联调 task CLOSE**（workspace `task_stage_w_e2e_join_acceptance` · 复测回接后由维护者拍板）
- 阶段 P 平台项

---

## failure_paths

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----------|----------|--------|----------|
| 四闸任一 pending 即 30 | **拒开工** | 是 | 是 |
| **SSE `event_type` 任一新增/改名/删改**（`lg-rag-sse-v1` 红线） | 20/40 审查拒收 · 退回 | 是 | 否 |
| **`hitl-browser-decide-v1` freeze 文件本体擅改**（未经契约闸） | 20/40 审查拒收 · 退回 | 是 | 否 |
| resume tenant 来源偏离 HG-W-TENANT-DESIGN ①钉死值（30 静默自选或第三方案） | 审查拒收 · 退回 | 是 | 否 |
| 消费日志/回执 tenant 回落默认 A（`d6bd262904544232` 错标复发） | 红测拦截（B 租户负样本）· 30 返修 | 是 | 否 |
| delegation 新单仍产 `tenant_id=''`（打戳遗漏路径） | 红测拦截 · 30 返修 | 是 | 否 |
| 守卫误拒同租户正样本 / 误放跨租户负样本 | 红测拦截 · 30 返修 | 是 | 否 |
| 手动/自动两 resume 入口 tenant 还原实现分叉（第二份实现/第二处回落） | 审查拒收（同源红线 · 对照 auto_resume.py 既有「同一条恢复路径」纪律） | 是 | 否 |
| **旧测 grep 影响面清单缺失**（编码旧行为的用例：resume 无 tenant 断言 / `tenant_id=''` fixture 断言等） | 40 拒收 · 禁止静默改测对齐 | 是 | 否 |
| 修复合入但未回接联调 C6 复测（B 身份拦单 approve+resume → 消费日志/回执 tenant=`ops-desk-pilot-b` 实证） | 联调挂账保持 · **拒 CLOSE** | 是（补复测） | 是 |

---

## 验收标准

- [ ] 人工闸：`HG-TASK-DRAFT` · `HG-AUDIT-R1` · `HG-GRAPH-MODULES` · `HG-W-TENANT-DESIGN` 均 approved 后方可勾选下列码项
- [ ] T-fix-1：B 身份拦单 approve+resume 后，消费日志 `capability_write_approval_consumed.tenant_id` 与回执 `ops_capability_receipts.tenant_id` = `ops-desk-pilot-b` 负样本测绿（红测先行）；A 身份全链正样本零变化测绿；手动/自动两入口同一还原实现（grep 实证）
- [ ] T-fix-1：tenant 还原 reset 成对（无泄漏 ContextVar · 对照 `run_worker.py:120/153`）；HG-W-TENANT-DESIGN ① fail-closed 语义落地（空 tenant / 头不一致拒）
- [ ] T-fix-2：delegation 类新单 `tenant_id` 非空且 = 当前租户负样本测绿（红测先行 · 对齐 `:1881-1925` 先例形态）；既有 capability_write 类打戳零变化回归
- [ ] 守卫：按 HG-W-TENANT-DESIGN ②落地后，跨租户消费 fail-closed 负样本（他租户单据不被消费）测绿；同租户消费正样本不误拒
- [ ] **回接条款**：修复合入后复测联调 C6 口径（workspace invoke §C6：B 租户发起写 → 拦单 tenant 非空 → B 身份 approve+resume → 消费/回执 tenant=`ops-desk-pilot-b` → 守卫真空不复现）；复测证据回填 workspace invoke 与 task 档
- [ ] `hitl-browser-decide-v1` 消费语义回归：decide 400/404/409/422 既有语义零变化（freeze 文件本体零 diff）
- [ ] SSE 事件表零 diff（`lg-rag-sse-v1` 不破 · 含 resume 段 `hitl.resumed`/`done` 帧语义零变化）
- [ ] `ruff` 触及路径绿；`pytest` 本波 + 既有 hitl/tenant/capability 回归绿
- [ ] **旧测 grep 影响面**（对照 `task_api_w_join_gap_fix` M3 口径）：30 交付前列出 `tests/` 中编码旧行为的用例清单（resume 无 tenant 即成功的断言 / `tenant_id=''` fixture 行 / 消费守卫仅 capability_write 类的断言等）——**逐条标注保留 / 修改 / 删除 + 理由**，随 PR 提交；禁止静默改测对齐
- [ ] `./scripts/graph-compile.sh` 绿（G-L1 薄备注同步）；不新增 G-L1 一级模块
- [ ] `npx spec-wave task lint --file docs/tasks/active/task_api_w_hitl_tenant_fix.md` PASS

---

## 依赖

| 依赖 | 说明 |
|------|------|
| 联调证据 | `../ops-desk-workspace/docs/harness/invokes/by-task/stage-w-e2e-join-acceptance/invoke_20261102_10_c8_evidence_archive.md`（§C6 实证 · §2 F3/N-R2-1/守卫真空 · §4 语义对照「tenant 上下文」行 · §7 #1/#2） |
| 联调收尾 | `../ops-desk-workspace/docs/harness/invokes/by-task/stage-w-e2e-join-acceptance/invoke_20261103_10_final_acceptance.md` §2（2026-11-03 · B2 坐实链尾） |
| backlog | `../ops-desk-workspace/docs/tasks/backlog/backlog_20261030_post_stage_w.md` B2（「联调已坐实 · 待立 fix task」· 2026-11-03 标注） |
| 联调 task（被阻塞） | `../ops-desk-workspace/docs/tasks/active/task_stage_w_e2e_join_acceptance.md`（N-R2-1/F3 复测回接待本 task 修复合入） |
| 同族已修项 | `docs/tasks/active/task_api_w_join_gap_fix.md`（W-fix-1 TTL / W-fix-2 只读谓词 · PR #307 · 本 task 不重叠回归） |
| 谓词/租户先例 | `docs/tasks/done/task_tenant_readonly_predicate.md`（:156 范围锚 · 谓词模式）· `app/ops/tenant_context.py`（F1=C · 唯一回落真源） |
| HITL 既有面 | `docs/tasks/done/task_hitl_resume_replay_contract.md` · `task_hitl_resume_async.md`（resume 异步同源执行体纪律）· `app/ops/hitl/{router,resume,auto_resume,store}.py` |
| 编码规范 | `docs/standards/CODING_BACKEND_L2_v1_zh.md` |

---

## 给执行帽的必读列表

1. `AGENTS.md`
2. 本 task（钉死契约 · 闸 · 非范围 · failure_paths）
3. workspace invoke `invoke_20261102_10_c8_evidence_archive.md`（§C6 · §2 F3/N-R2-1/守卫真空 · §4 · §7 #1/#2）
4. 代码：`app/ops/hitl/{router,resume,auto_resume}.py` · `app/ops/tenant_context.py` · `app/ops/lg_rag/multi/nodes.py`（`:318-320` / `:499-504` / `:554` / `:1881-1925` / `:2144-2230`）· `app/ops/lg_rag/run_worker.py:120-153` · `app/ops/deps.py:43-45` · `app/ops/lg_rag/router.py:376-384`
5. `docs/tasks/done/task_tenant_readonly_predicate.md`（租户谓词先例）
6. `docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`

---

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|----|------|------------|----------------------|----------------|
| R0 | 本 task = 两个已实证同族租户缺陷的合并修复竖切（N-R2-1 + F3 + 守卫真空）；不是新特性、不是 web UX | no | — | none |
| R1 | 范围切分：F7/F9/web UX 族（F1/F6/F8/F10/F14/F15）另行立项；N-R2-1 与 F3 合并（invoke §7 #2 明示「可与 N-R2-1 合并设计」· 守卫真空「并入上述 fix task 设计」） | no | — | 合并后单 task 承载两缺陷，30 需保持两红测族独立可验 |
| R2 | 设计咬合点：缺陷 1 修复方案依赖缺陷 2——若 resume tenant 取「decide 时快照」（单据 `tenant_id`），delegation 单 `''` 真空不修则快照无真值；故 T-fix-2 为 T-fix-1 选项 A 的硬前置，同题同修；回执错标根治点在 tenant 还原（消费上下文真值）而非回执写入侧 | no | — | 选项 A/B 各有风险面（A：历史 '' 单 fail-closed 拒 resume 的用户可见性；B：thread 不绑租户致「B 批 A 消费」）→ 挂 HG-W-TENANT-DESIGN |
| R3 | 闸设计：新增 HG-W-TENANT-DESIGN 承载三决策（tenant 来源 · delegation 守卫口径 · 历史 40 行处置）；双 freeze 零改入钉死契约 + failure_paths 红线；回接条款挂联调 C6 复测 | yes | 决策面已框死（全部落地为闸决策点或验收项）；实现接线属 30 实扫 | 历史 `tenant_id=''` 40 行的用户可见处置（拒 resume / 豁免文档化）须维护者签后 30 才知确切语义 |
| R4 | （未开） | — | early_stop at R3 | — |
| R5 | （未开） | — | early_stop at R3 | — |

**actual_last_round**：R3 · **early_stop**：yes · **residual_risks**：见 R3

### R0 · 问题框定

联调 C6 把 N-R2-1 从「20-R2 观察点」打成「实证缺陷」（B 单被 A 上下文消费 · 回执错标），同棒 F3 + 守卫真空坐实 delegation 链的租户真空。本 task 是修复轨——证据、锚点、期望行为已钉在 invoke；30 的性质是「按闸钉死值接线 + 红测负样本」。

### R1 · 范围切分

invoke §2 发现族中只取租户同族三件套（N-R2-1 / F3 / 守卫真空）。F7（重规划轰炸）与 F9（孤儿单去重）虽同涉 HITL 但语义正交（审批生命周期 vs 租户上下文），混入会失焦；web UX 族已有 backlog B10/B11 合并建议。W-fix-1/W-fix-2（前 task · PR #307）已闭环项不重叠。

### R2 · 合并设计与咬合点

N-R2-1 的修复选项 A「decide 时快照」以单据 `tenant_id` 为真源——而 F3 正是 delegation 单 `tenant_id=''`，不修则选项 A 对 delegation 单无真值可取（fail-closed 会全量拒 resume）；选项 B「请求重建」不依赖 F3，但引入「decide 后切租户 → B 批 A 消费」风险面（thread 不绑租户已实测）。故两缺陷同题：T-fix-2 是选项 A 的硬前置，也是守卫真空的必要条件（守卫查 `row.tenant_id` 非空才有意义）。回执错标（`d6bd262904544232`）根治点在消费上下文还原，不在回执写入侧加补丁。

### R3 · 闸设计 · 收敛

三个真决策点（①tenant 来源 A/B/组合 · ②delegation 守卫扩列 vs 豁免文档化 · ③历史 '' 40 行处置）都影响契约与用户可见语义，须维护者签 → 新增 `HG-W-TENANT-DESIGN`。双 freeze 零改（SSE event_type / hitl-browser-decide-v1 本体）为红线，入钉死契约 + failure_paths（维护者 issue #311 要求②）。回接条款挂联调 C6 复测，防「修复合入但挂账不销」。残险：历史 40 行处置的用户可见形态须签后才定，30 实扫回填修订表。

### R4 ·（未开 · early_stop）

本轮不展开；待 HG-W-TENANT-DESIGN 签收后由 20-R1 / 30 实扫补足。

### R5 ·（未开 · early_stop）

本轮不展开。

---

### 自检结论

| 命令 | 退出码 | 摘要 |
|------|--------|------|
| `npx spec-wave task lint --file docs/tasks/active/task_api_w_hitl_tenant_fix.md` | 0 | LINT: PASS（2026-11-03 · 10 起草棒） |
| `npx spec-wave task lint --file docs/tasks/active/task_api_w_hitl_tenant_fix.md` | 0 | LINT: PASS（2026-11-03 · 闸表签收修订后复跑 · 待 30 棒起填 pytest/ruff/graph-compile） |

---

## 修订

| 日期 | 说明 |
|------|------|
| 2026-11-03 | 10 起草壳（维护者 issue #311 令 · 联调实证双缺陷 N-R2-1+F3/守卫真空）· 四闸 pending · NO-GO 20/30 · R0–R3（R3 early_stop）· 红测先行入 test_strategy · 双 freeze 红线（SSE event_type / hitl-browser-decide-v1）入 failure_paths · 证据锚全引 workspace C8 invoke §C6/§2 + 终验 invoke §2 + backlog B2 · 零 `app/` diff |
| 2026-11-03 | PR #312 合入（squash `04245ef`）· 20-R1 审查 PASS（维护者 review · 语义面逐项核对）· 维护者签 HG-TASK-DRAFT（issue #311 评论）· 审查文落档 `docs/harness/invokes/by-task/api-w-hitl-tenant-fix/invoke_20261103_20_r1_audit.md` → HG-AUDIT-R1 签（auth311）· 维护者签 HG-GRAPH-MODULES + HG-W-TENANT-DESIGN（auth311 代录）· **三决策裁决**：① A+B 组合（单据 tenant 唯一真源 · 手动入口 session≠单据 → 403 · auto-scan 纯 A · 空 tenant 拒 resume）② 守卫扩列 ③ 历史 '' 从严拒 resume 不回填 · 钉死契约表草案→裁决值全量升格 · 状态 draft→active · GO 30（auth311 六要求：红测先行可见红→绿 / 旧测影响面清单 / 同源单实现 / 双 freeze 零 diff / ruff+pytest+graph-compile 全绿 / PR 逐条对照验收）· git_branch 改钉部署绑定分支 |
| 2026-11-04 | **回接条款·联调 C6 修复后复测全绿**（PR #313 merge `7800b2b` · 2026-11-04 02:44–02:49 UTC 实测 · 证据 workspace invoke `invoke_20261104_10_c6_retest.md` @ `f2aaf50`）：① B 链打戳+消费日志+回执 tenant=`ops-desk-pilot-b`（回执 `f14068d3b77c40f7` · 对照旧错标 `d6bd262904544232`）② A resume B 单 403 `tenant_scope_denied` ③ 历史 '' 单 `hitl_b28a21f4982e43b0983a` resume 409 fail-closed（裁决③落实）④ A 正样本全链零变化（回执 `e8c64c784a00479e`）· N-R2-1/F3/守卫真空三缺陷修复实证 · 从严口径执行 · **附带观察 O1**：sync invoke 路径无事件帧致 decide 归属 404（预存在 · 非本 PR 引入 · 建议另行立项） |
