# invoke · 50_close · p1-t3-goal-inject

- 时刻：2026-11-15 · 关账（wave_tip 3bd7ae50 · PR #393 CI 四绿）
- 关账人：本窗口（维护者 m02028「本窗口任务继续」授权）

## 验证台账

| 项 | 证据 |
|----|------|
| 目标测试 | tests/test_goal_inject.py 9 件真 PG 绿（本地 + CI 真跑） |
| 回归 | test_goal_store/input_isolation_wiring/prompt_slots/splittability/session_continuity/memory_injection(+consumer) 120 passed 1 skipped |
| CI | PR #393 四绿（rebase 到 #392 合并尖后重跑 2m35s pass） |
| 合并尖全量 | 干净 worktree（3bd7ae50）2116 passed / 2 skipped / 0 failed（41s） |
| off 态逐字节 | test_goal_inject.py off 双态对拍 + goal_store 调用计数=0 断言 |

## 偏差登记（三件）

1. ruff I001（continuity.py asyncio 导入序）——commit 前 ruff --fix 修复。教训承 T2 关账：commit 前 ruff 必跑。
2. test_prompt_slots::test_registry_covers_six_slots 红——六槽白名单断言按 07 §2 设计扩为七槽（goal_objective），改名 test_registry_covers_seven_slots；registry allowed_tree_files 同步补该文件。
3. **rebase 冲突修复事故**：与 #392 在 registry.yaml/01_modules.md 同区冲突，正则 union 清理时未料 git 冲突尾标为 `>>>>>>> <sha> (subject)` 带提交主题后缀，裸 `>>>>>>> <sha>` 正则失配 → registry.yaml 截断损坏（rebase --continue 在 python 校验失败的 && 链中仍被执行提交）+ 01_modules.md 残留垃圾行。修复=放弃正则 union，registry 从 origin/master 版 + 3dcad389 版 entry 块确定性重建。教训：rebase 冲突手工解，每步 && 链遇校验失败立即停（或分步跑）。

## 结论

验收 8 条全过：GOAL_INJECT_ENABLED 默认 off 逐字节+零调用 · on 态仅 active 单条头插 · ≤300ms 降级 span 分立 · importlib 守 lg-rag-outbound · slots 七槽+guide 扩展+_FORGE_ESCAPES · 归因分支置 memory 前 · 零图改动/零新 SSE 帧。P1-T4（入口接线 + uq 索引）依赖面已就绪。
