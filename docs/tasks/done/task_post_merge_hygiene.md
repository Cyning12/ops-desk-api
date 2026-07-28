# Task：PR #13 合入后文档归档（api）

> **状态**：completed  
> **类型**：仓库卫生（docs-only）  
> **关联**：`docs/tasks/done/task_api_tech_graph_ci.md`（原 active）· 00 统筹 `../ops-desk-workspace/docs/05-plan/03-post-go-live-hygiene-orchestration.md` 棒 A

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `post-merge-hygiene` |
| **git_branch** | `task/post-merge-hygiene` |
| **graph_change_layer** | `none` |
| **review_hat** | `20` |
| **thinking_profile** | `shortest` |
| **invoke_retention_profile** | `minimal` |
| **required_invoke_hats** | `30` |
| **test_strategy** | `recommended` |
| **test_strategy_note** | 无 pytest 义务；确认 `active/` 无该 completed task；`git status` 干净 |
| **code_quality_bar** | `not_applicable` |
| **orchestration** | 00 统筹棒 A；00 代签双闸（文档归档惯例） |

| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 本仓未启用 WikiTrack |
### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| **HG-GRAPH-MODULES** | approved | **30** | 00 代签：仅 task 文件搬家；不改图谱/业务 |
| HG-TASK-DRAFT | approved | 22-R1 | 维护者 2026-07-28：先收尾 |
| **HG-AUDIT-R1** | approved | **30** | 00 代签：docs-only 归档 |

---

## 背景与目标

PR #13（`task/api-tech-graph-ci`）已合入 `master`；task 标 completed，但曾滞留 `active/`。工作区已将文件移至 `done/`，**尚未在任务分支提交**。

**完成态**：

- [x] 从干净基线切 `task/post-merge-hygiene`（勿在 `master` 直改直推）
- [x] `docs/tasks/done/task_api_tech_graph_ci.md` 入版本库；`active/` 不再含该文件
- [x] 本 task 自检后可标 completed 并随 PR 一并归档，或留待下波卫生棒
- [x] commit → push → 开 PR →（维护者）merge

**不做**：业务码、CI、图谱正文、push `--force`、改默认分支

---

## 失败路径

| 触发 | 行为 | 可重试 |
|---|---|---|
| 在 `master` 上已有未提交搬家 | stash/带入任务分支，禁止直推 master | 是 |
| PR 冲突 | rebase `master` 后重开 | 是 |

---

## 验收标准

- [x] PR 合入后 `master` 上 `docs/tasks/active/` 无 `task_api_tech_graph_ci.md`
- [x] `docs/tasks/done/task_api_tech_graph_ci.md` 存在且状态 completed
- [x] 未改 `app/`、`.github/`、`docs/_tech_graph/`（除本 task 元数据外）

---

## 40 自检表（合入前）

| 项 | 结果 |
|---|---|
| 分支 | `task/post-merge-hygiene`（非 master 直推） |
| `task_api_tech_graph_ci` | active 删除 · done 保留 · status=completed |
| 本 task | completed · 已移入 `docs/tasks/done/` |
| 禁改范围 | 未触 `app/` / `.github/` / `docs/_tech_graph/` |
| harness verify | PASS · `task_post_merge_hygiene.md`（开工时 active 路径） |
| 30 invoke | `docs/harness/invokes/by-task/post-merge-hygiene/` |
| force push | 未使用 |

---

## CLOSE（合入后关账）

| 项 | 内容 |
|---|---|
| **日期** | 2026-07-28 |
| **PR** | [#14](https://github.com/Cyning12/ops-desk-api/pull/14) MERGED · `07747f3` |
| **归档** | 同 PR 已 `active→done`（`harness task close` 对已 done 路径不适用；LINT-DONE PASS） |
| **active/** | 已删 kickoff `PROMPT_30_post_merge_hygiene.md` |
| **分支清理** | 删 `task/post-merge-hygiene`（本地+远程） |
| **下一棒** | 交还 00（棒 B/C） |
