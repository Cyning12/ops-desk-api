# Invoke · 30 · sessions/latest@B 回归单测

> **hat**：30  
> **日期**：2026-09-18  
> **分支**：`task/tenant-readonly-predicate`  
> **task**：`docs/tasks/active/task_tenant_readonly_predicate.md`  
> **结论**：**PASS**（未 commit）

---

## 人工闸扫描（GATE_VERIFY）

| human_gate_id | task表status | blocks_30 | 30可开工？ |
|---------------|--------------|-----------|------------|
| HG-TASK-DRAFT | approved | Y | 可 |
| HG-AUDIT-R1 | approved | Y | 可 |
| HG-GRAPH-MODULES | approved | Y | 可 |
| HG-STAGE-T-DATA | approved | Y | 可 |
| HG-CONTRACT-FREEZE | approved | Y | 可 |

结论：可补回归测（业务码零改）

---

## 本窗

| 项 | 内容 |
|----|------|
| **背景** | 00 排查：web 切 B 后 `sessions/latest` 假 500（Vite 代理 ECONNREFUSED）；应用层该路径不读 tenant 头 |
| **改动** | 仅加测 `tests/test_tenant_context.py::test_sessions_latest_ok_after_switch_to_tenant_b` |
| **业务码** | **未改** |
| **commit** | **未 commit / 未 push** |

### 测覆盖

登录 → `POST /api/ops/auth/tenant`（`ops-desk-pilot-b`）→ `GET /api/ops/chat/sessions/latest`（头 `X-Ops-Tenant-Id: ops-desk-pilot-b`）→ **200** 且有 `id`。

### 命令

```text
.venv/bin/pytest tests/test_tenant_context.py -q --tb=short
→ 6 passed · exit 0
```
