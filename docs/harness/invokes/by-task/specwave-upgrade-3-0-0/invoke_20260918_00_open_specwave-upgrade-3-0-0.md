# invoke · 00 · specwave-upgrade-3-0-0 · 开窗

| 项 | 内容 |
|----|------|
| **时间** | 2026-09-18 |
| **帽** | 00 |
| **分支** | `task/specwave-3-0-0`（worktree：`/Users/cyning/Desktop/Ops-desk/ops-desk-api-specwave-3-0-0` · base `origin/master@48f0ac2`） |
| **task** | `docs/tasks/active/task_specwave_upgrade_3_0_0.md` |
| **签注** | 2026-09-18 · 00 代签 · 维护者令：「身为00统筹此task，授权签收所有过程文档」 |

## 维护者授权摘要

1. 统筹 spec-wave **2.4.2 → 3.0.0** 全链（00 起草初稿 → 20 → 30 → 40 → CLOSE）。  
2. **00 可代签全部过程文档与 HG-***（注明本签注句）。  
3. 代签 ≠ 亲自 30；无「00 本窗亲自 30」则禁改 `package.json` / CI / tests / 实现落地。  
4. 未另令不 commit/push/merge。

## 闸表初值 → 开窗后

| gate | status |
|------|--------|
| HG-TASK-DRAFT | **approved**（00 代签 · 2026-09-18） |
| HG-AUDIT-R1 | pending（待 20 R1） |

## 下一棒

派 **20-task-audit** 书面审查 → 落盘 `docs/harness/reviews/task_specwave_upgrade_3_0_0_audit_R1_20260918.md` → 00 代签 `HG-AUDIT-R1` → 派 **30**。

## 非范围锁

不改 `app/` · 不强升 host-adapt schema v2 · 不碰主仓 `task/supervisor-budget-h-beta` 脏树
