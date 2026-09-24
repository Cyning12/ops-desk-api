# Invoke · 30 · multi-replica-dualproc-tenant-session

> **日期**：2026-09-24  
> **帽**：30（00 委派）  
> **闸**：HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 全 approved · graph_change_layer=none  
> **目录**：`/private/tmp/opsdesk-wt-fix-dualproc` · 分支 `fix/multi-replica-dualproc-tenant-session`

## GATE_VERIFY

| gate | status | blocks_30 |
|------|--------|-----------|
| HG-TASK-DRAFT | approved | — |
| HG-AUDIT-R1 | approved | ✅ |
| HG-GRAPH-MODULES | approved | ✅ |

`npx spec-wave verify` → **PASS**（tip ≥ `0c91134`）

## 必做（执行结果）

1. ✅ verify PASS  
2. ✅ `_create_user` INSERT 补 `tenant_id`  
   - **值**：`ops-desk-pilot`（非字面 `dualproc`）  
   - **原因**：`dualproc_server` 的 `"dualproc"` 是 HITL store 行字段；session 真源须 ∈ `ALLOWED_TENANTS`（`ops-desk-pilot` / `ops-desk-pilot-b`）。字面 `dualproc` → `normalize_tenant` → **422 unknown_tenant**（5 failed）。task 逃生口：「若测需与 ORM 默认一致须在 commit 说明」  
3. ✅ `pytest tests/test_multi_replica_dualproc.py` → **9 passed** · 无 `tenant_id` / `NotNullViolation`  
4. ✅ `git diff origin/master -- app/` 空（本地 `master` 落后于 origin，以 origin 为准）  
5. ✅ FINDINGS #1 → closed + 修订行  
6. ✅ commit `1aaf11c` + push + **[PR #191](https://github.com/Cyning12/ops-desk-api/pull/191)**（repo 未开 auto-merge 权限，未启用）

## 禁（遵守）

未改 `app/` · 未改模型/迁移 · 未重写 dualproc 基建

## 修订

| 日期 | 说明 |
|---|---|
| 2026-09-24 | 00 下发 30 |
| 2026-09-24 | 30 落地：fixture + FINDINGS closed · 值=`ops-desk-pilot` · SHA `1aaf11c` · [PR #191](https://github.com/Cyning12/ops-desk-api/pull/191) |
