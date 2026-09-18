# Invoke：10-task · supervisor-budget-h-beta

| 字段 | 值 |
|------|-----|
| **时间** | 2026-09-17 |
| **帽** | 10-task |
| **task_slug** | `supervisor-budget-h-beta` |
| **git_branch** | `task/supervisor-budget-h-beta` |
| **task** | `docs/tasks/active/task_supervisor_budget_h_beta.md` |
| **上游** | `docs/discussions/2026-09-17_interview_gaps_adoption_and_landing_v0.md` §5 β 项 6 · §8 H |
| **00 invoke** | `invoke_20260917_00_open_supervisor-budget-h-beta.md` |
| **禁区** | 未改 `app/` / `tests/`；未代签 `HG-*` |

---

## 本帽交付

| 项 | 结果 |
|----|------|
| task 补全 | 钉死表 · failure_paths · 验收 · R0–R5 early_stop@R4 · 代码锚点实扫 |
| 人工闸 | 均保持 `pending`（本帽不代签） |
| `task lint` | **PASS** |

---

## Judgment（10）钉死摘要

| 项 | 值 |
|----|-----|
| 总步默认 | **32** · `MAX_SUPERVISOR_STEPS` / `LG_RAG_SUPERVISOR_MAX_STEPS` |
| 计数 | supervisor 图 8 类节点入口；**不计** router 子图 |
| 主闸 | `route_next_subtask` 耗尽 → **`aggregate`**（非 END） |
| 墙钟 | **降级**：非硬门；默认关；可选同姿态 |
| 共存 | 与 `MAX_SUBTASKS=4`、critic 1+1 并存；全局耗尽优先禁回环 |

---

## 下一棒

**20-task-audit** → 审查文落盘 → 00 代签 `HG-TASK-DRAFT` / 后续 `HG-AUDIT-R1` → GATE_VERIFY → 派 30

| 2026-09-17 | 10 补全首稿 |
