---
hat: 20
task_slug: hitl_ops_runbook
date: 2026-10-17
---

# invoke · 20-task-audit R1 · hitl_ops_runbook（HITL 生产使用流程手册 + 残留收口）

## 审查摘要

- 审查文：`docs/harness/reviews/task_hitl_ops_runbook_audit_R1_20261017.md`（址A · R1 书面审 · 未改 task · 未代签闸 · 零 git 操作）。
- **裁定：BLOCKER 退回 10-task**——B-1 思考轮控制表 R0–R5 六行 + 正文六节全为「（执行者回填）」占位（actual_last_round 亦占位）；全仓 grep「（执行者回填）」零先例，task 自引先例 task_compose_hitl_persistence_env / task_lg_rag_sse_run_worker 思考轮均实填闭合。设计决策（HMAC 排除 · auto 附录化 · FP-7 停派 · 坑位边界）须 10 起草面留痕，非 40 倒填面。
- 内容其余面全正向：码面锚点全亲读命中（hitl 端点族 :76/:161/:185/:530 · persistence.py:22,40,54-57 · lg_rag router :384-420 replay 409+Retry-After · run_stream_closed 本体 event_store.py:132 · compose:68）· 依赖档全在 · TC-1..9 可机断 · lint 亲跑 PASS。
- N-1（缺 HG-TASK-DRAFT 行）· N-2（test_strategy 自由文本）· N-3（闸 pending 系起草史实）· N-4（run_stream_closed 谓词本体锚点可补 event_store.py:132）照登不闸。
- HG-AUDIT-R1 approved 系 2026-10-17 维护者授权 00 代录（m00238 · R1 书面审豁免）· 本帽照登未代签；**内容阻塞未清零前 40 必须拒开工**；不附 40 Prompt。

## 过程

1. 读 task 全文 + reviews 先例对齐体例。
2. 锚点亲读：app/ops/hitl/router.py · persistence.py · app/ops/lg_rag/router.py · event_store.py · docker-compose.yml；依赖档（SPEC/两份验收/两份 CLOSE/compose+run_worker done 档/RUNBOOK 先例）存在性核实。
3. 思考轮占位先例核查：grep done/+active/ 全仓仅本档命中「（执行者回填）」→ 裁定 B-1。
4. task lint 亲跑 PASS（W3 仅自检占位 · lint 不查思考轮回填）。
5. 落审查文 + 本 invoke（未 commit · 零 git 操作）。
