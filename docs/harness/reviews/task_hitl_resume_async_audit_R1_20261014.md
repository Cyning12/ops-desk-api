# task_hitl_resume_async_audit_r1 — 20-task-audit R1 书面审查

| 键 | 值 |
|---|---|
| hat_id | 20-task-audit（R1） |
| 审查对象 | `docs/tasks/active/task_hitl_resume_async.md`（v0 初稿 · task lint PASS 复跑核真 exit=0） |
| 配套 invoke | `docs/harness/invokes/by-task/hitl-resume-async/invoke_20261014_10_task_draft.md` |
| 审查日期 | 2026-10-14 |
| 审查基准 | 启动令（web 00 移交 · B 方案）§4 契约钉死 / §5 决策点 / §6 验收 · base `master` 56e4a9f 亲读核真 |

## 结论摘要

- **内容审查：FAIL —— 单条阻塞退回（N1）+ 四条非阻塞 nits（n1–n4 随轮回填）**
- **流程闸：HG-AUDIT-R1 = pending** —— 依纪律本文不附 30 Prompt；文末为维护者（授权 00 代签形态）签闸清单
- 退回路径：00 转 10-task 回填 N1（+n1–n4）→ 20 R2 复审

## 逐项核对（启动令对照 · 全亲读核真）

### 1. 契约钉死六项 —— 全部落入 task 钉死表 · 锚点行号核真通过

| 启动令 §4 钉死项 | task 落点 | 亲读核真 |
|---|---|---|
| decide/resume 两步 · decide 默认不自动 resume | 钉死表行1（decide :184-269 · resume :466-529） | ✅ router.py:184 `decide_request` · :466 `resume_request` · docstring :193-199「默认（manual）本端点只置已决，不自动 resume」 |
| resume_mode 白名单 · 未知值 400 · immediate=立即调度 | 钉死表行2（:207-211 · docstring :116-120 · RESUME_MODES auto_resume.py:58-62） | ✅ 手工白名单 400 在 :207-211；docstring :116-120 钉 str 禁 Literal；RESUME_MODES 三元组 :58-62 |
| 驳回也可 resume 收工 | 钉死表行3（状态守卫 :487-491 · docstring :478-480） | ✅ :487-491 非 approved/rejected→409；:478-480 驳回必须能调原文在 |
| 终帧 done{status:'resumed', latency_ms:int≥0, 无 model 键} | 钉死表行4（resume.py:131-136 · close :124-137） | ✅ close() :124-137 · status :131 · latency_ms :135 `int((time.perf_counter()-self._started)*1000)` · 载荷键集 run_id/thread_id/status/events_persisted/latency_ms —— 无 model 键 |
| replay 在飞 409 + Retry-After: 2 | 钉死表行5（event_store.py:246 refuse_in_flight + 实证） | ✅ event_store.py:246-247 `if refuse_in_flight and not await run_stream_closed(run_id): raise LgRagRunInFlightError`；Retry-After 设置点实证于 lg_rag/router.py:420（见 n3） |
| ResumeError→409/503/502 映射表 | 钉死表行6（:495-509） | ✅ :496-506 五键 409 + checkpointer_not_configured 503 + 兜底 502 · :509 raise |

### 2. 范围/非范围两硬约束 —— 守住

- 「复用 RunWorker 不另造轮子」：范围 F1–F3 + 根因锚点节（task :53-57）写明复用形态清单；非范围「不改造 run_worker.py 本体」✅
- 「不动状态码与键名（web 零改动）」：D2 钉死约束（状态码 200 · 键集 {ok,request,resume,replay,ts} :513-533 核真 ✅）+ D3 先回执纪律 + 失败路径行5 ✅

### 3. R0–R5 思考轮 —— 充分

- 控制表 6 槽全填；R5 early_stop=true · reason「范围/钉死/决策点/failure_paths/验收互洽 · 无新增疑问」· residual_risks 填实（F3 接线面 + D1 键值形态留 30/00 定稿）✅
- R0 结论（请求内守卫 + 异步派发秒回 + 同源执行体 + 复用单飞/补偿形态）可支撑 30 开工 ✅

### 4. 启动令出入项处置 —— 得当

- JC 证据亲验：`git -C ../ops-desk-web log -1 a2b1b1f` 成立（commit「docs(joint-check): 40 机验回执 … JC-F1/JC-F2 联调发现」），确在 web 分支 `task/web-api-joint-check` 未并主线；task 依赖节 :129 照登 + git show 读取法 ✅；数值面（130–310s/30.1s/终帧实值）与启动令一致，无实质冲突 ✅

### 5. 两个 30 裁定面 —— 亲读核真 · task 已正确标注（非遗漏）

- `scan_orphan_runs_for_compensation`（run_worker.py:188-245）生产侧无周期接线：全仓 grep 调用方仅 `tests/test_lg_rag_sse_run_worker.py`（event_store.py:163 为 docstring 提及非调用）✅
- auto_resume 补偿扫描器仅 `auto_resume_mode()==MODE_AUTO` 时 lifespan 挂：main.py:52-54 亲读核真（manual 零创建 :50-51 注释明示）✅
- task :57 / F3 :68 / 失败路径行3 均标注「接线面 30 裁定」，invoke_10 关键裁定 2 同口径 ✅

### 6. Harness 结构面 —— 齐全

- 元信息表（task_slug/git_branch/implement_repo/test_strategy/graph_change_layer=G-L1/review_hat/required_invoke_hats=10,20,30,40/freeze_id）✅
- wiki_delta=`n/a` + note ✅；人工闸表三闸 pending + 维护者 2026-10-14 授权 00 代签留痕（说明列逐闸注明 · 签署动作归 00）✅
- 图谱分层预判 G-L1 与 `docs/_tech_graph/l1/01_modules.md` 现状相容（hitl 在 `api` 模块行 · resume 行为表述回写面成立）✅
- `task lint` 复跑 PASS（exit=0）✅
- TC1–TC8 可机断性逐条过：TC1 阻塞闸门红测（防恒绿）✅ TC2–TC5 契约对拍 ✅ TC6 崩溃兜底断言面 ✅ TC7 全量对拍+零新增红 ✅ TC8 live p95<1s + replay 409→200 + T-W2 S3/TC5 复跑（菜谱锚点实证存在）✅
- failure_paths 七条覆盖授权令四要求项（异步失败前端可见形态 / run_owner 反查失败 / 投递后崩溃孤儿补偿 / 重复 resume 幂等）✅

## 阻塞项（退回清单）

### N1 · 验收缺「旧测 grep 影响面」项（行为变更类 task 必备 · 20-task-audit skill 明文：缺则退回 10 补列）

- **事实**：本 task 为行为变更类（端点同步→异步 + 响应 `resume` 键值形态变「已受理」），验收 TC1–TC8 无「旧测 grep 影响面」枚举项；TC7 仅列测试文件面，未枚举消费变更面的旧测断言点。
- **实证影响面**（20 亲 grep · 供 10 照登）：消费 **resume 端点响应** `resume` outcome 键、异步化后必破的断言点共 4 处：
  - `tests/test_hitl_resume.py:362` — `assert res.json()["resume"]["state"]["route"] == "replan"`
  - `tests/test_hitl_pending_decide.py:501` — `state = resumed.json()["resume"]["state"]`
  - `tests/test_hitl_pending_decide.py:528` — 同上
  - `tests/test_hitl_pending_decide.py:661` — `state = res2.json()["resume"]["state"]`
- **区分不受影响面**：decide 响应 `resume` 块（required/auto_triggered/endpoint 键）消费点 `tests/test_hitl_pending_decide.py:367-368`、`tests/test_hitl_auto_resume.py:308/417-418/570/909` —— decide 面零 diff（非范围钉死），**不破**，回填时须写明此区分防误改。
- **回填要求**：验收节增补一项（建议 TC2 子项或独立 TC），内容为「旧测 grep 影响面：枚举消费 resume 响应 outcome 键的旧测断言点（上述 4 处为基线 · 30 开工前 grep 复核），逐点裁定适配形态（改断言为「已受理」形态 + replay 追帧断言 / 或经事件流取 outcome），并断言 decide 面 resume 块消费点零 diff」。

## 非阻塞 nits（随 N1 同轮回填）

- **n1 · 行号漂移**：task :52「ResumeEventSink 类 resume.py:112-162」—— 类起始实为 `resume.py:54`（:112-162 为 open()→cursor() 区间）；建议改 `:54-162`。
- **n2 · 测试面数目含糊**：TC7「等 8 文件」与实证面不齐 —— tests/test_hitl*.py 实有 7 件（test_hitl / test_hitl_approval_consumption / test_hitl_approved_replan_quality / test_hitl_auto_resume / test_hitl_pending_decide / test_hitl_resume / test_hitl_resume_events）+ test_lg_rag_sse_hitl / test_lg_rag_sse_resume / test_lg_rag_sse_run_worker 共 10 件相关；建议写准数目或改写「HITL/auto-resume 面全量」。
- **n3 · 契约锚点可补**：钉死表行5 现锚 event_store.py:246 + 实证；建议补 `app/ops/lg_rag/router.py:420`（`headers={"Retry-After": "2"}` 设置点）使 409+Retry-After 锚链完整。
- **n4 · 留档措辞**：invoke_retention_profile 写 `default`（10,30,40）而 required_invoke_hats 含 20 —— 按 v2.12 required 优先，并存合法但易误读；建议 profile 行注明「required_invoke_hats 优先于 profile」。

## 维护者签闸（20 后 · 30 前 · 维护者已授权 00 代签形态）

- [ ] 10-task 按 N1（+n1–n4）回填 task → 20 R2 复审 PASS
- [ ] 00 依维护者 2026-10-14 授权在 task 人工闸表将 HG-AUDIT-R1（及 HG-TASK-DRAFT / HG-GRAPH-MODULES）改为 approved（代签留痕 · 注明授权来源）
- [ ] commit task 文档（00 统提）
- [ ] 再下发 Harness 30 Prompt（task 表 approved 为真源 · 30 以表为准）

> 注：本审查文按要求不附 30 Prompt（HG-AUDIT-R1 仍 pending · 20-task-audit 纪律）。
