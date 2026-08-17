# Invoke：00 · lc-evidence-chain-hardening（统筹）

> **用途**：本 worktree 新 00 编排快照。00 **不实现** `app/` / `tests/` 业务代码。

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 00 |
| task_slug | `lc-evidence-chain-hardening` |
| freeze_id | `lc-evidence-http-v1`（保持，不升） |
| task_paths | `docs/tasks/active/task_lc_evidence_chain_hardening.md` |
| related_review_or_none | `docs/harness/reviews/spec_lc-evidence-chain-hardening_audit_R1_20260817.md` |
| git_branch | `task/lc-evidence-chain-hardening` |
| worktree_root | `.` |
| created_utc_or_local | 2026-08-17 |
| notes | 维护者下发 `PROMPT_00_orchestrate.md`；起草 SPEC 的原窗不参与实现；无关 active `task_ops_sync_sender_migration.md` 不混入 |

---

## 派发计划

| 步 | 帽 | 执行者 | 产出 |
|---|---|---|---|
| 1 | 读 | 00 | SPEC + 评审 §3 + git 确认（本 worktree · 正确分支） |
| 2 | 10-task | 00 | `task_lc_evidence_chain_hardening.md` + 10 invoke + `task lint` |
| 3 | 20-task-audit | 00 书面审 | `docs/harness/reviews/task_lc_evidence_chain_hardening_audit_R1_20260817.md` |
| 4 | 闸 | 维护者或 00 代签 | 内容零阻塞后 `HG-TASK-DRAFT` + `HG-AUDIT-R1` = approved |
| 5 | verify | 00 | `npx @cyning/harness verify --target . --task …`；pending 则拒开工 |
| 6 | 30+40 | **子 agent** | D1–D4 + pytest mock；00 不改业务码 |
| 7 | 机械核对 | 00 | pytest / ruff / graph.py diff 空 / graph-compile / verify PASS |
| 8 | 50 → CLOSE → PR | 00（维护者授权） | Langfuse token 人工项不挡机械关账 |

---

## 交付摘要

- **验证命令**（00 独立重跑）：
  - ruff 触及路径 → 0 · All checks passed
  - pytest 三文件 → 0 · **48 passed**
  - `git diff origin/master -- app/ops/chat/graph.py` → 空
  - `./scripts/graph-compile.sh` → 0
  - `npx @cyning/harness verify --target . --task docs/tasks/active/task_lc_evidence_chain_hardening.md` → VERIFY: PASS
- **变更路径**：见 30 invoke；00 仅 task/reviews/invokes
- **下一棒**：CLOSE: PASS（`--allow-unchecked` 仅 Langfuse 人工项）→ commit → PR 合入 master

### GATE_VERIFY（00 · 派 30 前）

| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---------------|--------------|-----------------|--------|-----------|------------|
| HG-TASK-DRAFT | approved | 00 代签（本会话 orchestrate） | Y | N | Y |
| HG-AUDIT-R1 | approved | 00 代签（20 R1 pass） | Y | Y | Y |
| HG-GRAPH-MODULES | approved | 已 approved（只改备注） | Y | Y | Y |

reviews：`task_lc_evidence_chain_hardening_audit_R1_20260817.md` 存在且 R1 内容 pass？ **是**

pre-30 invoke：`required ∩ {10,20,00}` 齐全？ **是**（有 00、10；required=10,30）

结论：**可派 30**

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-08-17 | 00 开工：读 SPEC / 确认分支 / 起草 10-task |
| 2026-08-17 | 20 R1 pass · 代签闸 · verify PASS · 派 30 |
| 2026-08-17 | 00 机械核对 + 50 PASS；下一棒 CLOSE / PR |
