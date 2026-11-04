# Invoke · 40 帽 · 独立验收（fix-hitl-decide-owner-fallback）

| 字段 | 值 |
|------|-----|
| hat_id | `40`（独立验收棒 · 合并后复验） |
| task_slug | `fix-hitl-decide-owner-fallback` |
| task_paths | `docs/tasks/active/task_fix_hitl_decide_owner_fallback.md` |
| related_review_or_none | PR #319 lead 终审 APPROVED（review 5763950599 · 全程委托验收决策授权 = issue #315 评论 #6623253310） |
| git_branch | `fix/decide-fallback-task-c2838ef4cc6f`（40 证据档 · base `master` @ `9c0bc68` = PR #319 merge） |
| created_utc_or_local | 2026-11-04 |
| notes | lead 令「合并后执行 40 独立验收 invoke（task 档要求），证据回填本 PR 线程」· 本棒在**合并后 master** 上独立复验（非分支自验） |

---

## §1 · 验收范围（task 档验收标准逐条）

| # | 验收项 | 结果 | 证据 |
|---|--------|------|------|
| 1 | 人工闸四闸 approved | ✅ | verify 闸表全 approved（本棒复跑） |
| 2 | 红测负样本①（红线）：sync invoke 写闸 → decide 不再 404（approved/rejected） | ✅ | `test_decide_frameless_run_falls_back_to_thread_owner_approved/rejected` + pending 同源可见（合并后 master 复跑绿） |
| 3 | 负样本②：thread 属主他人 → 仍 404 不越权 | ✅ | `test_decide_frameless_thread_owned_by_other_still_404` |
| 4 | 负样本③：thread 行缺失 → 仍 404 + error 日志 | ✅ | `test_decide_frameless_no_thread_row_still_404_fail_closed` |
| 5 | 正样本：有帧 run 零变化（绝不走兜底 · mock 断言） | ✅ | `test_decide_framed_run_never_uses_thread_fallback` |
| 6 | 码面锚点：兜底仅兜 `run_owner` 返 None 一路 · SSE 事件写入面零 diff · freeze 两文件零 diff | ✅ | merge diff（`3075f66..9c0bc68`）仅 7 文件：`hitl/router.py`（helper 兜底分支）+ `lg_rag/thread_store.py`（`thread_owner` 只读）+ 测试 + RUNBOOK + 图谱 + task/invoke 档；**`event_store.py` 与 freeze 文件均不在 diff 面** |
| 7 | RUNBOOK §1.7 与码面一致 + docstring 同步 | ✅ | §1.7 五声明（不补帧/末位兜底/decide 可达/sink=None 无 replay 面/排障锚）逐条对拍 `router.py _run_owner_of` 与 `:488-489` 现状一致 |
| 8 | ruff 绿 + pytest 目标组绿 | ✅ | ruff 0.15.21 All checks passed · 合并后 master `pytest tests/test_hitl_decide_owner_fallback.py tests/test_hitl_pending_decide.py` → 29 passed |
| 9 | graph-compile 绿 · 不新增 G-L1 一级模块 | ✅ | 30 棒 EXIT=0 · hitl 行备注追加（模块数不变） |
| 10 | spec-wave task lint PASS | ✅ | 本棒复跑 LINT: PASS |

## §2 · 合并后独立复验命令（master @ 9c0bc68）

| 命令 | 退出码 | 摘要 |
|------|--------|------|
| `npx spec-wave verify --target . --task docs/tasks/active/task_fix_hitl_decide_owner_fallback.md` | 0 | VERIFY: PASS（四闸 approved · 图谱锚点 vocabulary_empty 跳过照登） |
| `npx spec-wave task lint --file docs/tasks/active/task_fix_hitl_decide_owner_fallback.md` | 0 | LINT: PASS |
| `pytest tests/test_hitl_decide_owner_fallback.py tests/test_hitl_pending_decide.py`（合并后 master worktree） | 0 | 29 passed |
| `ruff check app/ops/hitl/router.py app/ops/lg_rag/thread_store.py`（0.15.21） | 0 | All checks passed |
| `git diff 3075f66..9c0bc68 --stat` | 0 | 7 文件 +419/-3 · event_store/freeze 零面 |

## §3 · 结论

**40 独立验收 PASS**（合并后 master 复验 · 十项全过 · 零偏差）。issue #315 修复链闭环：10 起草 → 20-R1 → 30 实现（PR #319 MERGED `9c0bc68` · CI 4/4 绿）→ 40 本棒。

**留档**：①PR #317/#319 的 lead（Cyning12）approval 因 PR 已合均未补 Co-authored-by 署名（按规则不 rewrite 已合 PR）。②active→done 迁档与 CLOSE 文档未在本授权面（lead 令止于 40 + 证据回填），待维护者/lead 另行决策。

---

### 修订

| 日期 | 说明 |
|------|------|
| 2026-11-04 | 40 独立验收棒 invoke 落档（合并后 master 复验十项全过 · 证据回填 PR #319 线程） |
