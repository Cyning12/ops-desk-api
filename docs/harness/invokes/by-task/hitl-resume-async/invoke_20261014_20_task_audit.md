# invoke_20261014_20_task_audit — hitl-resume-async · 20-task-audit R1 书面审查

| 键 | 值 |
|---|---|
| hat_id | 20-task-audit（R1） |
| task | `docs/tasks/active/task_hitl_resume_async.md`（v0 初稿） |
| 审查文 | `docs/harness/reviews/task_hitl_resume_async_audit_R1_20261014.md` |
| 分支 | `task/hitl-resume-async` |
| 日期 | 2026-10-14 |

## 结论

**FAIL —— 单条阻塞退回（N1：验收缺「旧测 grep 影响面」项）+ n1–n4 非阻塞 nits 随轮回填**。退回路径：00 转 10-task 回填 → 20 R2 复审。HG-AUDIT-R1 维持 pending，未附 30 Prompt（纪律）。

## 审查动作留痕

1. 加载 skill `harness-20-task-audit` 获取审查规范（行为变更类 task「旧测 grep 影响面」checklist 明文：缺则退回 10 补列）
2. 亲读核真（base `master` 56e4a9f）：
   - `app/ops/hitl/router.py` :110-269（decide/白名单/docstring）· :360-539（sink/执行体/resume_request/映射表/响应键集）
   - `app/ops/hitl/resume.py` :100-359（ResumeEventSink open/close/cursor · _resume_with · resume_hitl_run fail-closed）
   - `app/ops/hitl/auto_resume.py` 全文 313 行（RESUME_MODES/_BACKGROUND_TASKS/schedule_auto_resume/_claim_and_execute/scan_approved_not_resumed_once/start_compensation_scanner）
   - `app/ops/lg_rag/run_worker.py` 全文 245 行（bus/worker/orphan scan）
   - `app/ops/lg_rag/event_store.py` :125-254（run_stream_closed/list_open_runs/refuse_in_flight:246）
   - `app/main.py` :40-64（lifespan 仅 MODE_AUTO 挂扫描器 :52-54）
   - `app/ops/lg_rag/router.py:420` Retry-After: 2 设置点（grep 实证）
3. 全仓 grep 核真：`scan_orphan_runs_for_compensation` 生产侧无调用方（仅 tests/test_lg_rag_sse_run_worker.py）✅
4. web 侧亲验：`git -C ../ops-desk-web log -1 a2b1b1f` 成立（JC 证据在 task/web-api-joint-check 未并主线）· 移交令 invoke_20261014_00_dispatch_api.md 在 web 工作树 ✅
5. 旧测影响面实证（N1 证据）：grep tests 消费 resume 端点响应 outcome 键断言点 4 处 —— test_hitl_resume.py:362 · test_hitl_pending_decide.py:501/528/661；decide 面 resume 块消费点（test_hitl_pending_decide.py:367-368 · test_hitl_auto_resume.py:308/417-418/570/909）不受影响
6. `npx dsh-coding-kit task lint --file docs/tasks/active/task_hitl_resume_async.md` 复跑 PASS（exit=0）

## 逐项核对结论

启动令 §4 契约钉死六项全部落入 task 且锚点核真通过；范围/非范围两硬约束守住；R0–R5 充分（R5 early_stop 理由/风险填实）；出入项（JC 证据未并主线）处置得当；两个 30 裁定面（orphan scan 无生产接线 · 扫描器仅 auto 挂）核真且 task 正确标注；Harness 元信息/wiki_delta/留档/闸表齐全。详见审查文。

## 退回清单（转 10-task）

- **N1（阻塞）**：验收补「旧测 grep 影响面」项 —— 枚举消费 resume 响应 outcome 键的旧测断言点（基线 4 处：test_hitl_resume.py:362 · test_hitl_pending_decide.py:501/528/661），逐点裁定适配形态；并断言 decide 面 resume 块消费点零 diff
- n1：ResumeEventSink 类行号 :112-162 → :54-162
- n2：TC7「等 8 文件」数目写准（实证 10 件相关）
- n3：钉死表行5 补锚 lg_rag/router.py:420
- n4：invoke_retention_profile 注明 required_invoke_hats 优先

## 禁区自查

未改 task/app/tests 实质内容 · 未签任何 human_gate · 未 push · 产出 git add 不 commit（00 统提）· HG-AUDIT-R1 pending 未附 30 Prompt

---

# R2 复审节（2026-10-14 · 复审令：核销 R1 退回清单 + 回退复核 + lint 复跑）

| 键 | 值 |
|---|---|
| hat_id | 20-task-audit（R2） |
| task | `docs/tasks/active/task_hitl_resume_async.md`（v0.1 · 吸收 R1 退回回填） |
| 审查文 | `docs/harness/reviews/task_hitl_resume_async_audit_R2_20261014.md` |

## R2 结论

**PASS —— N1（阻塞）+ n1–n4 全部核销 · 回填零回退 · lint 复跑 PASS**。HG-AUDIT-R1 维持 pending，签闸清单在审查文末节（维护者授权 00 代签 · 签署动作归 00），未附 30 Prompt（纪律）。

## R2 审查动作留痕

1. 读 task v0.1 全文（210 行）逐条对照 R1 退回清单
2. N1 核销亲读（base 56e4a9f · 断言点原文复核行号与裁定形态）：
   - 必破断言 4 处全部精确命中：`tests/test_hitl_resume.py:362`（`res.json()["resume"]["state"]["route"] == "replan"`）· `tests/test_hitl_pending_decide.py:501`（+:502-503 replan 链）· `:528`（+:529-530 settle 驳回链）· `:661`（+:662-663 DB 实库链）
   - decide 面零 diff 区分点全部命中：`test_hitl_pending_decide.py:367-368`（required/endpoint）· `test_hitl_auto_resume.py:308`（全字典对拍）/ `:417-418` / `:570` / `:909`（auto_triggered/required）
   - 适配形态双路径（改断言为「已受理」+ replay 追帧取终帧 / 经事件流取 outcome）与 F1/F4 约束互洽，30 可机断执行
3. n1 核销：ResumeEventSink :54-162 三处联动一致（task :52 / :138 / :203）
4. n2 核销：TC7「10 件」全名列出（test_hitl*.py 7 + lg_rag 3）
5. n3 核销：钉死行5 补锚 `app/ops/lg_rag/router.py:417-421` —— 亲读 :417-421 精确命中（Retry-After: 2 字面 :420）
6. n4 核销：retention 注明 required_invoke_hats 优先（task :25）
7. 回退复核：三闸 pending 零预签 · 钉死表行1-4/6 未动 · 范围/非范围/D1-D3/failure_paths 7 条/R0-R5 零回退 · 修订记录 v0.1 行如实
8. lint 复跑：`npx spec-wave task lint --file docs/tasks/active/task_hitl_resume_async.md` → PASS（exit=0 · CLI v3.3.0 · 正确子命令形 `task lint --file`）

## R2 禁区自查

未改 task/app/tests 实质内容 · 未签任何 human_gate · 未 push · 产出 git add 不 commit · 复审令警示的另一线改动（app/main.py · docs/discussions/2026-09-24_*.md）当前工作树不存在（git status 亲验）· 零触碰

