# Task：Supervisor 无依赖子任务并发下发并按 Host subtask_id 归并

> **状态**：`done`（2026-09-21 归档 · 代码已在 `chore/upgrade-langgraph-1.2` 入库：`034fe7c` 并发归并 + `e80378c` ReAct 收口 + `tests/test_supervisor_parallel_join.py`；**PR 未开、未合 master**，见 `docs/HANDOFF_recent-2days_v1_zh.md` §3-P0）  
> **关联图谱**：`docs/_tech_graph/l1/01_modules.md` · `docs/_tech_graph/l1/10_flow_lg_rag.md` · `docs/_tech_graph/l1/10_flow_lg_rag.graph.yaml`  
> **落盘**：`docs/tasks/done/task_supervisor_parallel_join.md`（2026-09-21 已 `git mv` 归档）  
> **分支**：`task/supervisor-parallel-join`（自 `master` `8be477c`）  
> **类型**：feature / lg_rag supervisor 编排  
> **无关**：禁止改 `docs/tasks/active/task_tenant_readonly_predicate.md` 及其闸表  
> **00 代签位**：2026-09-19 · 00 代签 · 维护者令开启 supervisor 并发归并 · `HG-TASK-DRAFT=approved` · `HG-AUDIT-R1=approved`（审查文 R2 pass）· `HG-GRAPH-MODULES=approved`（本 task `graph_change_layer=G-L1`，确有 lg_rag 备注/flow 变更）

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `supervisor-parallel-join` |
| **git_branch** | `task/supervisor-parallel-join` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 行为变更。先写可失败单测再改分派/归并；不连真外网、不连真 LLM。编码条链 `docs/standards/CODING_BACKEND_L2_v1_zh.md` |
| **code_quality_bar** | `strict` |
| **graph_change_layer** | `G-L1` |
| **graph_delta** | `docs/_tech_graph/l1/01_modules.md` 的 lg_rag 行备注必改；拓扑从串行条件边改为一次多工人时，`docs/_tech_graph/l1/10_flow_lg_rag.md` 与 `docs/_tech_graph/l1/10_flow_lg_rag.graph.yaml` 的 dispatch/回边必改 |
| **graph_delta_note** | 不新增一级模块。无新公共方法则不扩 G-L2 indexes |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 只改 lg_rag 进程内归并契约与 G-L1 备注，不产生 coding_wiki 新条目；读序仍走既有 `docs/coding_wiki/README.md` |
| **review_hat** | `20` |
| **invoke_retention_profile** | `default` |
| **required_invoke_hats** | `10,30,40` |
| **orchestration** | `Cursor Task 链 · 00 统筹` |
| **audit_profile** | `full` |
| **semi_auto** | `false` |
| **close_pr_policy** | `required` |
| **experience_capture** | `recommended` |
| **kpi_rubric** | `KPI_RUBRIC_v1_2` |
| **kpi_aggregator** | `CLOSE` |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | approved | 22-R1, 30 | 2026-09-19 · 00 代签 · 维护者令开启 supervisor 并发归并 |
| HG-AUDIT-R1 | approved | 30 | 2026-09-19 · 00 代签 · 维护者令开启 supervisor 并发归并 · 审查文 `docs/harness/reviews/task_supervisor_parallel_join_audit_R2_20260919.md` 内容 pass |
| HG-GRAPH-MODULES | approved | 30 | 2026-09-19 · 00 代签 · 维护者令开启 supervisor 并发归并 · 本 task 确有 G-L1 变更（`lg_rag` 行备注；拓扑改一次多工人时 flow md/yaml 必改） |

---

## 背景与目标

Supervisor 今天是串行：条件边一次只返回一个节点名，工人结束后再回 dispatch，并用 `len(subtask_results)` 当下标。两个无依赖子任务不能同时在飞；后返回的结果会按到达顺序对错位。

完成态：无依赖的子任务由 Supervisor **一次下发多个工人**。各自返回后按 **Host 签发的 `subtask_id`** 归并。计划内每个 id 都有终态（成功或错误）后，才进入 aggregator。有明确前后依赖的项仍串行，不与前驱同批。模型给出的 `t1` 一类 id 只作别名，不做关联键。

---

## 现状锚点（只读 · 10 实扫 · 30 必读）

| 主题 | 路径 · 行 | 事实 |
|------|-----------|------|
| 串行拓扑 | `app/ops/lg_rag/multi/graph.py` L5–14 模块说明；L42–48 `_DISPATCH_MAP`；L78 supervisor 条件边；L79–80 三个工人都再走 `route_next_subtask` | 条件边一次一个节点名。工人结束再回来。这是串行 |
| 下标推进 | `app/ops/lg_rag/multi/nodes.py` L198–203 `_pending_subtask` | `idx = len(subtask_results)`，按下标取下一项 |
| 模型别名 | 同文件 L145–181 `_parse_subtasks`，L172 缺 id 补 `t{i+1}`；L235 空 allowlist 与 L269 LLM fallback 都写成 `{"id": "t1", ...}` | 两处都是模型别名，不能当并发关联键。契约不变：有 `run_id` 时由 Host 签发，缺失时禁用 `t1` |
| 一次一条 | 同文件 L285–298 `route_next_subtask` | 注释写明每个工人必须恰好追加一条结果，靠长度单调推进 |
| 上限 | 同文件 L52 `MAX_SUBTASKS = 4`；L160 `items[:MAX_SUBTASKS]` | 超出截断。本波不放宽 |
| RAG 会话 | 同文件 L370–372 `astream_router_agent(..., thread_id=f"lg-rag-subtask-{subtask_id or 'x'}")` | 现用结果上的 id（常为 `t1`）拼 thread。兄弟任务会串会话 |
| 归并 | `app/ops/lg_rag/state.py` L21–27 `merge_subtask_results` | `None` 清空（Critic 回环）；否则追加。不按 id 去重、不丢未知 id |
| schema | `app/ops/lg_rag/schemas/subtasks.py` L10–22 `SubtaskItem` | 字段只有 `id` / `type` / `input` / `tool` / `args`。`extra=ignore`。**没有** `depends` / `depends_on` |
| 提示词 | `app/ops/prompts/templates.py` L23–36 `lg_rag.supervisor.system` | 示例 id 为 `t1`；写「按执行顺序排列」。这不是可测依赖字段 |
| run_id 签发 | `app/ops/lg_rag/router.py` L266 `run_id = uuid.uuid4().hex`，L271–275 传入 `iter_lg_rag_sse` | 仅 stream 路径有这次 run 的 run_id |
| invoke 无 run_id | 同文件 L207–253 `invoke_lg_rag` | 不签发 run_id |
| 未进图 | `app/ops/lg_rag/sse_stream.py` L186 `rid = run_id or uuid.uuid4().hex`；L282–284 调图只传 `query` / `thread_id` / `history_turns` | SSE 用了 run_id，图入口没收到。禁止在 supervisor 内再造一套 uuid |
| cursor | `app/ops/lg_rag/sse_replay.py` L12–14 `cursor = "{run_id}:{seq}"` | 与下面的 `subtask_id` 字符串形状相同，是不同字段。SSE `seq` 在 `sse_stream.py` L188 从 0 起、每帧 +1（首帧为 1） |
| 既有 payload | `app/ops/lg_rag/progress_stream.py` L92–96 | `payload` 里已有 `subtask_id`。可继续带 Host 值。不是新 SSE 顶层字段 |
| 图谱边 | `docs/_tech_graph/l1/10_flow_lg_rag.graph.yaml`：`s_dispatch` 出边为单分支；L641–660 工人「回 dispatch（追加一条结果）」 | 描述的是串行。行号锚点相对现码可能过期，30 以现码为准 |

既有单测回归面：见下方验收「旧测 grep 影响面」（不止本段原先点名的三个文件）。

---

## 范围

- [ ] 无依赖子任务可在同一次分派里同时交给多个工人（rag / extract / tool 的既有节点）。有 `depends_on` 的项不得与任一前驱同批。
- [ ] 校验通过后由 Host 签发关联键。模型 id（含缺省补的 `t{i+1}`、fallback 的 `t1`）只写入 `alias`。
- [ ] `subtask_id = "{run_id}:{seq}"`。`run_id` 与本次 lg-rag run 已有的 run_id 同一字符串。Host `seq` 从 1 起，同一 `run_id` 内递增；Critic 回环重拆**不**从 1 重置。该计数器与 SSE `seq` **独立**，禁止为了避开字符串相同而把两者错开。
- [ ] 分派载荷必须带 `subtask_id`、`type`、`input`，以及有则 `tool` / `args`。工人返回必须原样带回同一个 `subtask_id`。计划项上若仍保留 `id`，必须等于该 `subtask_id`，禁止再放模型 id。
- [ ] 归并：id 不在本轮计划里则丢弃；该 id 已有终态则丢弃后到的重复条。收齐条件是每个计划 id 都有终态，不是 `len(subtask_results) == N`。收齐后才进 aggregator。
- [ ] `merge_subtask_results` 的 `None` → 清空 保持不变（Critic 回环）。追加路径必须满足上一条，不能无条件把未知 id / 重复终态拼进去。
- [ ] RAG 工人内部 `astream_router_agent` 的 `thread_id` 改为该 `subtask_id`（不要再加 `lg-rag-subtask-` 前缀，也不要用模型 alias）。长度远小于现有 255 截断，不另造会话 id。
- [ ] 子任务 dict 增加可选 `depends_on`（见下节）。`SubtaskItem` 今日 `extra=ignore`，不加字段则声明会被丢掉。只加这个可选字段，不改 SSE，不建表。
- [ ] 允许在 `lg_rag.supervisor.system` 增加一句：可选 `depends_on`，值指向本轮别名。单测用注入计划，不要求真 LLM 发出该字段。
- [ ] 图谱：见 `graph_delta`。只改必要备注/边。

---

## 非范围

- A2A、跨进程工人、新表、改 `lg-rag-sse-v1` 顶层字段
- 把「子读不到别人的计划」做成安全隔离。本波只保证归并键正确。工人仍可能读到父 state
- 不改 Capability Gateway 行为（`app/ops/capability/**` 无行为 diff）
- 不放宽 `MAX_SUBTASKS`（仍为 4）
- 不改总步默认 32 的定义；不改 `chat/graph.py`
- 不动 `docs/tasks/active/task_tenant_readonly_predicate.md`
- 不把 `subtask_id` 写入 SSE `cursor`；不把 SSE `seq` 与 Host `seq` 合成一个计数器
- 不把提示词里的「按执行顺序排列」解释成隐式依赖

---

## 10 钉死契约（00/30 不得静默改义）

### 关联键

| 项 | 钉死 |
|----|------|
| 签发者 | Host。不用 LLM 的 id |
| 形状 | `subtask_id = "{run_id}:{seq}"`，`seq` 从 1 起 |
| run_id 真源 | stream：`router.py` 已签发的那个值，经 `iter_lg_rag_sse` **传入图**。禁止 supervisor / 节点内再 `uuid` |
| invoke | 今日无 run_id。30 在 `invoke_lg_rag` 用与 stream 相同的 `uuid.uuid4().hex` 签发**一次**再传入。这是对齐既有签发，不是第二套 id |
| 别名 | 模型 `id`，缺省时现码补的 `t{i+1}`，写入 `alias`。fallback 单 rag 在 run_id 存在时同样由 Host 签发，`alias` 可为 `t1` |
| 载荷 | 必含 `subtask_id`、`type`、`input`；有 tool/args 则带上。返回原样带回同一 `subtask_id` |
| RAG thread | `thread_id` 等于该 `subtask_id` |

### 依赖判定（现码没有等价机制，不叠第二套）

现码没有 `depends` / `depends_on`。列表顺序和提示词「按执行顺序排列」**不是**依赖。

字段名：`depends_on`（可选，只加在子任务 dict / `SubtaskItem`）。

| 值 | 含义 |
|----|------|
| 缺省 / `null` / `[]` | 无依赖。可与其他无依赖项同批下发 |
| `list[str]` | 每一项必须解析到**本轮计划内另一项**。只允许两种写法：已签发的 `subtask_id`，或该项的 `alias`（模型 id / `t{i+1}`） |
| 指向自身、计划外、无法解析、成环 | 非法。见失败路径 |

签发顺序：先给通过校验且未超 cap 的项签发 `subtask_id`，模型 id 写入 `alias`，再解析 `depends_on`。模型输出时只能写 alias（它不知道 Host id）。解析后，该项的等待集合必须是本轮已签发 id。

有依赖的项：所有前驱都有终态之后才下发，**不得**与任一前驱同批。前驱的错误终态也算终态，后继可以在此后下发。非法依赖项本身不派工人。

### 归并与收齐

- 终态：保留结果带本轮计划内的 `subtask_id`，且含 `output` 或 `error`（有其一即可）。两者都没有的返回，Host 将该次分派写成带 `error` 的终态，避免收齐挂起。
- 未知 id：丢弃，不计入收齐，不按下标塞进别的项。
- 已有终态的 id：后到的重复条丢弃，不覆盖。
- 收齐：本轮计划中每个已签发 id 都有恰好一条保留终态。然后才进 aggregator。禁止用结果列表长度等于 N 当作收齐。
- 本轮计划 = 本次签发的 id 集合。Critic 清空结果后的新计划只用新 id 收齐；旧 id 不在新计划里。

### SSE 与 cursor

- 禁止把 `subtask_id` 写入 SSE `cursor`。`cursor` 仍只由 `make_cursor(run_id, sse_seq)` 生成。
- 禁止改 `lg-rag-sse-v1` 顶层字段（`run_id` / `seq` / `ts_ms` / `agent_role` / `event_type` / `payload` / `cursor`）。
- 既有 `payload.subtask_id` 可带 Host 值。
- 两个 `seq` 计数器独立。字符串都可能是 `{run_id}:1`，靠字段区分，不靠改计数起点。

### 预算（不改定义，防止并行挂起）

`MAX_SUBTASKS` 仍为 4。总步默认 32 的定义不改。预算耗尽后不再开新批次；已在飞的仍按 id 归并；尚未终态的计划 id 由 Host 写入错误终态，再走既有「耗尽 → aggregate」（不直跳 END）。

### run_id 缺失

图内签发前读不到非空 `run_id`：不签发、不派工人、**不**把 `t1` / `tN` 写成关联键。放一条无 Host id 的错误结果（`error` 说明 run_id 缺失）后走既有 aggregate。禁止静默 fallback 成 `id=t1` 再去跑 rag。

---

## 失败路径（failure_paths）

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----------|----------|--------|----------|
| `HG-AUDIT-R1` pending 即 30 改码 | 执行 Agent **拒开工** | 是 | 内部拒派。无新 SSE 字段 |
| 返回的 id 不在本轮计划 | 丢弃该条，不按下标写入 | 否 | 不进入综合。无新 SSE 字段 |
| 同一计划 id 已有终态又来一条 | 丢弃后到条，不覆盖 | 否 | 已终态结果不改口。已发出的既有 progress 帧不撤回。无新字段 |
| 工人执行失败（异常或 `error`） | 该计划 id 占一条错误终态；收齐不因此卡住 | 否（该工人） | 既有 aggregator 能读到该 `error` 文本。无新 SSE 字段 |
| 工人漏带 `subtask_id`，或与分派值不一致 | 该条丢弃。Host 按分派记录给该 id 写错误终态。禁止用下标补位 | 否 | 同上，既有 `error` 文本。无新字段 |
| `depends_on` 成环，或指向计划外 / 无法解析 | 涉事项不派工人，各写错误终态。禁止把非法依赖当成无依赖去并行 | 否 | 既有 `error` 文本。无新字段 |
| 计划项超过 `MAX_SUBTASKS`（4） | 只对前 4 项签发并下发；第 5 项不签发 | 否 | 最多 4 条子任务结果。无新字段 |
| 签发时 `run_id` 缺失或空白 | 不签发、不用 `t1`、不派工人；一条错误结果后进 aggregator | 是（补上本次 run 的 run_id 再跑） | 既有综合里的错误文本，或日志。禁止新 SSE 字段。若整次失败，只能用既有 invoke `ok: false` 外壳或既有 `event_type=error` |
| 实现把 `subtask_id` 写入 `cursor`，或增删 `lg-rag-sse-v1` 顶层字段 | 审查 / verify 拒收 | 是（回滚） | 无（内部） |
| 总步预算耗尽时仍有未终态计划 id | 不再下发新批次；未终态 id 补错误终态后再 aggregate | 否 | 既有耗尽后的综合。无新字段 |

---

## 验收标准

- [ ] 两个互不依赖的子任务同批在飞时，各自绑定不同的 `subtask_id`，不会都读到 `len(subtask_results)` 的同一个下标。单测在 `tests/test_lg_rag_multi.py` 或邻接新文件
- [ ] 后返回的结果按 `subtask_id` 对上计划项，不按到达顺序错位
- [ ] 同一 id 的第二条终态不覆盖第一条
- [ ] 未知 id 被丢弃，且不使收齐被长度凑齐
- [ ] 带合法 `depends_on` 的项不与前驱同批；前驱终态之后才下发
- [ ] 工人失败写入错误终态后，计划仍能收齐并进入 aggregator
- [ ] `run_id` 缺失时结果关联键不是 `t1` / `tN`，且没有派工人
- [ ] 超过 4 项的计划只签发 4 个 `subtask_id`（`MAX_SUBTASKS` 常量仍为 4）
- [ ] RAG 工人 `astream_router_agent` 的 `thread_id` 等于该 `subtask_id`，两个兄弟任务的 thread 不同
- [ ] `format_sse_event` / `make_cursor` 仍用 SSE `seq` 写 `cursor`；单测证明不得把 `subtask_id` 写入 `cursor`。顶层字段集不增不减。`payload.subtask_id` 允许是 Host 值
- [ ] **旧测 grep 影响面**（本条不能用全量 pytest 代替）。点名：`tests/test_lg_rag_multi.py` · `tests/test_critic_rebind.py` · `tests/test_lg_rag_supervisor_capability_catalog.py` · `tests/test_lg_rag_structured_output_p2.py` · `tests/test_supervisor_budget.py` · `tests/test_lg_rag_sse_stream.py` · `tests/test_lg_rag_sse_resume.py`。允许改的断言：id（计划/结果关联键从模型 `t1` 改为 Host `subtask_id`）；归并（不再把未知 id 或重复终态拼进列表）；路由（串行下标、模型 `t1` 作关联键；若 `route_next_subtask` 不再返回单个节点名，对应单测改为「同批两个无依赖工人同时在飞且不共享下标」）。必须仍绿：`merge_subtask_results` 的 `None` 清空、`MAX_SUBTASKS=4`、SSE 顶层字段集不增不减、`cursor` 仍由 `make_cursor(run_id, sse_seq)` 生成、Capability Gateway 行为不变（`app/ops/capability/**` 无行为 diff）
- [ ] 全量与 CI 一致：`.github/workflows/pytest.yml` 的 `run` 为 `.venv/bin/pytest tests -q --tb=short`（无 marker 裁剪；注释里的 intent marker **未启用**）。本地等价 `pytest tests -q --tb=short`。主题可先跑上条点名文件，验收勾选以全量为准。全量绿不能代替「旧测 grep 影响面」
- [ ] 若改了模块备注或 flow：CLOSE 前 `./scripts/graph-compile.sh` 通过。10 不跑 compile、不改图谱
- [ ] `npx --yes spec-wave task lint-wiki-delta --target .` 通过
- [ ] `app/ops/capability/**` 无行为 diff；`docs/tasks/active/task_tenant_readonly_predicate.md` 无 diff
- [ ] 触及 Python 通过 `ruff check`（路径至少含 `app/ops/lg_rag` 与本次新增/修改的 `tests`）。条链 `docs/standards/CODING_BACKEND_L2_v1_zh.md`

---

## 依赖

- 编码规范：`docs/standards/CODING_BACKEND_L2_v1_zh.md`
- 图谱：`docs/_tech_graph/l1/01_modules.md` · `docs/_tech_graph/l1/10_flow_lg_rag.md` · `docs/_tech_graph/l1/10_flow_lg_rag.graph.yaml`
- 闸片段：`docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`
- 00 开工：`docs/harness/invokes/by-task/supervisor-parallel-join/invoke_20260919_00_start.md`
- 回归测：`tests/test_lg_rag_multi.py` · `tests/test_lg_rag_sse_stream.py` · `tests/test_lg_rag_sse_resume.py`
- CI：`.github/workflows/pytest.yml`

---

## 给执行帽的必读列表

1. `AGENTS.md`
2. 本 task 全文，尤其「10 钉死契约」与失败路径。30 首输出先对照 `docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`；`HG-AUDIT-R1` 仍为 pending 则拒开工
3. `docs/standards/CODING_BACKEND_L2_v1_zh.md`
4. 代码锚点：`app/ops/lg_rag/multi/graph.py` · `app/ops/lg_rag/multi/nodes.py` · `app/ops/lg_rag/state.py` · `app/ops/lg_rag/schemas/subtasks.py` · `app/ops/lg_rag/router.py` · `app/ops/lg_rag/sse_stream.py` · `app/ops/lg_rag/sse_replay.py` · `app/ops/prompts/templates.py`
5. 图谱：`docs/_tech_graph/l1/01_modules.md` · `docs/_tech_graph/l1/10_flow_lg_rag.md`
6. 过程 invoke：`docs/harness/invokes/by-task/supervisor-parallel-join/`
7. 20 审查落盘 `docs/harness/reviews/`（`audit_profile=full`）。20 不在 `required_invoke_hats` 留档集合内，与 `default` 一致

一次路由如何同时指向多个工人，由 30 选型。task 不指定框架 API 名。可观察契约只看：同批两个无依赖工人同时在飞，且不共享下标。

---

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|----|------|------------|----------------------|----------------|
| R0 | 缺口是串行下标，不是缺 SSE 字段 | no | — | none |
| R1 | 进程内同批下发 + 按 Host id 归并；依赖只认显式字段 | no | — | none |
| R2 | 现码无 depends；新增可选 `depends_on`；顺序不是依赖 | no | — | 提示不改则模型不会自发写该字段；单测注入覆盖 |
| R3 | run_id 用 stream 已有值传入图；缺失失败，禁用 t1；cursor 隔离 | no | — | invoke 今日无 run_id，须在入口签一次 |
| R4 | 收齐按计划 id 终态集，不按长度；失败也占终态；cap 仍为 4 | no | — | none |
| R5 | G-L1 备注必改；扇出则 flow 与 graph.yaml 必改；无新公共方法则不扩 G-L2 | no | — | 多目标 API 由 30 选型；兄弟任务不做状态隔离 |

**actual_last_round**：R5 · **early_stop**：no · **residual_risks**：见 R2 / R3 / R5 行

### R0 · 问题框定

`graph.py` L78–80 与 `route_next_subtask` 一次只选一个节点；`_pending_subtask` 用结果条数当下标。并发时两个工人会抢下标 0。目标是归并键，不是新事件协议。

### R1 · 边界

一次下发多个既有工人，仍在本进程 StateGraph 内。不做 A2A、不改 Gateway、不改 SSE 顶层字段、不把计划隔离当安全需求。有显式依赖的项保持串行，避免一刀切并行。

### R2 · 依赖从哪来

`SubtaskItem` 无依赖字段，且 `extra=ignore`。提示词「按执行顺序排列」不可测，不能当成依赖，否则无依赖项也无法同批。本波只认可选 `depends_on`，合法值只能指向本轮已签发 id 或 `alias`。

### R3 · run_id 与 cursor

stream 的 run_id 在 `router.py` L266，但 `sse_stream.py` L282 没传进图。必须接上这一字符串，禁止节点内再 uuid。`invoke_lg_rag` 没有 run_id，只允许在该入口用同一种 `uuid.uuid4().hex` 签一次。图内仍缺失则失败，不许退回 `t1`。`sse_replay.py` 的 cursor 与 `subtask_id` 形状相同，字段必须分开，seq 计数器独立。

### R4 · 收齐

`merge_subtask_results` 今天只追加。未知 id、重复终态都会把长度凑乱。收齐改为「每个计划 id 一条终态」。工人失败、漏带 id、非法依赖都要占终态或丢弃后补终态，否则 aggregator 进不去。cap 仍是前 4 项。

### R5 · 图谱

`01_modules.md` 的 lg_rag 行要写明并发下发 + 按 id 归并，不新增一级模块。若实现把「一次返回一个节点名」改成一次多工人，`10_flow_lg_rag.md` 与 `10_flow_lg_rag.graph.yaml` 的 dispatch 出边和工人回边必须改。现有符号已在 G-L2 indexes 里；不新增公共方法就不扩 indexes。

---

## 实现备忘（子 Agent 回填）

| 项 | 状态 | 备注 |
|----|------|------|
| 10 起草 task | ✅ | 2026-09-19 · 闸未签 |
| 20 审查 | ✅ | 审查文 R2 pass；闸已在人工闸表 `approved`（本行只记事实，30 不改闸） |
| 30 实现 | ✅ | 2026-09-19 · Host `subtask_id` 签发；无依赖 `Send` 同批；`subtask_join` 按 id 收齐；`depends_on` 串行。未 commit |
| 40 verify | ✅ | 2026-09-19 · 点名 pytest 84 passed；lint-wiki-delta 与 graph-compile exit 0。全量未勾：`tests/test_chat_ws.py` 两条既有失败，不在本 diff |
| 图谱 | ✅ | `01_modules.md` lg_rag 备注 + `10_flow_lg_rag` dispatch/回边；`./scripts/graph-compile.sh` exit 0。未改闸 status |

---

## 测试策略（Harness）

**test_strategy**: `required`

- 先单测再改分派与归并。用注入的计划与假工人，不调用真模型。
- 全量命令与 `.github/workflows/pytest.yml` 一致，见验收节。无 marker 裁剪。

---

### 自检结论（执行者）

2026-09-19 · hat **40** 独立自检 · 分支 `task/supervisor-parallel-join`（`git branch --show-current`）· 未 commit / 未 push。人工闸三行仍为 task 表原 `approved`，本帽未改 status。

工作目录：仓根。命令与退出码（本帽真跑）：

| 命令 | 退出码 | 摘要 |
|------|--------|------|
| `.venv/bin/pytest tests/test_supervisor_parallel_join.py tests/test_lg_rag_multi.py tests/test_critic_rebind.py tests/test_lg_rag_supervisor_capability_catalog.py tests/test_lg_rag_structured_output_p2.py tests/test_supervisor_budget.py tests/test_lg_rag_sse_stream.py tests/test_lg_rag_sse_resume.py -q --tb=line` | **0** | **84 passed**，1 warning，1.59s |
| `npx --yes spec-wave@3.0.0 task lint-wiki-delta --target .`（与 `.github/workflows/lint-wiki-delta.yml` 一致） | **0** | `LINT-WIKI-DELTA: PASS` · scanned=117 · issues=0 |
| `./scripts/graph-compile.sh` | **0** | check OK · mermaid normalize ok（词汇 Warning 不咬 exit） |
| `.venv/bin/ruff check app/ops/lg_rag tests/test_supervisor_parallel_join.py tests/test_lg_rag_multi.py tests/test_lg_rag_structured_output_p2.py tests/test_lg_rag_supervisor_capability_catalog.py tests/test_supervisor_budget.py tests/eval/test_eval_agent_golden.py` | **0** | All checks passed |

验收摘要（有命令或源码抽查才标 pass）：

| # | 验收 | 结论 |
|---|------|------|
| 1 | 无依赖同批、不同 `subtask_id`、不共享下标 | **pass** · `test_parallel_workers_do_not_share_index` / `test_route_fans_out_two_independent_workers` 含于 84 passed |
| 2 | 后返回按 `subtask_id` 对齐 | **pass** · `test_late_result_joins_by_id_not_arrival_order` |
| 3 | 同 id 第二条终态不覆盖 | **pass** · `test_merge_drops_unknown_and_duplicate_terminal` |
| 4 | 未知 id 丢弃，不靠长度凑齐 | **pass** · 同上，断言集合等于计划且 `len==2` |
| 5 | 合法 `depends_on` 不与前驱同批，前驱终态后才下发 | **pass** · `test_route_dependent_not_in_same_batch` / `test_depends_on_waits_for_predecessor_terminal` |
| 6 | 工人失败占错误终态后仍进 aggregator | **pass** · `test_worker_error_is_terminal_and_reaches_aggregator` |
| 7 | `run_id` 缺失不用 `t1`/`tN`、不派工人 | **pass** · `test_missing_run_id_does_not_dispatch_t1` |
| 8 | 超过 4 项只签发 4 个 id；`MAX_SUBTASKS` 仍为 4 | **pass** · `test_host_seq_not_reset_and_cap_four`；源码 `MAX_SUBTASKS = 4` |
| 9 | RAG `thread_id` 等于该 `subtask_id`，兄弟不同 | **pass** · `test_rag_thread_id_equals_subtask_id` |
| 10 | `cursor` 仍 `make_cursor(run_id, sse_seq)`；不把 `subtask_id` 写入 cursor | **pass** · `test_cursor_is_sse_seq_not_subtask_id`；`sse_replay.py` diff 0 字节；调用点为 `make_cursor(rid, seq)` |
| 11 | 旧测 grep 影响面（点名文件） | **pass** · 上表 pytest 含全部点名文件，exit 0 |
| 12 | 全量 `pytest tests` 与 CI 一致且全绿 | **不勾 pass** · 本帽未重跑全量。抽查：`git diff` 不含 `tests/test_chat_ws.py` 与 `app/ops/chat/**`；两处源码无 `lg_rag` / `subtask_id`。记为「仓内既有失败，非本 task 验收」。不因此打回 30 |
| 13 | 改了图谱则 `graph-compile` 通过 | **pass** · exit 0 |
| 14 | `lint-wiki-delta` | **pass** · exit 0 |
| 15 | `app/ops/capability/**` 无行为 diff；`task_tenant_readonly_predicate.md` 无 diff | **pass** · 上述路径 `git diff` 0 字节 |
| 16 | 触及 Python `ruff check` | **pass** · exit 0 |

非范围抽查：`MAX_SUBTASKS` 仍为 4；`make_cursor` 签名与调用均未写入 `subtask_id`；Capability Gateway 与 `task_tenant_readonly_predicate.md` 无 diff。

已知未测项：本帽未重跑 `.venv/bin/pytest tests -q --tb=short`。`tests/eval/test_eval_agent_golden.py` 仅注入 `run_id`，未单独跑（ruff 已覆盖该文件）。未改闸、未 commit、未 push。结论：**不打回 30**。

---

### KPI（00）

Task_KPI%: 80

| 维 | 分 | 依据 |
|----|----|------|
| 闸与委派 | 5 | 10→20 退回→10 回填→20 R2→代签→verify PASS 后才派 30。00 未改 `app/`、`tests/` |
| 主题验收 | 4 | 40 对点名 pytest / graph-compile / lint-wiki-delta 有退出码。全量 `pytest tests` 未绿（`tests/test_chat_ws.py` 两条，不在本 diff） |
| 关账 | 2 | 维护者令不 commit、不 push，故无 PR。`task close` 干跑为 `CLOSE: BLOCKED` |

---

### 经验总结

（`experience_capture: recommended` · 关账可选）

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-09-19 | 10-task 首稿。锚点按现码行号。闸三行 pending，未代签 |
| 2026-09-19 | 按 R1 B-1 补旧测 grep 影响面。顺手补锚点 L235 空 allowlist 的 `t1`（契约语义未改） |
| 2026-09-19 | 30 实现：Host id 同批下发与按 id 归并。验收勾选未全勾（chat WS 两条既有失败） |
| 2026-09-21 | 代码随两日集中开发入库 `chore/upgrade-langgraph-1.2`（脱离 specwave 过程，见 HANDOFF）；task 归档 active→done；PR 待开 |
