# Invoke：10-task · structured-output-gateway-p0

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 10-task |
| task_slug | `structured-output-gateway-p0` |
| freeze_id | 无 |
| task_paths | `docs/tasks/active/task_structured_output_gateway_p0.md` |
| related_review_or_none | 上游 SPEC `docs/spec/agent-infra/SPEC-structured-output-gateway_v0.md`（HG-SPEC-SIGNOFF=approved） |
| git_branch | `task/structured-output-gateway` |
| worktree_root | `.` |
| created_utc_or_local | 2026-08-26 |
| notes | 仅 task；不改 app/tests 业务实现；闸 pending；无关 active 不混入；Capability Gateway 不进本波 |

---

## 可复制 Prompt 快照

00 执行 10-task：按 SPEC §4 P0 闸化；验收 / failure_paths / 非范围 / R0–R3 + 思考轮控制；`HG-TASK-DRAFT` / `HG-AUDIT-R1` 起草时 pending。

---

## 裁决

- 总轨拆四子 task：P0 / P1 / P2 / P3；本文件仅 P0。
- P0 = `parse_only` + Pydantic + 公共 JSON 提取（封装/替换 `_extract_json_object`）。
- 禁止：`complete_structured`、节点接入、Capability Gateway、改 `chat/graph.py`、Agently 依赖。

## 结论摘要

必做：可 import `parse_only`（或等价公开 API）；Host 权威 schema 失败；公共 extract + deterministic repair 边界；委托 multi `_extract_json_object`；单测 mock；G-L1 `lg_rag` 备注不增一级模块。

---

## 交付摘要

- **验证命令**：`npx dsh-coding-kit task lint --file docs/tasks/active/task_structured_output_gateway_p0.md` → **LINT: PASS**
- **变更路径**：`docs/tasks/active/task_structured_output_gateway_p0.md` · 本 invoke
- **下一棒**：20 R1 已过 · 闸已代签 → verify → 派 30

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-08-26 | 10-task 首稿落盘 |
| 2026-08-26 | lint PASS；闸代签后待 verify |
