# Invoke · 50 帽 · CLOSE 收口（fix-seen-surface-idempotency）

| 字段 | 值 |
|------|-----|
| hat_id | `50`（close · 关账棒 · 纯文档轨零业务码） |
| task_slug | `fix-seen-surface-idempotency` |
| task_paths | ~~`docs/tasks/active/task_fix_seen_surface_idempotency.md`~~ → `docs/tasks/done/task_fix_seen_surface_idempotency.md`（已归档） |
| related_review_or_none | `docs/tasks/close/close_fix_seen_surface_idempotency_20261106.md`（CLOSE 档） |
| git_branch | `close/seen-surface-idempotency` |
| created_utc_or_local | 2026-11-06 |
| notes | 关账依据链：issue #335 `6668554143`（立项令）→ PR #345 review `5792245814`（四闸签认 + 决策点②）→ `6669768156`（30 授权六条件 + 决策点①委派裁决）→ PR #346 merge `6daccb1`（30 验收）→ `6670686601`（40 复跑销项令）→ 40 invoke 机制面 PASS → 本棒按既定收口执行；#335 关 issue 由维护者执行（bot 不 close issue） |

---

## §1 · 关账摘要

- **40 结论定格**：机制面 PASS——独立复跑全绿（新测 3 / 关联 119 / 全量 2068 零新增红 · worktree `/tmp/verify40-seen` @ `6daccb1`）· 红线对拍零命中 · verify PASS；偏差①（live 面令界未跑）②（worktree 无 .env 墙钟拉长 · 环境性）如实登记
- **收口产物**：task 档 active→done 归档（状态 done + 40 注 + 验收全勾选 + hat 40 自检回填）· CLOSE 档 · active/README 关账行 · done/README 补登 · 40/50 invoke 落档
- **零码改动**：本棒纯文档（git mv + CLOSE 档 + invoke ×2 + 双 README）

## §2 · 验证

| 命令 | 退出码 | 摘要 |
|------|--------|------|
| `npx spec-wave task lint --file docs/tasks/done/task_fix_seen_surface_idempotency.md` | 0 | LINT: PASS（归档后路径复跑） |
| `npx spec-wave verify --target . --task docs/tasks/done/task_fix_seen_surface_idempotency.md` | 0 | VERIFY: PASS（四闸 approved · 归档后路径） |
| `git diff origin/master...HEAD --stat`（关账棒） | 0 | 仅文档面（task 档迁移 + CLOSE 档 + 40/50 invoke + 双 README）· 零 `app/` diff |

## §3 · 终态

- **issue #335**：待维护者关 issue（bot 不 close issue · 已声明）
- **后续跟踪**：无另波（#339 planner-args 已有独立 issue 跟踪 · 非本 task 产物）；live 面补验如维护者需要建议另窗（预备 #339 口径）
- **评审署名登记**：PR #345 review `5792245814` / PR #346 lead 验收均因 merge 先于署名改写，未署名（按规不 rewrite 已合并 PR · 记录在 CLOSE 档 §五）
- 分支 `fix/seen-surface-idempotency` / `close/seen-surface-idempotency` / `agent/idempotency-fix-task-4b3782da80c4` 移交清理

---

### 修订

| 日期 | 说明 |
|------|-----|
| 2026-11-06 | 50 关账棒 invoke 落档（40 机制面 PASS 定格 + 收口产物清单 + 零码改动验证） |
