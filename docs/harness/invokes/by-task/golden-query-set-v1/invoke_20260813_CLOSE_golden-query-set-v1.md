# Invoke：CLOSE · golden-query-set-v1

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | CLOSE |
| task_slug | `golden-query-set-v1` |
| related_30 | invoke_20260811_30_golden-query-set-v1.md |
| git_branch | `task/golden-query-set-v1` |
| created_utc_or_local | 2026-08-13 |
| notes | 功能已落地；关账前对齐 73 条定稿与 close 机械项 |

---

## CLOSE 结论：**PASS**

### 完成态核对

| 项 | 证据 |
|---|---|
| yaml 条数/象限 | 73 · 26/20/16/11（`evals/golden/queries_v1.yaml`） |
| runner / 卫生 | `evals/golden/run_eval.py` · `hygiene_denylist.yaml` |
| 单测 | `.venv/bin/pytest tests/test_golden_eval_runner.py` → 13 passed |
| 首跑报告 | `reports/r4.yaml`（首跑 71；定稿后下游按 73） |
| 闸 | HG-TASK-DRAFT / HG-AUDIT-R1 approved；minimal → invoke `30` |
| 规模修订 | 初签 71 → G67 双审 cc4f30f → 73 |

### 关账动作

- task 卡：状态 `completed` · `## 验收标准` · `### 自检结论` · `### KPI` · `graph_delta_note`
- 文件名对齐 slug：`task_golden-query-set-v1.md`（避免 harness 剥 `_v1`）
- `npx @cyning/harness task close --file docs/tasks/active/task_golden-query-set-v1.md --yes`
- 归档 → `docs/tasks/done/task_golden-query-set-v1.md`
