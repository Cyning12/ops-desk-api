# invoke · 文档健康修复 · 陈旧合入状态表述更正（2026-10-30）

| 项 | 内容 |
|----|------|
| **时间** | 2026-10-30 |
| **性质** | 维护者变更请求（2026-10-30）· 纯文档改动 · 零业务码 |
| **分支** | `fix/doc-stale-merge-status`（自 `master` 建 · `git pull --ff-only` 已同步） |
| **范围** | 陈旧「待合入 / 未合 master / NO-GO」表述与磁盘实态冲突的更正 + 全仓体检 |

## 改了什么

1. `docs/discussions/2026-09-17_interview_gaps_adoption_and_landing_v0.md`
   - §5 进度行：PR #141「待合入」→ MERGED 2026-09-18（merge commit `4896701`）；阶段 T「NO-GO 30」→ Fixture 轨已 CLOSE（`f048c57` ∈ master · PR #142 · `8be477c` · web PR #76）。
   - §8.4 一句话：同上两处更正。
   - 修订表加 2026-10-30 行。
2. `docs/tasks/done/task_tenant_readonly_predicate.md` header：「PR 未开、未合 master」→ PR #142 MERGED 2026-09-18（merge commit `8be477c`）· `f048c57` ∈ master；修订表加 2026-10-30 行。
3. 全仓体检 `grep -rn "待合入\|未合\|未 merge\|NO-GO" docs/`：另修 5 处与实态冲突的陈旧行（见下「体检处置」），每处均加修订注记（2026-10-30）。

## 证据 commit / 命令

| 事实 | 证据 |
|------|------|
| PR #141 MERGED 2026-09-18 | `git log --format='%h %ad %s' --date=short 4896701 -1` → `4896701 2026-09-18 Merge pull request #141` |
| `f048c57` ∈ master | `git branch --contains f048c57` → master |
| 阶段 T PR 号 | `git log --oneline --merges --all \| grep -i tenant` → `8be477c Merge pull request #142`（2026-09-18） |
| `chore/upgrade-langgraph-1.2` 已合 | `852454a 2026-09-21 Merge pull request #143`；`034fe7c`/`e80378c` ∈ master |
| PR #58 MERGED 2026-08-26 | merge commit `15064ed` |
| PR #22 MERGED 2026-07-28 | merge commit `0cb5524` |

## 体检处置（其余命中）

- **已修**（与磁盘实态冲突的当前态表述）：`task_supervisor_budget_h_beta.md` CLOSE 表 PR #141 待合入；`task_supervisor_parallel_join.md` header「PR 未开、未合 master」（实随 PR #143 合入）；`HANDOFF_recent-2days_v1_zh.md` §0「尚未合并、未开 PR」（实 PR #143 已合）；`task_structured_output_gateway_p0/p1/p2.md`「同分支待合入」（实 PR #58 已合）；`task_harness_upgrade_2.19.0.md`「PR #22 待合入」（实已合）。
- **不改·列入报告**（带日期的历史实证记录 / 条件句，书写时为真，改写会 falsify 历史）：memory-facts-p1 SPEC（PR #144 条件句）、memory-fusion-weight-tuning R1 审查（#146 未合 · 2026-09-21 时点）、memory-embedding-backfill SPEC/task（金样未合 · 2026-09-21 实扫）、hitl-auto-resume 审查/task/invokes（`f57b4ae` 未 merge · 2026-10-10 时点 · PR #223 于 10-11 合入）、RUNBOOK_local-acceptance（langgraph 升级验收当日快照）、task_cap_portable_core（PR #65 闸语句 · 已合 `9cc260f`）、api-prompts-sync / graph-anchor-profile-fix 的 R1 照登注（sibling 分支当时未合 · #298/#299/#300 已于 10-30 合入）、invoke/_prompts/close_* 过程档、qdrant-server-upgrade（workspace 仓 · 本仓不可证）、DEF-023（上游 kit · 本仓不可证）。

## Verify

- 无仓内 markdown lint；`spec-wave verify` 需 task 档且本批为维护者变更请求无 active task → 跳过。
- `./scripts/graph-compile.sh` → 全绿（OK · done）。
- 未 merge：PR 由 00 执行合并。
