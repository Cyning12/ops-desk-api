# Task Audit R1：supervisor-parallel-join · 退回 10-task

> **hat_id**：20-task-audit  
> **task**：`docs/tasks/active/task_supervisor_parallel_join.md`  
> **日期**：2026-09-19 · 审查人：20-task-audit  
> **分支**：`task/supervisor-parallel-join`（本帽核实 · `git branch --show-current` · HEAD `8be477c`）  
> **task lint**：本帽复跑 `spec-wave task lint --file docs/tasks/active/task_supervisor_parallel_join.md` → **LINT: PASS**（机械闸不查 K7）  
> **required_invoke_hats**：`10,30,40`（不含 20）· 本轮不另写 20 invoke  
> **task 回填**：有内容阻塞 · **未改** task 正文 / 人工闸表 / `app/` / `tests/`

## 结论摘要

| 维度 | 结论 |
|------|------|
| **内容** | **退回 10-task** · 1 项内容阻塞（验收标准缺「旧测 grep 影响面」） |
| **流程闸** | `HG-AUDIT-R1` **仍 pending**（blocks 30）· `HG-TASK-DRAFT` / `HG-GRAPH-MODULES` 均为 pending · 本帽不代签 |
| **30 授权** | **未签发** · 本轮禁止开工 · 本文件不附 30 Prompt |

**总评**：钉死契约、失败路径、非范围、思考轮与现码锚点（抽查四文件及邻接锚点）可执行，**不构成**退回理由。本 task 自标「行为变更」，并改 fallback（禁用 `t1` 作关联键）与归并语义；验收标准没有字面项「旧测 grep 影响面」。按 20 checklist（K7）此项缺则退回 10 补列，禁止指示 30。

---

## 审查核对

| # | 审查点 | 结论 |
|---|--------|------|
| 1 | 验收能测到六条行为 | **通过**（见下）。阻塞不在这些条本身 |
| 2 | Host `subtask_id="{run_id}:{seq}"`；不用模型 `t1` 作关联键；alias 可留；分派带 `subtask_id`/`type`/`input` 及有则 `tool`/`args`；工人原样带回；收齐按计划 id 终态，不是 `len==N` | **通过**。「10 钉死契约 · 关联键 / 归并与收齐」与范围条一致 |
| 3 | RAG `thread_id` 用 `subtask_id` | **通过**。范围与验收均写：等于该 `subtask_id`，去掉 `lg-rag-subtask-` 前缀，不用 alias |
| 4 | 非范围 | **通过**。无 A2A、无跨进程、无新表、不改 `lg-rag-sse-v1` 顶层字段、不做安全隔离、不改 Capability Gateway、`MAX_SUBTASKS` 仍为 4；另钉不改总步 32、不改 `chat/graph.py`、不动兄弟 task、不把两个 `seq` 合成一个计数器 |
| 5 | 依赖 | **通过**。无 `depends_on` / `null` / `[]` 可同批；合法前驱终态后才下发、不得同批；列表顺序与提示词「按执行顺序排列」明文不是依赖。新字段可测（验收「带合法 `depends_on`」+ failure_paths 成环/计划外）。`SubtaskItem` 现码确无该字段且 `extra=ignore` |
| 6 | `cursor` 与 `subtask_id` | **通过**。形状都可是 `{run_id}:{seq}`；禁止写入 `cursor`；两计数器独立、禁止错开起点。验收要求单测证明 `make_cursor` 仍用 SSE `seq` |
| 7 | 元信息 / failure_paths / 思考轮 | **通过**。`graph_change_layer=G-L1` · `review_hat=20` · `test_strategy=required` · failure_paths 表覆盖闸拒开工、未知 id、重复终态、工人失败占终态、漏带 id、非法依赖、cap=4、run_id 缺失、cursor/SSE 误改、预算耗尽补终态。R0–R5 控制表与正文回填闭合；`early_stop=no`；`actual_last_round=R5`；residual 在 R2/R3/R5 |
| 8 | 现状锚点 vs 现码 | **通过**（抽查，见下节）。无「按错锚点改」级不符。一处漏列见非阻塞 |
| 9 | 行为变更 · 旧测 grep 影响面（K7） | **阻塞**。`test_strategy_note` 写「行为变更」；改校验后的关联键与 `merge_subtask_results` 追加语义、以及 `t1` fallback。验收标准全文无「旧测 grep 影响面」。现状锚点只点 3 个测文件，盖不住会改断言的旧测 |

### 核对 1 · 六条行为均在「验收标准」

| 行为 | task 落点 |
|------|-----------|
| 同批不共用下标 | 验收第 1 条：两个互不依赖项各绑不同 `subtask_id`，不得都读 `len(subtask_results)` |
| 后到按 id 不错位 | 验收第 2 条 |
| 重复 id 不覆盖已终态 | 验收第 3 条；failure_paths 同行 |
| 未知 id 丢弃 | 验收第 4 条：丢弃且不得用长度凑齐 |
| 依赖链不并行 | 验收第 5 条：合法 `depends_on` 不与前驱同批 |
| 失败工人占终态、收齐不卡住 | 验收第 6 条；钉死「两者都没有则 Host 写成带 `error` 的终态」 |

### 核对 8 · 现码抽查（只读）

| task 锚点 | 现码 | 判定 |
|-----------|------|------|
| `graph.py` L5–14 串行说明；L42–48 `_DISPATCH_MAP`；L78 条件边；L79–80 三工人再走 `route_next_subtask` | 一致。条件边一次一个节点名 | 相符 |
| `nodes.py` L198–203 `_pending_subtask` 用 `len(results)` 当下标 | L202 `idx = len(results)` | 相符 |
| L145–181 `_parse_subtasks`；L172 缺 id 补 `t{i+1}` | L172 `item.id or f"t{i + 1}"` | 相符 |
| L269 fallback `id: t1` | L269 同字面 | 相符。另见非阻塞 L235 |
| L285–298 `route_next_subtask` 要求每个工人恰好追加一条、靠长度推进 | L290–291 注释同义；返回单个 `str` | 相符 |
| L52 `MAX_SUBTASKS = 4`；L160 `items[:MAX_SUBTASKS]` | 一致 | 相符 |
| L370–372 `thread_id=f"lg-rag-subtask-{subtask_id or 'x'}"` | 一致 | 相符 |
| `state.py` L21–27 `None` 清空，否则追加；不按 id 去重 | 一致 | 相符 |
| `schemas/subtasks.py` L10–22 仅 `id/type/input/tool/args`，`extra=ignore`，无 `depends_on` | 一致 | 相符 |
| `templates.py` L23–36 示例 `t1`、L34「按执行顺序排列」 | 一致 | 相符 |
| `router.py` L266 `run_id`；L271–275 传入 `iter_lg_rag_sse`；L207–252 `invoke_lg_rag` 不签发 run_id | 一致（task 写到 L253，函数止于 L252，差空行） | 相符 |
| `sse_stream.py` L186 `rid = run_id or uuid`；L188 `seq=0` 后每帧 +1；L282–284 调图只传 `query` / `thread_id` / `history_turns` | 一致。`ainvoke_supervisor_agent` / `astream_supervisor_agent` 均无 `run_id` 参数 | 相符 |
| `sse_replay.py` L12–14 `cursor = "{run_id}:{seq}"` | 一致 | 相符 |
| `progress_stream.py` L92–96 `payload` 已有 `subtask_id` | 一致 | 相符 |
| `10_flow_lg_rag.graph.yaml` L641–660「回 dispatch（追加一条结果）」 | L643 / L650 / L657 标签一致。`s_dispatch` 在 yaml 有四条条件出边（L597–639），运行时一次只选一条，与「串行」陈述一致。task 已写行号可能过期、30 以现码为准 | 相符 |
| CI | `.github/workflows/pytest.yml` L47 为 `.venv/bin/pytest tests -q --tb=short`；L49 marker 行已注释 | 相符 |

---

## 阻塞项（内容 · 退回 10-task）

### B-1 · 「验收标准」缺「旧测 grep 影响面」

本 task 是行为变更：改分派（一次一节点 → 同批多工人）、改归并（无条件追加 → 未知 id / 重复终态丢弃）、改 fallback（`id=t1` 不得再当关联键）。20 checklist 要求验收标准含字面项「旧测 grep 影响面」，缺则退回。`task lint` 不查此项。

现状锚点只列：

- `tests/test_lg_rag_multi.py`
- `tests/test_lg_rag_sse_stream.py`
- `tests/test_lg_rag_sse_resume.py`

只读 grep 显示，关联键从 `t1` 换成 Host id、或 `merge_subtask_results` 不再无条件追加时，至少这些既有测的断言会动，且未进入验收：

| 文件 | 为何算影响面 |
|------|----------------|
| `tests/test_critic_rebind.py` | `test_subtask_results_reducer_append_then_none_clears` 断言未知第二条被追加；`None` 清空必须仍绿 |
| `tests/test_lg_rag_supervisor_capability_catalog.py` | 多处断言计划 `id` 为 `t1`（含 fallback） |
| `tests/test_lg_rag_structured_output_p2.py` | 解析出口断言 `id=t1` |
| `tests/test_supervisor_budget.py` | `route_next_subtask` 断言单一返回值 `"rag_subtask"` / `"aggregate"`。task 允许 30 自选多目标 API，旧断言可能必须改，须写明允许改什么 |
| `tests/test_lg_rag_multi.py` | 已在锚点。另有 `subtasks == [{"id": "t1", ...}]` 与 `len(subtask_results)==N` |
| `tests/test_lg_rag_sse_stream.py` · `tests/test_lg_rag_sse_resume.py` | 已在锚点。SSE 顶层字段与 `cursor` 必须仍绿，须与「允许改的 id 断言」分开写 |

**修订要求（只改 task，10-task 做）**：在小节「验收标准」增加一条，标题含字面「旧测 grep 影响面」，点名上表文件，并写清两类边界：

- 允许改的断言：计划/结果关联键从模型 `t1` 改为 Host `subtask_id`；归并不再把未知 id 或重复终态拼进列表；若 30 改变 `route_next_subtask` 返回形状，对应单测改为「同批两个无依赖工人同时在飞且不共享下标」
- 必须仍绿、禁止为了新语义改掉的行为：`merge_subtask_results(…, None)` 仍清空；`MAX_SUBTASKS` 仍为 4；`lg-rag-sse-v1` 顶层字段不增不减；`cursor` 仍只由 SSE `seq` 生成；`app/ops/capability/**` 无行为 diff

不要把「全量 pytest 绿」代替这一条。全量命令已在验收里，不够充当影响面清单。

---

## 非阻塞（10 回填 B-1 时可顺手写 · 单独不退回）

1. **第二处 `t1`**：`nodes.py` L235 空 allowlist 也写 `{"id": "t1", ...}`，锚点表只引 L269。契约已要求一切 fallback 在有 `run_id` 时由 Host 签发、缺失时禁用 `t1`。建议在「现状锚点」补 L235，避免 30 只改 L269。
2. **`invoke_lg_rag` 行号**：函数止于 L252，task 写 L207–253。事实（不签发 run_id）正确。
3. **HG-TASK-DRAFT `blocks_hats`**：仍写 `22-R1`。V2 审查帽是 20-task-audit。与既有 task 口径相同，不阻塞。

思考轮 **不退回**。R0–R5 不必重开，除非 10 为写清旧测边界而改了契约语义（不应改）。

---

## 回填清单（给 10-task · 只改 task）

- [ ] **验收标准**：补「旧测 grep 影响面」一条（B-1）。点名 `tests/test_lg_rag_multi.py` · `tests/test_critic_rebind.py` · `tests/test_lg_rag_supervisor_capability_catalog.py` · `tests/test_lg_rag_structured_output_p2.py` · `tests/test_supervisor_budget.py` · `tests/test_lg_rag_sse_stream.py` · `tests/test_lg_rag_sse_resume.py`。写明允许改的 id/归并/路由断言，以及必须仍绿的 `None` 清空、cap=4、SSE 顶层、`cursor`、Capability Gateway
- [ ] **现状锚点**（建议）：补 `nodes.py` L235 空 allowlist `id: t1`
- [ ] 不改人工闸表 status（三行保持 pending）
- [ ] 不改钉死契约语义来迁就旧测
- [ ] 修订后重跑 `spec-wave task lint`，再送 20-task-audit R+1
- [ ] **禁止**在 R+1 通过前下发 30

---

## 维护者签闸（20 后 · 30 前）

- [ ] 已读 R1 审查结论（本轮退回 10-task · 内容未过 · 待 R+1）
- [ ] 在 task 人工闸表将 HG-AUDIT-R1 改为 approved（维护者 · 日期）——本轮不要签；须 10 回填且 R+1 内容零阻塞之后
- [ ] commit task 文档或确认已签
- [ ] 再下发 Harness 30 Prompt

30 Agent 将以 task 表为准；pending 时必须拒开工（见 TEMPLATE_30_gate_stop.md）。
