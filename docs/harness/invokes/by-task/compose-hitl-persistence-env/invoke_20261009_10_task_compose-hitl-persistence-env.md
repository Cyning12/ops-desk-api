# Invoke：10-task · compose-hitl-persistence-env

| 字段 | 值 |
|------|-----|
| hat_id | 10-task |
| task | `docs/tasks/active/task_compose_hitl_persistence_env.md` |
| 日期 | 2026-10-09 |
| 类型 | config 小 task（免 SPEC · 依据=`docs/acceptance/20261009_chat-history-hitl-ux_local_acceptance.md:46` 偏差登记第 2 行处置令） |
| 产出 | 验收（A1 渲染对拍 / A2 db 态端点 / A3 默认零 diff / A4 改动边界 / A5 回归）· failure_paths ×7 · 非范围 · 钉死契约 · 思考轮 R0–R3 early_stop |
| 锚点实读 | `docker-compose.yml:51-70`（api.environment 块 · 无 OPS_HITL_PERSISTENCE）· `:61-65`（LG_RAG_DELEGATION_TOKEN_* 范式）· `app/ops/hitl/persistence.py:22`（ENV_PERSISTENCE）· `:40`（空串→null）· `app/ops/hitl/router.py:74-79`（/runtime） |

## 验证命令

```text
npx spec-wave task lint --file docs/tasks/active/task_compose_hitl_persistence_env.md
```

## 人工闸（落稿时全 pending · 人签前 30 拒开工）

| human_gate_id | status |
|---------------|--------|
| HG-TASK-DRAFT | pending |
| HG-AUDIT-R1 | pending |
| HG-GRAPH-MODULES | pending |

| 2026-10-09 | 10 起草完成 · 交 20-task-audit R1 → 维护者签 |
