# Invoke · 30 帽 · 实现（fix-hitl-decide-owner-fallback）

| 字段 | 值 |
|------|-----|
| hat_id | `30`（实现棒 · 红测先行） |
| task_slug | `fix-hitl-decide-owner-fallback` |
| task_paths | `docs/tasks/active/task_fix_hitl_decide_owner_fallback.md` |
| related_review_or_none | `docs/harness/reviews/task_fix_hitl_decide_owner_fallback_audit_R1_20261104.md`（20-R1 委托自签 PASS） |
| git_branch | `fix/hitl-decide-owner-fallback`（base `master` @ `3075f666` = PR #317 squash） |
| created_utc_or_local | 2026-11-04 |
| notes | 开工授权 = issue #315 评论 #6623212135（B+C 签认 · 30 待闸签收后另行授权）+ PR #317 lead 验收评论（「merge 后 30 按档开工」· 2026-11-04 MERGED `3075f666`）；GATE_VERIFY 四闸 approved（task 档闸表） |

---

## §1 · 实现摘要

- **红测先行**：`tests/test_hitl_decide_owner_fallback.py` 9 测先红（patch 面缺失 + decide 404 现状）→ 实现后 9/9 绿
  - 负样本①（维护者红线）：无帧 run + thread 属主本人 → decide approved/rejected 均 200 不再 404 · pending 同源可见
  - 负样本②：thread 属主他人 → 仍 404 不越权 · 单据保持 pending
  - 负样本③：thread 行缺失 → 仍 404 + error 日志（fail-closed）
  - 正样本：有帧 run 绝不走兜底（thread_owner mock 断言 not awaited · 事件表第一真源）
  - 降级：兜底反查异常 → 404 不 500 + error 日志
  - DB 亲跑（skipif DB_AVAILABLE）：真 `run_owner`（无帧返 None）+ 真 `OpsLgRagThread` 行 → decide 200；`thread_owner` 缺失行返 None
- **D-fix-1 实现**：`app/ops/hitl/router.py _run_owner_of`——`run_owner` 返 None 时按单据 `thread_id` 末位反查 `lg_rag.thread_store.thread_owner`；异常 catch → None（fail-closed 不变）；docstring 同步声明 · `app/ops/lg_rag/thread_store.py` 增只读 `thread_owner`（零迁移 · 无 ORM 关系映射 → 测试 user/thread 两次独立提交先例）
- **D-fix-2 实现**：`docs/guides/RUNBOOK_hitl_ops_v1_zh.md` 增 §1.7「sync invoke 面 HITL 审批链（行为差异声明）」（不补帧裁定 / 末位兜底口径 / decide 可达 / resume 无 replay 面 / 排障锚）
- **G-L1 图谱**：`docs/_tech_graph/l1/01_modules.md` hitl 行备注追加（不新增一级模块 · 零新跨模块边 · 不增 implementedBy）· `graph-compile.sh` EXIT=0
- **非范围守界**：`_open_event_sink`/resume 链零触碰 · SSE 事件写入面零 diff · freeze 两文件零 diff · 无 schema 迁移

## §2 · 验证

| 命令 | 退出码 | 摘要 |
|------|--------|------|
| `pytest tests/test_hitl_decide_owner_fallback.py` | 0 | 9 passed（红→绿） |
| `pytest tests/test_hitl_pending_decide.py test_hitl_resume*.py test_hitl.py test_hitl_auto_resume.py` | 0 | 124 passed 零回归 |
| `ruff check app/ops/hitl/router.py app/ops/lg_rag/thread_store.py tests/test_hitl_decide_owner_fallback.py` | 0 | All checks passed（ruff 0.15.21） |
| `./scripts/graph-compile.sh` | 0 | 全 flow OK · mermaid normalize check 9 md |
| `pytest tests`（全量） | 见 §3 | 见 §3 |

## §3 · 全量对拍

- **分支全量**：`pytest tests` → 2041 passed · 4 failed · 2 skipped（85s）
- **master 基线对拍**（origin/master `3075f66` worktree 亲跑同 4 件）：同 4 件同败——`test_tc8_diff_whitelist` / `test_embedder_failure_degrades_with_marker` / `test_hitl_cross_instance_resume` / `test_diff_whitelist_scenario_stage_rewire` 全为**既有环境性基线红**（3.8s 同败 · 与 #313 验收时「既有 28 红双口径实证」同族）
- **结论：零新增红** ✅

## §4 · 下一棒

`40`（独立验收 invoke）→ lead 复审验收决策（PR #317 review 令）→ CLOSE

---

### 修订

| 日期 | 说明 |
|------|------|
| 2026-11-04 | 30 实现棒 invoke 落档（红测先行 9→绿 · 124 回归绿 · ruff/graph-compile 绿 · 全量对拍出货前回填） |
