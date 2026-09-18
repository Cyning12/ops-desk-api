# Invoke · 40 reverify（关账前复验）· supervisor-budget-h-beta

> **hat**：40  
> **日期**：2026-09-18  
> **分支**：`task/supervisor-budget-h-beta`（已核对 `git branch --show-current`）  
> **task**：`docs/tasks/done/task_supervisor_budget_h_beta.md`（先前过程 CLOSE 已 mv）  
> **性质**：关账前复验（代码已实现但未 commit）  
> **禁区**：只验证 · 未改 `app/` 实现逻辑 · 未 commit/push

---

## 质量门（本帽真跑 · 退出码实录）

| 命令 | 退出码 | 结果 |
|------|--------|------|
| `pytest tests/test_supervisor_budget.py tests/test_lg_rag_multi.py tests/test_critic_rebind.py tests/test_lg_rag_supervisor_capability_catalog.py -q` | **0** | **41 passed** in 0.50s |
| `ruff check` 触及路径（`multi/budget.py` · `nodes.py` · `graph.py` · `state.py` · `strategy/{intent,builder,critic}.py` · `tests/test_supervisor_budget.py`） | **0** | All checks passed |
| `./scripts/graph-compile.sh` | **0** | 9 graphs · 132 nodes · 194 edges · check OK · mermaid normalize ok |
| `npx --yes spec-wave@2.4.2 verify --target . --task docs/tasks/done/task_supervisor_budget_h_beta.md` | **0** | VERIFY: PASS（HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 均 approved） |
| `npx --yes spec-wave@2.4.2 task lint-wiki-delta --target .` | **0** | LINT-WIKI-DELTA: PASS（scanned=114 · issues=0） |
| `git diff --stat -- app/ops/chat/graph.py` | **0** | 零 diff（无输出） |

---

## 抽查 B1–B5（本复验口径）

| # | 抽查项 | 结论 | 证据 |
|---|--------|------|------|
| B1 | 默认总步 **32** | ✅ | `budget.py` `DEFAULT_MAX_SUPERVISOR_STEPS=32` · runtime `get_max_supervisor_steps()==32` · env≤0 回退 32 |
| B2 | 耗尽→**aggregate**（非 END） | ✅ | `route_next_subtask` 首判 `is_supervisor_budget_exhausted` → `"aggregate"` · 有 pending 仍收束 · 单测绿 |
| B3 | 墙钟默认关 | ✅ | `get_max_wall_seconds()` 缺省/`≤0` → `0.0` · SPOT_OK |
| B4 | 辅闸禁 retry/rebind | ✅ | `decide_critic_verdict` / `route_after_critic` 全局耗尽→`"end"` · 单测绿 |
| B5 | G-L1 备注 · **无新一级模块** | ✅ | `01_modules.md` lg_rag 行备注 + HG 签收行；模块表仍为既有一级集合 |

**勾选：B1–B5 全 ✅** · 本帽无小修。

---

## 残留风险

1. 默认 32 若真实金样仍紧，须改 task/钉死表后再调常量（禁静默改小）。
2. 墙钟薄实现（默认关）；硬门化另跟进。
3. 工作树仍 **未 commit**（含 `budget.py` 等）——交 00 CLOSE / 维护者另令提交。

---

## 结论

**40 REVERIFY PASS** · 门禁全绿 · 可交 **00 CLOSE**（归档侧已 done；Git 仍待维护者 commit/PR） · 未 commit/push
