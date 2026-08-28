# Invoke：00 · ops-sync-sender-migration

| 字段 | 值 |
|---|---|
| hat_id | 00 |
| task_slug | ops-sync-sender-migration |
| git_branch | `task/ops-sync-sender-migration` |
| 授权 | 过程签收 / 验收 / PR；**禁** 00 改 `app/`/`tests/` |
| 本波不做 | RAG · Eval E0/E1 · capability · 旧仓脚本适配层 |

---

## GATE_VERIFY

| human_gate_id | task 表 status | 一致？ | blocks_30 | 30 可开工？ |
|---|---|---|---|---|
| HG-TASK-DRAFT | approved | Y | N | Y |
| HG-AUDIT-R1 | approved | Y | N | Y |
| HG-GRAPH-MODULES | approved | Y | N | Y |

- reviews：`task_ops_sync_sender_migration_audit_R1_20260828.md` · pass
- pre-30 invoke：00 + 10
- verify：`npx dsh-coding-kit verify --target . --task docs/tasks/active/task_ops_sync_sender_migration.md` → **VERIFY: PASS**

方案定稿：迁移旧 runner 进本仓。机读 `OPS_ADMIN_SYNC_TOKEN` Bearer（仅 sync POST）。增量 48h，不扩表。

---

## 波次

| 阶段 | 状态 |
|---|---|
| 10-task | ✓ |
| R1 | ✓ |
| 00 代签 | ✓ |
| GATE_VERIFY | ✓ | VERIFY: PASS |
| 30 | ✓ | 子代理 [30](36d62dff-5205-40e1-b432-0d0479dad573) |
| 40 机械 | ✓ | ruff 绿 · pytest 20 passed · graph-compile OK |
| CLOSE | ✓ | PR [#88](https://github.com/Cyning12/ops-desk-api/pull/88) |

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-28 | 本波开工 sync；迁移旧 runner；00 不实现 |
| 2026-08-28 | 00 CLOSE PASS · PR #88 |
