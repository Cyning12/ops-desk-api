# Task：LangGraph lg_rag Phase 1（基础单 Agent 旁路）

> **状态**：active（draft · 待人审）  
> **类型**：feature / Agent 框架落地（LangGraph 旁路）  
> **总纲**：`docs/guides/PLAN-langgraph-agent-framework_v1.md`  
> **实现说明书**：`docs/guides/IMPL_langgraph-lg-rag-phase1_v1.md`（S0–S9，本 task 的 30 手写说明书）  
> **上游资产**：`app/ops/lc_evidence_chain/`（`ainvoke_evidence_answer`，黑盒复用）  
> **实现仓**：本仓（Open Folder = 本仓根）  
> **建议分支**：`task/lg-rag-phase1`（当前 `task/rag-embed-api-backend` 已 CLOSE，须另切）  
> **无关**：勿与 `task_ops_sync_sender_migration`（GHA sync sender）混改。

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `lg-rag-phase1` |
| **git_branch** | `task/lg-rag-phase1` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | mock `ainvoke_evidence_answer` 的单测（不连库/LLM 可绿）；CLI 冒烟需真 db+向量+LLM，本地手动执行；Golden 对齐为抽样级 A（同 query 直连 vs 图 answer 一致） |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1` |
| **graph_delta** | `docs/_tech_graph/l1/01_modules.md` |
| **graph_delta_note** | 增一行 `lg_rag`：LangGraph 旁路单 Agent（START→rag→END）；黑盒复用 `lc_evidence_chain`；默认不进入 chat/graph |
| **wiki_delta** | `n/a` |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,30` |
| **orchestration** | 单 task；IMPL 即 30 说明书 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | 2026-08-19 维护者会话直签（「签收，进行下一步」）：确认 MessagesState 方案与 Phase 1 范围 |
| HG-AUDIT-R1 | approved | 30 | 2026-08-19 维护者会话直签：省略独立 20 R1 审查轮（IMPL 即 30 说明书，范围小） |
| HG-GRAPH-MODULES | approved | 30 | 2026-08-19 已登记 `lg_rag` 于 `docs/_tech_graph/l1/01_modules.md`（含人签记录行） |

---

## 背景与目标

总纲 PLAN 已定 LangGraph 为 Agent 框架方向；LCEL 旁路 `lc_evidence_chain` 已稳定（含 tracing / hardening / HTTP freeze）。Phase 1 把它封装为**最小 LangGraph 单 Agent 旁路**：`START → rag_node → END`，state 用内建 `MessagesState`（`messages` + `add_messages` reducer），**不进现网 Chat SSE**，CLI/库级可跑通并带 Checkpointer 快照。

**完成态**：

- [x] `app/ops/lg_rag/` 填实：`__init__.py`（export）· `nodes.py`（`rag_node`）· `graph.py`（`build_basic_agent` / `ainvoke_basic_agent`）
- [x] state 采用 langgraph 内建 `MessagesState`（`LgRagState` 薄子类；草稿自定义 Pydantic 方案已废弃）
- [x] `InMemorySaver` 冒烟通过；同 `thread_id` 二次 invoke messages 续写（mock 单测 2→4 条）
- [x] Langfuse：tag / `run_name`=`lg-rag` 执行树可见（API 实证：`name=lg-rag`、tags=[lc-evidence-chain, lg-rag]、session=thread_id；修复内层 run_name 抢占，改用 `propagate_attributes`）
- [x] `scripts/lg_rag_smoke.py` CLI 冒烟（含 `--parity`；真链 exit 0）
- [x] `tests/test_lg_rag_basic.py` mock 单测绿（3 passed）
- [x] Golden 级别 A：严格相等对非确定 LLM 不适用（维护者 2026-08-19 确认「不一致属正常」）；判定改为 mock 恒等 + 真链引用重叠（`--parity` 已实跑通过）
- [x] G-L1 登记 + `./scripts/graph-compile.sh` 通过；`git diff master -- app/ops/chat/graph.py` 为空

---

## 范围（本仓）

1. **S0 骨架**：填实 `app/ops/lg_rag/__init__.py` / `graph.py`；包可 import（`from app.ops.lg_rag import build_basic_agent`）。
2. **State 定义（第一步，本次用户点名先落盘）**：`MessagesState` 方案——直接用内建或薄子类；`messages` 走 `add_messages` reducer，node 返回增量列表。清理/改写现有草稿 `state.py` 与 `nodes.py`（后者含错误导入 `langchain.graph`，应为 `langgraph.graph`）。
3. **S1 依赖**：确认 `langgraph>=0.2,<0.3` 已装；`InMemorySaver` 可用。`langgraph-checkpoint-postgres` **本波可后置**（见非范围）。
4. **S2 `rag_node`**：黑盒调 `ainvoke_evidence_answer`；`ChainResult.answer` 用属性访问；不复制 retrieve SQL / grader / prompt。
5. **S3 图组装**：`StateGraph(MessagesState)` + `START`/`END` 显式边（风格对齐 `app/ops/chat/graph.py`）；`build_basic_agent(checkpointer=None)` 默认 `InMemorySaver`；`ainvoke_basic_agent(query, thread_id=...)` 截断 thread_id ≤255。
6. **S4 Langfuse**：`ainvoke_basic_agent` 注入 `_trace_config`（CallbackHandler + tags/session_id + run_name=`lg-rag`）+ `trace_span`；不改 Chat service。
7. **S6 冒烟脚本** `scripts/lg_rag_smoke.py`：`--query` / `--thread-id`；tracing on 时 `flush_traces()`。
8. **S7 单测** `tests/test_lg_rag_basic.py`：mock chain 断言追加 AIMessage；可选同 thread_id 两次 invoke 断言 messages 增长。
9. **S8 Golden 级别 A**：抽样 N 条 parity 断言（脚本或单测均可）；**不改** `evals/golden/run_eval.py` 主语义。
10. **S9 图谱**：`docs/_tech_graph/l1/01_modules.md` 增 `lg_rag` 行；`graph-compile.sh` 通过。

---

## 非范围（Phase 1 明确不做）

- Router / 条件边（Phase 2）；rewrite / evaluate 循环（Phase 3）
- 挂 `POST /api/ops/chat/stream`（避免搅动现网 SSE；旁路 CLI/库级即可）
- 改 `lc_evidence_chain` 内部拓扑（黑盒复用）
- 改 `app/ops/chat/graph.py`（硬约束）
- `PostgresSaver` / `langgraph-checkpoint-postgres`（可后置到 Phase 1 尾或另开 task；若做须处理 asyncpg→psycopg DSN 与 `setup()` 建表）
- 全量 73 条 golden「答问通过率」（另开 eval 入口 / 下个 task）

---

## 依赖

| 项 | 说明 |
|---|---|
| 总纲 | `docs/guides/PLAN-langgraph-agent-framework_v1.md` |
| 说明书 | `docs/guides/IMPL_langgraph-lg-rag-phase1_v1.md`（S0–S9） |
| 上游链 | `app/ops/lc_evidence_chain/chain.py` · `ainvoke_evidence_answer` · `types.ChainResult` |
| tracing | `app/ops/tracing`（`ensure_langfuse_environment` / `trace_span` / `tracing_enabled` / `flush_traces`） |
| 风格对照 | `app/ops/chat/graph.py`（START/END 显式边；**只读不改**） |
| 编码规范 | `docs/standards/CODING_BACKEND_L2_v1_zh.md` |
| 运行时 | `langgraph>=0.2,<0.3`（已在 requirements/pyproject） |

---

## 实施步骤（建议 · 30）

1. 切分支 `task/lg-rag-phase1`。
2. 落盘 state：按 IMPL 采用 `MessagesState`；改写/删除草稿 `state.py` 的 `LgRagState`；修正 `nodes.py` 错误导入。
3. `nodes.py` `rag_node` + `graph.py` `build_basic_agent` / `ainvoke_basic_agent`（InMemorySaver 默认）。
4. `__init__.py` export；import 自检。
5. Langfuse 注入 + smoke 脚本；本地真链冒烟一次。
6. mock 单测 + 级别 A parity 抽样。
7. G-L1 登记 + `graph-compile.sh`；确认 `git diff master -- app/ops/chat/graph.py` 空。
8. PR 前：`ruff check` 触及文件 + `pytest tests/test_lg_rag_basic.py -q`。

---

## 验收标准

- [x] `.venv/bin/python -c "from app.ops.lg_rag import build_basic_agent"` 通过
- [x] state 为 `MessagesState` 薄子类 `LgRagState`；`messages` 增量 reducer 语义正确
- [x] 本地真链 `ainvoke_basic_agent('自动压缩被取消怎么办')` 返回非空 answer（含证据引用）
- [x] 同 `thread_id` 二次 invoke：state.messages 含上一轮 Human+AI（InMemorySaver 续写）
- [x] Langfuse UI 可见 tag `lg-rag` / run_name `lg-rag` 执行树（Langfuse API 复查确认 name/tags/session 正确；树形 root lg-rag → rag → lc-evidence-chain 完整）
- [x] `pytest tests/test_lg_rag_basic.py` 绿（3 passed，mock 不连库）
- [x] 级别 A：按维护者确认「LLM 生成不一致属正常」调整判定——封装无损由 mock 恒等单测确定性证明；真链 parity 改断言双侧非空 + 引用证据标识重叠（实测 overlap=[2720]，exit 0）
- [x] `git diff master -- app/ops/chat/graph.py` 为空；`lc_evidence_chain` 无改动
- [x] G-L1 `01_modules.md` 含 `lg_rag` 行；`./scripts/graph-compile.sh` exit 0
- [x] `ruff check` 触及路径绿

---

## failure_paths

| 触发 | 行为 | 可重试 | 用户可见 |
|---|---|---|---|
| chain 内部失败（db/LLM/embed） | `rag_node` 异常上抛，ainvoke 失败 | Y | CLI 非零退出 / 调用方异常 |
| messages 中无 HumanMessage | `rag_node` raise ValueError | Y | 明确报错 |
| thread_id 过长 | 截断 ≤255 | Y | 无感 |
| Langfuse 未配置 | tracing off，图正常执行（nullcontext） | Y | 无 trace |
| 误改 chat/graph 或 chain 内部 | 验收打回 | N | PR 拒绝 |
| PG checkpointer DSN 误用 asyncpg（若提前做 S5） | 连接失败；本波默认不做 | Y | 文档已列坑 |

---

## 给执行帽必读（本仓）

1. 本 task（仓内 active 为执行真值）
2. `docs/guides/IMPL_langgraph-lg-rag-phase1_v1.md`（30 说明书 S0–S9）
3. `docs/guides/PLAN-langgraph-agent-framework_v1.md`（Phase 1 验收对照）
4. `app/ops/lc_evidence_chain/chain.py` · `types.py`（ChainResult 字段）
5. `app/ops/chat/graph.py`（风格对照 · 只读）
6. `app/ops/tracing`（Langfuse 约定）
7. `docs/standards/CODING_BACKEND_L2_v1_zh.md`

---

## 思考轮

### 思考轮控制

| 字段 | 值 |
|---|---|
| **actual_last_round** | R3 |
| **early_stop** | yes（IMPL 已含 S0–S9 细节，本草稿仅做对齐与闸化） |
| **residual_risks** | 现有未跟踪草稿 `state.py`/`nodes.py` 与 IMPL 方案冲突，30 须先清理；InMemorySaver 仅进程内，重启丢快照（PG 后置已知悉）；级别 A parity 对温度/随机性敏感，必要时规范化后比较。 |

### R0
IMPL 明写「无 approved task 禁改码」；本 task 即补齐此前置。

### R1
Phase 1 state 采用内建 `MessagesState`，草稿 `LgRagState`（Pydantic 自定义）与说明书冲突，落盘时以说明书为准。

### R2
PG checkpointer 后置不挡 Phase 1 验收；asyncpg DSN 坑已记入 failure_paths。

### R3
硬约束复核：不动 chat/graph.py、不拆 chain、落 `app/ops/lg_rag/` 既有空壳。

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-19 | 初版（AI 起草 · 待 HG-TASK-DRAFT 人审）：依据 IMPL S0–S9；用户点名第一步先落盘 state 定义 |
| 2026-08-19 | 维护者会话签收三闸；切 `task/lg-rag-phase1`；落盘第一步：`state.py`（`LgRagState`=`MessagesState` 薄子类）+ 修正 `nodes.py` 错误导入 + G-L1 登记 |
| 2026-08-19 | 修复 Langfuse trace 命名：内层 LCEL CallbackHandler 在其根 run `update_trace(name="lc-evidence-chain")` 抢占 trace 名（后置 `update_current_trace` 抢不回）；改用官方 `propagate_attributes(trace_name=...)` 包裹 ainvoke，API 实证 name=`lg-rag`；验收项转 [x] |
| 2026-08-19 | 维护者裁定级别 A：LLM 生成不一致属正常；`--parity` 判定改为双侧非空 + 引用标识重叠（`_extract_refs`），实跑 overlap=[2720] exit 0；验收项转 [x] |
| 2026-08-19 | 30/40 按 IMPL 顺序填实：S2 `rag_node` + S3/S4 `graph.py`（InMemorySaver + Langfuse 注入）+ S0 export + S7 mock 单测（3 passed）+ S6 冒烟脚本（真链 exit 0）；级别 A 严格相等受 LLM 非确定影响标 [~]；全量 pytest 204 passed / 3 failed（chat_ws/router 因本地测试库缺 `ops_knowledge_chunks` 表，与本改动无关，待人工复核） |
