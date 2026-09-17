# Invoke · 30 implement · capability-contract-hardening

> **hat**：30  
> **日期**：2026-09-17  
> **分支**：`task/capability-contract-hardening`  
> **task**：`docs/tasks/active/task_capability_contract_hardening.md`

---

## 人工闸扫描（GATE_VERIFY · 首输出）

| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---------------|--------------|-----------------|--------|-----------|------------|
| HG-TASK-DRAFT | approved | approved | Y | Y | 可 |
| HG-AUDIT-R1 | approved | approved | Y | Y | 可 |
| HG-GRAPH-MODULES | approved | approved | Y | Y | 可 |

reviews：`docs/harness/reviews/task_capability_contract_hardening_audit_R1_20260917.md` 存在且 R1 通过？是  
pre-30 invoke：`required ∩ {10,20,00}` 齐全？是  
机械：`npx --yes spec-wave verify --target . --task docs/tasks/active/task_capability_contract_hardening.md` → **VERIFY: PASS**  
结论：**可进入读码/改码**

---

## 实现范围

阶段 H · A–F 竖切。非范围：T/W/P、chat 拓扑、commit/push。

## 改动文件列表

- `app/ops/capability/types.py` — `tenant_scoped`
- `app/ops/capability/schema_validate.py` — 最小 args 校验（新）
- `app/ops/capability/gateway.py` — schema 校验 + span metadata
- `app/ops/capability/policy.py` — 租户门
- `app/ops/capability/defaults.py` · `manifests/builtin.v1.yaml` · `manifest.py`
- `app/ops/strategy/config.py` · `builder.py` — allowlist map；废 None=全开
- `app/ops/lg_rag/schemas/subtasks.py` · `multi/nodes.py` — SubtaskItem.args + tool_exec
- `docs/standards/CODING_BACKEND_L2_v1_zh.md` — P-16
- `docs/_tech_graph/l1/01_modules.md` · `10_flow_capability.graph.yaml`（+ compile 产物）
- 单测：`tests/test_capability_{gateway,lookups,policy,manifest}.py` · `test_strategy_builder.py`

## 测试命令与结果

```text
ruff check app/ops/capability app/ops/strategy app/ops/lg_rag/multi app/ops/lg_rag/schemas tests/test_capability_* tests/test_strategy_builder.py
→ All checks passed!

pytest tests/test_capability_gateway.py tests/test_capability_lookups.py \
  tests/test_capability_policy.py tests/test_capability_manifest.py \
  tests/test_strategy_builder.py tests/test_lg_rag_supervisor_capability_catalog.py -q
→ 75 passed, 8 skipped

./scripts/graph-compile.sh → OK
npx --yes spec-wave task lint-wiki-delta --target . → LINT-WIKI-DELTA: PASS
chat/graph.py → 零 diff
```

## 残留风险

1. 直接调用 lookup Gateway 未带 `tenant_id` 会 fail-closed（tool_exec 已注试点租户；其它调用方须补 ctx）。
2. 最小 schema 校验器非完整 JSON Schema（无 oneOf/$ref）；默认能力够用，复杂 schema 需后续加依赖或增强。

## 结论

**30 PASS** · 交 40 · 未 CLOSE · 未 commit/push
