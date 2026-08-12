# Invoke：10 · rag-sparse-arm-c（00 统筹开工）

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 10 |
| task_slug | `rag-sparse-arm-c` |
| task_paths | `docs/tasks/active/task_rag_sparse_arm_c.md` |
| related_review_or_none | `docs/harness/reviews/task_rag_sparse_arm_c_audit_R1_20260812.md` |
| git_branch | `task/rag-sparse-arm-c` |
| created_utc_or_local | 2026-08-12 |
| notes | 00 统筹：闸已签 · 派 30/40 · **00 不改业务码** |

---

## GATE_VERIFY（摘要）

| human_gate_id | task表status | blocks_30 | 30可开工？ |
|---|---|---|---|
| HG-TASK-DRAFT | approved | N | — |
| HG-AUDIT-R1 | approved | Y | Y（须 R1 文已落） |

## 本轮（10）

1. 确认承接 A 否决与入口保留策略已写入 task  
2. 落 R1 审查文；开分支 `task/rag-sparse-arm-c`  
3. 派 30（含 40）实现 Agent  

禁止本轮：改 `app/**` 业务实现。
