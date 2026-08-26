# SPEC：Capability Gateway（v0 · 初版）

> **状态**：`active`（SPEC 已签收 · 实现按 task 分期）  
> **track**：`agent-infra` / capability  
> **上游讨论**：`docs/discussions/2026-08-26_lg-rag-agent-capability-architecture.md`  
> **对照思想**：Agently `Action`（Registry + Dispatcher + Executor）；**非**业界 LLM Gateway  
> **下游**：须 00 拆 task → 10/20 → `HG-AUDIT-R1` 后才可 30；本 SPEC **不**直接授权 30  
> **Open Folder（实现）**：`ops-desk-api/`  
> **建议包路径（草案）**：`app/ops/capability/`（落地时以 task 为准）

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **spec_slug** | `capability-gateway` |
| **invoke_slug** | `capability-gateway`（开 task 后启用） |
| **test_strategy** | `required` |
| **test_strategy_note** | 单元：Registry 注册/筛选/未知 id；adapter mock invoke；接入 `tool_exec_node` 后 `tests/test_lg_rag_multi.py` 不回归 |
| **graph_change_layer（建议）** | `G-L1`（`lg_rag` 备注 + 可选新模块行） |
| **freeze_id** | 无业务 HTTP freeze（旁路内部）；若暴露新 HTTP 另开 freeze |
| **默认分支（建议）** | `task/capability-gateway` |

### 人工闸（SPEC 阶段）

| human_gate_id | status | 说明 |
|---|---|---|
| **HG-SPEC-SIGNOFF** | approved | 维护者会话签收 2026-08-26；实现波次由 00 拆 task，禁止单次 30 吞 P0–P3 |

---

## 1. 背景与目标

### 背景

- Phase 4 `tool_exec_node` 使用进程内 `MOCK_TOOLS` 字典直调，无统一编目、筛选、策略、观测契约。  
- `app/tools/run_code.py` 等为 CLI/sandbox 类草稿，未接入图。  
- LangGraph 仅有 `ToolNode`（原生 tool_calls），**不能**覆盖 MCP / sandbox / skill / plan 驱动直调。  
- 讨论结论：自建 **Capability Gateway**（俗称 ToolsManager），对上给节点统一接口，对下挂多协议 adapter。

### 一句话目标

为 LangGraph（及日后其他调用方）提供 **能力注册 · 按角色筛选 · 统一 invoke · 可观测日志** 的应用层网关；首版吞掉 `MOCK_TOOLS`，预留 MCP / sandbox / skill 扩展点。

### 非目标（v0）

- 实现完整 MCP client / 生产 sandbox / 真实 GitHub API  
- 在网关内做复合问题拆解（仍属 supervisor）  
- 替换或绑架 `get_llm_provider`（那是薄 LLM Gateway）  
- 改 `app/ops/chat/graph.py`  
- 引入 Agently 运行时依赖  
- Skill 完整执行引擎（仅预留 `kind=skill` 与 provide/invoke 语义）

---

## 2. 命名与边界

```text
LangGraph 节点（编排）
        │  list / schemas_for_llm / invoke
        ▼
Capability Gateway     ◄── 本 SPEC
        │
   ┌────┼────┬─────────┐
   ▼    ▼    ▼         ▼
local  MCP  sandbox   skill(预留)
  fn  client runner   provide|invoke
```

| 术语 | 定义 |
|---|---|
| **capability_id** | 稳定字符串 id（如 `mock_get_issue_status`） |
| **kind** | `local_fn` \| `mcp` \| `sandbox` \| `cli` \| `skill` \| `other` |
| **Filter** | 按 `node_role` / `mode` / 用户策略裁剪可见集合 |
| **Invoke** | `invoke(capability_id, args, ctx) → CapabilityResult` |
| **Adapter** | 某一 `kind` 的执行后端实现 |

**与 LLM Gateway 区分**：本网关不路由模型供应商；只执行「外置能力」。

---

## 3. 契约草案（接口级 · 实现可换）

### 3.1 注册表条目（概念字段）

| 字段 | 必填 | 说明 |
|---|---|---|
| `capability_id` | Y | 唯一 |
| `kind` | Y | 见上 |
| `description` | Y | 给人 / LLM schema 用 |
| `args_schema` | N | JSON Schema 或等价；FC 暴露时必填 |
| `tags` | N | 筛选用 |
| `risk_level` | N | `low` \| `medium` \| `high`；高风险可要求 policy |
| `enabled` | Y | 默认 true |

### 3.2 Gateway 表面（最小）

```text
register(spec, adapter) -> None
unregister(capability_id) -> bool
list(*, filter: CapabilityFilter | None) -> list[CapabilitySpec]
schemas_for_llm(*, filter) -> list[dict]     # 供 bind_tools / ToolNode 可选
invoke(capability_id, args, *, ctx) -> CapabilityResult
provide(capability_id, *, ctx) -> CapabilityResult   # P3：kind=skill 注入上下文
```

`CapabilityResult` 建议字段：`ok` · `output` · `error` · `capability_id` · `duration_ms` · `meta`（可进 Langfuse）。

`provide` vs `invoke`（`kind=skill`）：前者注入上下文，后者跑可执行步骤；P3 仅 stub（`invoke` 未实现引擎），与 `docs/skills/` 人读 Skill 划界。

### 3.3 Filter（v0 最小）

| 维度 | 例 |
|---|---|
| `node_role` | `tool_exec` \| `supervisor` \| `react_subagent` |
| `mode` | `router` \| `supervisor` \| `basic` |
| `tags_any` / `kinds` | 白名单裁剪 |
| `deny_high_risk` | bool |

### 3.4 Policy（v0 仅占位）

- 未知 `capability_id` → 错误结果，**不**抛垮整图（对齐现 `tool_exec` 容错）。  
- host-only 策略键（审批、放宽 sandbox）**禁止**由模型 plan 字段写入（对齐 Agently `HOST_ONLY_POLICY_KEYS` 思想）。  
- v0 可只实现「未知 id / 执行异常 → `ok=False`」。

---

## 4. 接入面（分波）

| 波次 | 内容 | 验收草案 |
|---|---|---|
| **P0** | Registry + `local_fn` adapter；迁移 `MOCK_TOOLS`；`tool_exec_node` 改调 Gateway | multi 单测绿；行为与现 mock 等价 |
| **P1** | `schemas_for_llm` + 可选 `ToolNode` adapter（原生 FC 子图） | 单独 smoke；不强制挂主路径 |
| **P2** | MCP / sandbox / cli adapter 各至少 1 个探针实现 | 文档 + mock 单测；默认关闭 |
| **P3** | `kind=skill`：`provide()` 注入上下文 vs `invoke()` 可执行步骤 | 与 `docs/skills/` 边界文档对齐 |

---

## 5. 观测

- 每次 `invoke` 写 span（或当前 span metadata）：`capability_id` · `kind` · `ok` · `error` 截断。  
- 与现有 `trace_span("tool_exec")` 兼容，避免双根 trace。

---

## 6. 失败路径

| 触发 | 行为 | 可重试 |
|---|---|---|
| 未注册 id | `ok=False`，节点记入 `subtask_results` | N |
| adapter 异常 | `ok=False` + `error`，不中断后续子任务 | Y（上层） |
| Filter 不可见却被 invoke | 视为未注册 / blocked | N |
| Policy 拒绝 | `blocked` 状态（P1+） | 视审批 |

---

## 7. 测试策略（开 task 时细化）

- Registry：注册、重复 id、unregister、list+filter  
- local_fn：成功 / 抛错  
- 接入：`test_lg_rag_multi` 全绿；三图并存不回归  
- 禁止：真实外网 MCP/sandbox 作为默认 CI

---

## 8. 修订记录

| 日期 | 版本 | 说明 |
|---|---|---|
| 2026-08-26 | v0 | 初版：讨论落盘；P0–P3 波次；与 Agently Action / LLM Gateway 划界 |
| 2026-08-26 | v0 | `HG-SPEC-SIGNOFF=approved`；状态 `active`；本波优先落地队列：**后于** structured-output-gateway |
| 2026-08-26 | v0 | structured-output PR #58 MERGED；本 SPEC **升为当前实现优先**；由 00 拆 P0–P3 task |
| 2026-08-26 | v0 | **P0–P3 落地状态**：P0 Registry + `local_fn` + `tool_exec` 接入；P1 `schemas_for_llm` + 可选 ToolNode adapter；P2 mcp/sandbox/cli **mock 探针**（默认关闭）；P3 `kind=skill` · `provide()` 注入上下文 vs `invoke()` 可执行步骤（**stub** · 无完整引擎）+ 与 `docs/skills/` 划界（`GUIDE_capability-gateway-p3-skill-boundary_v0.md`）。分支 `task/capability-gateway` |
