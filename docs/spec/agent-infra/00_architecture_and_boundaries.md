# Agent Infra · 架构与边界（L0）

> **层级**：L0 架构（跨域）  
> **状态**：`active`（2026-08-26 讨论结论落盘；**不**授权 30）  
> **配套**：[`01_upgrade_roadmap.md`](./01_upgrade_roadmap.md) · 域 SPEC / ROADMAP

---

## 1. 一句话分层

```text
编排壳（StateGraph.compile · 静态拓扑）
    │  list / invoke / parse_only / acomplete_structured
    ├─ Capability Gateway     ← 外置能力（可插拔插件）
    └─ Structured Output GW   ← 结构化出口（Host 权威 · 非可选 tool）
         │
    LLM Provider（薄 · 另议）  ← 模型供应商，不是能力网关
```

| 层 | 职责 | 默认不做什么 |
|---|---|---|
| **编排壳** | 节点何时调谁；失败后条件边 / fallback / END | 动态为每请求 `compile` 新图 |
| **Capability** | 注册 · 筛选 · 统一 `invoke` · adapter | 复合问题拆解；路由模型供应商 |
| **Structured Output** | extract → repair → schema →（可选）纠偏重试 | 业务答案质量评分；Skill |
| **LLM Provider** | `complete` | 工具执行 |

---

## 2. 与 Agently 的对照（非 1:1）

| Agently | 本仓近似 | 差异 |
|---|---|---|
| Agent 实例 | `StateGraph.compile()` + 会话/thread | Agent ≈ 会话+Action+Prompt+DataFlow；Graph ≈ **固定拓扑状态机** |
| `@func` / Action 注册 | `capability.register(spec, adapter)` | 同属 Registry 思想 |
| `use_actions` 挂载 | 构图时接到执行节点 + `list(filter)` 给 planner | 能力在 **build 前**注册，不是改已 compile 图 |
| output-control DataFlow | Structured Output Gateway | 有契约节点**强制**走 Host 管道 |
| Skill | `kind=skill` provide/invoke（stub） | 与 `docs/skills/` 人读 Skill 划界 |

---

## 3. Capability 挂载模式（选型钉死）

| 模式 | 做法 | 本仓态度 |
|---|---|---|
| **A · Registry + 节点 `invoke`** | 进程注册；planner/tool_exec 按 id 调用 | **默认 · 可迁移主路径** |
| **B · `bind_tools` + `ToolNode`** | LangGraph 原生 FC 环 | **非主路径**；可选桥须隔离出核心导出 |
| C · 每能力一 node | 静态 `add_node` | 能力少时可；扩展性差 |

**可迁移硬约束**：`app/ops/capability/` **内核**不得依赖 `langgraph`；FC/`ToolNode` 桥若保留，须在 `extras` / 可选适配层，不得污染默认包出口。

---

## 4. Planner · 赋能列表 · 「调用链」是不是新图？

功能完整 Agent（非 demo）推荐：

```text
静态图：planner → dispatch ⇄ workers(tool_exec/rag/…) → aggregator → END
              ↑____________________|
```

- Planner 读 `capability.list(filter=…)`（赋能列表）→ 产出 **plan 数据**（子任务列表 / 调用链描述）。  
- 「调用链」落在 **state**，由固定 `dispatch` 解释执行。  
- **默认不会**每个请求动态 `StateGraph().compile()` 出一张新图。  
- 真·动态构图列为非目标（难观测、难 checkpoint、难迁移）。

心智模型：

```text
Agent 运行时 ≈  compiled StateGraph（编排壳）
            +  Capability Gateway（可插拔赋能）
            +  Structured Output Gateway（结构化出口）
            +  Planner 节点（读赋能列表 → 写 plan → 继续或结束）
```

### 4.1 Strategy Builder · Intent · 再赋能（H1–H5 之后）

> 详规：[`03_strategy_and_intent_plan_v0.md`](./03_strategy_and_intent_plan_v0.md) · [`strategy/`](./strategy/)  
> **现状**：S1 allowlist + S2 Intent + S3 catalog manifest 已落地；S4 Critic→rebind **进行中**（`task/critic-rebind`）。

目标分层（仍 Mode A · 静态图）：

```text
Intent（细 schema）→ Strategy Builder（写 allowlist 入 state）
    → Work Planner / supervisor（只读可见集拆 plan）
    → workers → Critic
         │                │
         └─ 同 catalog ───┘
         └─ 能力缺口 → 回 Builder（rebind）
```

| 层 | 职责 |
|---|---|
| **Strategy Builder** | 本轮可见 capability/skill + 预算策略 → state；**不是**更大权限的 supervisor |
| **Policy** | Host 硬闸；Builder 不可改键 |
| **Work Planner** | 赋能集内拆 plan（现 `supervisor_node`） |
| **Critic** | 质量/能力缺口分流；先窄后宽 |

- 全量目录可由 **YAML/manifest** 动态加载注册；Builder **只裁剪、不注册**。  
- Intent：现 `router` 三路可作外层闸；更灵活靠 **LLM + SO 细意图**，业务耦合迁出硬编码 prompt。

---

## 5. Structured Output 触发方式

- **节点显式调用**，不是图中间件自动套所有 LLM 输出。  
- 有结构化契约的节点必须走 Gateway；失败后业务 fallback 仍由节点写（如单 rag），并标 `structured_output_fallback`。  
- **禁止**把 Host 校验做成模型可跳过的 Capability/MCP tool。

### 两条 API（与接入选型）

| API | LLM | 适用 |
|---|---|---|
| `parse_only` | 无 | 节点已 `complete` 一次后只校验（**lg_rag 现状**，避免双重 LLM） |
| `acomplete_structured` | 有；失败则 OUTPUT CORRECTION 完整重生成 | 新调用方或日后节点合并 complete+校验 |

纠偏路径的 LLM = Gateway 经 `llm_ctx` / `get_llm_provider` 的**独立调用**，不是「上一个 node 对象」。

---

## 6. 正交与组合

```text
（可选）Strategy Builder 写 allowlist
        │
supervisor 拆 plan（Structured Output 校验 plan · tool id ∈ 可见集）
        │
        ▼
tool_exec → Capability.invoke（再经 Policy）
rag_sub   → lc_evidence（黑盒）
extract   → Structured Output 校验抽取结果
```

先结构化 plan，再 invoke 能力——允许；两网关**不互相替代**。  
Strategy Builder 与 Policy **不互相替代**（裁可见集 ≠ 执行硬闸）。

### 6.1 观测与测评（正交）

> 详规：[`04_eval_and_observability_plan_v0.md`](./04_eval_and_observability_plan_v0.md)

- **运行时事实** → Langfuse traces / metadata（已有 `app/ops/tracing.py`）。  
- **判定** → 仓内 Eval harness（金标、确定性评估器）+ Langfuse Scores / Datasets / Experiments。  
- SO Gateway **不做**业务答案质量分；准确性测评属 Eval / Critic / grader。  
- 默认**不**双开 LangSmith；基础设施可用性用 Prometheus/日志互补。

---

## 7. 修订记录

| 日期 | 说明 |
|---|---|
| 2026-08-26 | 初版：会话讨论结论落盘（Mode A、静态图+plan、SO 触发与纠偏边界） |
| 2026-08-27 | §4.1：Strategy Builder / Intent / Critic 再赋能；与 H1–H5 缺口对齐 |
| 2026-08-27 | §6.1：Eval/Observability 与 Langfuse 边界；挂 04 |
| 2026-08-27 | §4.1 现状：S1 allowlist Builder 已落地；S2/S4 仍缺口 |
| 2026-08-27 | §4.1 现状：S2 Intent 已落地；S3/S4 仍缺口 |
| 2026-08-28 | §4.1 现状：S3 catalog manifest 已落地；S4 仍缺口 |
| 2026-08-28 | §4.1 现状：S4 Critic rebind 开工（`task/critic-rebind`） |
