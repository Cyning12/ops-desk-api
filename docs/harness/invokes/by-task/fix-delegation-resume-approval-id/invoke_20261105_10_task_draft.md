# Invoke · 10 帽 · task 起草（fix-delegation-resume-approval-id）

| 字段 | 值 |
|------|-----|
| hat_id | `10`（task/文档 · 起草棒 · 纯文档轨零业务码） |
| task_slug | `fix-delegation-resume-approval-id` |
| task_paths | `docs/tasks/active/task_fix_delegation_resume_approval_id.md` |
| related_review_or_none | `none`（20-R1 审查文落盘 `docs/harness/reviews/task_fix_delegation_resume_approval_id_audit_R1_20261106.md`） |
| git_branch | `agent/approval-id-fix-task-be209a5f60c8`（10 起草 PR 分支 · PR #341 · 30 用 `fix/delegation-resume-approval-id`） |
| created_utc_or_local | 2026-11-05 |
| notes | 维护者 issue #334 comment `6662721599` 令按 Harness 流程起草 fix task（**10 帽活**）；授权边界：只产 task 档 + lint PASS + PR——30 改码须待 task 人工闸签收后另行授权 |

---

## §1 · 起草摘要

- **task 档**：`docs/tasks/active/task_fix_delegation_resume_approval_id.md`（10 起草壳 · 零 `app/` / `tests/` diff · PR #341 · squash `c162d1d`）
- **缺陷源**：issue #334（backlog）——delegation 路径 resume 时未对称清理 approval_id，与主路径语义不齐（来源 #323 stage-w 40 invoke 实测证据链 `docs/harness/invokes/by-task/stage-w-write-expand/`）
- **起草内容**：设计闸 HG-DELEGATION-RESUME-APPROVAL-ID-DESIGN 两决策点（①清理落点三案：A `_apply_hitl_decision` 统一应用点=倾向 / B delegation 消费侧局部 / C 单据面写回=禁；②resume 单路径兼容性）· 维护者四红线入 failure_paths（resume 单路径 / SSE 事件表零 diff / 消费门 fail-closed 永不放宽 / 改码面收敛）· 红测负样本（delegation resume 后 approval_id 已清 · 端到端断言）入 test_strategy · R0–R5 全轮 · 10 钉死契约五条
- **四闸**：HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES（none 口径签认）/ HG-DELEGATION-RESUME-APPROVAL-ID-DESIGN 全 pending · NO-GO 20/30 · 30 待闸签收后另行授权

## §2 · 验证

| 命令 | 退出码 | 摘要 |
|------|--------|------|
| `npx spec-wave task lint --file docs/tasks/active/task_fix_delegation_resume_approval_id.md` | 0 | LINT: PASS（2026-11-05 · 起草棒） |
| `npx spec-wave verify --target . --task docs/tasks/active/task_fix_delegation_resume_approval_id.md` | 2 | VERIFY: BLOCKED（四闸 pending · 设计停点 · 与 NO-GO 20/30 一致） |
| `ruff check app tests` | 1 | 13 枚 master 既有基线红（UP038/UP007 · 非本档引入 · 零新增） |
| CI（PR #341 @ 4ee71a3） | — | 4/4 绿（check / import-linter / lint-wiki-delta / pytest） |

## §3 · 下一棒

`20-R1` 书面审（审查文落盘 `docs/harness/reviews/`）→ 维护者签 HG-DELEGATION-RESUME-APPROVAL-ID-DESIGN + 三常闸 → PR 出货待审 → **30 待闸签收后另行授权**（issue #334 维护者令）→ 40 → CLOSE

---

### 修订

| 日期 | 说明 |
|------|------|
| 2026-11-05 | 10 起草棒 invoke 落档 |
| 2026-11-06 | **四闸签认 + 30 授权**：lead PR #341 review `5789202776` 审查通过并签认四闸 approved（设计闸裁决=案 A 路径 · 对称清理单点落 nodes.py :2162+:2177 · 一次 cleanup 主/委/审三态收敛 · 兼容语义显性化零行为变化）· issue #334 comment `6664735511` 30 授权（六交付条件入 task 档修订表）· PR #341 验收合并（`c162d1d`）· 30 棒 invoke 另落 `invoke_20261106_30_implement.md` |
