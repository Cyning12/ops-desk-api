> **复制说明（双址过渡 · 2026-10-15 CLOSE 棒落）**：本档系址A 原件 `docs/harness/reviews/task_hitl_resume_async_audit_R2_20261014.md` 的逐字复制件（审查门禁双址规约 v1 §二 过渡期口径 · 址B 存档命名 `YYYYMMDD_<slug>_r<n>.md`）；址A 原件原址原内容不动，正文与本件逐字一致（仅本行与下一行说明为增量）。
> **来源**：址A（verify 门禁消费址）→ 址B（20 书面审存档址）· CLOSE 文档 `docs/tasks/close/close_hitl_resume_async_20261015.md`

# task_hitl_resume_async_audit_r2 — 20-task-audit R2 复审（R1 退回回填核销）

| 键 | 值 |
|---|---|
| hat_id | 20-task-audit（R2） |
| 审查对象 | `docs/tasks/active/task_hitl_resume_async.md`（v0.1 · 吸收 20 R1 退回回填） |
| 前序审查文 | `docs/harness/reviews/task_hitl_resume_async_audit_R1_20261014.md`（R1 FAIL · N1 + n1–n4） |
| 配套 invoke | `docs/harness/invokes/by-task/hitl-resume-async/invoke_20261014_20_task_audit.md`（R1 节 + 本文 R2 节） |
| 审查日期 | 2026-10-14 |
| 审查基准 | R1 退回清单逐条核销 + 回填无回退复核 · base `master` 56e4a9f 断言点亲读核真 |

## 结论摘要

- **内容审查：PASS —— R1 核销清单 N1 + n1–n4 全部核销闭合 · 回填未引入新问题 · task lint 复跑 PASS（exit=0）**
- **流程闸：HG-AUDIT-R1 维持 pending** —— 依纪律本文不附 30 Prompt；文末为维护者（授权 00 代签形态）签闸清单，签署动作归 00

## R1 退回清单逐条核销

### N1（阻塞）· 验收补「旧测 grep 影响面」项 —— ✅ 核销（TC2b 落成 · 断言点亲读核真）

task v0.1 新增 **TC2b**（验收节第 3 条），含两部分，全部亲读复核：

**(a) 必破断言 4 处 —— 行号与断言形态逐点命中（base 56e4a9f）：**

| task 引用 | 亲读原文 | 核对 |
|---|---|---|
| `tests/test_hitl_resume.py:362` | `assert res.json()["resume"]["state"]["route"] == "replan"` | ✅ 精确命中（消费 resume 响应 outcome · 异步化后 `resume` 键变「已受理」形态必破） |
| `tests/test_hitl_pending_decide.py:501` | `state = resumed.json()["resume"]["state"]` → :502 `hitl_unlocked_ids == [_T1]` · :503 `react_observation.verdict == "replan"` | ✅ 精确命中（批准链） |
| `tests/test_hitl_pending_decide.py:528` | `state = resumed.json()["resume"]["state"]` → :529 `hitl_unlocked_ids == []` · :530 `verdict == "settle"` | ✅ 精确命中（驳回链 · task 标注「驳回链同形态 → verdict=="settle"」属实） |
| `tests/test_hitl_pending_decide.py:661` | `state = res2.json()["resume"]["state"]` → :662 `hitl_unlocked_ids == [_T1]` · :663 `verdict == "replan"` | ✅ 精确命中（DB 实库链） |

**(b) decide 面 `resume` 块消费点零 diff 区分（防误改 · decide 属非范围钉死）—— 逐点亲读命中：**

- `tests/test_hitl_pending_decide.py:367-368`：`body["resume"]["required"] is True` · `endpoint.endswith(...)` ✅（decide 响应面）
- `tests/test_hitl_auto_resume.py:308`：`res.json()["resume"] == {required, method, endpoint}` 全字典对拍 ✅
- `tests/test_hitl_auto_resume.py:417-418`：`auto_triggered is True` · `required is False` ✅
- `tests/test_hitl_auto_resume.py:570` / `:909`：`auto_triggered is True` ✅（两处）

**裁定形态可执行性**：TC2b 要求 30「逐点裁定适配形态（改断言为『已受理』形态 + replay 追帧取终帧断言 / 或经事件流取 outcome）」—— 两条适配路径均与 task F1/F4 约束互洽（响应键名不动 · 落盘链行为零 diff · 终帧逐键不变），30 可机断执行 ✅。「30 开工前 grep 复核」前置句防行号漂移 ✅。

### n1 · ResumeEventSink 类行号 :112-162 → :54-162 —— ✅ 核销（三处联动一致）

- task :52 根因锚点节：`ResumeEventSink 类 resume.py:54-162` ✅
- task :138 必读列表：`resume.py:54-162/:288-355` ✅
- task :203 自检结论：`resume.py:54-162,:288-355` ✅
- 与 R1 亲读真值（类起始 :54 · close 终帧 :124-137）一致 ✅

### n2 · TC7 数目写准 —— ✅ 核销（10 件全名列出）

task :124 TC7 改述「HITL/auto-resume 面 **10 件**」并全名列出：`test_hitl.py` · `test_hitl_approval_consumption.py` · `test_hitl_approved_replan_quality.py` · `test_hitl_auto_resume.py` · `test_hitl_pending_decide.py` · `test_hitl_resume.py` · `test_hitl_resume_events.py`（7 件）+ `test_lg_rag_sse_hitl.py` · `test_lg_rag_sse_resume.py` · `test_lg_rag_sse_run_worker.py`（3 件）—— 与 R1 grep 实证 10 件一致 ✅。

### n3 · 钉死表行5 补锚 —— ✅ 核销（锚点亲读精确）

task :92 钉死表行5 现含 `app/ops/lg_rag/router.py:417-421`（`headers={"Retry-After": "2"}` :420 设置点）。亲读 `app/ops/lg_rag/router.py:412-425`：`except LgRagRunInFlightError` → `HTTPException(409, detail="Run is still in flight; retry after it settles.", headers={"Retry-After": "2"})` 正在 :417-421 · Retry-After 字面在 :420 ✅。

### n4 · invoke_retention_profile 措辞 —— ✅ 核销

task :25 现为 `default`（10,30,40 留存 · … · **required_invoke_hats 优先于 profile**（v2.12 · 20 留存不因 default 省略））—— required 优先语义明示 ✅。

## 回填无回退复核（范围 / 契约钉死 / 思考轮）

- **三闸仍 pending 零预签**：task :3 状态行 + :35-37 人工闸表三行全部 pending · 维护者授权 00 代签仅留痕说明列 · 签署动作归 00 ✅
- **契约钉死表**：行1-4、行6 与 R1 核真结论逐字一致未动；仅行5 按 n3 补锚（加固非改动）✅
- **范围 F1–F5 / 非范围 9 条 / 契约决策点 D1–D3 / failure_paths 7 条**：与 v0 一致 · 零回退 ✅
- **R0–R5 思考轮**：控制表与五轮正文未动（R5 early_stop 理由/residual 保持）✅
- **修订记录**：v0.1 行如实载明 N1+n1–n4 回填内容与断言点清单 ✅；自检结论（task :203）更新为「20 R1 FAIL 退回已回填 · 复跑 lint PASS」✅

## 门禁复跑

```
npx spec-wave task lint --file docs/tasks/active/task_hitl_resume_async.md
LINT: PASS · task_hitl_resume_async.md   EXIT=0
```

（CLI v3.3.0 · `dsh-coding-kit` 为同入口过渡别名；正确子命令形为 `task lint --file`）

## 签闸清单（维护者 · 授权 00 代签形态 · 签署动作归 00）

R2 结论 PASS，task v0.1 已具备签闸条件。建议 00 按维护者 2026-10-14 授权（「授权00签收后续所有文档」）代签：

1. **HG-TASK-DRAFT** → approved（初稿质量 R1/R2 两轮核销完毕）
2. **HG-AUDIT-R1** → approved（本文即 R 轮审查真值 · R2 PASS）
3. **HG-GRAPH-MODULES** → approved（G-L1 预判 R1 已核对与 `docs/_tech_graph/l1/01_modules.md` 现状相容 · 30 按实判回写义务存续）

签后 30 方可开工（红测先行 TC1 · 接线面 F3 与「已受理」键值形态 D1 由 30 裁定 · commit 由 00 统提）。

## 禁区自查

未改 task/app/tests 实质内容 · 未签任何 human_gate · 未 push · 产出仅本文 + invoke R2 节（git add 不 commit · 00 统提）· 复审令警示的另一线改动（app/main.py · docs/discussions/2026-09-24_*.md）当前工作树不存在（git status 亲验：仅本 task 线暂存件 + 未跟踪 .pnpm-store/ · pnpm-lock.yaml）· 全程零触碰
