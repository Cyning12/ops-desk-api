# Invoke：30（含 40）· post-merge-hygiene

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 30（含 40 自检） |
| task_slug | `post-merge-hygiene` |
| task_paths | `docs/tasks/done/task_post_merge_hygiene.md`（原 active） |
| related_review_or_none | `docs/harness/reviews/task_post_merge_hygiene_audit_R1_20260728.md` |
| git_branch | `task/post-merge-hygiene` |
| created_utc_or_local | 2026-07-28 |
| notes | 00 统筹棒 A；docs-only 归档；禁止 master 直推 |

---

## 可复制 Prompt 快照

```text
你是 Harness 30（含 40 自检）。Open Folder = ops-desk-api 仓根。

读：
- docs/tasks/active/task_post_merge_hygiene.md
- docs/harness/reviews/task_post_merge_hygiene_audit_R1_20260728.md
- docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md
- 00 统筹：../ops-desk-workspace/docs/05-plan/03-post-go-live-hygiene-orchestration.md（棒 A）

纪律：
1. 首输出 GATE_VERIFY；闸已 approved 才改文件。
2. 禁止在 master 直推。从最新 origin/master 建 task/post-merge-hygiene。
3. 若工作区已有 active→done 的 task_api_tech_graph_ci 搬家，纳入本分支提交；否则完成搬家。
4. 可把本 task 与 PROMPT/R1 一并提交；合入后将本 task 标 completed 并移入 done/（可同 PR 或 follow-up）。
5. invoke_retention_profile=minimal：落盘 30 invoke。
6. 跑 npx @cyning/harness verify --target . --task docs/tasks/active/task_post_merge_hygiene.md（或合入前等价检查）。
7. commit → push -u → gh pr create。不 force push。不改 app/、CI、图谱正文。

完成后：回填自检表；汇报 PR URL。
```

---

## GATE_VERIFY（首输出摘要）

| human_gate_id | task表status | blocks_30 | 30可开工？ |
|---|---|---|---|
| HG-TASK-DRAFT | approved | N | Y |
| HG-AUDIT-R1 | approved | Y | Y |
| HG-GRAPH-MODULES | approved | Y | Y |

reviews R1 存在且签收：是 · minimal 无 pre-30 硬闸 · 结论：可开工

---

## 交付摘要

- **分支**：`task/post-merge-hygiene` ← `origin/master`
- **搬家**：`task_api_tech_graph_ci.md` active→done（已 completed）
- **本 task**：标 completed · 移入 `docs/tasks/done/`；PROMPT + R1 一并入 PR
- **禁改**：未触 `app/`、`.github/`、`docs/_tech_graph/`
- **verify**：PASS · exit 0（开工时对 active task 路径）
- **下一棒**：维护者 merge PR；交还 00（棒 B/C 并行/独立）

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-07-28 | docs-only 归档 + PR |
