# Invoke：30 执行编码 · overview-metrics

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 30（含 40 自检闭环） |
| task_slug | `overview-metrics` |
| freeze_id | — |
| task_paths | `docs/tasks/active/task_overview_metrics.md` |
| related_review_or_none | 无 |
| git_branch | `task/overview-metrics` |
| worktree_root | — |
| created_utc_or_local | 2026-07-24 |
| notes | 用户批准：补 first_review_at 列 + snake_case + 不包外壳 |

---

## 可复制 Prompt 快照

```text
## 30 开工（签闸后 · 须 GATE_VERIFY）

@docs/tasks/active/task_overview_metrics.md
@docs/harness/prompts/30-execute-code.md
@docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md
@docs/_tech_graph/01_struct.md

【开工前】
1. 首输出 FRAGMENT_30_gate_verify 闸扫描表（读 task 人工闸表，比对用户声称）
2. 仅当 HG-AUDIT-R1=approved（task 表）→ 可改码

【实现】
- 分支：task/overview-metrics · 仅 task 所列路径
- 范围：Alembic migration first_review_at、overview 指标实现
  （cycle/review median、throughput、trend、sync、scan）、测试
- test_strategy: required → 先红后绿

【Verify】
- pytest tests · ruff check app tests · ./scripts/graph-compile.sh
```

---

## 交付摘要（本帽结束时填）

- **验证命令**：`pytest tests`（84 passed）· `ruff check app tests scripts`（绿）· `./scripts/graph-compile.sh`（绿）· `alembic upgrade head`（dev 库已应用）
- **变更路径**：`app/ops/overview.py`、`app/db/models.py`（+first_review_at）、`alembic/versions/20260724_pr_first_review_at.py`、`tests/test_overview.py`、`tests/conftest.py`、`tests/test_import_from_supabase.py`（tz 断言）、`docs/_tech_graph/01_struct.md`
- **范围追加（验证阶段发现）**：`clean_sync_data` fixture 全表清空会删 dev 库真实导入数据 → tests 整体隔离到独立 `opsdesk_test` 库（conftest 自动建库 + create_all + settings 就地改写）
- **已知项**：模型/DDL tz 漂移（部分列 DDL 为 timestamptz、模型为 timestamp）——`_median_days` 已归一化，漂移对齐留后续任务
- **下一棒**：CLOSE；维护者重跑导入恢复 dev 数据并抽查 overview 非空指标

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-07-24 | 30 执行 + 40 自检完成落盘 |
