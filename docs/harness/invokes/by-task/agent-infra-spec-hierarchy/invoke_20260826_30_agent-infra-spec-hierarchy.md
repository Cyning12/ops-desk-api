# Invoke：30 · agent-infra-spec-hierarchy（00 代执行 docs 落地）

| 字段 | 值 |
|------|-----|
| hat_id | 30（docs-only · **00 代执行**，不派业务子 agent） |
| 分支 | `docs/agent-infra-spec-hierarchy` |
| 范围 | 仅 `docs/spec/agent-infra/**` 及相关索引/讨论链 + harness 过程档 |

## GATE_VERIFY（开工前）

| human_gate_id | task表status | blocks_30 | 可开工 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | N | Y |
| HG-AUDIT-R1 | approved | Y | Y |
| HG-GRAPH-MODULES | approved | Y | Y |

`npx dsh-coding-kit verify --target . --task docs/tasks/active/task_agent_infra_spec_hierarchy.md` → 预期 PASS

## 执行清单

1. 暂存 docs / harness 过程档（排除一切 `app/`）
2. commit → push `-u` → `gh pr create`
3. 回填本 invoke：PR URL、文件清单
4. **不** merge（交维护者）；merge 后关账

## 禁区

- `app/` · `tests/` · `docs/_tech_graph/` 业务改动
- 直推 master

| 2026-08-26 | 00 代执行开工 |
