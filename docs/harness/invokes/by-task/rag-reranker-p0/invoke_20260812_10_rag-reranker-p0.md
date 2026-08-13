# Invoke：10 · rag-reranker-p0（00 统筹开工）

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 10 |
| task_slug | `rag-reranker-p0` |
| task_paths | `docs/tasks/active/task_rag_reranker_p0.md` |
| related_review_or_none | `docs/harness/reviews/task_rag_reranker_p0_audit_R1_20260812.md` |
| git_branch | `task/rag-reranker-p0` |
| created_utc_or_local | 2026-08-12 |
| notes | 00 统筹：SPEC 已签 · 闸代签 · 派 30/40 · **关账前停** · r4-R 维护者复测 · 本帽不改业务码 |

---

## GATE_VERIFY（摘要）

| human_gate_id | task表status | blocks_30 | 30可开工？ |
|---|---|---|---|
| HG-TASK-DRAFT | approved | N | — |
| HG-AUDIT-R1 | approved | Y | Y（R1 文已落） |

## 本轮（10）

1. 起草 task 对齐 SPEC D1–D4；生产默认锁 false  
2. 落 R1 审查文；签 HG-TASK-DRAFT / HG-AUDIT-R1（维护者授权 00）  
3. 派 30（含 40）；明确 r4-R 不由 30 代跑  

禁止本轮：改 `app/**` 业务实现。
