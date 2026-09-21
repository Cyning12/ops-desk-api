# Task Audit R2：supervisor-parallel-join · 签收 / 关闭

> **hat_id**：20-task-audit  
> **task**：`docs/tasks/active/task_supervisor_parallel_join.md`  
> **对照**：`docs/harness/reviews/task_supervisor_parallel_join_audit_R1_20260919.md` 回填清单（B-1）  
> **日期**：2026-09-19 · 审查人：20-task-audit  
> **分支**：`task/supervisor-parallel-join`（本帽核实）  
> **task lint**：复跑 `spec-wave task lint --file docs/tasks/active/task_supervisor_parallel_join.md` → **LINT: PASS**  
> **required_invoke_hats**：`10,30,40`（不含 20）· 本轮不另写 20 invoke  
> **task 回填**：R1 B-1 已由 10 写入验收标准 · **本帽未改** task / 人工闸表 / `app/` / `tests/`

## 结论摘要

| 维度 | 结论 |
|------|------|
| **内容** | **PASS** · 零内容阻塞 · R2 终轮 · **签收 / 关闭** |
| **流程闸** | `HG-AUDIT-R1` **仍 pending**（blocks 30）· `HG-TASK-DRAFT` / `HG-GRAPH-MODULES` 均为 pending · 本帽不代签 |
| **30 授权** | **未签发** · pending 时禁止附 30 Prompt；真值在 task 人工闸表 |

**总评**：R1 唯一硬伤（验收标准缺「旧测 grep 影响面」）已补上。七个测文件、允许改 / 必须仍绿的边界、钉死契约、三道闸均符合回填清单。不退回 10。

---

## 对照 R1 回填清单

| # | R1 要求 | R2 核对 |
|---|---------|---------|
| 1 | 「验收标准」含字面「旧测 grep 影响面」，且不能用全量 pytest 代替 | **通过**。验收条写「**旧测 grep 影响面**（本条不能用全量 pytest 代替）」；下一条再写「全量绿不能代替」 |
| 2 | 点名七个测文件 | **通过**。`test_lg_rag_multi.py` · `test_critic_rebind.py` · `test_lg_rag_supervisor_capability_catalog.py` · `test_lg_rag_structured_output_p2.py` · `test_supervisor_budget.py` · `test_lg_rag_sse_stream.py` · `test_lg_rag_sse_resume.py` 均在该条 |
| 3 | 允许改 id / 归并 / 路由 | **通过**。id：模型 `t1` → Host `subtask_id`；归并：不再拼未知 id 或重复终态；路由：若 `route_next_subtask` 不再返回单个节点名，单测改为「同批两个无依赖工人同时在飞且不共享下标」 |
| 4 | 必须仍绿：`None` 清空、`MAX_SUBTASKS=4`、SSE 顶层、`cursor`、Capability Gateway | **通过**。同条写明 `merge_subtask_results` 的 `None` 清空、cap=4、SSE 顶层字段集不增不减、`cursor` 仍由 `make_cursor(run_id, sse_seq)` 生成、`app/ops/capability/**` 无行为 diff |
| 5 | 不改钉死契约语义 | **通过**。关联键、`depends_on`、归并收齐、SSE/`cursor`、预算、run_id 缺失禁用 `t1` 与 R1 所见一致。锚点补 L235 时写明「契约不变」 |
| 6 | 三道闸仍 pending | **通过**。`HG-TASK-DRAFT` / `HG-AUDIT-R1` / `HG-GRAPH-MODULES` 均为 `pending`，未写成 approved |
| 7 | 建议补 L235 | **已做**（非硬门）。「模型别名」行现为 L235 空 allowlist 与 L269 LLM fallback 都写 `{"id": "t1", ...}` |

R1 已通过、本轮未要求重开的项（六条可测行为、非范围、R0–R5、现码锚点）保持有效。思考轮未改义，不退回。

---

## 阻塞

无。

---

## 非阻塞（不退回 · 30 知情即可）

1. **「依赖」节**仍只列三个回归测文件。验收「旧测 grep 影响面」才是清单真值；现状锚点已指向该条。30 以验收条为准，不必改依赖节。
2. **路由括号较密**：「允许改的断言 · 路由（串行下标、模型 `t1` 作关联键…）」是允许改旧断言，不是允许继续用 `t1` 当关联键。钉死契约与 id 分句仍要求改成 Host `subtask_id`。
3. **`invoke_lg_rag` 行号**仍写 L207–253（函数止于 L252）。事实不变。`blocks_hats` 仍写 `22-R1`。均不阻塞。

---

## 回填清单

无（内容零阻塞 · **未改** task 实质 · **未改**人工闸表 status）。

---

## 签收

**内容签收 / 关闭**（终轮 R2）。  
R1 B-1 已闭合。请维护者在 task 人工闸表将 `HG-AUDIT-R1` 改为 `approved` 之后，才可下发 30。本文件不附 30 Prompt。

---

## 维护者签闸（20 后 · 30 前）

- [ ] 已读 R2 审查结论
- [ ] 在 task 人工闸表将 HG-AUDIT-R1 改为 approved（维护者 · 日期）
- [ ] commit task 文档或确认已签
- [ ] 再下发 Harness 30 Prompt

30 Agent 将以 task 表为准；pending 时必须拒开工（见 TEMPLATE_30_gate_stop.md）。
