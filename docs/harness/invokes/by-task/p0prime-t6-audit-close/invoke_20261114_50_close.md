# invoke · p0prime-t6-audit-view · 50_close

- 日期：2026-11-14 · 阶段：CLOSE
- 合并：PR #377 squash merge 51b39fe1（CI 四件全绿）
- registry：status=closed · wave_tip=51b39fe
- task 单迁移：docs/tasks/done/task_p0prime_t6_audit_view.md（自检结论/实现备忘已回填）

## 验证台账（承 40 自检结论 8 项）
目标测试 2 passed（真 PG）· scratch 迁移 up/down/up 实证 · task lint PASS · ruff 绿 · 干净 worktree 全量 2090 passed/2 skipped/1 failed（唯一红=既有 ta2）· CI 四件全 pass · 全局红线零触碰。

## 偏差
1. registry.yaml YAML 粘连事件（amend 修复 · 教训：追加后必跑 test_wave_gate_registry）。
2. 时间窗 naive-UTC vs timestamptz 口径注记（测试内锚定，消费侧沿用）。
3. source_id=源表 PK（非 receipt_id）回查口径。
4. 既有红 ta2（test_ta2_ttl_db_store_expired_not_consumed）维持另立 task 跟踪，不随本波。
