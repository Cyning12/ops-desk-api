# Invoke：00 · critic-rebind（S4 · 统筹至 CLOSE）

| 字段 | 值 |
|---|---|
| hat_id | 00 |
| task_slug | critic-rebind |
| git_branch | `task/critic-rebind` |
| orchestration | strategy-and-intent 第四棒 = S4 |
| 统筹窗口 | **本会话**（维护者「继续 S4」） |
| 授权 | 过程签收 / 验收 / PR / merge；**禁** 00 改 `app/`/`tests/` |

---

## GATE_VERIFY

| human_gate_id | task 表 status | 一致？ | blocks_30 | 30 可开工？ |
|---|---|---|---|---|
| HG-TASK-DRAFT | approved | Y | N | Y |
| HG-AUDIT-R1 | approved | Y | N | Y |
| HG-GRAPH-MODULES | approved | Y | N | Y |

- reviews：`task_critic_rebind_audit_R1_20260828.md` · **pass**
- pre-30 invoke：00 + 10 ✓
- verify：`npx dsh-coding-kit verify --target . --task docs/tasks/active/task_critic_rebind.md` → **VERIFY: PASS**（2026-08-28）

---

## 波次循环

| 阶段 | 状态 | 说明 |
|---|---|---|
| 10-task | ✓ | |
| 20 R1 | ✓ | |
| 00 代签 | ✓ | |
| GATE_VERIFY | ✓ | VERIFY: PASS · task_critic_rebind.md |
| 30 | ✓ | 30/40 invoke 落盘 |
| 00 机械验收 | ✓ | pytest 29 · ruff · graph-compile · chat/graph.py 0 |
| CLOSE | ✓ | 归档 `docs/tasks/done/task_critic_rebind.md` |

---

## 硬约束

- 规则 stub；预算 1+1；禁止无界 ReAct
- 不改 chat/router/basic 拓扑；不绕过 Policy
- 回环必须能重置 `subtask_results`

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-28 | S4 00 统筹启动 |
