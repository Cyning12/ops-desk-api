# Invoke：00 · strategy-builder-allowlist（S1 · 统筹至 CLOSE）

| 字段 | 值 |
|---|---|
| hat_id | 00 |
| task_slug | strategy-builder-allowlist |
| git_branch | `task/strategy-builder-allowlist` |
| orchestration | strategy-and-intent 首棒 = S1 |
| 统筹窗口 | **本会话**（维护者 Prompt 指定 · 至 CLOSE + PR MERGED） |
| 授权 | `PROMPT_00_strategy-builder-s1` · 过程签收 / 验收 / PR / merge；**禁** 00 改 `app/`/`tests/` |

---

## GATE_VERIFY（本回合 · 过程闸）

### S0（规划）

| human_gate_id | 真值位置 | status |
|---|---|---|
| HG-SPEC-SIGNOFF | `03_strategy_and_intent_plan_v0.md` · `strategy/ROADMAP` | **approved**（00 代签 · 维护者 Prompt 授权 · 2026-08-27） |

### S1（实现 task）

| human_gate_id | task 表 status | 一致？ | blocks_30 | 30 可开工？ |
|---|---|---|---|---|
| HG-TASK-DRAFT | approved | Y | N | Y |
| HG-AUDIT-R1 | approved | Y | N | Y |
| HG-GRAPH-MODULES | approved | Y | N | Y |

- reviews：`task_strategy_builder_allowlist_audit_R1_20260827.md` · **pass**
- pre-30 invoke：00 + 10 ✓（本回合落盘）
- verify：`npx dsh-coding-kit verify --target . --task docs/tasks/active/task_strategy_builder_allowlist.md` → **VERIFY: PASS**（2026-08-27）

---

## 波次循环（本 task）

| 阶段 | 状态 | 说明 |
|---|---|---|
| S0 签收 | ✓ | 03 + ROADMAP + README + 02 下游指针 |
| docs-only CLOSE | ✓ | `task_strategy_builder_spec` → done/ |
| 10-task | ✓ | 本回合起草 allowlist task |
| 20 R1 | ✓ | audit R1 pass |
| 00 代签 | ✓ | HG-TASK-DRAFT + HG-AUDIT-R1 + HG-GRAPH-MODULES |
| GATE_VERIFY | ✓ PASS | verify CLI 2026-08-27 |
| 30 | ✓ PASS | invoke_20260827_30_40 · [`30 S1 allowlist`](c27d58b5-4c3c-436b-9e4a-8fa56dedc7a9) |
| 40 | ✓ PASS | pytest 30 · ruff 0 · graph-compile 0 · chat/graph.py 0 diff |
| CLOSE | ✓ PASS | 归档 done/ · PR 待开 |

---

## 硬约束（已写入 task / 30 Prompt）

- Mode A：`list_capabilities` + invoke；静态图 + 动态 allowlist；禁止动态 compile
- Builder 不得绕过 Policy；不得由模型随意 register
- 不改 `chat/graph.py` 拓扑；不引 Agently
- 空 allowlist → fallback 单 rag；None 不允许（强制 Builder）
- 不混改无关 active task

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-27 | S0 代签 · 拆 S1 · 00 统筹启动 |
| 2026-08-27 | 30/40 PASS · 机械验收 PASS · CLOSE |
