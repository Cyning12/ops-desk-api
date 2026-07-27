# Invoke：10-task · glayer-phase-alpha-api

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 10-task |
| task_slug | `glayer-phase-alpha-api` |
| freeze_id | — |
| task_paths | `docs/tasks/active/task_glayer_phase_alpha_api.md` |
| related_review_or_none | `docs/harness/reviews/task_glayer_phase_alpha_api_audit_R1_20260727.md` |
| git_branch | `task/glayer-phase-alpha-api-v1` |
| worktree_root | — |
| created_utc_or_local | 2026-07-27 |
| notes | **补录**：对齐回合已产出方案；本文件补 10 帽落盘。正式流程应先 10→20→再 30。 |

---

## 可复制 Prompt 快照

```text
## 10-task · 图谱物理分层 Phase α（ops-desk-api）

@docs/harness/prompts/10-task-requirements.md
规格包：Projects/docs/harness/spec/graph_skill_layering_v1/
（README · DECISIONS · PLAN_migration_ops_desk · OPEN_QUESTIONS C1–C4）

【目标】
把平铺 docs/_tech_graph 升为 l0/l1/l2/shared；docs/skills S-L0/S-L1；
递归 export；chat 域 G-L2 indexes。不改 web/ios/Projects 规格。

【须写入 task】
- graph_change_layer: mixed · review_hat: 20 · thinking_profile: tripartite
- invoke_retention_profile: default（必留 10,30,40）
- 人工闸：HG-PILOT-OPSDESK-GLAYER · HG-GRAPH-MODULES · HG-AUDIT-R1 · HG-TASK-DRAFT
- C1–C4 建议默认；failure_paths；验收可勾选
- 分支：task/glayer-phase-alpha-api-v1

【禁止】
本帽不改业务代码、不迁目录；不签发 HG-AUDIT-R1（由维护者/20 签）
```

---

## 交付摘要（本帽结束时填）

- **产出**：`docs/tasks/active/task_glayer_phase_alpha_api.md`（范围/验收/失败路径/人闸/C1–C4）
- **建议 test_strategy**：`recommended`（`./scripts/graph-compile.sh` + 路径存在性）
- **下一棒**：20-task-audit（R1 审查文）→ 签闸后 **30**
- **过程债**：首次执行时未先落本 invoke，直接 30；现补录以闭合 `default=10,30,40`

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-07-27 | 补录 10-task invoke（纠正帽链缺口） |
