# Invoke · 30 · multi-replica-dualproc-tenant-session

> **日期**：2026-09-24  
> **帽**：30（00 委派）  
> **闸**：HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 全 approved · graph_change_layer=none  
> **目录**：`/private/tmp/opsdesk-wt-fix-dualproc` · 分支 `fix/multi-replica-dualproc-tenant-session`

## 必做

1. `npx spec-wave verify --task docs/tasks/active/task_multi_replica_dualproc_tenant_session.md` → PASS  
2. 改 `_create_user`：`INSERT INTO ops_sessions` 增加 `tenant_id` 列，值 **`"dualproc"`**（对齐 `dualproc_server` HITL/租户）  
3. `pytest tests/test_multi_replica_dualproc.py`（Python：主仓 `.venv`）；确认无 `tenant_id` NOT NULL  
4. `git diff master -- app/` 必须空  
5. FINDINGS #1 → `closed` + 修订行  
6. commit + push + **可开 PR**（本 fix 小 · 40 可同棒或紧随）；标题建议 `fix(test): dualproc fixture 补 ops_sessions.tenant_id`

## 禁

改 `app/` · 改模型/迁移 · 重写 dualproc 基建

## 修订

| 日期 | 说明 |
|---|---|
| 2026-09-24 | 00 下发 30 |
