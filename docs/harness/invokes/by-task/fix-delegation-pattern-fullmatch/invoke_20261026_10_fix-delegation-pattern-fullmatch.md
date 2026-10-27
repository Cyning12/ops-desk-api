# Invoke：10 · fix-delegation-pattern-fullmatch（10-task 落稿）

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 10 |
| task_slug | `fix-delegation-pattern-fullmatch` |
| task_paths | `docs/tasks/active/task_fix_delegation_pattern_fullmatch.md` |
| related_review_or_none | none（待 20-task-audit R1 落盘 `docs/harness/reviews/` 后回填） |
| git_branch | `task/fix-delegation-pattern-fullmatch`（30 开工自 master 切出 · 当前工作区 `task/specwave-3-5-0` 为别的任务分支勿混用） |
| created_utc_or_local | 2026-10-26 |
| notes | 10-task 落稿：委派令牌 pattern 约束 `re.search`→`re.fullmatch`（delegation.py:304 一行 · fail-closed 收紧）；**本帽不改业务码**；bugfix 免 SPEC；30 派棒前须 20-task-audit R1 + HG-AUDIT-R1 维护者人签 |

---

## GATE_VERIFY（摘要 · 真值以 task 人工闸表为准）

| human_gate_id | task表status | blocks_30 | 30可开工？ |
|---|---|---|---|
| HG-TASK-DRAFT | pending | N（blocks 22-R1, 30 初稿人扫） | — |
| HG-AUDIT-R1 | **pending** | Y | **N（须维护者人签）** |
| HG-GRAPH-MODULES | approved（graph_change_layer=none 预期不再签 · 01_modules.md:79 在册口径） | Y | 条件满足（不阻塞） |

## 本轮（10）

1. 落稿 `docs/tasks/active/task_fix_delegation_pattern_fullmatch.md`（验收 TC1–TC8 · failure_paths FP-1~FP-6 · 思考轮 R0–R5）
2. 兼容性预扫落档：manifests 无 pattern 键；`param_constraints` 仅 delegation.py（:178,195,225,239,252,262,265,268,289,291,405,425,426,454,555）+ 测试/文档；30 红测前须复扫对拍（FP-4）
3. 建本 invoke 骨架（pre-30 义务）；**不**派 30——待 20-task-audit R1 + HG-AUDIT-R1 人签

禁止本轮：改 `app/**` / `tests/**` 业务实现与测试；git commit / 切分支；触碰 `docs/arch-browser/dist/site-data.json`（工作区既有 M · 别人分支）。
