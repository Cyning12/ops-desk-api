# Invoke：30 执行编码 · import-null-sync-type（fix）

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 30（含 40 自检闭环） |
| task_slug | `import-null-sync-type` |
| freeze_id | — |
| task_paths | `docs/tasks/active/task_import_null_sync_type.md` |
| related_review_or_none | 无 |
| git_branch | `fix/import-null-sync-type` |
| worktree_root | — |
| created_utc_or_local | 2026-07-24 |
| notes | 紧急修复；用户批准方案：sync_type NULL → "legacy" |

---

## 可复制 Prompt 快照

```text
## 30 开工（fix 分支 · 用户已批准方案）

@docs/tasks/active/task_import_null_sync_type.md
@docs/harness/prompts/30-execute-code.md

【实现】
- 分支：fix/import-null-sync-type
- 范围：scripts/import_from_supabase.py _VALUE_DEFAULTS 机制；
  sync_type NULL → "legacy"；单测 + scratch 源集成断言
- test_strategy: required

【Verify】
- pytest tests · ruff check app tests scripts
```

---

## 交付摘要（本帽结束时填）

- **验证命令**：`pytest tests`（78 passed）· `ruff check app tests scripts`（绿）
- **变更路径**：`scripts/import_from_supabase.py`、`tests/test_import_from_supabase.py`、`docs/tasks/active/task_import_null_sync_type.md`
- **背景**：真实 Supabase 导入 `ops_sync_runs` 因历史行 `sync_type IS NULL` 触发 NotNullViolation 整表回滚；其余 5 表（repos 2 / issues 599 / PRs 1440 / scan 47 / graph 44）已成功导入
- **下一棒**：CLOSE → PR → 用户重跑导入幂等补齐 sync_runs

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-07-24 | 30 执行 + 40 自检完成落盘 |
