# invoke · 00 · capability-contract-hardening · 本窗开工

| 项 | 内容 |
|----|------|
| **时间** | 2026-09-17 |
| **帽** | 00 |
| **主题** | 阶段 H · Capability / Host 契约硬化（波次 α） |
| **分支** | `task/capability-contract-hardening`（自 `master` 新建） |
| **task** | `docs/tasks/active/task_capability_contract_hardening.md`（00 极简壳） |
| **上游** | `docs/discussions/2026-09-17_interview_gaps_adoption_and_landing_v0.md` §1 A · §5 · §8 |
| **Prompt** | [PROMPT_00_orchestrate.md](./PROMPT_00_orchestrate.md) · `_prompts/PROMPT_00_capability-contract-hardening.md` |

---

## 维护者授权（本窗有效 · 全文摘要）

1. **统筹授权**：00 统筹阶段 H 下一（或一组）task：起草 → 审查 → 实现 → verify → CLOSE。  
2. **代签授权**：00 可代签本主题全部过程文档与人工闸表字段，包括但不限于：
   - task 头注 / 人工闸表（`HG-AUDIT-R1`、`HG-TASK-DRAFT`、相关 `HG-*`）
   - `docs/harness/reviews/*` 审查结论签收
   - `docs/harness/invokes/by-task/<slug>/*` 过程 invoke 的闸状态与 CLOSE 过程签
   - task 迁 `done/`、ROADMAP/讨论稿回写中的过程签收栏  
   **签注格式**：`2026-09-17 · 00 代签 · 维护者令开启`  
3. **代签 ≠ 亲自改码**：无「00 本窗亲自 30」例外句 → **禁止** 00 改 `app/`、`tests/` 实现；中间实现交子 Agent（10/20/30/40）。  
4. **Git**：未说 commit/push → 不 push；commit 仅当维护者另令。

范围锁：**仅阶段 H**；禁止扩阶段 T / W / P 实现。

---

## 闸表初值（本窗）

| 闸 | 状态 | 备注 |
|----|------|------|
| HG-TASK-DRAFT | pending | 00 已落极简壳 · 待 10 补全后 00 可代签 |
| HG-AUDIT-R1 | pending | 20 通过后 00 可代签 · **pending 则拒派 30** |
| HG-GRAPH-MODULES | pending（本 task 行） | 仓 `01_modules.md` 历史 approved；本 task 若改 G-L1 备注须签一行 |

---

## 本窗动作日志

| 时刻 | 动作 | 结果 |
|------|------|------|
| 开工 | 确认分支 | 原 `master` → 新建并切换 `task/capability-contract-hardening` |
| 扫描 | `docs/tasks/active/task_*` | **无**本主题 task |
| 落盘 | task 极简壳 | `docs/tasks/active/task_capability_contract_hardening.md` |
| 落盘 | 本 invoke | 写入维护者授权全文摘要 + 闸表初值 |
| 下一棒 | 派 **10-task** | 补全验收 / failure_paths / R0–R5 / test_strategy；`task lint` PASS |

---

## Judgment（00）

- **gate/risk**：闸均 pending · 合规拒 30  
- **hat_self**：未改 `app/`/`tests/` · 仅壳 + invoke · 符合 delegate-only  

## 下一棒

**10-task**：补全 `task_capability_contract_hardening.md` → 落 `invoke_*_10_*.md` → 回报 00 → 派 20。
