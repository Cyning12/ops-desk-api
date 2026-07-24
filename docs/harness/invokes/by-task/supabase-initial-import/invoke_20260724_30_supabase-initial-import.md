# Invoke：30 执行编码 · supabase-initial-import

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 30（含 40 自检闭环） |
| task_slug | `supabase-initial-import` |
| freeze_id | — |
| task_paths | `docs/tasks/active/task_supabase_initial_import.md` |
| related_review_or_none | 无 |
| git_branch | `task/supabase-initial-import` |
| worktree_root | — |
| created_utc_or_local | 2026-07-24 |
| notes | 用户批准：直连 Supabase；范围 repos/issues/PRs/sync_runs/scan/graph |

---

## 可复制 Prompt 快照

```text
## 30 开工（签闸后 · 须 GATE_VERIFY）

@docs/tasks/active/task_supabase_initial_import.md
@docs/harness/prompts/30-execute-code.md
@docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md
@docs/_tech_graph/01_struct.md

【开工前】
1. 首输出 FRAGMENT_30_gate_verify 闸扫描表（读 task 人工闸表，比对用户声称）
2. 仅当 HG-AUDIT-R1=approved（task 表）→ 可改码

【实现】
- 分支：task/supabase-initial-import · 仅 task 所列路径
- 范围：scripts/import_from_supabase.py、列映射与 schema 探测、
  幂等 upsert（保留源 UUID + repo 冲突 remap）、--dry-run/--only/--batch-size、
  .env.example、docs/ops/supabase-import-guide.md、测试
- test_strategy: required → 先红后绿

【Verify】
- pytest tests · ruff check app tests scripts · ./scripts/graph-compile.sh
- 未设置 SUPABASE_DATABASE_URL → exit 2
```

---

## 交付摘要（本帽结束时填）

- **验证命令**：`pytest tests`（77 passed，含 6 个新增用例）· `ruff check app tests scripts`（绿）· `./scripts/graph-compile.sh`（绿）· 无 DSN 运行 exit 2（实测）
- **变更路径**：`scripts/import_from_supabase.py`（新增）、`tests/test_import_from_supabase.py`（新增）、`docs/ops/supabase-import-guide.md`（新增）、`.env.example`、`scripts/create_initial_user.py` / `scripts/graph_yaml_to_json.py`（ruff --fix 顺带清理）
- **测试设计**：scratch 数据库 `opsdesk_src` 模拟 Supabase 源（含 timestamptz、多余列、NULL JSONB）；覆盖 roundtrip、幂等二次执行、repo 冲突 remap、dry-run 不写
- **下一棒**：CLOSE（`harness task close`）；真实 Supabase 导入由维护者按指引文档执行验收

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-07-24 | 30 执行 + 40 自检完成落盘 |
