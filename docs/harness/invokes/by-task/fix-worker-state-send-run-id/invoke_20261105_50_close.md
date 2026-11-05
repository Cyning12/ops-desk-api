# Invoke · 50 帽 · CLOSE 收口（fix-worker-state-send-run-id）

| 字段 | 值 |
|------|-----|
| hat_id | `50`（close · 关账棒 · 纯文档轨零业务码） |
| task_slug | `fix-worker-state-send-run-id` |
| task_paths | ~~`docs/tasks/active/task_fix_worker_state_send_run_id.md`~~ → `docs/tasks/done/task_fix_worker_state_send_run_id.md`（已归档） |
| related_review_or_none | `docs/tasks/close/close_fix_worker_state_send_run_id_20261105.md`（CLOSE 档） |
| git_branch | `close/worker-state-send-run-id` |
| created_utc_or_local | 2026-11-05 |
| notes | 关账依据链：issue #329 `6660516133`（40 复跑令）→ 40 invoke 机制面 PASS + 偏差②停下报 → issue #329 `6661645452`（**维护者裁定 (a) 按机制面 PASS 关账 · planner args 另波 #339**）→ 本棒按既定收口执行；#329 关 issue 由维护者执行（bot 不 close issue） |

---

## §1 · 关账摘要

- **40 结论定格**：机制面 PASS（live 免 shim 消费闭环 ×2 实证 · 全量 2063 passed 零新增红 · 红线零破）——stage-w 40 偏差登记①实质销项；偏差②（真落笔 · planner string-args · 预存在非本链）维护者裁定另波跟踪（issue #339）
- **收口产物**：task 档 active→done 归档（验收标准全勾选 + 状态 done + 裁定修订行）· CLOSE 档 · active/README 关账行 · done/README engineering 补登 · 40 invoke 偏差②/裁定回执回填（偏差编号对齐裁定）
- **零码改动**：本棒纯文档（git mv + 4 文档文件）

## §2 · 验证

| 命令 | 退出码 | 摘要 |
|------|--------|------|
| `npx spec-wave task lint --file docs/tasks/done/task_fix_worker_state_send_run_id.md` | 0 | LINT: PASS（归档后路径复跑） |
| `git diff master...HEAD --stat`（关账棒） | 0 | 仅文档面（task 档迁移 + CLOSE 档 + 双 README + 40/50 invoke）· 零 `app/` diff |

## §3 · 终态

- **issue #329**：待维护者关 issue（bot 不 close issue · 已声明）
- **后续跟踪**：supervisor planner args 文档化 → issue #339（另波立项 · 同源 stage-w 40 观察③）
- 分支 `fix/worker-state-send-run-id` / `close/worker-state-send-run-id` / `agent/run-id-fix-task-cdc1b46e15dc` 移交清理

---

### 修订

| 日期 | 说明 |
|------|------|
| 2026-11-05 | 50 关账棒 invoke 落档 |
