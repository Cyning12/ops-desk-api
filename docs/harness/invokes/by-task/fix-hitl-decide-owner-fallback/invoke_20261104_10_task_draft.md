# Invoke · 10 帽 · task 起草（fix-hitl-decide-owner-fallback）

| 字段 | 值 |
|------|-----|
| hat_id | `10`（task/文档 · 起草棒 · 纯文档轨零业务码） |
| task_slug | `fix-hitl-decide-owner-fallback` |
| task_paths | `docs/tasks/active/task_fix_hitl_decide_owner_fallback.md` |
| related_review_or_none | `docs/harness/reviews/task_fix_hitl_decide_owner_fallback_audit_R1_20261104.md`（20-R1 委托自签 · 同 PR 落档） |
| git_branch | `agent/decide-fallback-task-c2838ef4cc6f`（10 起草 PR 分支） |
| created_utc_or_local | 2026-11-04 |
| notes | 维护者 issue #315 评论 #6623212135 令立项（B+C 签认 + 红线）· #6623253310 全程委托自签过程文档；授权边界：只产 task 档 + 20-R1 审查文 + 闸表代录 + lint PASS + PR，30 改码待闸签收后另行授权 |

---

## §1 · 起草摘要

- **task 档**：`docs/tasks/active/task_fix_hitl_decide_owner_fallback.md`（10 起草壳 · 零 `app/` diff）
- **缺陷源**：issue #315——sync invoke 无 run 事件帧 → `_run_owner_of` 返 None → decide 404 → 审批链断（预存在行为 · 非 #313 引入）；实测锚 workspace `invoke_20261104_10_c6_retest.md` §5
- **起草内容**：B+C 签认落地（thread 末位反查兜底 + RUNBOOK 行为差异声明 · 不选 A 留痕）· HG-DECIDE-FALLBACK-DESIGN 三决策点（机制源 / 作用面 / 声明口径）· 维护者双红线入 failure_paths（SSE 事件表零 diff · 负样本「sync invoke→decide 不再 404」）· 红测先行入 test_strategy · R0–R3 思考轮（R3 early_stop）
- **四闸**：pending 起 → 本 PR 第二棒 00 代录 approved（依据 #6623212135 + #6623253310 留痕）→ 出货后 lead 复审决策 merge

## §2 · 验证

| 命令 | 退出码 | 摘要 |
|------|--------|------|
| `npx spec-wave task lint --file docs/tasks/active/task_fix_hitl_decide_owner_fallback.md` | 0 | LINT: PASS（2026-11-04 · 起草棒） |
| `git diff master...HEAD --stat`（起草棒） | 0 | 仅 task 档 + 审查文 + invoke · 零 `app/` diff |

## §3 · 下一棒

`20-R1`（委托自签 · 审查文 `docs/harness/reviews/task_fix_hitl_decide_owner_fallback_audit_R1_20261104.md` 同 PR 落档）→ `00` 代录四闸 approved → PR 出货 → **lead（维护者代理人）复审验收并决策 merge**（#6623253310）→ 30 待另行授权

---

### 修订

| 日期 | 说明 |
|------|------|
| 2026-11-04 | 10 起草棒 invoke 落档 |
