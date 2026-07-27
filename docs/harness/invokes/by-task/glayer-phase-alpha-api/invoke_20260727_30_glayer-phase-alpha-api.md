# Invoke：30 执行 · glayer-phase-alpha-api

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 30-execute |
| task_slug | `glayer-phase-alpha-api` |
| freeze_id | — |
| task_paths | `docs/tasks/active/task_glayer_phase_alpha_api.md` |
| related_review_or_none | `docs/harness/reviews/task_glayer_phase_alpha_api_audit_R1_20260727.md` |
| git_branch | `task/glayer-phase-alpha-api-v1` |
| worktree_root | — |
| created_utc_or_local | 2026-07-27 |
| notes | 过程偏差：用户签闸+「开工」后直进 30，当时未落 10/40 invoke；现已补录。 |

---

## 可复制 Prompt 快照

```text
## 30 开工（签闸后 · 须 GATE_VERIFY）

@docs/tasks/active/task_glayer_phase_alpha_api.md
@docs/harness/prompts/30-execute-code.md
@docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md
@docs/_tech_graph/LAYER_README.md

【开工前】
1. 首输出 GATE_VERIFY（读 task 人工闸表）
2. HG-PILOT-OPSDESK-GLAYER / HG-AUDIT-R1 / HG-GRAPH-MODULES = approved → 可改

【实现】
- 分支：task/glayer-phase-alpha-api-v1
- 物理分层 l0/l1/l2/shared；01_modules；递归 export；chat G-L2；docs/skills
- C1–C4 / B1–B5 按建议默认
- 禁止改 web/ios/Projects 规格

【Verify】
- ./scripts/graph-compile.sh
```

---

## GATE_VERIFY（执行时）

| human_gate_id | task表status | blocks_30 | 30可开工？ |
|---|---|---|---|
| HG-PILOT-OPSDESK-GLAYER | approved | Y | Y |
| HG-AUDIT-R1 | approved | Y | Y |
| HG-GRAPH-MODULES | approved | Y | Y |

结论：可开工 · C1–C4 建议默认 · B1–B5 同意

---

## 交付摘要（本帽结束时填）

- **验证命令**：`./scripts/graph-compile.sh`（绿，4 graphs）
- **变更路径**：`docs/_tech_graph/**` · `docs/skills/**` · `scripts/graph-compile.sh` · `scripts/graph_yaml_to_json.py` · `AGENTS.md` · `.claude/skills/*` · task/invoke/review
- **下一棒**：40 自检（已补录 `invoke_20260727_40_*.md`）

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-07-27 | 30 执行落盘；同日补齐 10/40 并规范化元信息表 |
