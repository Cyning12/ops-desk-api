# Task：Capability · 可迁移内核（portable core）

> **状态**：active（闸已签 · **待 docs PR #65 merge 后派 30**）  
> **类型**：feature / agent-infra（升级轨波次 1）  
> **上游 ROADMAP**：`docs/spec/agent-infra/capability/ROADMAP_portable_core_v0.md` §U1 + §U2  
> **总轨**：`agent-infra-upgrade`  
> **分支**：`task/cap-portable-core`（**必须从最新 master**，含 #65）  
> **前置**：`agent-infra-spec-hierarchy` PR [#65](https://github.com/Cyning12/ops-desk-api/pull/65) MERGED  
> **无关**：勿与 `ops-sync-sender-migration` / `rag-answer-mixed-evidence` / `retrieval-longquery-analysis` 混改。

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `cap-portable-core` |
| **git_branch** | `task/cap-portable-core` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | `tests/test_capability_gateway.py` + `tests/test_lg_rag_multi.py` 全绿；新增/调整：默认导出无 langgraph；extras 桥可测；list+filter（node_role）单测；mock only，不连真 LLM/外网 MCP |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1` |
| **graph_delta** | `docs/_tech_graph/l1/01_modules.md` |
| **graph_delta_note** | 仅 `capability` 行备注「可迁移内核 · Mode A」；**不**新增一级模块 |
| **wiki_delta** | `n/a` |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,30` |
| **invoke_retention_profile** | `default` |
| **freeze_id** | 无 |
| **orchestration** | 总轨波次 1；合入后可穿插 `so-schema-hygiene` |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | 2026-08-26 00 代签 · 维护者 Prompt 授权 |
| HG-AUDIT-R1 | approved | 30 | 2026-08-26 00 代签；`docs/harness/reviews/task_cap_portable_core_audit_R1_20260826.md` |
| HG-GRAPH-MODULES | approved | 30 | 仅备注；不增一级（00 按仓惯例代处理） |

> **HG-SPEC-SIGNOFF**：现行 v0 已签；本 task 为 ROADMAP 升级，不重签 v0。若破坏性改默认导出需升 v1 → **停问维护者**。

---

## 背景与目标

Capability Gateway P0–P3 已落地，但默认包出口仍导出 `as_tool_node`（依赖 `langgraph.prebuilt.ToolNode`），阻碍「带走内核」。本 task 按 ROADMAP §U1 把 Mode A（`list_capabilities` + `invoke`）钉成可迁移主路径；§U2 文档化 filter / plan-in-state 契约。

**现状锚点（实现时以代码为准）**：

- 包：`app/ops/capability/`
- LG 桥：`adapters/langchain_tools.py`（`as_structured_tools` / `as_tool_node`）经 `adapters/__init__.py` 与包 `__init__.py` 默认导出
- 主路径：`lg_rag` `tool_exec` 已走 `invoke`

---

## 范围 / 非范围

**范围（U1）**：

1. `gateway` / `registry` / `types` / `adapters/local_fn`（及 mcp/sandbox/cli/skill **adapter 实现**）**不** import `langgraph`
2. 将 `langchain_tools`（ToolNode 桥）移出默认导出：建议 `app.ops.capability.extras.langchain`（或等价路径）；`__init__.py` / `adapters/__init__.py` 默认 `__all__` **不再**含 `as_tool_node` / `as_structured_tools`
3. 主路径钉死 Mode A：`list_capabilities(filter=…)` + `invoke`；`schemas_for_llm` 保留为**纯数据**（无 LG）
4. 更新引用方 import（若有从默认包取 ToolNode 桥）→ extras
5. G-L1 `capability` 备注一句「可迁移内核」
6. 单测调整：默认 import 路径不拖 langgraph；extras 仍可测

**范围（U2 · 同 task）**：

1. 文档化推荐 filter（如 `node_role` / tags / kinds 给 supervisor vs tool_exec）——可写 ROADMAP 附录或短 DESIGN（`docs/guides/`）
2. 明确：调用链是 **state 内 plan**，静态 dispatch 解释；**不** compile 新图
3. 单测：`list_capabilities` + filter 行为（已有可增强，不强制改 supervisor prompt）

**非范围**：

- 真 MCP（→ `cap-mcp-real`）
- 改 supervisor 拆解算法 / prompt（除非 U2 单测需要的极小文档对齐）
- 改 `app/ops/chat/graph.py` 拓扑
- Agently 运行时依赖
- 把 Host/SO 校验做成可选 Capability/MCP tool
- 默认动态 `StateGraph.compile`
- `so-schema-hygiene` / 波次 4
- 升 SPEC `_v1`（除非默认导出破坏性变更且维护者确认）

---

## 验收标准

- [ ] `rg -n 'langgraph' app/ops/capability` **仅**命中 extras（或零）；核心模块零命中
- [ ] `from app.ops.capability import …` 默认导出**不含** `as_tool_node` / `as_structured_tools`（或显式标 deprecated 且不 import langgraph）
- [ ] Mode A：`list_capabilities` + `invoke` 仍为 tool_exec / 规划侧主路径
- [ ] 未知 id → `ok=False`，不拖垮图（既有行为不回归）
- [ ] `pytest tests/test_capability_gateway.py tests/test_lg_rag_multi.py` 绿
- [ ] `ruff check` 触及路径绿
- [ ] `chat/graph.py` 零 diff
- [ ] U2：filter/plan-in-state 文档 + list+filter 单测可勾
- [ ] G-L1 备注 + `./scripts/graph-compile.sh`（若改图谱）exit 0
- [ ] 无 Agently；无默认 CI 外网

---

## failure_paths

| 触发 | 行为 | 可重试 |
|---|---|---|
| 未知 capability_id | `ok=False`，不中断后续子任务 | N |
| adapter 异常 | `ok=False` + error | Y（上层） |
| 误改 chat/graph 或引入 Agently | 打回 | N |
| 把 LG 桥留在默认导出 | 打回 U1 | N |
| 默认 CI 打外网 MCP | 打回 | N |

---

## 依赖

- `docs/spec/agent-infra/capability/ROADMAP_portable_core_v0.md`
- `docs/spec/agent-infra/00_architecture_and_boundaries.md` §3
- `docs/spec/agent-infra/capability/SPEC-capability-gateway_v0.md`（不改契约正文，除非勘误）
- `docs/standards/CODING_BACKEND_L2_v1_zh.md`
- `docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`
- `app/ops/capability/**` · `app/ops/lg_rag/**`（仅 import/备注必要时）

---

## 给执行帽（30）必读

1. 本 task（验收 + 非范围 + failure_paths）
2. ROADMAP §U1/U2
3. FRAGMENT_30_gate_verify · CODING_BACKEND_L2
4. 触及代码：`app/ops/capability/`（含 `__init__` / adapters）
5. **硬约束**：核心默认导出零 langgraph；Mode A 为主；未知 id → ok=False；不改 supervisor 算法；不改 `chat/graph.py`；单测 mock

---

## 思考轮

### 思考轮控制

| 字段 | 值 |
|---|---|
| **actual_last_round** | R5 |
| **early_stop** | no |
| **residual_risks** | 外部若已 `from app.ops.capability import as_tool_node` 需改 extras；破坏性默认导出是否升 v1——本 task 倾向非破坏（移出默认 + 文档指引），若测出破坏面过大则 **停问维护者** |

### R0
U1 优先去 LG；U2 同 task 降协调成本。

### R1
不新增一级模块；G-L1 仅备注。

### R2
历史 P1 ToolNode 不删实现，只降级为 extras。

### R3
未知 id 容错继承 v0；不拖垮图。

### R4
U2 不强制改 supervisor prompt，避免与拆解算法纠缠。

### R5
docs #65 未合入前不派 30，避免读序路径与 master 不一致。

---

### 自检结论

> pending · 待 #65 merge 后派 30；实现完成后由 00 机械回填

---

## 修订记录

| 日期 | 说明 |
|---|---|
| 2026-08-26 | 10 起草 U1+U2；00 代签三闸；阻塞于 docs PR #65 |
