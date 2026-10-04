# Invoke：CLOSE · hitl-browser-decide（B2 HITL 浏览器决策面）

| 字段 | 值 |
|---|---|
| hat_id | CLOSE（00 统筹） |
| task_slug | `hitl-browser-decide` |
| task_paths | `docs/tasks/done/task_hitl_browser_decide.md`（已归档） |
| related_review_or_none | R1 `docs/harness/reviews/task_hitl_browser_decide_audit_R1_20260930.md`（通过 0 阻塞 · 4 nit 随 30 闭合） |
| git_branch | `task/chat-history-hitl-ux` → PR #204 MERGED（`eb22a66` · CI 四绿） |
| created_utc_or_local | 2026-09-30 |

---

## 链路留痕

10 拆解（裁定 D/E 上抛）→ 维护者令「安全推荐」落定 D1/E1 → 20 R1 通过 → 维护者签 HG-TASK-DRAFT/HG-AUDIT-R1/HG-GRAPH-MODULES（2026-09-30）→ 30/40 交付 `c39e659`（叠 B1 之上）→ 维护者令单 PR → PR #204 CI 四绿 MERGED → CLOSE。

## 交付摘要

| 项 | 内容 |
|---|---|
| **产出** | `GET /api/ops/hitl/pending` + `POST /api/ops/hitl/requests/{id}/decide`（`app/ops/hitl/router.py` +141/-2）· `tests/test_hitl_pending_decide.py` 20 用例 · G-L1 图谱备注 |
| **验收** | 14/14 机断全绿；pytest 1647 passed · lint-imports 0 broken · graph-compile 0 · lint-wiki-delta PASS；N2 真 PG decide→重启→resume 链真跑 |
| **红线** | OA 签名面/`signature.py`/`_require_signed`/callback/resume 零 diff 实测 · decide 不自动 resume（spy 断言）· store 语义零改 · B1 交付物零回退 |
| **签闸链** | HG-TASK-DRAFT · HG-AUDIT-R1 · HG-GRAPH-MODULES 全 approved（维护者 2026-09-30） |
| **KPI** | kpi_aggregator=CLOSE · 验收勾选 14/14 · PR #204 MERGED `eb22a66` |
| **遗留** | E1 下多 maintainer 不能互批他人 run（归属隔离设计使然 · R5 已标注）；未落帧 run 的申请对所有 maintainer 不可见不可决（error 日志可观测）；前端 F2 另立 SPEC（Q4） |
