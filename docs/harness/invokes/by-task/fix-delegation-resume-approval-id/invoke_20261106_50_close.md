# Invoke · 50 帽 · CLOSE 收口（fix-delegation-resume-approval-id）

| 字段 | 值 |
|------|-----|
| hat_id | `50`（close · 关账棒 · 纯文档轨零业务码） |
| task_slug | `fix-delegation-resume-approval-id` |
| task_paths | ~~`docs/tasks/active/task_fix_delegation_resume_approval_id.md`~~ → `docs/tasks/done/task_fix_delegation_resume_approval_id.md`（已归档） |
| related_review_or_none | `docs/tasks/close/close_fix_delegation_resume_approval_id_20261106.md`（CLOSE 档） |
| git_branch | `close/approval-id-fix-task-be209a5f60c8` |
| created_utc_or_local | 2026-11-06 |
| notes | 关账依据链：issue #334 `6664735511`（30 授权六条件）→ `6665660681`（锚点修正裁定 + 第七条）→ PR #343 review `5790425462`（lead 验收七条件全过 APPROVED）→ issue #334 `6666638933`（40 复跑销项令 · #339 偏差口径）→ 40 invoke 机制面 PASS → 本棒按既定收口执行；#334 关 issue 由维护者执行（bot 不 close issue） |

---

## §1 · 关账摘要

- **40 结论定格**：机制面 PASS——live delegation on 全链**单消费实证**（签发门唯一台账 `delegation_approval_consumed{request_id=hitl_78f72333…}` · 写闸同 id 零 `capability_write_approval_consumed` · token issued/verified · 执行触达 · run `eedd75f3…`）· 全量 2065 passed 零新增红 · 红线零破；偏差①（模型层空规划 · 切 V4-Pro 即成功）②（真落笔 planner string-args）如实登记
- **收口产物**：task 档 active→done 归档（状态 done + 40 注 + 验收全勾选 + 自检回填）· CLOSE 档 · active/README 关账行 · done/README 补登 · 40/50 invoke 落档
- **零码改动**：本棒纯文档（git mv + 4 文档文件）

## §2 · 验证

| 命令 | 退出码 | 摘要 |
|------|--------|------|
| `npx spec-wave task lint --file docs/tasks/done/task_fix_delegation_resume_approval_id.md` | 0 | LINT: PASS（归档后路径复跑） |
| `git diff origin/master...HEAD --stat`（关账棒） | 0 | 仅文档面（task 档迁移 + CLOSE 档 + 40/50 invoke + 双 README）· 零 `app/` diff |

## §3 · 终态

- **issue #334**：待维护者关 issue（bot 不 close issue · 已声明）
- **后续跟踪**：supervisor planner args 文档化 → issue #339（另波立项 · 同源 stage-w 40 观察③ · 偏差②销项）
- **评审署名登记**：PR #343 lead（Cyning12）approval review `5790425462` 因 merge 先于署名改写，未署名（按规不 rewrite 已合并 PR · 记录在 CLOSE 档 §五）
- 分支 `fix/approval-id-fix-task-be209a5f60c8` / `close/approval-id-fix-task-be209a5f60c8` / `agent/approval-id-fix-task-be209a5f60c8` 移交清理

---

### 修订

| 日期 | 说明 |
|------|------|
| 2026-11-06 | 50 关账棒 invoke 落档 |
