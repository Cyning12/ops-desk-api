# Invoke：00 · lg-rag-supervisor-capability-catalog（H1 · 统筹至 CLOSE）

| 字段 | 值 |
|---|---|
| hat_id | 00 |
| task_slug | lg-rag-supervisor-capability-catalog |
| git_branch | `task/lg-rag-supervisor-capability-catalog` |
| orchestration | agent-host-plan 首棒 = H1 |
| 统筹窗口 | **本会话**（维护者指定 · 至 CLOSE） |

---

## GATE_VERIFY

| human_gate_id | task 表 status | 一致？ | blocks_30 | 30 可开工？ |
|---|---|---|---|---|
| HG-TASK-DRAFT | approved | Y | N | Y |
| HG-AUDIT-R1 | approved | Y | N | Y |
| HG-GRAPH-MODULES | approved | Y | N | Y |

- reviews：`task_lg_rag_supervisor_capability_catalog_audit_R1_20260827.md` · **pass**
- pre-30 invoke：00 + 10 ✓
- verify：`npx dsh-coding-kit verify --target . --task docs/tasks/active/task_lg_rag_supervisor_capability_catalog.md`（本 00 回合执行）

---

## 波次循环（本 task）

| 阶段 | 状态 | 说明 |
|---|---|---|
| 10-task | ✓ | invoke_20260827_10 |
| 20 R1 | ✓ | audit R1 pass |
| 00 代签 | ✓ | HG-TASK-DRAFT + HG-AUDIT-R1 |
| GATE_VERIFY | ✓ PASS | verify CLI 2026-08-27 |
| 30 | ✓ PASS | invoke_20260827_30_40 |
| 40 | ✓ PASS | H1 6 + p2 12 + capability 25 |
| **CLOSE** | **✓ PASS** | 归档 done/ · 2026-08-27 |

---

## 硬约束（30 Prompt 已写入）

- Mode A：`list_capabilities` + invoke；静态图 + 动态 plan
- 不改 `chat/graph.py` 拓扑
- 非法 tool id → **整 plan fallback 单 rag**
- 不混改无关 active task

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-27 | H1 签收 · 00 统筹启动 |
