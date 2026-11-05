# Invoke · 10 帽 · task 起草（fix-worker-state-send-run-id）

| 字段 | 值 |
|------|-----|
| hat_id | `10`（task/文档 · 起草棒 · 纯文档轨零业务码） |
| task_slug | `fix-worker-state-send-run-id` |
| task_paths | `docs/tasks/active/task_fix_worker_state_send_run_id.md` |
| related_review_or_none | `none`（20-R1 审查文下一棒落盘 `docs/harness/reviews/task_fix_worker_state_send_run_id_audit_R1_*.md`） |
| git_branch | `agent/run-id-fix-task-cdc1b46e15dc`（10 起草 PR 分支 · 30 用 `fix/worker-state-send-run-id`） |
| created_utc_or_local | 2026-11-05 |
| notes | 维护者 issue #329 comment `6658235851` 令按 Harness 流程起草 fix task（**10 帽活**）；授权边界：只产 task 档 + 10 invoke + `npx spec-wave task lint` PASS + PR——30 改码须待 task 人工闸签收后另行授权 |

---

## §1 · 起草摘要

- **task 档**：`docs/tasks/active/task_fix_worker_state_send_run_id.md`（10 起草壳 · 零 `app/` / `tests/` diff）
- **缺陷源**：issue #329 + 40 invoke 偏差登记①（`stage-w-write-expand/invoke_20261105_40_verify.md` §5）——`_worker_state`（nodes.py:1359）Send 载荷不含 `run_id` → tool_exec 写消费门 `_run_id_of(state)` 空串 fail-closed → HITL resume 后重下发永远再拦；PR #303 时期潜伏 · 非 #327 回归；shim 补位后 live 八段全通（修复形态已验证）
- **起草内容**：设计闸 HG-WORKER-STATE-RUN-ID-DESIGN 两决策点（①修复落点三案：A `_worker_state` 补键=推荐 / B `route_next_subtask` 无条件补 / C 消费门放宽=禁；②回归影响面：delegation 已有 run_id 兼容 + 旧测适配口径）· 维护者四红线入 failure_paths（SSE 事件表零 diff / hitl 消费语义 freeze 不动 / resume 单路径 / 消费门 fail-closed 永不放宽）· 红测负样本（真派发路径 · resume 后重下发不再被拦 · 真落笔断言）入 test_strategy · R0–R5 全轮 · 10 钉死契约五条
- **四闸**：HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES（none 口径签认）/ HG-WORKER-STATE-RUN-ID-DESIGN 全 pending · NO-GO 20/30 · 30 待闸签收后另行授权

## §2 · 验证

| 命令 | 退出码 | 摘要 |
|------|--------|------|
| `npx spec-wave task lint --file docs/tasks/active/task_fix_worker_state_send_run_id.md` | 0 | LINT: PASS（2026-11-05 · 起草棒 · 零 warn） |
| `npx spec-wave verify --target . --task docs/tasks/active/task_fix_worker_state_send_run_id.md` | 0 | VERIFY: BLOCKED（HG-AUDIT-R1 pending · 四闸全 pending · 设计停点 · 与 NO-GO 20/30 一致） |
| `git diff master...HEAD --stat`（起草棒） | 0 | 仅 task 档 + invoke · 零 `app/` diff |

## §3 · 下一棒

`20-R1` 书面审（审查文落盘 `docs/harness/reviews/` · 零阻塞须写明核对项）→ 维护者签 HG-WORKER-STATE-RUN-ID-DESIGN 两决策点 + 三常闸 → PR 出货待审 → **30 待闸签收后另行授权**（issue #329 维护者令）→ 40 → CLOSE

---

### 修订

| 日期 | 说明 |
|------|------|
| 2026-11-05 | 10 起草棒 invoke 落档 |
