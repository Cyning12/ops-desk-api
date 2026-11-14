# invoke_50

- **日期**：2026-11-14
- **task_slug**：p0prime-t3-checkpointer-default-on
- **hat**：50
- **动作**：CLOSE 波次——registry entry active→closed 钉 wave_tip=1456f3b（merge commit 1456f3b9 · PR #371）；task 档 git mv → done/ 状态 closed 回填实现备忘/自检/经验
- **验证记录**：干净 worktree（无 .env · detached 645e4f08）全量 1878 passed / 205 skipped / 0 failed（32s）；ruff app+tests 全绿；graph-compile 通过；spec-wave task lint PASS；PR #371 CI 四件全绿
- **偏差如实登记**：① N-R2-1 真 PG 复测本地不可行（docker 停 · 无本地 PG），待首个 PG 环境执行，已列 task 单验收偏差并将登记 issue #23；② 主仓 .env 残留（OPS_HITL_PERSISTENCE=db · OPS_CAPABILITY_ALLOW_WRITE_TAGS=testing 等）致本地 hitl 9 件红，经 env 覆盖重跑（45 passed）+ 干净 worktree 双重对照证实非 T3 diff 引入；③ 灰度三步 ②③（生产单副本翻转+观察 1 周）属运营侧动作，不在本卡交付面
