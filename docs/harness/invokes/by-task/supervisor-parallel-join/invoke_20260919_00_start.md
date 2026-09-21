# invoke · 00 · supervisor-parallel-join · 本窗开工

| 项 | 内容 |
|----|------|
| **时间** | 2026-09-19 |
| **帽** | 00 |
| **主题** | Supervisor 无依赖子任务并发下发，按 Host 签发 `subtask_id` 归并后再进 aggregator |
| **分支** | `task/supervisor-parallel-join`（自 `master` `8be477c` 新建） |
| **task** | `docs/tasks/active/task_supervisor_parallel_join.md`（本棒不写正文 · 交 10-task） |
| **勿动** | `docs/tasks/active/task_tenant_readonly_predicate.md` 及其闸表；不扩充 Capability 工具、不开 MCP |

---

## 维护者授权（本窗有效 · 全文摘要）

代签注明：**2026-09-19 · 00 代签 · 维护者令开启 supervisor 并发归并。**

1. **统筹授权**：00 统筹本主题：起草 → 审查 → 实现 → verify → CLOSE。
2. **代签授权**：00 可代签本主题过程文档与人工闸表，包括 `HG-TASK-DRAFT`、`HG-AUDIT-R1`、确有图谱变更时的 `HG-GRAPH-MODULES`、reviews、invoke、task 迁 `done/`。
3. **代签 ≠ 亲自改码**：无「00 本窗亲自 30」例外句。禁止 00 改 `app/`、`tests/`。实现交 10/20/30/40。
4. **Git**：未另令则不 commit、不 push。

范围锁：无依赖子任务可一次下发多个工人；按 Host `subtask_id` 归并；计划内每个 id 终态齐了才进 aggregator；有明确前后依赖仍串行。禁止 A2A、跨进程工人、新表、改 `lg-rag-sse-v1` 字段、把「子读不到别人的计划」做成安全隔离、改 Capability Gateway、放宽 `MAX_SUBTASKS`（仍为 4）。

工作区注记：开工前 `task/lg-rag-shared-state-boundary` 有未提交改动，已 `git stash`（message：`wip lg-rag-shared-state-boundary parked by 00 before supervisor-parallel-join`），不带入本分支。

---

## 闸表初值（本窗）

| 闸 | 状态 | 备注 |
|----|------|------|
| HG-TASK-DRAFT | approved | 2026-09-19 · 00 代签 · 维护者令开启 supervisor 并发归并 · R2 内容 pass 后 |
| HG-AUDIT-R1 | approved | 2026-09-19 · 00 代签 · 审查文 R2 pass 后才签 · 签前曾 pending，当时拒派 30 |
| HG-GRAPH-MODULES | approved | 2026-09-19 · 00 代签 · 本 task `graph_change_layer=G-L1`，确有 lg_rag 备注/flow 变更 |

---

## 本窗动作日志

| 时刻 | 动作 | 结果 |
|------|------|------|
| 开工 | 确认分支 | 原 `task/lg-rag-shared-state-boundary`（脏树已 stash）→ `master` → 新建 `task/supervisor-parallel-join` |
| 扫描 | `docs/tasks/active/` | 本主题无 task；`task_tenant_readonly_predicate.md` 保持不动 |
| 落盘 | 本 invoke | 写入维护者授权全文摘要 + 闸表初值 |
| 下一棒 | 派 **10-task** | 起草 `task_supervisor_parallel_join.md`；00 不写 task 正文 |
| R1 | 派 **20** | 内容退回：验收缺「旧测 grep 影响面」 |
| 回填 | 派 **10** | 只补该验收条；lint PASS |
| R2 | 派 **20** | 内容 pass · 审查文 `docs/harness/reviews/task_supervisor_parallel_join_audit_R2_20260919.md` |
| 代签 | task 人工闸表 | 三闸 approved。代签 ≠ 改 `app/`/`tests/` |

---

## Judgment（00）

- **gate/risk**：人工闸三行 approved。`task close` 干跑 `CLOSE: BLOCKED`（无 PR、验收未全勾、状态仍 draft）。未 `--yes`
- **hat_self**：未改 `app/`/`tests/`。已派 10 / 20 / 30 / 40。符合 delegate-only

## 下一棒

停。等维护者决定是否 commit / PR。不要在本窗 push。
