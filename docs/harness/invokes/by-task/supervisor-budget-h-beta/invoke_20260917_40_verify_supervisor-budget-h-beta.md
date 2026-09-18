# Invoke · 40 verify · supervisor-budget-h-beta

> **hat**：40  
> **日期**：2026-09-17  
> **分支**：`task/supervisor-budget-h-beta`（已核对 `git branch --show-current`）  
> **task**：`docs/tasks/active/task_supervisor_budget_h_beta.md`  
> **上游**：30 PASS · `invoke_20260917_30_implement_supervisor-budget-h-beta.md`  
> **禁区**：未扩 T/W/P；未改 SSE freeze；未 commit/push；未 CLOSE / git mv done

---

## 质量门（本帽真跑 · 退出码实录）

| 命令 | 退出码 | 结果 |
|------|--------|------|
| `pytest tests/test_supervisor_budget.py tests/test_lg_rag_multi.py tests/test_critic_rebind.py tests/test_lg_rag_supervisor_capability_catalog.py -q` | **0** | **41 passed** in 0.36s |
| `ruff check` 触及路径（`multi` / `state.py` / `strategy/{critic,intent,builder}.py` / 相关 tests） | **0** | All checks passed |
| `./scripts/graph-compile.sh` | **0** | 9 graphs · 132 nodes · 194 edges · check OK · mermaid normalize ok |
| `npx --yes spec-wave verify --target . --task docs/tasks/active/task_supervisor_budget_h_beta.md` | **0** | VERIFY: PASS（HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 均 approved） |
| `npx --yes spec-wave task lint-wiki-delta --target .` | **0** | LINT-WIKI-DELTA: PASS（scanned=114 · issues=0） |
| `git diff --stat -- app/ops/chat/graph.py` | **0** | 零 diff（bytes=0） |

---

## 验收 B1–B5 逐条勾选

| # | 验收点 | 结论 | 证据 |
|---|--------|------|------|
| B1 | 总步预算硬门：默认 32 · state 计数 · 主闸耗尽→`aggregate` · 耗尽旗标 | ✅ | `budget.py` `DEFAULT_MAX_SUPERVISOR_STEPS=32` · `state.py` 字段 · `route_next_subtask` 首判耗尽→`"aggregate"` · `test_route_next_subtask_budget_exhausted_goes_aggregate_even_with_pending` |
| B2 | 墙钟薄实现（非硬门）：默认 0=关；超时同→aggregate | ✅ | `get_max_wall_seconds` 默认 0 · `test_route_wall_clock_exhausted_goes_aggregate` |
| B3 | 与 4·1+1 共存；辅闸禁耗尽后再 retry/rebind | ✅ | `MAX_SUBTASKS=4` / critic 1+1 仍在；`decide_critic_verdict`/`route_after_critic` 全局耗尽→`"end"` |
| B4 | 单测：压低/垫高→aggregate；回归绿；辅闸测 | ✅ | `tests/test_supervisor_budget.py` + 既有 multi/critic/catalog **41 passed** |
| B5 | G-L1 备注薄；不新增一级模块 | ✅ | `01_modules.md` lg_rag H-β 备注 + 签收行；graph-compile 绿 |

**勾选数：B1–B5 全 ✅**（与 30 声明一致；40 无缺口小修）。

---

## 验收标准门禁 + 抽查

| 抽查项 | 结论 |
|--------|------|
| 耗尽→`aggregate`（非 END） | ✅ `route_next_subtask` 返回 `"aggregate"`；有 pending 仍收束 |
| env≤0 回退 32 | ✅ `LG_RAG_SUPERVISOR_MAX_STEPS=0/-3/abc` → 32（SPOT_OK + 单测） |
| 辅闸禁 retry/rebind | ✅ `decide_critic_verdict` / `route_after_critic` → `"end"` |
| 未扩 T/W/P · 未改 SSE freeze · `chat/graph.py` 零 diff | ✅ |
| 8 类节点入口 bump（不计 router 子图） | ✅ intent/builder/supervisor/三 agent/aggregator/critic 均 `bump_supervisor_step` |

---

## failure_paths 抽查

| 路径 | 姿态 | 抽查 |
|------|------|------|
| 总步 ≥ max | → `aggregate` · 置旗 | ✅ |
| 墙钟超时（若开） | 同→aggregate | ✅ |
| 全局耗尽仍触 critic | 禁 retry/rebind · `"end"` | ✅ |
| critic 局部 1+1（全局未耗尽） | 既有 END | ✅ 既有 `test_critic_rebind` 绿 |
| env 非法 → 无限步 | 回退 32 | ✅ |
| 误扩 T/W/P / 改 `chat/graph.py` | 拒收 | ✅ 未发生 |

---

## 40 小修

无。

---

## 残留风险

1. 默认 32 若真实金样仍紧，须回调 task/钉死表再改常量（禁静默改小）——30 已记，40 确认未改默认。
2. 墙钟为薄实现（默认关）；硬门化另跟进。

---

## 结论

**40 PASS** · verify PASS · 交 **00 · 50+CLOSE** · 未 commit/push · 未 CLOSE
