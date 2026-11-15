# invoke · 50_close · p1-t1-goal-store

- 时刻：2026-11-15 · 关账（wave_tip 3d6eaecd · PR #387 CI 四绿）
- 关账人：本窗口（维护者 m02028「本窗口任务继续」授权）

## 验证台账

| 项 | 证据 |
|----|------|
| 目标测试 | tests/test_goal_store.py 6 件真 PG 绿（本地 + rebase 后 CI 真跑 2m10s pass） |
| CI | PR #387 四绿（rebase 到 #386 合并尖后重跑 · DB 用例真跑） |
| 无新迁移 | ORM __table_args__ 索引名逐字对齐既有迁移（07 §5 T1 行裁定） |

## 偏差登记（两件）

1. **事故**：worktree .venv 符号链接被 git add -A 提交（.gitignore `.venv/` 尾斜杠只挡目录不挡符号链接）→ CI uv venv「File exists」→ fix commit 摘除。教训：worktree 建符号链接后立即 git status 核对面。
2. **rebase 同区冲突**：registry.yaml 与 #386 entry 同区（保留双 entry 解）——同 ta2/T2b 教训复现。

## 结论

验收 6 条全过；P1-T2（continuity 注入槽位）依赖本模块，可派单。
