# invoke · 00 start · supervisor-first-fail-closed（2026-10-19）

> **帽**：00（delegate-only · 本窗不改实现码）
> **前置**：SPEC v0 R1 审查 conditional_pass（docs/harness/reviews/spec_supervisor-first-fail-closed_audit_R1_20261019.md）· HG-SPEC-SIGNOFF=approved（维护者本窗指示 · 00 代签）

## 00 定夺（维护者 2026-10-19 本窗原话三条）

1. **「改动范围需要在完成后同步修改对外展示的web展示」** → 后端本 task 完成后，同步对外 Web 展示对新 `error{stage:supervisor_plan}` 帧的呈现（用户可区分「编排不可用」与「检索答完」）。**时序=后端完成后**；落 ops-desk-web 仓**另 task**，本 task 记为下游棒，不进本 task 范围。
2. **「N2归为error」** → R1-N2 边缘形态裁定：locked 空 + preserved 非空（hitl 批准单步写形态）的重规划失败，**归入「首次失败 → error」**；分叉判据保持 `if locked:` **不扩**为 locked or preserved。
3. **「其他条目都按照建议来执行」** → R1-N1（S4 缺省 risk_hint→high 收紧显式写入验收断言）· R1-N3（扩 `error.stage` 字面量回写 05 §4.2 词表 + 01_modules.md 备注）· R1-N4（补本 invoke）全部吸收进 task 草稿。

## 闸态（派棒时）

| 闸 | 状态 |
|---|---|
| HG-SPEC-SIGNOFF | **approved**（2026-10-19 · 00 代签 · 见 SPEC 闸表） |
| HG-AUDIT-R1 | pending（待 task 草稿 + 20-task-audit + 人签） |
| HG-GRAPH-MODULES | approved（01_modules.md:79 · 2026-08-30） |

## 下一棒

派 **10-task** 子 Agent 起草 `docs/tasks/active/task_supervisor_first_fail_closed.md`（slug=`supervisor-first-fail-closed` · 分支 `task/supervisor-first-fail-closed` · HG-AUDIT-R1=pending · **禁改 `app/`**）。完成后 → 20-task-audit → HG-AUDIT-R1 人签 → 30。
