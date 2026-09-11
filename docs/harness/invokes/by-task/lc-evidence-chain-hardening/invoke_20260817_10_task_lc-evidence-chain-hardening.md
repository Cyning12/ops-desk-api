# Invoke：10-task · lc-evidence-chain-hardening

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 10-task |
| task_slug | `lc-evidence-chain-hardening` |
| freeze_id | `lc-evidence-http-v1`（保持，不升） |
| task_paths | `docs/tasks/active/task_lc_evidence_chain_hardening.md` |
| related_review_or_none | 上游 SPEC `docs/spec/lc-evidence-chain/SPEC-lc-evidence-chain-hardening_v1.md` · 评审 `docs/guides/REVIEW_lc_evidence_chain_third_party_20260816.md` |
| git_branch | `task/lc-evidence-chain-hardening` |
| worktree_root | `.` |
| created_utc_or_local | 2026-08-17 |
| notes | 仅 task；不改 `app/` / `tests/` 业务实现；闸 pending；无关 active `task_ops_sync_sender_migration.md` 不混入 |

---

## 可复制 Prompt 快照

本帽指令已由 00 执行（Open Folder = 本 worktree）。要点：单 task 收 D1–D4；R0–R5 + 思考轮控制；验收 / failure_paths / 非范围齐全；`HG-TASK-DRAFT` / `HG-AUDIT-R1` 起草时 pending。

---

## 裁决

- 单 task，不拆多个实现 task。
- 真值：已签 SPEC + 评审 §3；Trace 树已完成故排除。
- 禁止：改 graph、升 freeze、CE→EXACT、timeout 60、缓存、单例、接回 Graph。

## 结论摘要

必做：`complete()` 聚合上报 usage（仍返回 str；两 Provider 一处 helper）；grader 异常 → grades=[] → refuse / HTTP 200；`kept` 按 `relevance.level` 降序（同档稳定）；G-L1 一句。

---

## 交付摘要

- **验证命令**：`npx @cyning/harness task lint --file docs/tasks/active/task_lc_evidence_chain_hardening.md` → **LINT: PASS**
- **变更路径**：`docs/tasks/active/task_lc_evidence_chain_hardening.md` · 本 invoke
- **下一棒**：20-task-audit 已委托 00 书面审；内容零阻塞后签 `HG-TASK-DRAFT` + `HG-AUDIT-R1`；未签禁 30

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-08-17 | 10-task 首稿落盘 |
