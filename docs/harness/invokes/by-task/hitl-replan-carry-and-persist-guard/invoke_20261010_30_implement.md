# Harness 30 实现 invoke — hitl-replan-carry-and-persist-guard

- task：docs/tasks/active/task_hitl_replan_carry_and_persist_guard.md
- R1 审查：docs/harness/reviews/task_hitl_replan_carry_and_persist_guard_audit_R1_20261010.md（PASS 零阻塞）
- worktree：ops-desk-api-worktrees/t-hitl-carry-and-persist-guard（分支 task/hitl-carry-and-persist-guard · base master bdd45f9）
- 日期：2026-10-10 · 帽位：30 实现

## GATE_VERIFY（首输出 · 开工前已跑）

| 项 | 结果 |
| --- | --- |
| npx spec-wave verify | EXIT=0 · VERIFY: PASS |
| HG-TASK-DRAFT | approved |
| HG-AUDIT-R1 | approved |
| HG-GRAPH-MODULES | approved（图谱在册 · 本文 00 代录形态随行） |

授权：三闸 approved · 30 开工。

## 实现范围（钉死）

1. **replan 保号**：supervisor replan 三路径对 P=hitl_unlocked_ids∩未解决步骤保留原 subtask_id（LLM 新步骤照常盖章新 id · 空 unlocked 逐字节零 diff · 禁授权面扩大）。
2. **persist 建单前检查**：_persist_hitl acreate 前查 (run_id, subtask_id) 有无新鲜 approved 单据（复用消费门同一 TTL/归一/blocked_by 守卫 · 禁第二份实现）；读异常 fail-open 照建单 + hitl_persist_guard_read_failed warning（键名钉死）。

## 改动清单

**app/ops/lg_rag/multi/nodes.py**（实现 · T1/T2 既有函数零改）：
- `_unlocked_preserved_rows(state, locked)` :746 — P=hitl_unlocked_ids∩plan行∩无终态∩非locked → dict(row) 副本带回
- `_stamp_host_plan(..., preserved=None)` :630 — full=locked+preserved+plan · cap 计入 preserved · prefix/recoverable 仍仅随 locked · 空 preserved 逐字节不变
- supervisor_node 接线 :1013（空 allowlist 短路）:1091（统一收口）— `preserved=_unlocked_preserved_rows(state, locked)` 两处传入 · fallback-carry 路径零改（P⊆未解决后缀自然含于 _carry_plan）
- `_approved_fresh_for_subtask(state, *, subtask_id, capability_id)` :1560 — 建单检查：复用消费门同一 `_decided_at_ts` 归一/TTL(`OPS_HITL_APPROVAL_CONSUMPTION_TTL_SECONDS`)/blocked_by 守卫（禁第二份实现）· 读异常 fail-open False + `hitl_persist_guard_read_failed` warning :1581
- `_persist_hitl` 接线 :1679 — 命中新鲜 approved → `hitl_persist_guard_skip` info + continue（不产新行不伪造行）

**tests/test_hitl_approval_consumption.py**（测试 · 新增 TB 段 :616-1100）：
- 辅助：_guard_row/_guard_state/_llm_returning/_new_step_suffix/_five_keys_bytes/_persist_scenario + 导入扩展（json/SimpleNamespace/AsyncMock/patch · nodes 增 _unlocked_preserved_rows/supervisor_node）
- TB 枚：TB1×1 :668 · TB2×2 :702/:730 · TB3×2 :750/:777 · TB4×1 :835 · TB5×1 :869 · TB6×7 :976-1100（含 Db store 组 :1066）

**docs/_tech_graph/l1/01_modules.md**（图谱）：lg_rag 行备注（T4 段）+ 在册行（00 代录形态）

## TB 逐项验收

| TB | 断言 | 结果 |
| --- | --- | --- |
| TB1 正常路径保号 | ids==[s1,s2,run:3] · 保号行逐键==原行 · seq==3 · prefix==[s1] · recoverable==1 | PASS |
| TB2 fallback 保号 | LLM RuntimeError → _carry_plan 沿用 ids==[s1,s2] · seq 不变 | PASS |
| TB2 空 allowlist 短路 | allowed=[] 不调 LLM · ids==[s1,s2] · prefix/recoverable 不变 | PASS |
| TB3 变异反例 control | 非 unlocked 未解决步不回带 · 新计划 ids==[s1,run:3] | PASS |
| TB3 双终态防御（FP-8） | unlocked 但有终态 → _unlocked_preserved_rows==[] 且不在新计划 | PASS |
| TB4 空 unlocked 逐字节 | 键缺失 vs 显式空列表双跑五键（subtasks/seq/prefix/recoverable/修剪面）逐字节全等 + golden 字面钉 | PASS |
| TB5 全链收口 | consume-hit→resume→真 supervisor_node replan 保号 [sid,run:2]→消费门台账→令牌→tool_exec→done==planned==1·unsatisfied False | PASS |
| TB6① 命中跳过 | 新鲜 approved → created==[] · store 零新增 pending · skip 日志 | PASS |
| TB6② 对照照建 | 无 approved → 照建 1 条 pending | PASS |
| TB6③ 超 TTL 照建 | decided_at 过期 → 不匹配照建（镜像消费门 TTL） | PASS |
| TB6④ 缺 capability_id 键 | 旧单据缺键 → 不匹配照建（不扩面 · 前置断言确为缺键） | PASS |
| TB6⑤ 单据类型守卫 | blocked_by=prefix_touch_required 的 approved → 不匹配照建 | PASS |
| TB6⑥ fail-open | alist 抛异常 → 照建 + `hitl_persist_guard_read_failed` warning | PASS |
| TB6⑦ Db store 组 | DbHitlStore 真读（decided_at ISO str 归一）命中 → 跳过建单 · 前后清理 | PASS |
| TB7 回归面 | 见验证留证（107 passed） | PASS |
| TB8 环境性红 | 见验证留证（4 红=master 基线同名同数 · 零新增红） | PASS |

## 验证留证

- **B1 冲突面亲跑**（TB7）：`pytest tests/test_react_observe.py tests/test_hitl_approval_consumption.py tests/test_hitl_auto_resume.py` → **107 passed**（exit 0 · T1 34+T2 39 面 + N-3 定位枚全含）
- **全量 pytest**（TB8）：**4 failed, 1762 passed, 1 skipped**（65s）——4 红=test_capability_lookups×3 + test_lg_rag_multi::test_unknown_tool_at_invoke_recorded_and_continues，与钉死 master 基线环境性红同名同数（delegation env 系）→ **零新增红**；.env 与主仓 diff 一致（ENV_IDENTICAL）
- **ruff 零新增**：nodes.py 6 处告警与 git show master 对拍同 6 类（I001×2/F401 CapabilityFilter/C401/UP045×2）→ 零新增；测试文件修 E731 后 All checks passed
- **graph-compile**：EXIT=0（图谱回写后复跑仍 0）
- **task lint**：`npx spec-wave task lint --file docs/tasks/active/task_hitl_replan_carry_and_persist_guard.md` → **LINT: PASS** exit 0
- **TB 新增 14 枚全绿**（1+2+2+1+1+7）（-k tb 收集跑 · 含 Db skipif 组实操-B）

## 留转 40 清单

1. **live 全链**（done{completed} 正面收口）：resume→replan 保号→消费→真执行→completed 整链以真服务实跑留证（本帽 TB5 已以真图 InMemorySaver+真 supervisor_node/tool_exec_node 覆盖同链单元级 · 40 补 HTTP/SSE 层 live）。
2. Db store 组 TB6⑦ 依赖本地 PostgreSQL（DB_AVAILABLE skipif）——40 live 环境应实跑非 skip。
3. 4 红 master 基线环境性（delegation env 系）非本 task 引入 · 40 复核口径不变。
