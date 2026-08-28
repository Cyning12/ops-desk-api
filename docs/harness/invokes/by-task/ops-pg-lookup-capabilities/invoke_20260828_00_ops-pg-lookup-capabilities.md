# Invoke：00 · ops-pg-lookup-capabilities

| 字段 | 值 |
|---|---|
| hat_id | 00 |
| task_slug | ops-pg-lookup-capabilities |
| git_branch | `task/ops-pg-lookup-capabilities` |
| 授权 | 过程签收 / 验收 / PR；**禁** 00 改 `app/`/`tests/` |
| 本波不做 | sync sender 实现 · Eval E0/E1 |

---

## GATE_VERIFY

| human_gate_id | task 表 status | 一致？ | blocks_30 | 30 可开工？ |
|---|---|---|---|---|
| HG-TASK-DRAFT | approved | Y | N | Y |
| HG-AUDIT-R1 | approved | Y | N | Y |
| HG-GRAPH-MODULES | approved | Y | N | Y |

- reviews：`task_ops_pg_lookup_capabilities_audit_R1_20260828.md` · pass
- pre-30 invoke：00 + 10
- verify：`npx dsh-coding-kit verify --target . --task docs/tasks/active/task_ops_pg_lookup_capabilities.md` → **VERIFY: PASS**

---

## 波次

| 阶段 | 状态 |
|---|---|
| 10-task | ✓ |
| R1 | ✓ |
| 00 代签 | ✓ |
| GATE_VERIFY | ✓ | VERIFY: PASS |
| 30 | in_progress | 本会话派子代理 |

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-28 | 本波开工 lookup；sync / Eval 另棒 |
