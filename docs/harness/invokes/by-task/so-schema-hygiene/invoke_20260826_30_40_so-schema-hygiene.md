# Invoke：30(+40) · so-schema-hygiene

| 字段 | 值 |
|------|-----|
| hat_id | 30-execute / 40-verify |
| task | `docs/tasks/active/task_so_schema_hygiene.md` |
| 分支 | `task/so-schema-hygiene` |
| 日期 | 2026-08-26 |

## GATE_VERIFY（首输出 · 零 diff）

| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---------------|--------------|-----------------|--------|-----------|------------|
| HG-TASK-DRAFT | approved | — | Y | N（22-R1） | — |
| HG-AUDIT-R1 | approved | 可派 30 | Y | Y | 是 |
| HG-GRAPH-MODULES | approved | 仅备注 | Y | Y | 是 |

reviews：`docs/harness/reviews/task_so_schema_hygiene_audit_R1_20260826.md` 存在 · 是

pre-30 invoke：`10` 齐全 · 是（`required_invoke_hats=10,30`）

机械：`npx dsh-coding-kit verify --target . --task docs/tasks/active/task_so_schema_hygiene.md` → **VERIFY: PASS**

结论：可进入读码/改码

## 实现摘要（H1）

1. 新建 `app/ops/lg_rag/schemas/`：`RouteDecision` / `SubtasksPlan` / `SubtaskItem` / `ExtractResult`
2. `lg_rag/nodes.py` · `lg_rag/multi/nodes.py` import → `app.ops.lg_rag.schemas`
3. `structured_output.schemas` 保留短期 deprecated re-export；包顶 `__all__` 不含业务 schema
4. G-L1：`01_modules.md` 备注「域 schema 在 lg_rag/schemas」；未把 graph-compile 时间戳噪声入仓

## 40 结果

| 检查 | 结果 |
|------|------|
| `.venv/bin/pytest` 指定 5 文件 | 46 passed |
| `ruff check` 触及路径 | All checks passed |
| `app/ops/chat/graph.py` | 零 diff |
| verify | PASS |
| 循环 import 冒烟 | `from app.ops.lg_rag.schemas import …` OK |

## 残留风险

- `structured_output.schemas` deprecated re-export 删期（ROADMAP 后续）
- 旧路径深 import 仅经 deprecate 指针兼容；新代码应走 `lg_rag.schemas`

| 2026-08-26 | 30/40 完成 · 可本地 commit · 未 push |
