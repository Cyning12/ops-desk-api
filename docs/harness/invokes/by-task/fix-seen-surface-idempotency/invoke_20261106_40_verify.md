# Invoke · 40 帽 · 复跑销项（fix-seen-surface-idempotency）

| 项 | 内容 |
|----|------|
| **帽** | 40-verify · **日期** 2026-11-06 |
| **task** | `docs/tasks/done/task_fix_seen_surface_idempotency.md`（40 后归档 · 本 invoke 随关账 PR 落盘） |
| **分支** | `close/seen-surface-idempotency`（reset 自 origin/master `6daccb1` = PR #346 squash 合入点 · 40 全程零仓内码改动 · 独立复跑在 `/tmp/verify40-seen` worktree @ `6daccb1`） |
| **核验对象** | PR #346 全量 diff（`git diff ec87535..6daccb1` · 码面 3 文件）+ 负样本对拍独立复跑 + 关联回归 + 全量零新增红 |
| **依据** | issue #335 维护者 comment `6670686601`（40 复跑销项令 · 签收窗口至 2026-11-06 07:00 · 全绿则关账 · #339 偏差口径预留） |
| **结论** | **机制面 PASS**：独立复跑全绿（新测 3 / 关联 119 / 全量 2068 passed · 4 failed = 既有基线同形零新增红）· 红线对拍零命中 · verify PASS——偏差①live 面本次令未含未跑 · ②worktree 无 .env 墙钟拉长（环境性）如实登记 |

---

## 1. 闸态 verify（`6daccb1` 实跑）✅

`npx spec-wave verify --target . --task docs/tasks/done/task_fix_seen_surface_idempotency.md` → **VERIFY: PASS** · 四闸 approved。

## 2. 红线对拍（`git diff ec87535..6daccb1`）✅

- delta 码面恰 3 文件：`nodes.py`（巡检层守卫 `_write_blocked_call_keys` + 建单层守卫 `_write_intent_live_key` + 迁附带回分支 · +151/-1）· `hitl/store.py`（`arelocate_linkage` · +75/-0）· 新测 `test_fix_seen_surface_idempotency.py`（3 枚）——全落 30 交付面；
- **红线零命中**：消费门（`_approval_consumed`/`_write_execution_approval`/`_match_fresh_approved`）· resume 单路径（`router.py`/`resume.py`）· SSE（`event_store`/`sse_*`）· worker freeze（`run_worker.py`）· 委派令牌 · auto-resume · HITL 表结构 全零 diff。

## 3. 测试独立复跑（不采信 30 自报 · `/tmp/verify40-seen` @ `6daccb1`）✅

- **新测 3 枚**：`pytest tests/test_fix_seen_surface_idempotency.py` → **3 passed**（负样本 reset→首轮巡检→恰一笔 + overlap 零新增 / 同 sid 重放 attach 对拍 / 成功孪生 guard-skip 对拍）；
- **关联回归 7 文件**：`pytest test_write_approval_gate test_hitl_approval_consumption test_hitl_approved_replan_quality test_hitl_resume test_fix_delegation_resume_approval_id test_fix_worker_state_send_run_id test_stage_w_write_expand` → **119 passed**（零适配）；
- **全量**：`pytest tests` → **2068 passed · 4 failed**——4 failed 与 merge 前分支及 master 基线逐枚同形（`test_lg_rag_write_replay_guard::test_tc8_diff_whitelist` / `test_strategy_scenario::test_diff_whitelist_scenario_stage_rewire` / `test_memory_vector_p1::test_embedder_failure_degrades_with_marker` / `test_multi_replica_dualproc::test_hitl_cross_instance_resume` · diff-whitelist ×2 / embedder env ×1 / dualproc env ×1）· **零新增红**；
- `ruff check app tests` 零新增（30 自检已 All checks passed · 40 零码改动不复跑）· `./scripts/graph-compile.sh` EXIT=0（30 自检 · 40 零图谱面）。

## 4. 偏差登记

- **偏差①（live 面未跑 · 令界口径）**：维护者 40 令（`6670686601`）明确范围 = 独立复跑对拍 + 关联回归 + 全量零新增红确认，未含 live 要求 → live 实测未执行；机制面（负样本对拍 + 全量双证）销项。若后续补 live 撞 #339 planner-args 已知缺陷，按 #329/#334 同口径：机制面 PASS + 偏差如实登记，不静默修。
- **偏差②（环境性墙钟）**：40 worktree 无 `.env`，全量套件中网络型用例走真实超时路径，墙钟较主 checkout 显著拉长（套件自身 75s · 总时长受 env 解析影响）——环境性非仓码语义，不影响结果判定。

## 给维护者的裁定建议

1. **40 机制面 PASS 可 CLOSE**（关账 PR 待 lead 窗口内验收）；task 档移 `docs/tasks/done/` 按仓内既定收口；
2. issue #335 关 issue 由维护者执行；
3. live 面如需补验（worker 重启后首轮巡检单拉起实测），建议另窗执行并预备 #339 偏差口径。

---

### 修订

| 日期 | 说明 |
|------|-----|
| 2026-11-06 | 40 核验落盘：verify 闸态 / 红线对拍 / 独立复跑三阶实录 / 偏差①②登记 / 机制面 PASS 结论 |
