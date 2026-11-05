# Invoke · 10 帽 · task 起草（fix-seen-surface-idempotency）

| 字段 | 值 |
|------|-----|
| hat_id | `10`（task/文档 · 起草棒 · 纯文档轨零业务码） |
| task_slug | `fix-seen-surface-idempotency` |
| task_paths | `docs/tasks/active/task_fix_seen_surface_idempotency.md` |
| related_review_or_none | `none`（20-R1 审查文落盘 `docs/harness/reviews/task_fix_seen_surface_idempotency_audit_R1_<日期>.md`） |
| git_branch | `agent/idempotency-fix-task-4b3782da80c4`（10 起草 PR 分支 · 部署绑定末段=工单名 · 30 预登记 `fix/seen-surface-idempotency`） |
| created_utc_or_local | 2026-11-06 |
| notes | 维护者 issue #335 comment `6668554143` 令按 Harness 流程起草 fix task（**10 帽活**）；授权边界：只产 task 档 + 10 invoke + lint PASS + PR——30 改码须待 task 人工闸签收后另行授权；受理依据 = 窗口授权 2026-11-05 22:26 → 2026-11-06 07:00（lead 代行签收与验收） |

---

## §1 · 起草摘要

- **task 档**：`docs/tasks/active/task_fix_seen_surface_idempotency.md`（10 起草壳 · 零 `app/` / `tests/` diff）
- **缺陷源**：issue #335（backlog）——`reset_worker_seen_surface` 后首次巡检重复拉起存量 write ticket（幂等缺口）；worker 重启后 seen 面重置无幂等守卫，触发 overlap_warning 噪音（来源 #323 stage-w 40 invoke 实测证据链 `docs/harness/invokes/by-task/stage-w-write-expand/`）
- **起草内容**：设计闸 HG-WRITE-TICKET-IDEMPOTENCY-DESIGN 两决策点（①修复落点三案：A 巡检层守卫=倾向 / B 建单拉起层守卫 / C 只压警告=禁；②ticket 幂等键语义 = status/seen_surface 双条件位 · 缺一不可）· 四红线 + worker freeze 不动语义入 failure_paths（FP-2~FP-5 · FP-8）· 红测负样本（reset 后首轮巡检不重复拉起 · 端到端断言）入 test_strategy · R0–R5 全轮 · 10 实扫声明（字面符号零命中 · 承载面留 30 红测探针 · 承 delegation 锚点修正先例）
- **四闸**：HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES（none 口径）/ HG-WRITE-TICKET-IDEMPOTENCY-DESIGN 全 pending · NO-GO 20/30 · 30 待闸签收后另行授权

## §2 · 验证

| 命令 | 退出码 | 摘要 |
|------|--------|------|
| `npx spec-wave task lint --file docs/tasks/active/task_fix_seen_surface_idempotency.md` | 0 | LINT: PASS（2026-11-06 · 起草棒） |
| `npx spec-wave task lint-wiki-delta --target .`（CI 同形预检） | 0 | LINT-WIKI-DELTA: PASS（scanned: 209 · missing: 0 · issues: 0） |
| `npx spec-wave verify --target . --task docs/tasks/active/task_fix_seen_surface_idempotency.md` | 0 | VERIFY: BLOCKED（四闸 pending · HG-AUDIT-R1 / HG-GRAPH-MODULES / HG-WRITE-TICKET-IDEMPOTENCY-DESIGN · 与 NO-GO 20/30 一致 · 设计停点预期语义） |

## §3 · 下一棒

`20-R1` 书面审（审查文落盘 `docs/harness/reviews/`）→ 维护者签 HG-WRITE-TICKET-IDEMPOTENCY-DESIGN + 三常闸 → PR 出货待审 → **30 待闸签收后另行授权**（issue #335 维护者令）→ 40 → CLOSE

---

### 修订

| 日期 | 说明 |
|------|-----|
| 2026-11-06 | 10 起草棒 invoke 落档 |
