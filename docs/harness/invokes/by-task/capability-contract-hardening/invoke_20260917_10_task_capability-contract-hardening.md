# Invoke：10-task · capability-contract-hardening

| 字段 | 值 |
|------|-----|
| **时间** | 2026-09-17 |
| **帽** | 10-task |
| **task_slug** | `capability-contract-hardening` |
| **git_branch** | `task/capability-contract-hardening` |
| **task** | `docs/tasks/active/task_capability_contract_hardening.md` |
| **上游** | `docs/discussions/2026-09-17_interview_gaps_adoption_and_landing_v0.md` §1 A · §5 α · §8 H |
| **00 invoke** | `invoke_20260917_00_start_capability-contract-hardening.md` |
| **禁区** | 未改 `app/` / `tests/`；未代签 `HG-AUDIT-R1` |

---

## 本帽交付

| 项 | 结果 |
|----|------|
| task 补全 | A–F 同竖切 · failure_paths · R0–R4 early_stop · 真实代码锚点 · 钉死契约表 |
| 人工闸 | 均保持 `pending`（本帽不代签） |
| `task lint` | **PASS**（无 W6/W7） |

---

## Judgment（10）

- **竖切**：A–F 默认同 task；B 兼容风险若爆可跟进拆棒（已写非范围/跟进）
- **范围锁**：T/W/P 与 β 预算未写入验收
- **口径 F**：注册表 ≠ 注册中心；业务不变量不进 `args_schema`

---

## 下一棒

**20-task-audit** → 审查文落盘 → 00 代签 `HG-TASK-DRAFT` / 后续 `HG-AUDIT-R1` → GATE_VERIFY → 派 30

| 2026-09-17 | 10 补全首稿 |
