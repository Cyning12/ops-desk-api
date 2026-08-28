# Agent Infra · 长期 SPEC 包

> **用途**：LangGraph 旁路（`lg_rag` 等）之上的**应用层基础设施**契约；与单次业务 task 解耦，可跨版本迭代。  
> **状态约定**：`draft` → `active` → `stable`；破坏性契约变更升 `_vN`；升级路线写 `ROADMAP_*`，不污染 v0 已落地契约正文。  
> **上游讨论**：`docs/discussions/`（[架构对照](../../discussions/2026-08-26_lg-rag-agent-capability-architecture.md) · [阶段性总结](../../discussions/2026-08-26_agent-host-architecture-phase-summary.md)）  
> **下游落地**：须另开 `docs/tasks/active/task_*.md` + 人工闸；**本目录本身不授权 30 改码**。

---

## 文档层级（读序）

| 层 | 路径 | 写什么 | 不写什么 |
|---|---|---|---|
| **L0 总纲** | 本 README | 索引、读序、命名边界、当前状态表 | 实现细节 |
| **L0 架构** | [`00_architecture_and_boundaries.md`](./00_architecture_and_boundaries.md) | Agent / Graph / Capability / SO 边界；Mode A；静态图+动态 plan | 波次验收清单 |
| **L0 升级总表** | [`01_upgrade_roadmap.md`](./01_upgrade_roadmap.md) | Gateway 升级轨（**stable**） | 单 SPEC 契约条文 |
| **L0 Host 规划** | [`02_agent_host_plan_v0.md`](./02_agent_host_plan_v0.md) | Agent Host flesh 波次 H1–H5（**completed**） | 实现细节 |
| **L0 策略轨** | [`03_strategy_and_intent_plan_v0.md`](./03_strategy_and_intent_plan_v0.md) | Strategy Builder · Intent · Critic 再赋能（**active** · S0 签收） | 实现细节 |
| **L0 测评轨** | [`04_eval_and_observability_plan_v0.md`](./04_eval_and_observability_plan_v0.md) | 持续观测 · 可用性/准确性/稳定性 · Langfuse 边界（**active · E0 签收**） | 实现细节 |
| **L1 域夹** | `capability/` · `structured-output/` · `strategy/` · `eval/` 等 | 该域 README + 现行 SPEC + 域 ROADMAP | 跨域总序（回指 L0） |
| **L2 现行契约** | `*/SPEC-*_v0.md` | 已签收、P0–P3 已落地的接口与失败语义 | 未开工升级设想 |
| **L2 升级路线** | `*/ROADMAP_*_v0.md` | 下一波可拆 task 的升级规格 | 直接授权 30 |

```text
docs/spec/agent-infra/
├── README.md                              # L0 总纲（本文件）
├── 00_architecture_and_boundaries.md      # L0 架构边界
├── 01_upgrade_roadmap.md                  # L0 Gateway 升级（stable）
├── 02_agent_host_plan_v0.md               # L0 Host flesh（H1–H5 · completed）
├── 03_strategy_and_intent_plan_v0.md      # L0 策略轨（Strategy Builder · draft）
├── 04_eval_and_observability_plan_v0.md    # L0 测评轨（Eval · draft）
├── orchestration/                         # L1 · H1
├── session/                               # L1 · H3
├── prompt/                                # L1 · H4
├── skill/                                 # L1 · H5
├── strategy/                              # L1 · Strategy Builder
├── eval/                                  # L1 · 观测与测评
├── capability/                            # L1 域：能力网关（+ H2 ROADMAP）
│   ├── README.md
│   ├── SPEC-capability-gateway_v0.md      # L2 现行契约（P0–P3 已落地）
│   └── ROADMAP_portable_core_v0.md        # L2 升级：可迁移内核 / Mode A
├── structured-output/                     # L1 域：结构化出口
│   ├── README.md
│   ├── SPEC-structured-output-gateway_v0.md
│   └── ROADMAP_kernel_hygiene_v0.md       # L2 升级：schema 抽离等卫生项
├── SPEC-capability-gateway_v0.md          # POINTER（兼容旧链）
└── SPEC-structured-output-gateway_v0.md   # POINTER（兼容旧链）
```

**推荐读序（维护者 / 00）**：本 README → `00_architecture` → `01`（归档）→ `02`（H1–H5 归档）→ **`03` 策略** · **`04` 测评**（可并行）→ 域 ROADMAP → 开 task。

---

## 命名边界（强制）

| 名称 | 管什么 | 不是什么 |
|---|---|---|
| **Capability Gateway** | 节点 ↔ 外置能力（local_fn / MCP / sandbox / CLI / skill） | 业界 LLM Gateway；不是 LangGraph `ToolNode` 本身 |
| **Structured Output Gateway** | LLM 文本 → 校验/纠偏/预算重试 → 结构化结果 | Skill；不是模型可选 tool |
| **Strategy Builder** | 本轮可见能力/skill 白名单 + 预算策略 → state | 「更大权限的 supervisor」；不是 Policy；不直接 register |
| **Work Planner / supervisor** | 赋能集内拆 plan | 不决定本轮可见全集 |
| **Policy** | Host 执行硬闸（高危/env） | 不可由 Builder LLM 改键 |
| **Eval / Observability** | SLI 字典 · 金标 · Experiment · score；控制面默认 Langfuse | 完整自建 APM；SO Gateway 代答题评分 |
| **编排壳（StateGraph）** | 静态拓扑 + 解释 plan / allowlist | Agently Agent 的完整 1:1；默认不动态 compile 新图 |
| **LLM Gateway**（本仓另议） | 应用 ↔ 模型供应商 | 本包当前**不**立 SPEC |

---

## 当前资产状态

| ID | 现行契约 | 状态 | 升级落地（ROADMAP） |
|---|---|---|---|
| `capability-gateway` | [`capability/SPEC-capability-gateway_v0.md`](./capability/SPEC-capability-gateway_v0.md) | active · P0–P3 + portable U1–U3 | [`ROADMAP_portable_core_v0`](./capability/ROADMAP_portable_core_v0.md) · **U1–U3 DONE**（#66/#68） |
| `structured-output-gateway` | [`structured-output/SPEC-structured-output-gateway_v0.md`](./structured-output/SPEC-structured-output-gateway_v0.md) | active · P0–P3 + H1 卫生 | [`ROADMAP_kernel_hygiene_v0`](./structured-output/ROADMAP_kernel_hygiene_v0.md) · **H1 DONE**（#67）；H2 跳过 |

## Host flesh 规划（H1–H5 · completed）

| ID | 规划 | 状态 | 说明 |
|---|---|---|---|
| `agent-host-plan` | [`02_agent_host_plan_v0.md`](./02_agent_host_plan_v0.md) | **completed** · HG-SPEC-SIGNOFF approved | H1–H5 全轨 CLOSE · 2026-08-27 |

## 策略轨（active · S0 签收）

| ID | 规划 | 状态 | 首波 |
|---|---|---|---|
| `strategy-and-intent` | [`03_strategy_and_intent_plan_v0.md`](./03_strategy_and_intent_plan_v0.md) | **active** · HG-SPEC-SIGNOFF approved | **S4 DONE** [#84](https://github.com/Cyning12/ops-desk-api/pull/84) MERGED · S1–S4 实现闭环 |

## 测评轨（active · E0 签收）

| ID | 规划 | 状态 | 首波 |
|---|---|---|---|
| `eval-and-observability` | [`04_eval_and_observability_plan_v0.md`](./04_eval_and_observability_plan_v0.md) | **active** · HG-SPEC-SIGNOFF approved | **E0–E3 DONE** · **E4 开工** `eval-online-sample-scores` |

---

## 迭代规则

1. **现行契约（SPEC v0）**：只改已落地行为的勘误与修订记录；新设想进 ROADMAP。  
2. **ROADMAP**：可拆 task 的升级规格；**不**直接授权 30；落地后把「已完成」波次回写 ROADMAP + 必要时升 SPEC `_v1`。  
3. **破坏性变更**：新文件 `_vN`，本 README 换链；旧路径可留 POINTER。  
4. 与 Agently 对照只作思想对齐，禁止拖进运行时依赖。  
5. 首批接入面仍优先 `lg_rag`；**不**默认改 `chat/graph.py`。

---

## 关联

| 类型 | 路径 |
|---|---|
| 讨论 · Host 架构总结 | `docs/discussions/2026-08-26_agent-host-architecture-phase-summary.md` |
| **Host flesh 规划（H1–H5 · 归档）** | [`02_agent_host_plan_v0.md`](./02_agent_host_plan_v0.md) |
| **策略轨（Strategy Builder）** | [`03_strategy_and_intent_plan_v0.md`](./03_strategy_and_intent_plan_v0.md) |
| **测评轨（Eval · Langfuse）** | [`04_eval_and_observability_plan_v0.md`](./04_eval_and_observability_plan_v0.md) |
| Phase 4 设计 | `docs/guides/DESIGN_langgraph-lg-rag-phase4-multiagent_v1.md` |
| SO 与原生 API 并存 | `docs/guides/DESIGN_structured-output-gateway-coexistence_v0.md` |
| Capability skill 划界 | `docs/guides/GUIDE_capability-gateway-p3-skill-boundary_v0.md`（若存在） |
| 图谱前后对比 | `docs/guides/COMPARE_tech-graph-agent-infra-gateways_v0.md` |
| 实现包 | `app/ops/capability/` · `app/ops/structured_output/` |

---

## 修订记录

| 日期 | 摘要 |
|---|---|
| 2026-08-26 | 建索引；挂 capability / structured-output 两份 SPEC |
| 2026-08-26 | **细分文档层级**：L0 架构+升级总表；L1 域夹；L2 SPEC/ROADMAP；旧 SPEC 路径改 POINTER；讨论结论写入升级路线 |
| 2026-08-26 | **升级轨收官**：portable U1–U3 + SO H1 落地；H2/波次4 跳过；见 `01_upgrade_roadmap` |
| 2026-08-27 | **Host flesh 初版规划**：`02_agent_host_plan_v0` + H1–H5 域 ROADMAP；00 Prompt 草案 |
| 2026-08-27 | **策略轨落盘**：`03_strategy_and_intent_plan_v0` + `strategy/`；H1–H5 标 completed；命名边界补 Strategy Builder |
| 2026-08-27 | **测评轨落盘**：`04_eval_and_observability_plan_v0` + `eval/`；Langfuse 默认 · 混合 harness · 非完整自建 |
| 2026-08-27 | **策略轨 S0 签收**：03 + strategy ROADMAP `HG-SPEC-SIGNOFF=approved`；开 S1 `strategy-builder-allowlist` |
| 2026-08-27 | **S1 MERGED**：[#78](https://github.com/Cyning12/ops-desk-api/pull/78) allowlist 闭环 |
| 2026-08-27 | **S2 MERGED**：[#80](https://github.com/Cyning12/ops-desk-api/pull/80) Intent schema v1 |
| 2026-08-28 | **S3 MERGED**：[#82](https://github.com/Cyning12/ops-desk-api/pull/82) catalog manifest |
| 2026-08-28 | **测评轨 E0 签收**：04 + eval ROADMAP；E1 字典对照源码；下一棒 E2 |
| 2026-08-28 | 过程文档二次签收；E2–E5 分 task；00 不实现 |
| 2026-08-28 | E2 开工：`eval-goldenset-lg-rag` |
| 2026-08-28 | E2 MERGED · E3 开工：`eval-langfuse-experiment-ci` |
| 2026-08-28 | E3 MERGED · E4 开工：`eval-online-sample-scores` |
